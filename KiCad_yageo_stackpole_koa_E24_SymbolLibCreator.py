def createResStr(val, sizeResistor):
    sizeYageo = sizeResistor
    sizeStackpole = sizeResistor
    sizeKoa = sizeResistor
    if sizeResistor == "0402":
        sizeKoa = "1E"
    elif sizeResistor == "0603":
        sizeKoa = "1J"
    elif sizeResistor == "0805":
        sizeKoa = "2A"
    elif sizeResistor == "1206":
        sizeKoa = "2B"
    else:
        raise error

    if val <= 9.9:
        resistor = str(val).replace(".", "R").replace("0","")
        res_yageo = "RC"+sizeYageo+"FR-07" + resistor + "L"
        res_stackpole = "RMCF"+sizeStackpole+"FT" + str("%.2f" % round(val,2)).replace('.','R')
        res_koa = "RK73H"+sizeKoa+"TTD" + str("%.2f" % round(val,2)).replace('.','R') + "F"
    elif val <= 99:
        resistor = str(round(val))+"R"
        res_yageo = "RC"+sizeYageo+"FR-07" + resistor + "L"
        res_stackpole = "RMCF"+sizeStackpole+"FT" + str("%.1f" % round(val,1)).replace('.','R')
        res_koa = "RK73H"+sizeKoa+"TTD" + str("%.1f" % round(val,1)).replace('.','R') + "F"
    elif val <= 999:
        resistor = str(round(val))+"R"
        res_yageo = "RC"+sizeYageo+"FR-07" + resistor + "L"
        res_stackpole = "RMCF"+sizeStackpole+"FT" + str("%.1f" % round(val,1)).replace('.0','R')
        res_koa = "RK73H"+sizeKoa+"TTD" + str(round(val))+'0' + "F"
    elif val <= 9999:
        resistor = str(round(val/1000,1)).replace(".", "K").replace("K0","K")
        res_yageo = "RC"+sizeYageo+"FR-07" + resistor + "L"
        res_stackpole = "RMCF"+sizeStackpole+"FT" + str("%.2f" % round(val/1000,2)).replace('.','K')
        res_koa = "RK73H"+sizeKoa+"TTD" + str(round(val/10))+'1' + "F"
    elif val <= 99999:
        resistor = str(round(val/1000))+"K"
        res_yageo = "RC"+sizeYageo+"FR-07" + resistor + "L"
        res_stackpole = "RMCF"+sizeStackpole+"FT" + str("%.1f" % round(val/1000,1)).replace('.','K')
        res_koa = "RK73H"+sizeKoa+"TTD" + str(round(val/100))+'2' + "F"
    else:
        resistor = str(round(val/1000))+"K"
        res_yageo = "RC"+sizeYageo+"FR-07" + resistor + "L"
        res_stackpole = "RMCF"+sizeStackpole+"FT" + str("%.1f" % round(val/1000,1)).replace('.0','K')
        res_koa = "RK73H"+sizeKoa+"TTD" + str(round(val/1000))+'3' + "F"
    return resistor, res_yageo, res_stackpole, res_koa



## createLibEntry(resistor, value) ##
# resistor : string value, ex "1R1", "10K"
# value : float value, ex 1.1, 10000
# Returns a list of lines for the library entry of the resistor
#[" (symbol "RES_0603_10K_TKF_1%_1/10W" (pin_numbers hide) (pin_names (offset 0) hide) (in_bom yes) (on_board yes)",
#"    (property "Reference" "R" (at -1.905 0 90) (do_not_autoplace)"] etc
def createLibEntry(resistor, sizeResistor, power, res_yageo, res_stackpole, res_koa):
    entry = []
    entry.append('  (symbol "RES_'+sizeResistor+'_'+resistor+'_TKF_1%_'+power+'" (pin_numbers hide) (pin_names (offset 0) hide) (in_bom yes) (on_board yes)\n')
    entry.append('    (property "Reference" "R" (at -1.905 0 90) (do_not_autoplace)\n')
    entry.append('      (effects (font (size 1.27 1.27)))\n')
    entry.append('    )\n')
    entry.append('    (property "Value" "'+resistor+'" (at 1.905 0 90) (do_not_autoplace)\n')
    entry.append('      (effects (font (size 1.27 1.27)))\n')
    entry.append('    )\n')
    entry.append('    (property "Footprint" "00_Passives:RES SMD '+sizeResistor+' NORMAL" (at -3.81 0 90)\n')
    entry.append('      (effects (font (size 1.27 1.27)) hide)\n')
    entry.append('    )\n')
    entry.append('    (property "Datasheet" "https://www.yageo.com/upload/media/product/app/datasheet/rchip/pyu-rc_group_51_rohs_l.pdf" (at 3.81 1.27 90)\n')
    entry.append('      (effects (font (size 1.27 1.27)) hide)\n')
    entry.append('    )\n')
    entry.append('    (property "Datasheet 2" "https://www.seielect.com/catalog/sei-rmcf_rmcp.pdf" (at 21.59 2.54 90)\n')
    entry.append('      (effects (font (size 1.27 1.27)) hide)\n')
    entry.append('    )\n')
    entry.append('    (property "Datasheet 3" "https://www.koaspeer.com/pdfs/RK73H.pdf" (at 24.13 -2.54 90)\n')
    entry.append('      (effects (font (size 1.27 1.27)) hide)\n')
    entry.append('    )\n')
    entry.append('    (property "Mfg1" "Yageo" (at 8.89 0 90)\n')
    entry.append('      (effects (font (size 1.27 1.27)) hide)\n')
    entry.append('    )\n')
    entry.append('    (property "Mfg1 pn" "'+res_yageo+'" (at 6.35 0 90)\n')
    entry.append('      (effects (font (size 1.27 1.27)) hide)\n')
    entry.append('    )\n')
    entry.append('    (property "Mfg2" "Stackpole Electronics Inc" (at 11.43 0 90)\n')
    entry.append('      (effects (font (size 1.27 1.27)) hide)\n')
    entry.append('    )\n')
    entry.append('    (property "Mfg2 pn" "'+res_stackpole+'" (at 13.97 -1.27 90)\n')
    entry.append('      (effects (font (size 1.27 1.27)) hide)\n')
    entry.append('    )\n')
    entry.append('    (property "Mfg3" "KOA Speer" (at 16.51 0 90)\n')
    entry.append('      (effects (font (size 1.27 1.27)) hide)\n')
    entry.append('    )\n')
    entry.append('    (property "Mfg3 pn" "'+res_koa+'" (at 19.05 0 90)\n')
    entry.append('      (effects (font (size 1.27 1.27)) hide)\n')
    entry.append('    )\n')
    entry.append('    (property "ki_description" "RES '+resistor+' OHM 1% '+power+' '+sizeResistor+' Thick film" (at 0 0 0)\n')
    entry.append('      (effects (font (size 1.27 1.27)) hide)\n')
    entry.append('    )\n')
    entry.append('    (symbol "RES_'+sizeResistor+'_'+resistor+'_TKF_1%_'+power+'_1_1"\n')
    entry.append('      (rectangle (start -0.635 -1.27) (end 0.635 1.27)\n')
    entry.append('        (stroke (width 0) (type solid) (color 0 0 255 1))\n')
    entry.append('        (fill (type none))\n')
    entry.append('      )\n')
    entry.append('      (pin passive line (at 0 -2.54 90) (length 1.27)\n')
    entry.append('        (name "~" (effects (font (size 1.27 1.27))))\n')
    entry.append('        (number "1" (effects (font (size 1.27 1.27))))\n')
    entry.append('      )\n')
    entry.append('      (pin passive line (at 0 2.54 270) (length 1.27)\n')
    entry.append('        (name "~" (effects (font (size 1.27 1.27))))\n')
    entry.append('        (number "2" (effects (font (size 1.27 1.27))))\n')
    entry.append('      )\n')
    entry.append('    )\n')
    entry.append('  )\n')
    return entry

def main():
    sizeResistor = "1206"
    power = "1/4W"
    E24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]
    res = []
    i=1
    entries = [] #entries for the library
    output_file = "00_Resistors_"+sizeResistor+".kicad_sym"

    while i <= 100000:
        for val in E24:
            res.append(val*i) #[1.0, 1.1, ... 910000.0]
        i=i*10

    for val in res:
        resistor, res_yageo, res_stackpole, res_koa = createResStr(val, sizeResistor)
        entries.append(createLibEntry(resistor, sizeResistor, power, res_yageo, res_stackpole, res_koa))

    with open(output_file, 'a') as f: # Open and append lines
        f.writelines('(kicad_symbol_lib (version 20220914) (generator kicad_symbol_editor) \n')
        for entry in entries: # Each entry is a resistor, consisting of several library lines
            f.writelines(entry) # target.writelines([line1, line2, line3])
        f.writelines(')\n')
if __name__ == '__main__':
    main()