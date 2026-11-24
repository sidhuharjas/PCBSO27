"""Floorplan for Rev C (compact).  (x, y, rot): footprint pad-bbox centre in mm, KiCad rotation in degrees.

Board 70 x 56 mm.  Small SMD parts (LDO, caps, divider, VSYS diode) sit UNDER the Pico module,
which floats ~8.5 mm above the board on standard 2.54 mm sockets.  Tall parts (anything over ~6 mm)
must stay outside the module outline - relayout.py checks that (TALL below).
"""
BOARD_W, BOARD_H, CORNER_R = 70.0, 56.0, 3.5
HOLES = [(4.0, 4.0), (BOARD_W - 4.0, 4.0), (4.0, BOARD_H - 4.0), (BOARD_W - 4.0, BOARD_H - 4.0)]   # M3

PICO_CX, PICO_CY = 40.5, 27.5     # Pico 2 sockets, rot 180 -> GP0-GP15 column faces the connectors (east)
TALL = ['J1', 'J2', 'J3', 'J4', 'J5', 'J6', 'J7', 'J8', 'J9', 'J10', 'U2', 'C12', 'C14']

# XT30 housings are placed by footprint origin (pad 1); they plug in from the west edge
ORIGIN = {'J1': (16.2, 13.2, 90), 'J2': (16.2, 32.65, 90)}

PLACE = {
    'U1': (PICO_CX, PICO_CY, 180),
    # ---- battery / protection / switch column (x 19.5 .. 29.5)
    'F1':  (24.5, 15.9, 270),
    'D4':  (21.9, 25.0, 270),
    'C12': (27.0, 24.0, 0),
    'J3':  (24.5, 30.5, 90),
    'D3':  (24.5, 35.0, 0),
    'C1':  (24.5, 38.4, 0),
    'C14': (24.2, 44.8, 0),
    'U2':  (12.0, 46.0, 0),
    'C2':  (15.0, 50.6, 90),
    # ---- under the Pico (channel between the socket columns)
    'U3':  (40.0, 41.5, 0),
    'C13': (40.5, 36.0, 0),
    'C3':  (46.4, 37.4, 90),
    'C4':  (46.4, 41.4, 90),
    'D5':  (37.0, 49.6, 0),
    'C5':  (42.5, 49.6, 90),
    'R1':  (34.8, 21.5, 90),
    'R2':  (34.8, 25.5, 90),
    'R3':  (34.8, 29.5, 90),
    'C11': (37.8, 29.5, 90),
    # ---- right zone connectors (pad rows horizontal, pin 1 west)
    'J6':  (57.0, 50.7, 0),
    'J10': (56.54, 43.0, 90),
    'J4':  (57.0, 37.5, 0),
    'J5':  (57.0, 30.0, 0),
    'J7':  (55.27, 15.5, 180),
    'J8':  (55.75, 4.5, 0),
    'R4':  (62.2, 8.6, 0),
    'C9':  (62.2, 11.8, 90),
    'C6':  (57.0, 46.6, 0),
    'C7':  (64.2, 37.5, 90),
    'C8':  (64.2, 30.0, 90),
    # ---- top-left strip: BTN_MODE + status LED
    'J9':  (14.0, 4.5, 0),
    'R5':  (35.2, 7.5, 90),
    'C10': (35.2, 11.0, 90),
    'R7':  (21.0, 6.4, 0),
    'D2':  (24.6, 6.4, 0),
    # ---- bottom strip (below the module): power LED + test points; TP4 sits by the switch header
    'R6':  (46.0, 54.6, 0),
    'D1':  (49.6, 54.6, 0),
    'TP1': (30.0, 54.4, 0), 'TP2': (33.3, 54.4, 0), 'TP3': (36.6, 54.4, 0), 'TP4': (28.85, 31.0, 0),
}
PLACE.update({'H%d' % (i + 1): (x, y, 0) for i, (x, y) in enumerate(HOLES)})
