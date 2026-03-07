def createCapStr(val, sizeCap, voltage, dielectric="X7R"):
    """Create capacitor part numbers for different manufacturers"""
    sizeYageo = sizeCap
    sizeMurata = sizeCap
    sizeKemet = sizeCap
    
    # Convert voltage to manufacturer codes
    voltage_codes = {
        "6.3V": {"yageo": "5", "murata": "0J", "kemet": "8"},
        "10V": {"yageo": "6", "murata": "1A", "kemet": "9"},
        "16V": {"yageo": "7", "murata": "1C", "kemet": "C"},
        "25V": {"yageo": "9", "murata": "1E", "kemet": "E"},
        "50V": {"yageo": "0J", "murata": "1H", "kemet": "J"}
    }
    
    v_code = voltage_codes.get(voltage, voltage_codes["16V"])
    
    # Format capacitor value string
    if val < 1:  # pF range (< 1pF not common, but handle it)
        cap_str = str(val).replace(".", "p")
        pf_val = int(val)
    elif val < 1000:  # pF range
        cap_str = str(int(val)) + "p"
        pf_val = int(val)
    elif val < 1000000:  # nF range
        nf_val = val / 1000
        if nf_val < 10:
            cap_str = str(round(nf_val, 2)).replace(".", "n")
        else:
            cap_str = str(round(nf_val, 1)).replace(".", "n")
        pf_val = int(val)
    else:  # uF range
        uf_val = val / 1000000
        if uf_val < 10:
            cap_str = str(round(uf_val, 2)).replace(".", "u")
        else:
            cap_str = str(round(uf_val, 1)).replace(".", "u")
        pf_val = int(val)
    
    # Create EIA code for capacitor value (2 digits + multiplier)
    if pf_val < 10:
        eia_code = str(int(pf_val * 10)) + "9"  # x 0.1
    elif pf_val < 100:
        eia_code = str(pf_val) + "0"  # x 1
    elif pf_val < 1000:
        eia_code = str(int(pf_val / 10)) + "1"  # x 10
    elif pf_val < 10000:
        eia_code = str(int(pf_val / 100)) + "2"  # x 100
    elif pf_val < 100000:
        eia_code = str(int(pf_val / 1000)) + "3"  # x 1000
    elif pf_val < 1000000:
        eia_code = str(int(pf_val / 10000)) + "4"  # x 10000
    else:
        eia_code = str(int(pf_val / 100000)) + "5"  # x 100000
    
    # Generate part numbers based on dielectric type
    if dielectric == "NP0" or dielectric == "C0G":
        # NP0/C0G part numbers (5% tolerance typical for small values)
        cap_yageo = f"CC{sizeYageo}C0G{v_code['yageo']}BB{eia_code}"
        cap_murata = f"GRM{sizeMurata}C0G{eia_code}CA01"
        cap_kemet = f"C{sizeKemet}C{eia_code}F{v_code['kemet']}GACTU"
    else:
        # X7R part numbers (10% tolerance)
        cap_yageo = f"CC{sizeYageo}KRX7R8BB{eia_code}"
        cap_murata = f"GRM{sizeMurata}R71C{eia_code}KA01"
        cap_kemet = f"C{sizeKemet}C{eia_code}J{v_code['kemet']}GACTU"
    
    return cap_str, cap_yageo, cap_murata, cap_kemet


def createLibEntry(cap_val_str, sizeCap, voltage, cap_yageo, cap_murata, cap_kemet, dielectric="X7R", tolerance="10%"):
    """Create KiCad symbol library entry for a capacitor"""
    entry = []
    entry.append(f'  (symbol "CAP_{sizeCap}_{cap_val_str}_{voltage}_{dielectric}_{tolerance}" (pin_numbers hide) (pin_names (offset 0) hide) (in_bom yes) (on_board yes)\n')
    entry.append('    (property "Reference" "C" (at 0 2.54 0) (do_not_autoplace)\n')
    entry.append('      (effects (font (size 1.27 1.27)))\n')
    entry.append('    )\n')
    entry.append(f'    (property "Value" "{cap_val_str}" (at 0 -2.54 0) (do_not_autoplace)\n')
    entry.append('      (effects (font (size 1.27 1.27)))\n')
    entry.append('    )\n')
    entry.append(f'    (property "Footprint" "00_Passives:CAP_SMD_{sizeCap}_NORMAL" (at 0 -5.08 0)\n')
    entry.append('      (effects (font (size 1.27 1.27)) hide)\n')
    entry.append('    )\n')
    
    # Different datasheets for NP0 vs X7R
    if dielectric == "NP0" or dielectric == "C0G":
        datasheet1 = "https://www.yageo.com/upload/media/product/productsearch/datasheet/mlcc/UPY-GP_NP0_16V-to-50V_18.pdf"
        datasheet2 = "https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM_Series_NP0.pdf"
        datasheet3 = "https://content.kemet.com/datasheets/KEM_C1002_C0G_SMD.pdf"
    else:
        datasheet1 = "https://www.yageo.com/upload/media/product/productsearch/datasheet/mlcc/UPY-GP_NP0_16V-to-50V_18.pdf"
        datasheet2 = "https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM_Series.pdf"
        datasheet3 = "https://content.kemet.com/datasheets/KEM_C1002_X7R_SMD.pdf"
    
    entry.append(f'    (property "Datasheet" "{datasheet1}" (at 0 5.08 0)\n')
    entry.append('      (effects (font (size 1.27 1.27)) hide)\n')
    entry.append('    )\n')
    entry.append(f'    (property "Datasheet 2" "{datasheet2}" (at 0 7.62 0)\n')
    entry.append('      (effects (font (size 1.27 1.27)) hide)\n')
    entry.append('    )\n')
    entry.append(f'    (property "Datasheet 3" "{datasheet3}" (at 0 10.16 0)\n')
    entry.append('      (effects (font (size 1.27 1.27)) hide)\n')
    entry.append('    )\n')
    entry.append('    (property "Mfg1" "Yageo" (at 7.62 0 0)\n')
    entry.append('      (effects (font (size 1.27 1.27)) hide)\n')
    entry.append('    )\n')
    entry.append(f'    (property "Mfg1 pn" "{cap_yageo}" (at 10.16 0 0)\n')
    entry.append('      (effects (font (size 1.27 1.27)) hide)\n')
    entry.append('    )\n')
    entry.append('    (property "Mfg2" "Murata" (at 12.7 0 0)\n')
    entry.append('      (effects (font (size 1.27 1.27)) hide)\n')
    entry.append('    )\n')
    entry.append(f'    (property "Mfg2 pn" "{cap_murata}" (at 15.24 0 0)\n')
    entry.append('      (effects (font (size 1.27 1.27)) hide)\n')
    entry.append('    )\n')
    entry.append('    (property "Mfg3" "KEMET" (at 17.78 0 0)\n')
    entry.append('      (effects (font (size 1.27 1.27)) hide)\n')
    entry.append('    )\n')
    entry.append(f'    (property "Mfg3 pn" "{cap_kemet}" (at 20.32 0 0)\n')
    entry.append('      (effects (font (size 1.27 1.27)) hide)\n')
    entry.append('    )\n')
    entry.append(f'    (property "ki_description" "CAP {cap_val_str}F {voltage} {dielectric} {tolerance} {sizeCap} MLCC" (at 0 0 0)\n')
    entry.append('      (effects (font (size 1.27 1.27)) hide)\n')
    entry.append('    )\n')
    entry.append(f'    (symbol "CAP_{sizeCap}_{cap_val_str}_{voltage}_{dielectric}_{tolerance}_1_1"\n')
    entry.append('      (polyline\n')
    entry.append('        (pts (xy -1.27 0.508) (xy 1.27 0.508))\n')
    entry.append('        (stroke (width 0.254) (type solid) (color 0 0 255 1))\n')
    entry.append('        (fill (type none))\n')
    entry.append('      )\n')
    entry.append('      (polyline\n')
    entry.append('        (pts (xy -1.27 -0.508) (xy 1.27 -0.508))\n')
    entry.append('        (stroke (width 0.254) (type solid) (color 0 0 255 1))\n')
    entry.append('        (fill (type none))\n')
    entry.append('      )\n')
    entry.append('      (pin passive line (at 0 2.54 270) (length 2.032)\n')
    entry.append('        (name "~" (effects (font (size 1.27 1.27))))\n')
    entry.append('        (number "1" (effects (font (size 1.27 1.27))))\n')
    entry.append('      )\n')
    entry.append('      (pin passive line (at 0 -2.54 90) (length 2.032)\n')
    entry.append('        (name "~" (effects (font (size 1.27 1.27))))\n')
    entry.append('        (number "2" (effects (font (size 1.27 1.27))))\n')
    entry.append('      )\n')
    entry.append('    )\n')
    entry.append('  )\n')
    return entry


def main():
    sizes = ["0402", "0603", "0805", "1206"]
    voltages = ["6.3V", "10V", "16V", "25V", "50V"]
    
    # E6 series for larger values, E12 for smaller
    E6 = [1.0, 1.5, 2.2, 3.3, 4.7, 6.8]
    E12 = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]
    
    # Generate X7R capacitors (100pF and up)
    for sizeCap in sizes:
        for voltage in voltages:
            caps = []
            entries = []
            output_file = f"00_Capacitors_{sizeCap}_{voltage.replace('.', '_')}_X7R.kicad_sym"
            
            # Generate capacitor values
            # pF range (use E12): Starting from 100pF (most common minimum for MLCC)
            for val in E12:
                caps.append(val * 100)   # 100pF to 820pF
            
            # nF range (use E12): 1nF to 82nF
            for val in E12:
                caps.append(val * 1000)     # 1nF to 8.2nF
                caps.append(val * 10000)    # 10nF to 82nF
            
            # uF range (use E6): 0.1uF to 10uF
            for val in E6:
                caps.append(val * 100000)   # 0.1uF to 0.68uF
                caps.append(val * 1000000)  # 1uF to 6.8uF
                if val <= 1.5:
                    caps.append(val * 10000000)  # 10uF (only smallest values)
            
            # Create library entries
            for val in caps:
                cap_str, cap_yageo, cap_murata, cap_kemet = createCapStr(val, sizeCap, voltage, "X7R")
                entries.append(createLibEntry(cap_str, sizeCap, voltage, cap_yageo, cap_murata, cap_kemet, "X7R", "10%"))
            
            # Write to file
            with open(output_file, 'w') as f:
                f.write('(kicad_symbol_lib (version 20220914) (generator kicad_symbol_editor)\n')
                for entry in entries:
                    f.writelines(entry)
                f.write(')\n')
            
            print(f"Created {output_file} with {len(entries)} capacitors")
    
    # Generate NP0/C0G capacitors (small values: 1pF to 100nF)
    # NP0 is typically used for smaller, precision values
    for sizeCap in sizes:
        for voltage in voltages:
            caps_np0 = []
            entries_np0 = []
            output_file_np0 = f"00_Capacitors_{sizeCap}_{voltage.replace('.', '_')}_NP0.kicad_sym"
            
            # NP0 capacitors - smaller values with tighter tolerances
            # 1pF to 10pF (E12)
            for val in E12:
                if val >= 1.0:
                    caps_np0.append(val)  # 1pF to 8.2pF
            
            # 10pF to 100pF (E12)
            for val in E12:
                caps_np0.append(val * 10)   # 10pF to 82pF
                caps_np0.append(val * 100)  # 100pF to 820pF
            
            # 1nF to 100nF (E12) - upper range for NP0
            for val in E12:
                caps_np0.append(val * 1000)   # 1nF to 8.2nF
                caps_np0.append(val * 10000)  # 10nF to 82nF
            
            # Create library entries for NP0
            for val in caps_np0:
                cap_str, cap_yageo, cap_murata, cap_kemet = createCapStr(val, sizeCap, voltage, "NP0")
                entries_np0.append(createLibEntry(cap_str, sizeCap, voltage, cap_yageo, cap_murata, cap_kemet, "NP0", "5%"))
            
            # Write to file
            with open(output_file_np0, 'w') as f:
                f.write('(kicad_symbol_lib (version 20220914) (generator kicad_symbol_editor)\n')
                for entry in entries_np0:
                    f.writelines(entry)
                f.write(')\n')
            
            print(f"Created {output_file_np0} with {len(entries_np0)} capacitors")


if __name__ == '__main__':
    main()