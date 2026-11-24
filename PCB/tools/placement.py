"""Floorplan for Rev C, 85 x 65 mm (Rev B outline and M3 pattern, so the chassis plate still fits).
(x, y, rot): footprint pad-bbox centre in mm (board top-left origin), KiCad rotation in degrees.
The compact 70 x 56 variant is kept in archive/placement_compact_70x56.py."""
BOARD_W, BOARD_H, CORNER_R = 85.0, 65.0, 4.0
HOLES = [(4.0, 4.0), (81.0, 4.0), (4.0, 61.0), (81.0, 61.0)]   # M3, 77 x 57 mm pattern
TALL = ['J1', 'J2', 'J3', 'J4', 'J5', 'J6', 'J7', 'J8', 'J9', 'J10', 'U2', 'C12', 'C14']
PICO_CX, PICO_CY = 50.0, 37.0          # Pico 2 sockets, rot 180 -> GP0-GP15 column faces the connectors (east)

# XT30 housings are placed by footprint origin (pad 1); pad 2 is 5 mm further along the edge
ORIGIN = {'J1': (16.2, 12.15, 90), 'J2': (16.2, 32.0, 90)}

PLACE = {
    'U1': (PICO_CX, PICO_CY, 180),
    # ---- battery / protection cluster (west edge, top)
    'F1':  (24.5, 15.5, 270),
    'D4':  (29.0, 24.2, 270),
    'C12': (34.0, 24.0, 0),
    'J3':  (30.0, 31.2, 90),
    # ---- logic power chain, flows west
    'D3':  (31.0, 36.0, 0),
    'C1':  (24.0, 36.0, 0),
    'C14': (26.0, 43.5, 0),
    'U2':  (12.0, 46.0, 0),
    'C2':  (19.0, 47.0, 90),
    'U3':  (16.0, 56.5, 0),
    'C13': (23.0, 53.0, 0),
    'C3':  (22.6, 56.0, 0),
    'C4':  (22.6, 59.0, 0),
    'D5':  (33.0, 59.1, 180),
    'C5':  (37.4, 53.5, 90),
    # ---- battery sense, next to ADC0 (Pico pin 31)
    'R1':  (36.2, 30.0, 90),
    'R2':  (36.2, 34.0, 90),
    'R3':  (36.2, 40.0, 90),
    'C11': (32.5, 40.0, 90),
    # ---- right zone connectors (pad rows horizontal, pin 1 west)
    'J6':  (67.0, 60.2, 0),
    'J10': (66.54, 52.5, 90),
    'J4':  (67.0, 47.0, 0),
    'J5':  (67.0, 39.5, 0),
    'J7':  (65.27, 25.0, 180),
    # ---- top strip
    'J9':  (44.0, 6.5, 0),
    'J8':  (67.0, 6.5, 0),
    'R5':  (38.0, 8.5, 0),
    'C10': (51.0, 8.5, 0),
    'R4':  (57.5, 8.5, 0),
    'C9':  (75.0, 8.5, 0),
    # decoupling at the connectors
    'C6':  (75.0, 60.2, 90),
    'C7':  (75.0, 47.0, 90),
    'C8':  (75.0, 39.5, 90),
    # LEDs
    'R6':  (27.0, 63.0, 0),
    'D1':  (32.0, 63.0, 0),
    'R7':  (35.0, 13.0, 0),
    'D2':  (35.0, 10.5, 0),
    # test points
    'TP1': (9.0, 62.5, 0), 'TP2': (12.5, 62.5, 0), 'TP3': (16.0, 62.5, 0), 'TP4': (19.5, 62.5, 0),
}
PLACE.update({'H%d' % (i + 1): (x, y, 0) for i, (x, y) in enumerate(HOLES)})   # Rev B mounting pattern (chassis compatible)
