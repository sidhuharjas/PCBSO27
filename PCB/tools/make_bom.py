"""Build hardware/BOM.xlsx from tools/design.py (Rev D - 100% Through-Hole, Zero SMD)."""
import collections, os, sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D

# Exact verified in-stock Through-Hole (THT) parts keyed by (value, fp)
CATALOG = {
    ("RPi Pico 2 (RP2350)", "RobotEV:Pico2_Socket_2x20_P2.54mm"):
        ("2x 1x20 female pin header (2.54 mm, THT)", "Generic / Samtec",
         "SSQ-120-01-T-S (or 2x 20-pin 2.54mm female socket)", "DigiKey / Amazon", 1.50,
         "Solder sockets into PCB; plug RPi Pico 2 in with USB facing south edge"),
    ("15A Mini Blade", "Fuse:Fuseholder_Blade_Mini_Keystone_3568"):
        ("PCB Mini Automotive Blade Fuse Holder (30 A) + 15 A Mini Blade Fuse", "Keystone / Littelfuse",
         "3568 (DigiKey 36-3568-ND) + 0297015.WXNV (15A)", "DigiKey / Mouser", 2.00,
         "Tool-free 2-second fuse swap; buy spare 15 A mini blade fuses"),
    ("P6KE18A", "Diode_THT:D_DO-15_P10.16mm_Horizontal"):
        ("TVS diode 600 W unidirectional, 15.3 V standoff (DO-15 axial THT)", "Littelfuse / Yageo",
         "P6KE18A", "DigiKey / Mouser", 0.45,
         "Clamps brushed-motor inductive spikes; cathode band (K) to VBAT_F"),
    ("1N5822", "Diode_THT:D_DO-201AD_P12.70mm_Horizontal"):
        ("Schottky diode 40 V 3 A (DO-201AD axial THT)", "ON Semi / Vishay / Diodes Inc.",
         "1N5822 (or 1N5822G)", "DigiKey / Mouser", 0.40,
         "D3 = reverse-polarity + hold-up isolator; D5 = +5V->VSYS OR-ing (same part)"),
    ("470uF 25V", "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm"):
        ("470 uF 25 V radial aluminum electrolytic (D8.0 mm, P3.5 mm, low-ESR)", "Nichicon / Panasonic",
         "UPW1E471MPD (or EEU-FR1E471)", "DigiKey / Mouser", 0.55,
         "Upgraded to 25 V rating for fresh 8xAA packs (13.2 V); '+' lead = square pad"),
    ("10uF 50V", "Capacitor_THT:C_Disc_D6.0mm_W4.4mm_P5.00mm"):
        ("10 uF 50 V X7R/X7S radial ceramic MLCC (5.0 mm lead pitch, THT)", "TDK / Murata",
         "FG20X7R1H106KRT00 (alt: RDEC71H106K3K1H03B)", "DigiKey / Mouser", 0.90,
         "Low-ESR ceramic input (C1) & output (C2) bypass for U2 570 kHz buck"),
    ("R-78E5.0-0.5", "Converter_DCDC:Converter_DCDC_RECOM_R-78E-0.5_THT"):
        ("5 V 0.5 A switching buck regulator SIP-3 (7-28 V in, THT)", "RECOM Power",
         "R-78E5.0-0.5", "DigiKey / Mouser", 3.60,
         "Drop-in 7805 switching replacement (~88% eff., no heatsink); Pin 1 = square pad"),
    ("100nF 50V", "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"):
        ("100 nF (0.1 uF) 50 V X7R radial ceramic MLCC (5.0 mm pitch, THT)", "KEMET / TDK",
         "C320C104K5R5TA (alt: FG18X7R1H104KNT06)", "DigiKey / Mouser", 0.25,
         "C4 = shared east +3V3 bus bypass; C11 = VBAT_ADC 88 Hz LPF (same part)"),
    ("100k 1%", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal"):
        ("100 kOhm 1/4 W 1% axial metal film resistor (THT)", "Yageo / Vishay",
         "MFR-25FBF52-100K", "DigiKey / Mouser", 0.10,
         "Battery divider top leg (10.16 mm / 0.4 in standard bend pitch)"),
    ("22k 1%", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal"):
        ("22 kOhm 1/4 W 1% axial metal film resistor (THT)", "Yageo / Vishay",
         "MFR-25FBF52-22K", "DigiKey / Mouser", 0.10,
         "Battery divider bottom leg (12.9 V -> 2.33 V at GP26/ADC0)"),
    ("BATTERY 8xAA", "Connector_AMASS:AMASS_XT30PW-M_1x02_P2.50mm_Horizontal"):
        ("XT30PW-M right-angle PCB male plug (THT)", "AMASS",
         "XT30PW-M", "DigiKey / Amazon / AliExpress", 0.90,
         "Mates with female XT30 on 8xAA pack; Pin 1 = '-' GND, Pin 2 = '+' VBAT"),
    ("ESC_POWER", "Connector_AMASS:AMASS_XT30PW-F_1x02_P2.50mm_Horizontal"):
        ("XT30PW-F right-angle PCB female socket (THT)", "AMASS",
         "XT30PW-F", "DigiKey / Amazon / AliExpress", 0.90,
         "Mates with male XT30 on Weka ESC; Pin 1 = '-' GND, Pin 2 = '+' VBAT_F"),
    ("POWER_SWITCH", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"):
        ("2-pin 2.54 mm male header (THT)", "Molex / Amphenol",
         "22-28-4020 (or breakaway 1x40 strip)", "DigiKey", 0.25,
         "Connect to panel power switch (or install shunt jumper; <250 mA logic branch)"),
    ("ENC_LEFT (AS5600)", "Connector_JST:JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical"):
        ("JST-PH 4-pin 2.0 mm shrouded header (THT)", "JST",
         "B4B-PH-K-S", "DigiKey / Amazon", 0.35,
         "Same 4-pin JST-PH header used for J4 (ENC_L), J5 (ENC_R), and J6 (WT901)"),
    ("ENC_RIGHT (AS5600)", "Connector_JST:JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical"):
        ("JST-PH 4-pin 2.0 mm shrouded header (THT)", "JST",
         "B4B-PH-K-S", "DigiKey / Amazon", 0.35,
         "Pinout: 1=+3V3, 2=GND, 3=SDA, 4=SCL"),
    ("IMU (WT901)", "Connector_JST:JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical"):
        ("JST-PH 4-pin 2.0 mm shrouded header (THT)", "JST",
         "B4B-PH-K-S", "DigiKey / Amazon", 0.35,
         "Pinout: 1=+3V3, 2=IMU_TX (to WT901 RX), 3=IMU_RX (from WT901 TX), 4=GND"),
    ("LCD 1.69 (ST7789V2)", "Connector_PinHeader_2.54mm:PinHeader_2x04_P2.54mm_Vertical"):
        ("2x4 (8-pin) 2.54 mm male pin header (THT)", "Amphenol / Sullins",
         "68001-108HLF", "DigiKey", 0.40,
         "Plugs Waveshare 1.69\" LCD 8-wire harness (Pin 1 = square pad, +3V3)"),
    ("BTN_START", "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical"):
        ("JST-XH 2-pin 2.5 mm shrouded header (THT)", "JST",
         "B2B-XH-A", "DigiKey / Amazon", 0.30,
         "Momentary start trigger (pencil tap); GP15 internal pull-up"),
    ("BTN_MODE", "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical"):
        ("JST-XH 2-pin 2.5 mm shrouded header (THT)", "JST",
         "B2B-XH-A", "DigiKey / Amazon", 0.30,
         "Momentary mode select button; GP16 internal pull-up"),
    ("ESC_PWM", "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical"):
        ("1x3 2.54 mm male pin header (THT)", "Amphenol / Sullins",
         "68001-103HLF (or breakaway 1x40 strip)", "DigiKey", 0.20,
         "1=ESC_L (GP2), 2=ESC_R (GP3), 3=GND; leave ESC +5V BEC wire disconnected"),
}

OFFBOARD = [
    ("Raspberry Pi Pico 2 (RP2350)", 1, "Raspberry Pi", "SC1631 (with male headers)", "DigiKey / SparkFun", 6.00,
     "Plugs into U1 sockets; onboard RT6154A supplies +3V3 (300 mA max) and GP25 LED"),
    ("Weka Dual 20A Brushed ESC", 1, "Just Cuz Robotics", "Weka Dual 20A", "justcuzrobotics.com", 45.00,
     "XT30 power cable plugs into J2; CH1/CH2/GND servo leads plug into J10"),
    ("AS5600 magnetic encoder breakout + diametric magnet", 2, "Generic / AliExpress", "AS5600-12bit", "Amazon / AliExpress", 4.00,
     "Breakouts already include 4.7k I2C pull-ups; wire 4-pin JST-PH to J4/J5"),
    ("WitMotion WT901 TTL UART IMU", 1, "WitMotion", "WT901", "Amazon / WitMotion", 25.00,
     "Runs on +3V3 (<25 mA) from J6 so IMU works on USB-only bench testing too"),
    ("Waveshare 1.69\" 240x280 ST7789V2 IPS LCD", 1, "Waveshare", "1.69inch LCD Module", "Waveshare / Amazon", 13.00,
     "8-pin female jumper cable plugs onto J7 (+3V3 logic & power, <=90 mA)"),
    ("8xAA battery holder + XT30-F pigtail + 8x AA NiMH cells", 1, "Eneloop / Tenergy", "8xAA + XT30-F", "Amazon", 22.00,
     "Double-check XT30 polarity before first plug-in: flat side = '-', round side = '+'"),
    ("Panel latching toggle/rocker switch (logic power)", 1, "Any SPST >=1 A", "2-pin JST/Dupont to J3", "Amazon / DigiKey", 2.00,
     "Switches logic branch only (<250 mA); or bridge J3 with a 2.54 mm shunt jumper"),
    ("Momentary push buttons (start + mode)", 2, "Any NO tactile/arcade", "2-pin JST-XH pigtails", "Amazon", 1.50,
     "Plug into J8 (START, pencil-tap) and J9 (MODE)"),
    ("JST-PH 4-pin & JST-XH 2-pin pre-crimped harness kit", 1, "Generic", "JST-PH4 / XH2", "Amazon", 9.00,
     "Pre-crimped leads for J4, J5, J6, J8, J9"),
    ("Spare 15 A Mini Automotive Blade Fuses (5-pack)", 1, "Littelfuse", "0297015.WXNV", "AutoZone / DigiKey", 4.00,
     "Competition spares; tool-free swap into Keystone 3568 holder F1"),
    ("PCB fabrication (85x65 mm, 2-layer, 1.6 mm, 1 oz Cu)", 5, "JLCPCB / PCBWay", "Gerbers from build.py", "jlcpcb.com", 1.00,
     "Minimum qty 5 (~$5 total + shipping); standard 1 oz Cu is ample (6 mm double-sided bus)"),
]


def group_pcb_parts():
    groups = collections.OrderedDict()
    for p in D.PARTS:
        ref = p["ref"]
        if (ref.startswith("H") and ref[1:].isdigit()) or ref.startswith("TP"):
            continue
        key = (p["value"], p["fp"])
        if key not in groups:
            groups[key] = dict(refs=[], value=p["value"], fp=p["fp"], desc=p["desc"])
        groups[key]["refs"].append(ref)
    rows = []
    for key, g in groups.items():
        if key not in CATALOG:
            raise SystemExit("missing CATALOG entry for %r" % (key,))
        desc, mfr, mpn, vendor, price, notes = CATALOG[key]
        rows.append((", ".join(g["refs"]), len(g["refs"]), g["value"],
                     g["fp"].split(":", 1)[-1], desc, mfr, mpn, vendor, price, notes))
    return rows


def style_sheet(ws, headers, widths):
    hdr_fill = PatternFill("solid", fgColor="1F4E78")
    hdr_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    thin = Side(style="thin", color="CCCCCC")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    ws.append(headers)
    for i, w in enumerate(widths, 1):
        c = ws.cell(row=1, column=i)
        c.fill = hdr_fill
        c.font = hdr_font
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = border
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 26
    ws.freeze_panes = "A2"
    return border


def main():
    wb = Workbook()
    # ---- Sheet 1: PCB Parts (100% THT, 0 SMD)
    ws = wb.active
    ws.title = "PCB Parts (All-THT)"
    headers = ["Ref(s)", "Qty", "Value", "Footprint (THT)", "Description",
               "Manufacturer", "Part Number (MPN)", "Vendor", "Unit $", "Ext $", "Notes"]
    widths = [12, 6, 18, 34, 42, 20, 32, 18, 9, 10, 48]
    border = style_sheet(ws, headers, widths)
    body_font = Font(name="Calibri", size=10)
    alt_fill = PatternFill("solid", fgColor="F5F8FC")

    rows = group_pcb_parts()
    for idx, (refs, qty, val, fp, desc, mfr, mpn, vendor, price, notes) in enumerate(rows, 2):
        ws.append([refs, qty, val, fp, desc, mfr, mpn, vendor, price, f"=B{idx}*I{idx}", notes])
        for col in range(1, 12):
            c = ws.cell(row=idx, column=col)
            c.font = body_font
            c.border = border
            c.alignment = Alignment(vertical="center", wrap_text=True,
                                    horizontal="center" if col in (2, 9, 10) else "left")
            if idx % 2 == 1:
                c.fill = alt_fill
        ws.cell(row=idx, column=9).number_format = "$#,##0.00"
        ws.cell(row=idx, column=10).number_format = "$#,##0.00"
        ws.row_dimensions[idx].height = 24

    tot_row = len(rows) + 2
    ws.append(["TOTAL", f"=SUM(B2:B{tot_row - 1})", "", "0 SMD / 100% Through-Hole",
               f"{len(rows)} unique PCB BOM lines (excl. 4 M3 holes & 4 bare test pads)",
               "", "", "", "", f"=SUM(J2:J{tot_row - 1})", ""])
    tot_font = Font(name="Calibri", size=11, bold=True)
    tot_fill = PatternFill("solid", fgColor="D9E1F2")
    for col in range(1, 12):
        c = ws.cell(row=tot_row, column=col)
        c.font = tot_font
        c.fill = tot_fill
        c.border = border
    ws.cell(row=tot_row, column=2).alignment = Alignment(horizontal="center")
    ws.cell(row=tot_row, column=10).number_format = "$#,##0.00"
    ws.cell(row=tot_row, column=10).alignment = Alignment(horizontal="center")

    # ---- Sheet 2: Off-board modules & PCB fab
    ws2 = wb.create_sheet("Off-Board & Fab")
    headers2 = ["Item", "Qty", "Manufacturer", "Part / Spec", "Vendor", "Unit $", "Ext $", "Notes"]
    widths2 = [38, 6, 20, 26, 20, 9, 10, 50]
    border2 = style_sheet(ws2, headers2, widths2)
    for idx, (item, qty, mfr, spec, vendor, price, notes) in enumerate(OFFBOARD, 2):
        ws2.append([item, qty, mfr, spec, vendor, price, f"=B{idx}*F{idx}", notes])
        for col in range(1, 9):
            c = ws2.cell(row=idx, column=col)
            c.font = body_font
            c.border = border2
            c.alignment = Alignment(vertical="center", wrap_text=True,
                                    horizontal="center" if col in (2, 6, 7) else "left")
            if idx % 2 == 1:
                c.fill = alt_fill
        ws2.cell(row=idx, column=6).number_format = "$#,##0.00"
        ws2.cell(row=idx, column=7).number_format = "$#,##0.00"
        ws2.row_dimensions[idx].height = 24
    tot2 = len(OFFBOARD) + 2
    ws2.append(["TOTAL", f"=SUM(B2:B{tot2 - 1})", "", "", "", "", f"=SUM(G2:G{tot2 - 1})", ""])
    for col in range(1, 9):
        c = ws2.cell(row=tot2, column=col)
        c.font = tot_font
        c.fill = tot_fill
        c.border = border2
    ws2.cell(row=tot2, column=2).alignment = Alignment(horizontal="center")
    ws2.cell(row=tot2, column=7).number_format = "$#,##0.00"
    ws2.cell(row=tot2, column=7).alignment = Alignment(horizontal="center")

    out_path = os.path.join(os.path.dirname(HERE), "hardware", "BOM.xlsx")
    wb.save(out_path)
    total_qty = sum(r[1] for r in rows)
    total_cost = sum(r[1] * r[8] for r in rows)
    print(f"wrote {out_path} ({len(rows)} unique PCB lines, {total_qty} soldered parts, ~${total_cost:.2f}/board)")


if __name__ == "__main__":
    main()
