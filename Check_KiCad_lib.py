"""
KiCad Library Checker
Validates component data against online databases
Requires Python 3.9+
"""

import os
import sys
import json
import requests
import re
from pathlib import Path
from typing import Optional
import time

class ComponentChecker:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = requests.Session()
        self.results = []
        
    def parse_kicad_library(self, lib_path: str) -> list[dict]:
        """Parse KiCad symbol library (.kicad_sym format)"""
        components = []
        
        with open(lib_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        current_symbol = None
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # New symbol definition
            if '(symbol "' in line:
                match = re.search(r'\(symbol\s+"([^"]+)"', line)
                if match:
                    if current_symbol:
                        components.append(current_symbol)
                    current_symbol = {
                        'name': match.group(1),
                        'properties': {},
                        'manufacturers': [],
                        'line_number': i + 1
                    }
            
            # Property extraction
            elif current_symbol and '(property "' in line:
                prop_match = re.search(r'\(property\s+"([^"]+)"\s+"([^"]*)"', line)
                if prop_match:
                    prop_name = prop_match.group(1)
                    prop_value = prop_match.group(2)
                    current_symbol['properties'][prop_name] = prop_value
        
        if current_symbol:
            components.append(current_symbol)
        
        # Extract manufacturers from properties
        for comp in components:
            props = comp['properties']
            mfg_list = []
            
            # Look for Mfg1, Mfg2, Mfg3, etc.
            i = 1
            while f'Mfg{i}' in props or f'Mfg{i} pn' in props:
                mfg_name = props.get(f'Mfg{i}', '')
                mfg_pn = props.get(f'Mfg{i} pn', '')
                if mfg_pn:  # Only add if part number exists
                    mfg_list.append({
                        'name': mfg_name,
                        'pn': mfg_pn
                    })
                i += 1
            
            comp['manufacturers'] = mfg_list
            
        return components
    
    def check_octopart(self, mpn: str, manufacturer: str = "") -> dict:
        """Check component on Octopart API"""
        if not self.api_key:
            return {'error': 'No API key provided'}
        
        url = "https://octopart.com/api/v4/rest/parts/search"
        headers = {
            'Token': self.api_key,
            'Content-Type': 'application/json'
        }
        
        query = {
            'q': mpn,
            'limit': 5
        }
        
        try:
            response = self.session.get(url, headers=headers, params=query, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return self.parse_octopart_response(data, mpn, manufacturer)
            else:
                return {'error': f'API returned status {response.status_code}'}
        except Exception as e:
            return {'error': str(e)}
    
    def check_snapeda(self, mpn: str) -> dict:
        """Check component on SnapEDA (no API key required for basic search)"""
        url = f"https://www.snapeda.com/api/v1/parts/search"
        params = {'q': mpn}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    return {
                        'found': True,
                        'source': 'SnapEDA',
                        'matches': len(data['results'])
                    }
            return {'found': False, 'source': 'SnapEDA'}
        except Exception as e:
            return {'error': str(e)}
    
    def parse_octopart_response(self, data: dict, mpn: str, manufacturer: str) -> dict:
        """Parse Octopart API response"""
        results = data.get('results', [])
        
        if not results:
            return {'found': False, 'source': 'Octopart'}
        
        # Find exact match
        for result in results:
            part = result.get('part', {})
            part_mpn = part.get('mpn', '')
            part_mfg = part.get('manufacturer', {}).get('name', '')
            
            if part_mpn.upper() == mpn.upper():
                # Extract specs with normalized names
                specs = {}
                raw_specs = {}
                for spec in part.get('specs', []):
                    attr_name = spec.get('attribute', {}).get('name', '')
                    display_val = spec.get('display_value', '')
                    raw_specs[attr_name] = display_val
                    
                    # Normalize common spec names
                    attr_lower = attr_name.lower()
                    if 'resistance' in attr_lower and 'capacitance' not in attr_lower:
                        specs['resistance'] = display_val
                    elif 'capacitance' in attr_lower:
                        specs['capacitance'] = display_val
                    elif 'voltage' in attr_lower and 'rating' in attr_lower:
                        specs['voltage_rating'] = display_val
                    elif 'power' in attr_lower and ('rating' in attr_lower or 'watt' in attr_lower):
                        specs['power_rating'] = display_val
                    elif 'tolerance' in attr_lower:
                        specs['tolerance'] = display_val
                    elif 'temperature' in attr_lower and 'coefficient' in attr_lower:
                        specs['temperature_coefficient'] = display_val
                
                return {
                    'found': True,
                    'source': 'Octopart',
                    'mpn': part_mpn,
                    'manufacturer': part_mfg,
                    'description': part.get('short_description', ''),
                    'specs': specs,
                    'raw_specs': raw_specs,
                    'datasheet': part.get('best_datasheet', {}).get('url', '')
                }
        
        return {'found': False, 'source': 'Octopart', 'similar_parts': len(results)}
    
    def verify_component(self, component: dict) -> dict:
        """Verify a single component against online databases"""
        props = component['properties']
        value = props.get('Value', '')
        component_type = self.detect_component_type(component['name'], props)
        
        # Extract parameters from symbol name (e.g., "CAP_0402_1p_6.3V_NP0_5%")
        name_params = self.parse_symbol_name(component['name'])
        
        result = {
            'name': component['name'],
            'line': component['line_number'],
            'manufacturers': component.get('manufacturers', []),
            'value': value,
            'type': component_type,
            'name_params': name_params,
            'status': 'unknown',
            'issues': [],
            'mfg_results': []
        }
        
        if not component.get('manufacturers'):
            result['status'] = 'warning'
            result['issues'].append('No manufacturer part numbers specified')
            return result
        
        # Check each manufacturer variant
        all_not_found = True
        has_error = False
        
        for mfg in component['manufacturers']:
            mpn = mfg['pn']
            manufacturer = mfg['name']
            
            # Try Octopart first if API key available
            if self.api_key:
                online_data = self.check_octopart(mpn, manufacturer)
                time.sleep(0.5)  # Rate limiting
            else:
                # Fallback to SnapEDA
                online_data = self.check_snapeda(mpn)
                time.sleep(1)  # Be nice to free API
            
            mfg_result = {
                'manufacturer': manufacturer,
                'mpn': mpn,
                'online_data': online_data,
                'issues': []
            }
            
            if online_data.get('error'):
                has_error = True
                mfg_result['issues'].append(f"API error: {online_data['error']}")
            elif not online_data.get('found'):
                mfg_result['issues'].append('Component not found in database')
            else:
                all_not_found = False
                
                # Check for manufacturer name mismatch
                if manufacturer and online_data.get('manufacturer'):
                    if manufacturer.upper() != online_data['manufacturer'].upper():
                        mfg_result['issues'].append(
                            f"Manufacturer mismatch: '{manufacturer}' vs '{online_data['manufacturer']}'"
                        )
                
                # Perform component-specific verification
                if component_type == 'resistor':
                    self.verify_resistor_params(mfg_result, name_params, value, online_data)
                elif component_type == 'capacitor':
                    self.verify_capacitor_params(mfg_result, name_params, value, online_data)
            
            result['mfg_results'].append(mfg_result)
        
        # Set overall status
        if has_error:
            result['status'] = 'error'
        elif all_not_found:
            result['status'] = 'not_found'
            result['issues'].append('None of the manufacturer variants found in database')
        else:
            result['status'] = 'verified'
            # Collect all issues from mfg results
            for mfg_res in result['mfg_results']:
                if mfg_res['issues']:
                    result['issues'].extend([f"[{mfg_res['mpn']}] {issue}" for issue in mfg_res['issues']])
        
        return result
    
    def parse_symbol_name(self, name: str) -> dict:
        """Extract parameters from symbol name like 'CAP_0402_1p_6.3V_NP0_5%' or 'RES_0402_1R_TKF_1%_1/16W'"""
        params = {
            'package': None,
            'value': None,
            'voltage': None,
            'power': None,
            'tolerance': None,
            'dielectric': None,
            'film_type': None
        }
        
        parts = name.split('_')
        
        for part in parts:
            part_lower = part.lower()
            part_upper = part.upper()
            
            # Package size (4 digits)
            if re.match(r'\d{4}', part):
                params['package'] = part
            
            # Value (resistor: 1R, 10k, 1M; capacitor: 1p, 100n, 10u)
            elif re.match(r'[\d.]+[pnuµmkr]', part_lower):
                params['value'] = part
            
            # Voltage rating (e.g., 6.3V, 50V)
            elif re.search(r'[\d.]+v', part_lower):
                params['voltage'] = part
            
            # Power rating (e.g., 1/16W, 100mW, 0.1W)
            elif re.search(r'[\d./]+[mµ]?w', part_lower):
                params['power'] = part
            
            # Tolerance (e.g., 1%, 5%, 10%)
            elif re.match(r'[\d.]+%', part):
                params['tolerance'] = part
            
            # Capacitor dielectric type
            elif part_upper in ['NP0', 'C0G', 'X5R', 'X7R', 'X7S', 'Y5V', 'Z5U']:
                params['dielectric'] = part_upper
            
            # Resistor film type
            elif part_upper in ['TKF', 'THF', 'TNF', 'THICKFILM', 'THINFILM']:
                params['film_type'] = part_upper
        
        return params
    
    def detect_component_type(self, name: str, props: dict) -> str:
        """Detect if component is a resistor or capacitor"""
        name_lower = name.lower()
        value = props.get('Value', '').lower()
        
        # Check name patterns
        if any(x in name_lower for x in ['res', 'r_', '_r_', 'resistor']):
            return 'resistor'
        elif any(x in name_lower for x in ['cap', 'c_', '_c_', 'capacitor']):
            return 'capacitor'
        
        # Check value patterns
        if any(x in value for x in ['ohm', 'Ω', 'k', 'm']) and 'f' not in value:
            return 'resistor'
        elif any(x in value for x in ['f', 'µf', 'uf', 'pf', 'nf']):
            return 'capacitor'
        
        return 'unknown'
    
    def normalize_value(self, value_str: str, component_type: str) -> Optional[float]:
        """Normalize component value to base unit (Ohms or Farads)"""
        if not value_str:
            return None
        
        value_str = value_str.strip().upper().replace('Ω', 'R').replace('OHM', 'R')
        
        # Remove tolerance and other suffixes
        value_str = re.split('[±%]', value_str)[0].strip()
        
        try:
            if component_type == 'resistor':
                # Handle formats like: 1R, 10R, 4K3, 1M2, 10K, 1M
                # Where letter represents decimal point + multiplier
                
                # Check for letter-as-decimal notation (e.g., 4K3 = 4.3k, 1R5 = 1.5R)
                match = re.match(r'([\d.]+)([KMGR])([\d]+)?', value_str)
                if match:
                    before = float(match.group(1))
                    multiplier_letter = match.group(2)
                    after = match.group(3)
                    
                    # Combine before and after decimal
                    if after:
                        value = float(f"{before}.{after}")
                    else:
                        value = before
                    
                    # Apply multiplier
                    multipliers = {'G': 1e9, 'M': 1e6, 'K': 1e3, 'R': 1}
                    return value * multipliers.get(multiplier_letter, 1)
                
                # Simple format without letter-decimal (e.g., 10, 100, 1000)
                match = re.match(r'([\d.]+)', value_str)
                if match:
                    return float(match.group(1))
            
            elif component_type == 'capacitor':
                # Handle formats like: 1P, 100N, 10U, 4N7, 1U5
                # For capacitors: P=pF, N=nF, U/µ=µF
                
                # Check for letter-as-decimal notation (e.g., 4N7 = 4.7n, 1U5 = 1.5u)
                match = re.match(r'([\d.]+)([PNUµF])([\d]+)?', value_str)
                if match:
                    before = float(match.group(1))
                    multiplier_letter = match.group(2)
                    after = match.group(3)
                    
                    # Combine before and after decimal
                    if after:
                        value = float(f"{before}.{after}")
                    else:
                        value = before
                    
                    # Apply multiplier (to Farads)
                    multipliers = {
                        'F': 1,
                        'U': 1e-6, 'µ': 1e-6,  # microfarads
                        'N': 1e-9,  # nanofarads
                        'P': 1e-12  # picofarads
                    }
                    return value * multipliers.get(multiplier_letter, 1)
                
                # Simple numeric format
                match = re.match(r'([\d.]+)', value_str)
                if match:
                    return float(match.group(1))
        except:
            pass
        
        return None
    
    def extract_tolerance(self, value_str: str) -> Optional[str]:
        """Extract tolerance from value string"""
        if not value_str:
            return None
        
        # Look for tolerance patterns like ±5%, 1%, etc.
        match = re.search(r'[±]?\s*([\d.]+)\s*%', value_str)
        if match:
            return match.group(1) + '%'
        
        return None
    
    def verify_resistor(self, result: dict, props: dict, online_data: dict):
        """Verify resistor-specific parameters"""
        specs = online_data.get('specs', {})
        lib_value = props.get('Value', '')
        
        # Extract library parameters
        lib_resistance = self.normalize_value(lib_value, 'resistor')
        lib_power = props.get('Power', props.get('Power_Rating', ''))
        lib_tolerance = self.extract_tolerance(lib_value) or props.get('Tolerance', '')
        
        # Check resistance value
        if lib_resistance and specs.get('resistance'):
            online_resistance = self.normalize_value(specs['resistance'], 'resistor')
            if online_resistance and abs(lib_resistance - online_resistance) / online_resistance > 0.01:
                result['issues'].append(
                    f"Resistance mismatch: Library={lib_value} vs Online={specs['resistance']}"
                )
        
        # Check power rating
        if lib_power and specs.get('power_rating'):
            lib_power_val = self.normalize_power(lib_power)
            online_power_val = self.normalize_power(specs['power_rating'])
            
            if lib_power_val and online_power_val:
                if abs(lib_power_val - online_power_val) / online_power_val > 0.01:
                    result['issues'].append(
                        f"Power rating mismatch: Library={lib_power} vs Online={specs['power_rating']}"
                    )
        elif not specs.get('power_rating'):
            result['issues'].append('Power rating not found in online data')
        
        # Check tolerance
        if lib_tolerance and specs.get('tolerance'):
            if lib_tolerance.replace('%', '').strip() != specs['tolerance'].replace('%', '').strip():
                result['issues'].append(
                    f"Tolerance mismatch: Library={lib_tolerance} vs Online={specs['tolerance']}"
                )
    
    def verify_capacitor(self, result: dict, props: dict, online_data: dict):
        """Verify capacitor-specific parameters"""
        specs = online_data.get('specs', {})
        lib_value = props.get('Value', '')
        
        # Extract library parameters
        lib_capacitance = self.normalize_value(lib_value, 'capacitor')
        lib_voltage = props.get('Voltage', props.get('Voltage_Rating', ''))
        lib_tolerance = self.extract_tolerance(lib_value) or props.get('Tolerance', '')
        
        # Check capacitance value
        if lib_capacitance and specs.get('capacitance'):
            online_capacitance = self.normalize_value(specs['capacitance'], 'capacitor')
            if online_capacitance and abs(lib_capacitance - online_capacitance) / online_capacitance > 0.01:
                result['issues'].append(
                    f"Capacitance mismatch: Library={lib_value} vs Online={specs['capacitance']}"
                )
        
        # Check voltage rating
        if lib_voltage and specs.get('voltage_rating'):
            lib_voltage_val = self.normalize_voltage(lib_voltage)
            online_voltage_val = self.normalize_voltage(specs['voltage_rating'])
            
            if lib_voltage_val and online_voltage_val:
                if abs(lib_voltage_val - online_voltage_val) / online_voltage_val > 0.01:
                    result['issues'].append(
                        f"Voltage rating mismatch: Library={lib_voltage} vs Online={specs['voltage_rating']}"
                    )
        elif not specs.get('voltage_rating'):
            result['issues'].append('Voltage rating not found in online data')
        
        # Check tolerance
        if lib_tolerance and specs.get('tolerance'):
            if lib_tolerance.replace('%', '').strip() != specs['tolerance'].replace('%', '').strip():
                result['issues'].append(
                    f"Tolerance mismatch: Library={lib_tolerance} vs Online={specs['tolerance']}"
                )
    
    def verify_resistor_params(self, mfg_result: dict, name_params: dict, value: str, online_data: dict):
        """Verify resistor parameters from symbol name and value"""
        specs = online_data.get('specs', {})
        
        # Use value from name if available, otherwise from Value property
        lib_value = name_params.get('value') or value
        lib_resistance = self.normalize_value(lib_value, 'resistor')
        
        # Check resistance value
        if lib_resistance and specs.get('resistance'):
            online_resistance = self.normalize_value(specs['resistance'], 'resistor')
            if online_resistance and abs(lib_resistance - online_resistance) / online_resistance > 0.01:
                mfg_result['issues'].append(
                    f"Resistance mismatch: Library={lib_value} vs Online={specs['resistance']}"
                )
        
        # Check power rating from symbol name
        if name_params.get('power') and specs.get('power_rating'):
            lib_power_val = self.normalize_power(name_params['power'])
            online_power_val = self.normalize_power(specs['power_rating'])
            
            if lib_power_val and online_power_val:
                if abs(lib_power_val - online_power_val) / online_power_val > 0.01:
                    mfg_result['issues'].append(
                        f"Power rating mismatch: Library={name_params['power']} vs Online={specs['power_rating']}"
                    )
        
        # Check tolerance from symbol name
        if name_params.get('tolerance') and specs.get('tolerance'):
            lib_tol = name_params['tolerance'].replace('%', '').strip()
            online_tol = specs['tolerance'].replace('%', '').strip()
            if lib_tol != online_tol:
                mfg_result['issues'].append(
                    f"Tolerance mismatch: Library={name_params['tolerance']} vs Online={specs['tolerance']}"
                )
    
    def verify_capacitor_params(self, mfg_result: dict, name_params: dict, value: str, online_data: dict):
        """Verify capacitor parameters from symbol name and value"""
        specs = online_data.get('specs', {})
        
        # Use value from name if available, otherwise from Value property
        lib_value = name_params.get('value') or value
        lib_capacitance = self.normalize_value(lib_value, 'capacitor')
        
        # Check capacitance value
        if lib_capacitance and specs.get('capacitance'):
            online_capacitance = self.normalize_value(specs['capacitance'], 'capacitor')
            if online_capacitance and abs(lib_capacitance - online_capacitance) / online_capacitance > 0.01:
                mfg_result['issues'].append(
                    f"Capacitance mismatch: Library={lib_value} vs Online={specs['capacitance']}"
                )
        
        # Check voltage rating from symbol name
        if name_params.get('voltage') and specs.get('voltage_rating'):
            lib_voltage_val = self.normalize_voltage(name_params['voltage'])
            online_voltage_val = self.normalize_voltage(specs['voltage_rating'])
            
            if lib_voltage_val and online_voltage_val:
                if abs(lib_voltage_val - online_voltage_val) / online_voltage_val > 0.01:
                    mfg_result['issues'].append(
                        f"Voltage rating mismatch: Library={name_params['voltage']} vs Online={specs['voltage_rating']}"
                    )
        
        # Check tolerance from symbol name
        if name_params.get('tolerance') and specs.get('tolerance'):
            lib_tol = name_params['tolerance'].replace('%', '').strip()
            online_tol = specs['tolerance'].replace('%', '').strip()
            if lib_tol != online_tol:
                mfg_result['issues'].append(
                    f"Tolerance mismatch: Library={name_params['tolerance']} vs Online={specs['tolerance']}"
                )
        
        # Check dielectric type if available in specs
        if name_params.get('dielectric') and specs.get('temperature_coefficient'):
            lib_dielectric = name_params['dielectric'].upper()
            online_dielectric = specs['temperature_coefficient'].upper()
            
            # Map common names (C0G == NP0)
            if lib_dielectric == 'C0G':
                lib_dielectric = 'NP0'
            
            if lib_dielectric not in online_dielectric and online_dielectric not in lib_dielectric:
                mfg_result['issues'].append(
                    f"Dielectric mismatch: Library={name_params['dielectric']} vs Online={specs['temperature_coefficient']}"
                )
    
    def normalize_power(self, power_str: str) -> Optional[float]:
        """Normalize power rating to Watts"""
        if not power_str:
            return None
        
        power_str = power_str.strip().upper()
        
        try:
            # Handle fractions like "1/16W", "1/10W", "1/8W"
            if '/' in power_str:
                match = re.match(r'([\d]+)/([\d]+)W?', power_str)
                if match:
                    numerator = float(match.group(1))
                    denominator = float(match.group(2))
                    return numerator / denominator
            
            # Handle regular numbers with prefixes
            match = re.match(r'([\d.]+)\s*([MmµU]?)W?', power_str)
            if match:
                num = float(match.group(1))
                prefix = match.group(2).upper()
                
                if prefix in ['M', 'µ', 'U']:  # mW or µW
                    return num / 1000
                else:  # W
                    return num
        except:
            pass
        
        return None
    
    def normalize_voltage(self, voltage_str: str) -> Optional[float]:
        """Normalize voltage to Volts"""
        if not voltage_str:
            return None
        
        voltage_str = voltage_str.strip().upper()
        
        try:
            # Extract number
            match = re.match(r'([\d.]+)\s*([KM]?)V?', voltage_str)
            if match:
                num = float(match.group(1))
                prefix = match.group(2)
                
                if prefix == 'K':
                    return num * 1000
                elif prefix == 'M':
                    return num * 1e6
                else:
                    return num
        except:
            pass
        
        return None
    
    def generate_report(self, results: list[dict], output_file: str = 'library_check_report.txt'):
        """Generate a human-readable report"""
        verified = [r for r in results if r['status'] == 'verified']
        not_found = [r for r in results if r['status'] == 'not_found']
        warnings = [r for r in results if r['status'] == 'warning']
        errors = [r for r in results if r['status'] == 'error']
        
        # Separate by component type
        resistors = [r for r in results if r.get('type') == 'resistor']
        capacitors = [r for r in results if r.get('type') == 'capacitor']
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("KiCad Library Verification Report - SMD Resistors & Capacitors\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Total components checked: {len(results)}\n")
            f.write(f"  Resistors: {len(resistors)}\n")
            f.write(f"  Capacitors: {len(capacitors)}\n")
            f.write(f"  Other/Unknown: {len(results) - len(resistors) - len(capacitors)}\n\n")
            
            f.write(f"Status Summary:\n")
            f.write(f"  ✓ Verified: {len(verified)}\n")
            f.write(f"  ✗ Not found: {len(not_found)}\n")
            f.write(f"  ⚠ Warnings: {len(warnings)}\n")
            f.write(f"  ⚠ Errors: {len(errors)}\n")
            f.write(f"  ! Components with issues: {sum(1 for r in verified if r['issues'])}\n\n")
            
            if not_found:
                f.write("\n" + "=" * 80 + "\n")
                f.write("COMPONENTS NOT FOUND IN DATABASE\n")
                f.write("=" * 80 + "\n")
                for r in not_found:
                    f.write(f"\n[{r['name']}] (Line {r['line']}) - {r['type'].upper()}\n")
                    f.write(f"  MPN: {r['mpn']}\n")
                    f.write(f"  Manufacturer: {r['manufacturer']}\n")
                    f.write(f"  Value: {r['value']}\n")
                    f.write(f"  Issues: {', '.join(r['issues'])}\n")
            
            if warnings:
                f.write("\n" + "=" * 80 + "\n")
                f.write("WARNINGS (Missing Information)\n")
                f.write("=" * 80 + "\n")
                for r in warnings:
                    f.write(f"\n[{r['name']}] (Line {r['line']}) - {r['type'].upper()}\n")
                    f.write(f"  Issues: {', '.join(r['issues'])}\n")
            
            # Verified components with issues (most important)
            verified_with_issues = [r for r in verified if r['issues']]
            if verified_with_issues:
                f.write("\n" + "=" * 80 + "\n")
                f.write("VERIFIED COMPONENTS WITH MISMATCHES\n")
                f.write("=" * 80 + "\n")
                
                # Group by type
                res_issues = [r for r in verified_with_issues if r['type'] == 'resistor']
                cap_issues = [r for r in verified_with_issues if r['type'] == 'capacitor']
                
                if res_issues:
                    f.write("\n--- RESISTORS ---\n")
                    for r in res_issues:
                        f.write(f"\n[{r['name']}] (Line {r['line']})\n")
                        f.write(f"  MPN: {r['mpn']}\n")
                        f.write(f"  Manufacturer: {r['manufacturer']}\n")
                        f.write(f"  Library Value: {r['value']}\n")
                        if r['online_data'] and r['online_data'].get('specs'):
                            specs = r['online_data']['specs']
                            if specs.get('resistance'):
                                f.write(f"  Online Resistance: {specs['resistance']}\n")
                            if specs.get('power_rating'):
                                f.write(f"  Online Power: {specs['power_rating']}\n")
                            if specs.get('tolerance'):
                                f.write(f"  Online Tolerance: {specs['tolerance']}\n")
                        f.write(f"  ⚠ Issues:\n")
                        for issue in r['issues']:
                            f.write(f"    - {issue}\n")
                
                if cap_issues:
                    f.write("\n--- CAPACITORS ---\n")
                    for r in cap_issues:
                        f.write(f"\n[{r['name']}] (Line {r['line']})\n")
                        f.write(f"  MPN: {r['mpn']}\n")
                        f.write(f"  Manufacturer: {r['manufacturer']}\n")
                        f.write(f"  Library Value: {r['value']}\n")
                        if r['online_data'] and r['online_data'].get('specs'):
                            specs = r['online_data']['specs']
                            if specs.get('capacitance'):
                                f.write(f"  Online Capacitance: {specs['capacitance']}\n")
                            if specs.get('voltage_rating'):
                                f.write(f"  Online Voltage: {specs['voltage_rating']}\n")
                            if specs.get('tolerance'):
                                f.write(f"  Online Tolerance: {specs['tolerance']}\n")
                        f.write(f"  ⚠ Issues:\n")
                        for issue in r['issues']:
                            f.write(f"    - {issue}\n")
            
            # Perfect matches (no issues)
            perfect_matches = [r for r in verified if not r['issues']]
            if perfect_matches:
                f.write("\n" + "=" * 80 + "\n")
                f.write(f"PERFECTLY VERIFIED COMPONENTS ({len(perfect_matches)})\n")
                f.write("=" * 80 + "\n")
                f.write("\nAll parameters match online database:\n")
                for r in perfect_matches:
                    f.write(f"  ✓ {r['name']} - {r['mpn']}\n")
        
        print(f"\nReport saved to: {output_file}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Verify KiCad library components')
    parser.add_argument('library', help='Path to .kicad_sym library file')
    parser.add_argument('--api-key', help='Octopart API key (optional)', default=None)
    parser.add_argument('--output', help='Output report file', default='library_check_report.txt')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.library):
        print(f"Error: Library file not found: {args.library}")
        sys.exit(1)
    
    print(f"Parsing library: {args.library}")
    checker = ComponentChecker(api_key=args.api_key)
    
    components = checker.parse_kicad_library(args.library)
    print(f"Found {len(components)} components")
    
    if not components:
        print("No components found in library!")
        sys.exit(1)
    
    print("\nVerifying components...")
    results = []
    
    for i, component in enumerate(components, 1):
        print(f"Checking {i}/{len(components)}: {component['name']}", end='\r')
        result = checker.verify_component(component)
        results.append(result)
    
    print("\n\nGenerating report...")
    checker.generate_report(results, args.output)
    
    # Summary
    verified = sum(1 for r in results if r['status'] == 'verified')
    not_found = sum(1 for r in results if r['status'] == 'not_found')
    
    print(f"\n✓ Verified: {verified}")
    print(f"✗ Not found: {not_found}")
    print(f"⚠ Warnings: {sum(1 for r in results if r['status'] == 'warning')}")

if __name__ == '__main__':
    main()