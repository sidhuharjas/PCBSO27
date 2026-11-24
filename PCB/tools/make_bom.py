"""Build hardware/BOM.xlsx (what to buy) from tools/design.py.  Prices are left for you to fill in."""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import design as D
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT = os.path.join(os.path.dirname(HERE), 'hardware', 'BOM.xlsx')
F = 'Arial'
HDR = PatternFill('solid', fgColor='1F3864'); BAND = PatternFill('solid', fgColor='EEF2F8'); YEL = PatternFill('solid', fgColor='FFFF00')
thin = Side(style='thin', color='BFBFBF'); BOX = Border(left=thin, right=thin, top=thin, bottom=thin)

# (group key -> row).  refs are taken from design.PARTS so the list can't drift from the board.
by_ref = {p['ref']: p for p in D.PARTS}
def refs(*rs): return [r for r in rs if r in by_ref]
ROWS = [
 # category, refs, description, package, suggested part (verify stock), spare, note
 ('Resistor', refs('R1'), '100 kΩ 1 % thick film', '0805', 'Yageo RC0805FR-07100KL or equivalent', 5, 'Battery-sense divider, top leg'),
 ('Resistor', refs('R2'), '22 kΩ 1 % thick film', '0805', 'Yageo RC0805FR-0722KL or equivalent', 5, 'Divider bottom leg (max ADC input at 12.8 V pack ≈ 2.3 V)'),
 ('Resistor', refs('R4', 'R5'), '10 kΩ 1 % thick film', '0805', 'Yageo RC0805FR-0710KL or equivalent', 5, 'Button pull-ups'),
 ('Resistor', refs('R3', 'R6'), '1 kΩ 1 % thick film', '0805', 'Yageo RC0805FR-071KL or equivalent', 5, 'ADC series resistor, power-LED resistor'),
 ('Resistor', refs('R7'), '100 Ω 1 % thick film', '0805', 'Yageo RC0805FR-07100RL or equivalent', 5, 'Status-LED resistor'),
 ('Capacitor', refs('C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C11'), '100 nF, 50 V, X7R', '0805', 'Samsung CL21B104KBCNNNC or equivalent', 10, 'Decoupling / debounce / ADC filter'),
 ('Capacitor', refs('C2', 'C3'), '10 µF, 25 V, X5R/X7R', '0805', 'Samsung CL21A106KAYNNNE or equivalent', 4, '5 V and 3.3 V bulk'),
 ('Capacitor', refs('C1'), '10 µF, 25 V, X5R/X7R', '1206', 'Samsung CL31A106KAHNNNE or equivalent', 2, 'Buck input bulk'),
 ('Capacitor', refs('C13'), '22 µF, ≥16 V, X5R', '1206', 'Samsung CL31A226KAHNNNE or equivalent', 2, 'AMS1117 output, needs ≥ 22 µF'),
 ('Capacitor', refs('C12'), '100 µF, 16 V, low-ESR electrolytic', 'Radial D5 mm, 2.0 mm pitch', 'any 105 °C low-ESR 100 µF/16 V, 5 mm', 1, 'Bulk at the battery / ESC tap'),
 ('Capacitor', refs('C14'), '470 µF, 16 V, low-ESR electrolytic', 'Radial D8 mm, 3.5 mm pitch', 'any 105 °C low-ESR 470 µF/16 V, 8 mm', 1, 'Buck-input hold-up. A fresh alkaline pack is ≈ 12.8 V, so 16 V is the minimum rating'),
 ('LED', refs('D1'), 'LED green, 20 mA class', '0805', 'any 0805 green LED', 4, 'Power indicator (3.3 V, 1 kΩ)'),
 ('LED', refs('D2'), 'LED blue, 20 mA class', '0805', 'any 0805 blue LED', 4, 'Status indicator (100 Ω; blue Vf ≈ 3 V, current is small)'),
 ('Diode', refs('D3', 'D5'), 'Schottky 40 V 3 A', 'SMB (DO-214AA)', 'SS34 (many makers)', 2, 'D3 reverse-polarity, D5 buck → VSYS'),
 ('Diode', refs('D4'), 'TVS 16 V unidirectional, 600 W', 'SMB (DO-214AA)', 'SMBJ16A (many makers)', 1, 'Surge clamp on the fused battery rail'),
 ('Fuse', refs('F1'), '15 A fuse, rated ≥ 24 V DC', '2920 (7451 metric) SMD', '2920 SMD fuse, 15 A – check the footprint/current rating of the exact part', 1, 'Protects ESC feed and logic. Make sure its DC voltage rating ≥ 12.8 V'),
 ('IC', refs('U2'), '12 V → 5 V, 0.5 A DC-DC module', 'SIP-3 (RECOM R-78E)', 'RECOM R-78E5.0-0.5', 1, 'Logic supply (input range 7–34 V)'),
 ('IC', refs('U3'), '3.3 V 1 A LDO', 'SOT-223', 'AMS1117-3.3', 2, 'LCD / encoders / IMU rail'),
 ('Connector', refs('J1'), 'XT30PW male, right-angle PCB', 'AMASS XT30PW-M', 'AMASS XT30PW-M', 1, 'Battery in. Mates with a female XT30 plug on the pack lead'),
 ('Connector', refs('J2'), 'XT30PW female, right-angle PCB', 'AMASS XT30PW-F', 'AMASS XT30PW-F', 1, 'ESC power out. Mates with a male XT30 plug on the ESC lead'),
 ('Connector', refs('J4', 'J5', 'J6'), 'JST PH 2.0 mm, 4-pin, top entry', 'B4B-PH-K', 'JST B4B-PH-K-S', 1, 'Encoders L/R and IMU'),
 ('Connector', refs('J8', 'J9'), 'JST XH 2.5 mm, 2-pin, top entry', 'B2B-XH-A', 'JST B2B-XH-A', 1, 'START / MODE buttons'),
 ('Connector', refs('J3'), '1×2 male pin header, 2.54 mm', 'PinHeader 1x02', '2.54 mm breakaway male header strip', 1, 'Power switch / jumper. Buy a 1×40 strip and snap'),
 ('Connector', refs('J10'), '1×3 male pin header, 2.54 mm', 'PinHeader 1x03', '2.54 mm breakaway male header strip', 1, 'ESC PWM'),
 ('Connector', refs('J7'), '2×4 male pin header, 2.54 mm', 'PinHeader 2x04', '2.54 mm breakaway male header, 2 rows', 1, 'LCD. Buy a 2×40 strip and snap'),
]
EXTRA_ROWS = [  # not in design.PARTS but needed to build the board
 ('Connector', ['U1'], '2× 1×20 female socket, 2.54 mm, standard 8.5 mm height', 'Socket 1x20', 'Standard (not low-profile) female header', 1, 'The Pico must stand ~8.5 mm up: small parts sit under it'),
]

OFFBOARD = [  # category, item, qty, notes
 ('Brain', 'Raspberry Pi Pico 2 (RP2350), no pre-soldered headers needed', 1, 'Plugs into the two sockets. Buy a spare'),
 ('Motors / drive', 'Weka dual brushed 20 A ESC (PWM input)', 1, 'Takes 3 pins on J10; its 5 V BEC is not used'),
 ('Motors / drive', 'DartBox Gecko gearmotor, 22.5:1', 2, 'From your build; wires to the ESC, not the board'),
 ('Sensing', 'AS5600 magnetic encoder board', 2, 'One per wheel, with magnet; I2C on J4 / J5'),
 ('Sensing', 'WitMotion WT901 IMU (TTL UART)', 1, 'On J6; order VCC / RX / TX / GND'),
 ('UI', 'Waveshare 1.69" 240×280 LCD (ST7789V2)', 1, 'Its 8-wire lead goes to J7'),
 ('UI', 'Momentary push button (normally open), panel mount', 2, 'START and MODE, 2 wires each'),
 ('UI', 'Latching switch or toggle, ≥ 2 A, 2 wires', 1, 'Across J3'),
 ('Power', '8×AA battery holder with XT30 (female) lead', 1, 'Or a holder + XT30 female plug to solder'),
 ('Power', 'AA cells (NiMH recommended)', 8, ''),
 ('Power', 'XT30 male plug with 14–16 AWG lead, for the ESC end', 1, 'Mates with J2; skip if the ESC already has one'),
 ('Cables', 'JST PH 4-pin pre-crimped cable, 2.0 mm', 3, 'Encoders ×2, IMU ×1 (or PHR-4 housing + SPH-002T crimps)'),
 ('Cables', 'JST XH 2-pin pre-crimped cable, 2.5 mm', 2, 'Button leads (or XHP-2 housing + SXH-001T crimps)'),
 ('Cables', 'Dupont female-female jumpers, 2.54 mm', 11, '8 for the LCD, 3 for ESC PWM; or a 1×3 servo-style lead'),
 ('Hardware', 'M3 screws + standoffs/spacers (4×)', 4, 'Board is held on a 77 × 57 mm pattern'),
 ('PCB', 'Bare PCB, 85 × 65 mm, 2-layer, 2 oz copper', 5, 'Hardware/gerbers from `python tools/build.py`. Order 5; the minimum is usually 5'),
 ('Tools', 'Solder, flux, fine-tip iron; tweezers; 0805-friendly', 1, 'Hand-solderable: smallest parts are 0805'),
]

wb = Workbook()
ws = wb.active; ws.title = 'PCB parts'
ws['A1'] = 'EV controller board (Rev C): parts to buy'; ws['A1'].font = Font(name=F, size=14, bold=True)
ws['A2'] = ('Blue cells are yours to edit: Spare, Unit price, Have. Qty is counted from the Refs column. '
            'Part numbers are suggestions that match the footprints: check stock and datasheet before buying. Prices are left blank on purpose.')
ws['A2'].font = Font(name=F, size=9, italic=True); ws['A2'].alignment = Alignment(wrap_text=True, vertical='top'); ws.merge_cells('A2:L2'); ws.row_dimensions[2].height = 28
heads = ['#', 'Category', 'Refs', 'Qty', 'Description / value', 'Package', 'Suggested part (verify)', 'Spare', 'Order qty', 'Unit price ($)', 'Line total ($)', 'Notes']
HR = 4
for c, h in enumerate(heads, 1):
    cell = ws.cell(HR, c, h); cell.font = Font(name=F, bold=True, color='FFFFFF'); cell.fill = HDR; cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True); cell.border = BOX
r = HR + 1
for i, (cat, rf, desc, pkg, sug, spare, note) in enumerate(ROWS + EXTRA_ROWS, 1):
    vals = [i, cat, ', '.join(rf), f'=LEN(C{r})-LEN(SUBSTITUTE(C{r},",",""))+1', desc, pkg, sug, spare, f'=D{r}+H{r}', None, f'=I{r}*J{r}', note]
    for c, v in enumerate(vals, 1):
        cell = ws.cell(r, c, v); cell.font = Font(name=F, size=10); cell.border = BOX; cell.alignment = Alignment(vertical='top', wrap_text=c in (3, 5, 6, 7, 12))
        if i % 2 == 0: cell.fill = BAND
    ws.cell(r, 8).font = Font(name=F, size=10, color='0000FF'); ws.cell(r, 10).font = Font(name=F, size=10, color='0000FF'); ws.cell(r, 10).number_format = '$#,##0.00;($#,##0.00);-'; ws.cell(r, 11).number_format = '$#,##0.00;($#,##0.00);-'
    ws.cell(r, 10).fill = YEL
    r += 1
last = r - 1
ws.cell(r, 10, 'Parts total').font = Font(name=F, bold=True); ws.cell(r, 10).alignment = Alignment(horizontal='right')
t = ws.cell(r, 11, f'=SUM(K{HR+1}:K{last})'); t.font = Font(name=F, bold=True); t.number_format = '$#,##0.00;($#,##0.00);-'
ws.cell(r + 2, 1, 'Not bought: test points TP1–TP4 are bare copper pads, H1–H4 are M3 holes (screws are on the Off-board sheet). Reference counts come from tools/design.py.').font = Font(name=F, size=9, italic=True)
for col, w in zip('ABCDEFGHIJKL', [4, 11, 22, 6, 34, 22, 36, 7, 9, 13, 13, 52]): ws.column_dimensions[col].width = w
ws.freeze_panes = ws.cell(HR + 1, 1); ws.row_dimensions[HR].height = 30

w2 = wb.create_sheet('Off-board')
w2['A1'] = 'Everything else to buy (not on the PCB)'; w2['A1'].font = Font(name=F, size=14, bold=True)
w2['A2'] = 'Blue cells are yours to edit. Mark "Have" for anything you already own; Order qty then drops to what is left to buy.'; w2['A2'].font = Font(name=F, size=9, italic=True)
h2 = ['#', 'Category', 'Item', 'Qty needed', 'Have', 'Order qty', 'Unit price ($)', 'Line total ($)', 'Notes']
for c, h in enumerate(h2, 1):
    cell = w2.cell(4, c, h); cell.font = Font(name=F, bold=True, color='FFFFFF'); cell.fill = HDR; cell.alignment = Alignment(horizontal='center', wrap_text=True); cell.border = BOX
r = 5
for i, (cat, item, q, note) in enumerate(OFFBOARD, 1):
    vals = [i, cat, item, q, 0, f'=MAX(D{r}-E{r},0)', None, f'=F{r}*G{r}', note]
    for c, v in enumerate(vals, 1):
        cell = w2.cell(r, c, v); cell.font = Font(name=F, size=10); cell.border = BOX; cell.alignment = Alignment(vertical='top', wrap_text=c in (3, 9))
        if i % 2 == 0: cell.fill = BAND
    for c in (4, 5, 7): w2.cell(r, c).font = Font(name=F, size=10, color='0000FF')
    w2.cell(r, 7).fill = YEL; w2.cell(r, 7).number_format = '$#,##0.00;($#,##0.00);-'; w2.cell(r, 8).number_format = '$#,##0.00;($#,##0.00);-'
    r += 1
w2.cell(r, 7, 'Off-board total').font = Font(name=F, bold=True); w2.cell(r, 7).alignment = Alignment(horizontal='right')
t = w2.cell(r, 8, f'=SUM(H5:H{r-1})'); t.font = Font(name=F, bold=True); t.number_format = '$#,##0.00;($#,##0.00);-'
w3 = r + 2
w2.cell(w3, 7, 'Grand total (both sheets)').font = Font(name=F, bold=True); w2.cell(w3, 7).alignment = Alignment(horizontal='right')
g = w2.cell(w3, 8, f"=H{r}+'PCB parts'!K{last+1}"); g.font = Font(name=F, bold=True); g.number_format = '$#,##0.00;($#,##0.00);-'
for col, w in zip('ABCDEFGHI', [4, 15, 52, 11, 8, 10, 13, 14, 58]): w2.column_dimensions[col].width = w
w2.freeze_panes = 'A5'
wb.save(OUT); print('wrote', OUT)
