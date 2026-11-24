"""Floorplan for Rev D (All-THT, Zero-SMD, 85 x 65 mm chassis-compatible).

(x, y, rot): footprint pad-bbox centre in mm (board top-left origin), KiCad rotation in degrees.
Board outline (85 x 65 mm, R=4 mm) and M3 holes (77 x 57 mm) match Rev B/C identically.
ZERO parts sit under the Pico 2 module.
"""
BOARD_W, BOARD_H, CORNER_R = 85.0, 65.0, 4.0
HOLES = [(4.0, 4.0), (81.0, 4.0), (4.0, 61.0), (81.0, 61.0)]   # M3, 77 x 57 mm pattern

# Every soldered component is through-hole and stays outside the Pico 2 outline
TALL = ['J1', 'J2', 'J3', 'J4', 'J5', 'J6', 'J7', 'J8', 'J9', 'J10',
        'F1', 'D3', 'D4', 'D5', 'U2', 'C1', 'C2', 'C4', 'C11', 'C14', 'R1', 'R2']

PICO_CX, PICO_CY = 50.0, 37.0   # Pico 2 sockets, rot 180 -> GP0-GP15 face east connectors, USB at south edge

# XT30 housings are placed by footprint origin (pad 1 = '-' GND); plug in from west edge.
# With fixed polarity: J1.2 (+ VBAT) is at (16.2, 17.15) and J2.2 (+ VBAT_F) is at (16.2, 27.00),
# facing each other 9.85 mm apart — matching Keystone 3568's 9.92 mm fuse pitch!
ORIGIN = {'J1': (16.2, 12.15, 90), 'J2': (16.2, 32.0, 90)}

PLACE = {
    'U1': (PICO_CX, PICO_CY, 180),

    # ---- High-current battery/ESC bus (west-north): straight 3.0 mm bars J1(+) -> F1 -> J2(+)
    'F1':  (23.5, 22.1, 270),    # Pad 1 pair at y=17.14 (level w/ J1+), Pad 2 pair at y=27.06 (level w/ J2+)
    'D4':  (31.5, 22.0, 90),     # P6KE18A TVS: K (VBAT_F) at y=27.08, A (GND) at y=16.92
    'J3':  (29.8, 33.2, 0),      # Power switch: Pin 1 (VBAT_F) top, Pin 2 (VBAT_SW) bottom

    # ---- Logic power chain (west-south): D3 -> C14/C1 -> U2 -> C2 -> D5 -> Pico VSYS
    'D3':  (23.5, 39.8, 0),      # 1N5822: A (VBAT_SW) east at x=29.85, K (VBAT_D) west at x=17.15
    'C1':  (10.5, 43.0, 0),      # 10 uF ceramic input bypass next to U2.1
    'C14': (22.5, 49.5, 0),      # 470 uF 25V hold-up electrolytic behind D3
    'U2':  (11.5, 53.5, 0),      # RECOM R-78E5.0-0.5 (Pin 1=VBAT_D, 2=GND, 3=+5V)
    'C2':  (14.5, 58.6, 0),      # 10 uF ceramic 5V output bypass next to U2.3
    'D5':  (29.5, 59.5, 180),    # 1N5822 OR-ing: A (+5V) west at x=23.15, K (VSYS) east at x=35.85 -> U1.39

    # ---- Battery voltage sense right beside Pico Pin 31 (GP26/ADC0 at 41.11, 38.27)
    'R1':  (32.0, 49.5, 90),     # 100k: Pin 1 (VBAT_D) bottom (54.58), Pin 2 (VBAT_ADC) top (44.42)
    'R2':  (36.0, 49.5, 270),    # 22k: Pin 1 (VBAT_ADC) top (44.42), Pin 2 (GND) bottom (54.58)
    'C11': (35.5, 35.5, 90),     # 100nF ADC filter right beside U1.31

    # ---- East connector column (pad rows aligned 1-to-1 with Pico pins)
    'J7':  (65.27, 25.0, 180),   # 1.69" ST7789V2 LCD (2x4 header, Pin 1 bottom-right -> 0 vias!)
    'J5':  (67.0, 39.5, 0),      # Right AS5600 encoder (I2C1)
    'J4':  (67.0, 47.0, 0),      # Left AS5600 encoder (I2C0)
    'J10': (66.54, 52.5, 90),    # Weka dual ESC PWM (1x3 header)
    'J6':  (67.0, 60.2, 0),      # WitMotion WT901 IMU (UART0, +3V3)
    'C4':  (76.5, 43.5, 90),     # Shared +3V3 bypass cap for east connector bank

    # ---- North edge buttons (direct to Pico GP16 / GP15, internal pull-ups)
    'J9':  (43.0, 6.5, 0),       # MODE button
    'J8':  (62.0, 6.5, 0),       # START button

    # ---- Test points (clean bottom-west / top-west probing pads)
    'TP1': (9.5, 62.6, 0),       # +5V
    'TP3': (19.5, 62.6, 0),      # GND
    'TP4': (24.0, 34.2, 0),      # VBAT_SW
    'TP2': (79.5, 51.5, 0),      # +3V3
}
PLACE.update({'H%d' % (i + 1): (x, y, 0) for i, (x, y) in enumerate(HOLES)})
