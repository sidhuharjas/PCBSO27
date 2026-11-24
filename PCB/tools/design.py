"""Single source of truth for the Science Olympiad EV controller board (Rev D).

Edit this file, then run tools/build.py (or tools/relayout.py + tools/gen_sch.py) to
regenerate the schematic, PCB, BOM, and renders.

Rev D — Zero-SMD, minimal-component redesign (100% Through-Hole):
  - CRITICAL FIX: Corrected reversed polarity on J1 (XT30PW-M) and J2 (XT30PW-F)
    (KiCad AMASS XT30PW footprints have Pin 1 = '-' GND, Pin 2 = '+' VBAT/VBAT_F).
  - Eliminated 17 redundant components (29 -> 12 electrical parts; 26 -> 0 SMD parts!):
      * Removed U3 (AMS1117-3.3) + C13 + C3: Pico 2 onboard RT6154A SMPS (Pin 36 3V3)
        comfortably supplies all 3.3 V peripherals (~128 mA max vs 300 mA rating),
        enables full USB-only desk debugging, and removes AMS1117 MLCC oscillation risk.
      * Moved J6 (WT901 IMU, rated 3.3-5 V, <25 mA) to +3V3 so all sensors & LCD work
        on USB without battery power and with zero back-powering risk.
      * Removed C12 (100 uF), C5-C8 (redundant on-module caps; kept shared C4 100 nF
        on east +3V3 bus), R3 (R1||R2 = 18k already protects ADC + forms 88 Hz LPF),
        R4/R5/C9/C10 (use RP2350 internal pull-ups + software debounce on GP15/GP16),
        and D1/R6/D2/R7 (use Pico 2 onboard GP25 LED + 1.69" IPS LCD + TP1-TP4).
  - Converted all 12 remaining electrical components to 100% easy through-hole (THT),
    including a tool-free replaceable 15 A Mini Automotive Blade Fuse (Keystone 3568).
  - Kept the exact 85 x 65 mm outline and 77 x 57 mm M3 mounting pattern (chassis drop-in).
"""

SYM_LIB = "C:/Program Files/KiCad/10.0/share/kicad/symbols"
FP_LIB = "C:/Program Files/KiCad/10.0/share/kicad/footprints"

PROJECT = "RobotEV"
TITLE = "EV Controller Rev D - RP2350 / 8xAA / Weka dual ESC (All-THT)"
REV = "D"
DATE = "2026-11-24"

BOARD_W = 85.0
BOARD_H = 65.0
CORNER_R = 4.0
MOUNT_HOLE = "MountingHole:MountingHole_3.2mm_M3"

# ---------------------------------------------------------------- power rails
# VBAT      raw battery (+) at J1 pin 2, before the 15 A blade fuse
# VBAT_F    after F1: feeds ESC tap (J2 pin 2), TVS clamp (D4), and power switch (J3)
# VBAT_SW   after panel switch J3 (logic branch only, < 250 mA)
# VBAT_D    after reverse-polarity / hold-up Schottky D3; feeds C14, C1, U2, and VBAT sense
# +5V       U2 RECOM R-78E5.0-0.5 buck output
# VSYS      +5V through OR-ing Schottky D5 -> Pico 2 pin 39 (safe with simultaneous USB)
# +3V3      Pico 2 onboard RT6154A 3.3 V SMPS output (pin 36) -> LCD, encoders, WT901 IMU


def P(ref, value, sym, fp, pins, at, desc="", **kw):
    return dict(ref=ref, value=value, sym=sym, fp=fp, pins=pins, at=at, desc=desc, **kw)


# Note: `at` is only used by legacy gen_pcb.py; tools/relayout.py reads tools/placement.py.
PARTS = [
    # ---------------------------------------------------------------- logic
    P("U1", "RPi Pico 2 (RP2350)", "RobotEV:Pico2", "RobotEV:Pico2_Socket_2x20_P2.54mm",
      {1: "IMU_TX", 2: "IMU_RX", 3: "GND", 4: "ESC_L", 5: "ESC_R", 6: "ENC_L_SDA",
       7: "ENC_L_SCL", 8: "GND", 9: "ENC_R_SDA", 10: "ENC_R_SCL", 11: None,
       12: "LCD_CS", 13: "GND", 14: "LCD_SCK", 15: "LCD_MOSI", 16: "LCD_DC",
       17: "LCD_RST", 18: "GND", 19: "LCD_BL", 20: "BTN_START", 21: "BTN_MODE",
       22: None, 23: "GND", 24: None, 25: None, 26: None, 27: None, 28: "GND",
       29: None, 30: None, 31: "VBAT_ADC", 32: None, 33: "GND", 34: None, 35: None,
       36: "+3V3", 37: None, 38: "GND", 39: "VSYS", 40: None},
      (50.0, 37.0, 180),
      "Pico 2 in two 1x20 sockets; Pin 36 (3V3 SMPS) powers all 3.3 V peripherals (<=128 mA / 300 mA max)"),

    # ----------------------------------------------------- power & protection (100% THT)
    P("F1", "15A Mini Blade", "Device:Fuse",
      "Fuse:Fuseholder_Blade_Mini_Keystone_3568",
      {1: "VBAT", 2: "VBAT_F"}, (24.0, 22.1, 270),
      "Keystone 3568 PCB mini blade fuse holder + 15 A automotive blade fuse (tool-free swap)"),
    P("D4", "P6KE18A", "Device:D_TVS",
      "Diode_THT:D_DO-15_P10.16mm_Horizontal",
      {1: "VBAT_F", 2: "GND"}, (31.5, 22.0, 90),
      "600 W unidirectional TVS clamp (VRWM=15.3 V, VCL=25.2 V) against brushed-motor spikes"),
    P("D3", "1N5822", "Device:D_Schottky",
      "Diode_THT:D_DO-201AD_P12.70mm_Horizontal",
      {1: "VBAT_D", 2: "VBAT_SW"}, (23.0, 41.0, 0),
      "40 V 3 A Schottky: reverse-polarity protection + isolates C14 hold-up from motor sag"),
    P("C14", "470uF 25V", "Device:C_Polarized",
      "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm",
      {1: "VBAT_D", 2: "GND"}, (22.5, 49.5, 0),
      "Bulk hold-up cap on buck input so 8xAA stall sag cannot reset RP2350"),
    P("C1", "10uF 50V", "Device:C",
      "Capacitor_THT:C_Disc_D6.0mm_W4.4mm_P5.00mm",
      {1: "VBAT_D", 2: "GND"}, (11.5, 43.0, 0),
      "Low-ESR radial ceramic input bypass for U2 570 kHz switching buck"),
    P("U2", "R-78E5.0-0.5", "Converter_DCDC:R-78E5.0-0.5",
      "Converter_DCDC:Converter_DCDC_RECOM_R-78E-0.5_THT",
      {1: "VBAT_D", 2: "GND", 3: "+5V"}, (11.5, 53.5, 0),
      "12 V -> 5 V 0.5 A high-efficiency drop-in switching buck module (7-28 V in)"),
    P("C2", "10uF 50V", "Device:C",
      "Capacitor_THT:C_Disc_D6.0mm_W4.4mm_P5.00mm",
      {1: "+5V", 2: "GND"}, (15.5, 59.0, 0),
      "Low-ESR radial ceramic 5 V output bypass (same part as C1)"),
    P("D5", "1N5822", "Device:D_Schottky",
      "Diode_THT:D_DO-201AD_P12.70mm_Horizontal",
      {1: "VSYS", 2: "+5V"}, (29.5, 58.6, 180),
      "40 V 3 A Schottky OR-ing diode (+5V -> Pico VSYS) for safe simultaneous USB + battery"),
    P("C4", "100nF 50V", "Device:C",
      "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm",
      {1: "+3V3", 2: "GND"}, (76.0, 44.0, 90),
      "Shared local +3V3 decoupling capacitor at east sensor/LCD connector bank"),

    # ------------------------------------------------------- battery sense (100% THT)
    P("R1", "100k 1%", "Device:R",
      "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal",
      {1: "VBAT_D", 2: "VBAT_ADC"}, (31.5, 48.0, 90),
      "Battery divider top leg (1/4 W metal film); senses switched buck-input rail"),
    P("R2", "22k 1%", "Device:R",
      "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal",
      {1: "VBAT_ADC", 2: "GND"}, (35.5, 48.0, 270),
      "Battery divider bottom leg (12.9 V -> 2.33 V at GP26/ADC0; R1||R2 = 18k)"),
    P("C11", "100nF 50V", "Device:C",
      "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm",
      {1: "VBAT_ADC", 2: "GND"}, (35.5, 34.5, 90),
      "ADC low-pass filter (fc ~88 Hz) & sampling reservoir (same part as C4)"),

    # ------------------------------------------------------------ connectors (100% THT)
    # CRITICAL FIX vs Rev C: AMASS XT30PW footprints have Pin 1 = '-' (GND), Pin 2 = '+' (VBAT)!
    P("J1", "BATTERY 8xAA", "Connector_Generic:Conn_01x02",
      "Connector_AMASS:AMASS_XT30PW-M_1x02_P2.50mm_Horizontal",
      {1: "GND", 2: "VBAT"}, (16.2, 12.15, 90),
      "XT30PW-M: 8xAA battery pack input (Pin 1 = '-' GND, Pin 2 = '+' VBAT)"),
    P("J2", "ESC_POWER", "Connector_Generic:Conn_01x02",
      "Connector_AMASS:AMASS_XT30PW-F_1x02_P2.50mm_Horizontal",
      {1: "GND", 2: "VBAT_F"}, (16.2, 32.0, 90),
      "XT30PW-F: fused 12 V feed to Weka dual ESC (Pin 1 = '-' GND, Pin 2 = '+' VBAT_F)"),
    P("J3", "POWER_SWITCH", "Connector_Generic:Conn_01x02",
      "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
      {1: "VBAT_F", 2: "VBAT_SW"}, (31.5, 33.5, 0),
      "Latching panel switch or jumper (logic branch only, < 250 mA)"),
    P("J4", "ENC_LEFT (AS5600)", "Connector_Generic:Conn_01x04",
      "Connector_JST:JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical",
      {1: "+3V3", 2: "GND", 3: "ENC_L_SDA", 4: "ENC_L_SCL"}, (67.0, 47.0, 0),
      "Left AS5600 encoder on I2C0 (GP4/GP5); breakout supplies 4.7k pull-ups"),
    P("J5", "ENC_RIGHT (AS5600)", "Connector_Generic:Conn_01x04",
      "Connector_JST:JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical",
      {1: "+3V3", 2: "GND", 3: "ENC_R_SDA", 4: "ENC_R_SCL"}, (67.0, 39.5, 0),
      "Right AS5600 encoder on I2C1 (GP6/GP7); breakout supplies 4.7k pull-ups"),
    P("J6", "IMU (WT901)", "Connector_Generic:Conn_01x04",
      "Connector_JST:JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical",
      {1: "+3V3", 2: "IMU_TX", 3: "IMU_RX", 4: "GND"}, (67.0, 60.2, 0),
      "WT901 (3.3-5 V, <25 mA) on UART0: Pin 1=+3V3, Pin 2=WT901 RX<-GP0, Pin 3=WT901 TX->GP1"),
    P("J7", "LCD 1.69 (ST7789V2)", "Connector_Generic:Conn_02x04_Odd_Even",
      "Connector_PinHeader_2.54mm:PinHeader_2x04_P2.54mm_Vertical",
      {1: "+3V3", 3: "LCD_MOSI", 5: "LCD_CS", 7: "LCD_RST",
       2: "GND", 4: "LCD_SCK", 6: "LCD_DC", 8: "LCD_BL"}, (65.27, 25.0, 180),
      "Waveshare 1.69\" SPI1 LCD (GP9-GP14); 2x4 male header, rotated 180 deg (Pin 1 = square pad)"),
    P("J8", "BTN_START", "Connector_Generic:Conn_01x02",
      "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical",
      {1: "BTN_START", 2: "GND"}, (62.0, 6.5, 0),
      "Momentary start button to GND; enable GP15 internal pull-up + software debounce"),
    P("J9", "BTN_MODE", "Connector_Generic:Conn_01x02",
      "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical",
      {1: "BTN_MODE", 2: "GND"}, (43.0, 6.5, 0),
      "Momentary mode button to GND; enable GP16 internal pull-up + software debounce"),
    P("J10", "ESC_PWM", "Connector_Generic:Conn_01x03",
      "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
      {1: "ESC_L", 2: "ESC_R", 3: "GND"}, (66.54, 52.5, 90),
      "PWM servo signals to Weka dual ESC (leave ESC +5V BEC wire disconnected)"),

    # ----------------------------------------------------------- test points (bare pads)
    P("TP1", "+5V", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm",
      {1: "+5V"}, (9.0, 62.5, 0), "5 V buck output test pad"),
    P("TP2", "+3V3", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm",
      {1: "+3V3"}, (76.0, 53.0, 0), "3.3 V Pico SMPS rail test pad"),
    P("TP3", "GND", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm",
      {1: "GND"}, (13.0, 62.5, 0), "Ground reference test pad"),
    P("TP4", "VBAT_SW", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm",
      {1: "VBAT_SW"}, (27.0, 35.0, 0), "Switched battery test pad"),
]

MOUNTING_HOLES = [("H1", 4.0, 4.0), ("H2", 81.0, 4.0), ("H3", 4.0, 61.0), ("H4", 81.0, 61.0)]
for _ref, _x, _y in MOUNTING_HOLES:
    PARTS.append(P(_ref, "M3", "Mechanical:MountingHole",
                   "MountingHole:MountingHole_3.2mm_M3", {}, (_x, _y, 0), "M3 mounting hole"))

# ------------------------------------------------------------------ net list
POWER_NETS = ["GND", "VBAT", "VBAT_F", "VBAT_SW", "VBAT_D", "+5V", "VSYS", "+3V3"]

NET_WIDTH = {"VBAT": 2.5, "VBAT_F": 2.5, "VBAT_SW": 0.8, "VBAT_D": 0.8,
             "GND": 0.5, "+5V": 0.6, "+3V3": 0.6, "VSYS": 0.6}

ROUTE_ORDER = ["VBAT", "VBAT_F", "VBAT_SW", "VBAT_D", "VSYS", "+5V", "+3V3", "GND"]
ROUTE_FIRST = []
SILK_LABELS = {}
ESCAPES = {}
MANUAL_ONLY = set()
MANUAL_ROUTES = {}


def all_nets():
    nets = set()
    for p in PARTS:
        for n in p["pins"].values():
            if n:
                nets.add(n)
    return nets
