"""Single source of truth for the Science Olympiad EV controller board.

Edit this file, then run tools/build.py to regenerate the schematic and PCB.

Rev C: circuit (PARTS pins, nets) is read from here by tools/relayout.py. The "at" positions in
PARTS below are the Rev B placement and are NOT used any more - board placement lives in
tools/placement.py.

Board: RP2350 (Pico 2) robot controller / power distribution board
  - 8x AA battery input (XT30), 15 A fuse, TVS, reverse-polarity Schottky
  - 5 V buck (Recom R-78E5.0) + 3.3 V LDO (AMS1117-3.3)
  - 2x AS5600 wheel encoders on separate I2C buses (fixed 0x36 address)
  - WitMotion WT901 IMU on UART0
  - Weka dual 20 A ESC: fused power (XT30) + 2 PWM signals
  - Waveshare 1.69" ST7789V2 LCD on SPI1 (2x4 2.54 mm male header)
  - 2 momentary buttons (start trigger + mode), battery voltage sense
"""

SYM_LIB = "C:/Program Files/KiCad/10.0/share/kicad/symbols"
FP_LIB = "C:/Program Files/KiCad/10.0/share/kicad/footprints"

PROJECT = "RobotEV"
TITLE = "EV Controller - RP2350 / 8xAA / Weka dual ESC"
REV = "B"
DATE = "2026-11-14"

BOARD_W = 85.0
BOARD_H = 65.0
CORNER_R = 4.0
MOUNT_HOLE = "MountingHole:MountingHole_3.2mm_M3"

# ---------------------------------------------------------------- power rails
# VBAT      raw battery at the connector, before the fuse
# VBAT_F    after F1: feeds the ESC tap (J2) and the protection cluster
# VBAT_SW   after the panel switch J3 (logic branch only)
# VBAT_D    after the reverse-polarity Schottky D3, feeds the buck
# +5V       buck output
# VSYS      +5V through D5 (holds the Pico up if the 5 V rail dips)
# +3V3      LDO output


def P(ref, value, sym, fp, pins, at, desc="", **kw):
    return dict(ref=ref, value=value, sym=sym, fp=fp, pins=pins, at=at, desc=desc, **kw)


# (x, y, rotation) below are PCB footprint centres in mm, origin = board top-left.
PARTS = [
    # ---------------------------------------------------------------- logic
    P("U1", "RPi Pico 2 (RP2350)", "RobotEV:Pico2", "RobotEV:Pico2_Socket_2x20_P2.54mm",
      {1: "IMU_TX", 2: "IMU_RX", 3: "GND", 4: "ESC_L", 5: "ESC_R", 6: "ENC_L_SDA",
       7: "ENC_L_SCL", 8: "GND", 9: "ENC_R_SDA", 10: "ENC_R_SCL", 11: None,
       12: "LCD_CS", 13: "GND", 14: "LCD_SCK", 15: "LCD_MOSI", 16: "LCD_DC",
       17: "LCD_RST", 18: "GND", 19: "LCD_BL", 20: "BTN_START", 21: "BTN_MODE",
       22: "LED_STAT", 23: "GND", 24: None, 25: None, 26: None, 27: None, 28: "GND",
       29: None, 30: None, 31: "VBAT_ADC", 32: None, 33: "GND", 34: None, 35: None,
       36: None, 37: None, 38: "GND", 39: "VSYS", 40: None},
      (35.0, 30.0, 180), "Pico 2 in two 1x20 sockets, rotated so GP0-GP15 face the connectors"),

    # ---------------------------------------------------------------- power
    P("U2", "R-78E5.0-0.5", "Converter_DCDC:R-78E5.0-0.5",
      "Converter_DCDC:Converter_DCDC_RECOM_R-78E-0.5_THT",
      {1: "VBAT_D", 2: "GND", 3: "+5V"}, (11.0, 45.0, 0), "12 V -> 5 V 0.5 A switching module"),
    P("U3", "AMS1117-3.3", "Regulator_Linear:AMS1117-3.3",
      "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
      {1: "GND", 2: "+3V3", 3: "+5V"}, (13.0, 54.0, 0), "5 V -> 3.3 V, 1 A LDO for LCD and sensors"),

    # ------------------------------------------------------- protection chain
    P("F1", "15A", "Device:Fuse", "Fuse:Fuse_2920_7451Metric",
      {1: "VBAT", 2: "VBAT_F"}, (10.5, 5.0, 0),
      "Battery fuse: everything downstream (ESC tap + logic) is fused"),
    P("D4", "SMBJ16A", "Device:D_TVS", "Diode_SMD:D_SMB",
      {1: "VBAT_F", 2: "GND"}, (18.5, 5.0, 0),
      "Transient suppression on the fused battery rail"),
    P("D3", "SS34", "Device:D_Schottky", "Diode_SMD:D_SMB",
      {2: "VBAT_SW", 1: "VBAT_D"}, (26.0, 61.0, 90),
      "Reverse-polarity protection for the logic branch (buck input)"),
    P("C12", "100uF 16V", "Device:C_Polarized", "Capacitor_THT:CP_Radial_D5.0mm_P2.00mm",
      {1: "VBAT_F", 2: "GND"}, (20.0, 19.5, 0), "Bulk at the battery/ESC tap"),
    P("C14", "470uF 16V", "Device:C_Polarized", "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm",
      {1: "VBAT_D", 2: "GND"}, (52.0, 60.5, 0),
      "Bulk hold-up on the buck input so a sag cannot reset the Pico"),

    # ------------------------------------------------------------ connectors
    P("J1", "BATTERY 8xAA", "Connector_Generic:Conn_01x02",
      "Connector_AMASS:AMASS_XT30PW-M_1x02_P2.50mm_Horizontal",
      {1: "VBAT", 2: "GND"}, (10.5, 15.5, 90), "XT30 male: battery pack lead (unfused side)"),
    P("J2", "ESC_POWER", "Connector_Generic:Conn_01x02",
      "Connector_AMASS:AMASS_XT30PW-F_1x02_P2.50mm_Horizontal",
      {1: "VBAT_F", 2: "GND"}, (10.5, 31.0, 90),
      "XT30 female: fused 12 V feed to the Weka ESC"),
    P("J3", "POWER_SWITCH", "Connector_Generic:Conn_01x02",
      "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
      {1: "VBAT_F", 2: "VBAT_SW"}, (20.5, 10.5, 0),
      "Latching switch or jumper across; only feeds the logic branch"),
    P("J4", "ENC_LEFT (AS5600)", "Connector_Generic:Conn_01x04",
      "Connector_JST:JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical",
      {1: "+3V3", 2: "GND", 3: "ENC_L_SDA", 4: "ENC_L_SCL"}, (62.0, 10.0, 0),
      "I2C0 (GP4/GP5)"),
    P("J5", "ENC_RIGHT (AS5600)", "Connector_Generic:Conn_01x04",
      "Connector_JST:JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical",
      {1: "+3V3", 2: "GND", 3: "ENC_R_SDA", 4: "ENC_R_SCL"}, (62.0, 18.0, 0),
      "I2C1 (GP6/GP7)"),
    P("J6", "IMU (WT901)", "Connector_Generic:Conn_01x04",
      "Connector_JST:JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical",
      {1: "+5V", 2: "IMU_TX", 3: "IMU_RX", 4: "GND"}, (62.0, 26.0, 0),
      "WT901 order is VCC/RX/TX/GND: pin2 = WT901 RX <- Pico GP0, pin3 = WT901 TX -> GP1"),
    P("J7", "LCD 1.69 (ST7789V2)", "Connector_Generic:Conn_02x04_Odd_Even",
      "Connector_PinHeader_2.54mm:PinHeader_2x04_P2.54mm_Vertical",
      {1: "+3V3", 3: "LCD_MOSI", 5: "LCD_CS", 7: "LCD_RST",
       2: "GND", 4: "LCD_SCK", 6: "LCD_DC", 8: "LCD_BL"}, (51.5, 7.5, 0),
      "SPI1 on GP9-GP14; 2x4 male block, odd pins = 3V3/MOSI/CS/RST, even = GND/SCK/DC/BL"),
    P("J8", "BTN_START", "Connector_Generic:Conn_01x02",
      "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical",
      {1: "BTN_START", 2: "GND"}, (62.0, 35.0, 0), "Momentary (ON)-OFF, to GND"),
    P("J9", "BTN_MODE", "Connector_Generic:Conn_01x02",
      "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical",
      {1: "BTN_MODE", 2: "GND"}, (62.0, 43.0, 0), "Momentary (ON)-OFF, to GND"),
    P("J10", "ESC_PWM", "Connector_Generic:Conn_01x03",
      "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
      {1: "ESC_L", 2: "ESC_R", 3: "GND"}, (64.0, 52.0, 0),
      "PWM servo-style signals to the Weka dual ESC, male pins for the ESC lead"),

    # --------------------------------------------------------- battery sense
    P("R1", "100k", "Device:R", "Resistor_SMD:R_0805_2012Metric",
      {1: "VBAT_D", 2: "VBAT_DIV"}, (70.0, 44.0, 0),
      "Divider top, senses the buck-input rail"),
    P("R2", "22k", "Device:R", "Resistor_SMD:R_0805_2012Metric",
      {1: "VBAT_DIV", 2: "GND"}, (70.0, 48.0, 0), "Divider bottom"),
    P("R3", "1k", "Device:R", "Resistor_SMD:R_0805_2012Metric",
      {1: "VBAT_DIV", 2: "VBAT_ADC"}, (76.0, 48.0, 0), "ADC series protection"),
    P("C11", "100nF", "Device:C", "Capacitor_SMD:C_0805_2012Metric",
      {1: "VBAT_ADC", 2: "GND"}, (80.0, 48.0, 0), "ADC filter"),

    # -------------------------------------------------------------- buttons
    P("R4", "10k", "Device:R", "Resistor_SMD:R_0805_2012Metric",
      {1: "+3V3", 2: "BTN_START"}, (68.0, 38.0, 0), "Start button pull-up"),
    P("R5", "10k", "Device:R", "Resistor_SMD:R_0805_2012Metric",
      {1: "+3V3", 2: "BTN_MODE"}, (74.0, 38.0, 0), "Mode button pull-up"),
    P("C9", "100nF", "Device:C", "Capacitor_SMD:C_0805_2012Metric",
      {1: "BTN_START", 2: "GND"}, (68.0, 41.0, 0), "Debounce"),
    P("C10", "100nF", "Device:C", "Capacitor_SMD:C_0805_2012Metric",
      {1: "BTN_MODE", 2: "GND"}, (74.0, 41.0, 0), "Debounce"),

    # ----------------------------------------------------------------- LEDs
    P("R6", "1k", "Device:R", "Resistor_SMD:R_0805_2012Metric",
      {1: "+3V3", 2: "LED_PWR_A"}, (71.0, 28.0, 90), "Power LED resistor"),
    P("D1", "GREEN", "Device:LED", "LED_SMD:LED_0805_2012Metric",
      {1: "GND", 2: "LED_PWR_A"}, (76.0, 28.0, 90), "Power indicator"),
    P("R7", "100", "Device:R", "Resistor_SMD:R_0805_2012Metric",
      {1: "LED_STAT", 2: "LED_STAT_A"}, (71.0, 33.0, 0), "Status LED resistor (100R ~5mA)"),
    P("D2", "BLUE", "Device:LED", "LED_SMD:LED_0805_2012Metric",
      {1: "GND", 2: "LED_STAT_A"}, (76.0, 33.0, 0), "GP17 status LED"),

    # ----------------------------------------------------------------- caps
    P("C1", "10uF 25V", "Device:C", "Capacitor_SMD:C_1206_3216Metric",
      {1: "VBAT_D", 2: "GND"}, (21.6, 40.0, 90), "Buck input bulk"),
    P("C2", "10uF", "Device:C", "Capacitor_SMD:C_0805_2012Metric",
      {1: "+5V", 2: "GND"}, (21.6, 32.0, 90), "5 V bulk"),
    P("C3", "10uF", "Device:C", "Capacitor_SMD:C_0805_2012Metric",
      {1: "+3V3", 2: "GND"}, (20.9, 52.0, 0), "3V3 bulk"),
    P("C4", "100nF", "Device:C", "Capacitor_SMD:C_0805_2012Metric",
      {1: "+3V3", 2: "GND"}, (20.9, 56.0, 0), "3V3 decoupling"),
    P("C5", "100nF", "Device:C", "Capacitor_SMD:C_0805_2012Metric",
      {1: "VSYS", 2: "GND"}, (20.9, 48.0, 0), "VSYS decoupling (U1.39)"),
    P("C6", "100nF", "Device:C", "Capacitor_SMD:C_0805_2012Metric",
      {1: "+5V", 2: "GND"}, (68.5, 30.0, 0), "IMU supply decoupling"),
    P("C7", "100nF", "Device:C", "Capacitor_SMD:C_0805_2012Metric",
      {1: "+3V3", 2: "GND"}, (68.5, 14.0, 0), "Left encoder decoupling"),
    P("C8", "100nF", "Device:C", "Capacitor_SMD:C_0805_2012Metric",
      {1: "+3V3", 2: "GND"}, (68.5, 22.0, 0), "Right encoder decoupling"),
    P("D5", "SS34", "Device:D_Schottky", "Diode_SMD:D_SMB",
      {2: "+5V", 1: "VSYS"}, (50.0, 50.0, 90),
      "Buck output -> Pico VSYS; holds VSYS up if the 5 V rail sags"),
    P("C13", "22uF", "Device:C", "Capacitor_SMD:C_1206_3216Metric",
      {1: "+3V3", 2: "GND"}, (20.9, 45.5, 0), "AMS1117 output stability (needs >=22uF)"),

    # ----------------------------------------------------------- test points
    P("TP1", "+5V", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm",
      {1: "+5V"}, (77.0, 12.0, 0), "5 V rail"),
    P("TP2", "+3V3", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm",
      {1: "+3V3"}, (82.0, 12.0, 0), "3.3 V rail"),
    P("TP3", "GND", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm",
      {1: "GND"}, (77.0, 18.0, 0), "Ground"),
    P("TP4", "VBAT_SW", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm",
      {1: "VBAT_SW"}, (82.0, 18.0, 0), "Switched battery"),
]

MOUNTING_HOLES = [("H1", 4.0, 4.0), ("H2", 81.0, 4.0), ("H3", 4.0, 61.0), ("H4", 81.0, 61.0)]
for _ref, _x, _y in MOUNTING_HOLES:
    PARTS.append(P(_ref, "M3", "Mechanical:MountingHole",
                   "MountingHole:MountingHole_3.2mm_M3", {}, (_x, _y, 0), "M3 mounting hole"))

# ------------------------------------------------------------------ net list
POWER_NETS = ["GND", "VBAT", "VBAT_F", "VBAT_SW", "VBAT_D", "+5V", "VSYS", "+3V3"]

# copper width (mm) per net, signals default to 0.25
NET_WIDTH = {"VBAT": 1.2, "VBAT_F": 1.2, "VBAT_SW": 0.8, "VBAT_D": 0.8,
             "GND": 0.5, "+5V": 0.5, "+3V3": 0.5, "VSYS": 0.5}

# route order: wide/high-current nets first
ROUTE_ORDER = ["VBAT", "VBAT_F", "VBAT_SW", "VBAT_D", "+5V", "VSYS", "+3V3", "GND"]

# Nets routed before the wide power rails. The signals leaving U1's right-hand
# column have to cross the whole connector cluster, and a 1.2 mm VBAT track laid
# first chops that corridor into dead ends.
ROUTE_FIRST = ["LCD_SCK", "LCD_MOSI", "LCD_CS", "LCD_DC", "LCD_RST", "LCD_BL",
               "ESC_L", "ESC_R", "IMU_TX", "IMU_RX", "BTN_START", "BTN_MODE",
               "LED_STAT", "ENC_R_SDA", "ENC_R_SCL", "VBAT_ADC"]

# ------------------------------------------------------------------ silkscreen
SILK_LABELS = {
    "J1": ("BATT 8xAA", 0.0, -7.5),
    "J2": ("ESC PWR", 0.0, -8.5),
    "J3": ("PWR SW", 0.0, 6.0),
    "J4": ("ENC L", 0.0, -4.5),
    "J5": ("ENC R", 0.0, -4.5),
    "J6": ("WT901", 0.0, -4.5),
    "J7": ("LCD", 3.0, -4.0),
    "J8": ("START", 0.0, -5.5),
    "J9": ("MODE", -9.0, 5.0),
    "J10": ("ESC SIG", 9.0, 2.0),
}


# Nets whose pads sit in pockets the grid autorouter cannot leave: at 2.54 mm
# pitch the reserved halo of every neighbouring pin seals the 0.84 mm gap, so a
# 0.25 mm track has no legal cell to start from even though the pad is open.
# These are drawn first as explicit waypoints (mm, board coordinates) and the
# autorouter then routes around them. DRC verifies them like every other track.
# Short escape track per pad, from the pad centre to a point in open board.
# The grid router cannot start from a pad whose neighbouring pins are 2.54 mm
# away: their reserved halos meet across the 0.84 mm gap, so the pad has no
# legal cell to leave from even though copper would fit. The escape unseals it
# and the net is then autorouted normally from the escape end.
ESCAPES = {
    ("U1", "12"): (46.60, 26.19),      # LCD_CS
    ("U1", "16"): (46.60, 16.03),      # LCD_DC

    ("J7", "5"): (47.80, 8.77),
    ("J7", "6"): (55.00, 8.77),
}

# The two battery nets are routed explicitly: J1's unconnected XT30 shell pad is
# a hard keep-out next to F1, and the 1.25 mm pinch between J1/J2 and J3 cannot
# take a 1.2 mm rail. (polyline, width) each; 1.2 mm for the pack and the ESC
# tap, 0.8 mm for the < 0.3 A logic branch.
# Nets whose MANUAL_ROUTES already cover every pad, so the autorouter must skip
# them. Nets listed in MANUAL_ROUTES but not here still get autorouted: their
# entry is only a link for the pads the grid cannot reach.
MANUAL_ONLY = {"VBAT", "VBAT_F"}

MANUAL_ROUTES = {
    "VBAT": [([(16.18, 13.00), (10.90, 13.00), (10.90, 6.90), (7.11, 6.90)], 1.2)],
    # +3V3 link from the LCD header to the encoder header, around the top of the
    # JST-PH block: both pads are sealed 2.54/2.0 mm pitch pads and the net is
    # otherwise complete.
    "+3V3": [([(50.23, 3.69), (50.23, 1.90), (59.00, 1.90), (59.00, 9.45)], 0.5)],
    "VBAT_F": [([(13.89, 5.00), (13.20, 5.00), (13.20, 33.50), (16.65, 33.50)], 1.2),
               ([(13.89, 5.00), (16.37, 5.00), (16.37, 8.60), (18.80, 8.60),
                 (18.80, 18.90)], 0.8),
               ([(18.80, 9.22), (20.20, 9.22)], 0.8)],
}


def all_nets():
    nets = set()
    for p in PARTS:
        for n in p["pins"].values():
            if n:
                nets.add(n)
    return nets
