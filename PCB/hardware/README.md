# RobotEV controller board

Single-board controller and power distribution for the Science Olympiad
Electric Vehicle (4WD, 8×AA, Weka dual 20 A ESC, RP2350).

**Board:** 85 × 65 mm, 2 layers, 1.6 mm FR4, **2 oz copper recommended** (the ESC feed carries
motor stall current), 4 mm rounded corners, 4× M3 mounting holes on the same 77 × 57 mm pattern as
Rev B, so the chassis plate is unchanged. **Revision C** - same circuit and part list as Rev B,
re-placed and re-routed, plus two real bugs fixed (below). A buy list is in `BOM.xlsx`.

| | |
|---|---|
| MCU | Raspberry Pi Pico 2 (RP2350) in two 1×20 sockets, USB end toward the bottom edge |
| Battery | 8×AA pack on XT30 (9.6 V NiMH … ~12 V alkaline) |
| Motor driver | Weka dual 20 A ESC - fused power out + 2 PWM signals |
| Feedback | 2× AS5600 wheel encoders, WitMotion WT901 IMU |
| UI | 1.69" 240×280 ST7789V2 LCD on a 2.54 mm male header, 2 momentary buttons, 2 LEDs |
| Rails | VBAT → fuse → TVS/bulk → switch → Schottky → 5 V buck (0.5 A) → 3.3 V LDO; GND pours on both layers |

## What changed from Rev B

Rev B's README said "no shorts" and "ERC clean". Neither was true:

1. **VBAT shorted to VBAT_F** - two battery tracks crossed (KiCad reported `tracks_crossing`, which
   `build.py` filed as cosmetic), so the 15 A fuse F1 was bypassed. `tracks_crossing` is now a blocking
   DRC category.
2. **U3 (AMS1117-3.3) had no connections at all.** `gen_sch.py` embedded the symbol with an
   `(extends ...)` link KiCad could not resolve, so U3 had no pins: not in the netlist, not on the
   board, and ERC only showed three "unconnected wire endpoint" warnings. The +3V3 rail (LCD, both
   encoders, button pull-ups, power LED) therefore had **no source**. Fixed in `gen_sch.py`
   (`_flatten`) and in the checked-in schematic; U3's pads are now GND / +3V3 / +5V on the board.
3. **Layout.** 1 613 mm of copper and 102 vias → **533 mm and 107 vias** (20 signal/power vias, 87 sparse
   GND stitching vias). Signals run on F.Cu in the same order as the Pico pins; +3V3 and +5V are
   distributed on B.Cu; B.Cu is otherwise a solid GND plane. Connectors sit in one column on the east
   side, power on the west, buttons/LEDs on the north edge. XT30 housings are clear of the H1 screw
   head. Silkscreen labels no longer sit on pads or on the wrong part.
4. **Silkscreen art.** Front: refs, connector labels, `HARJAS SIDHU` (down the east edge) and a Voronoi
   web in the free space between parts. Back: `EV CONTROLLER REV C` and a full Voronoi web. All of it
   stops clear of pads, vias, screw heads and text. `relayout.py` generates it: change `seed=` in
   `back_art()` / `front_art()` for a different pattern, `NAME` for the name, or delete the
   `front_art(...)` call in `write_board()` to leave the front plain.
5. **Compact variant parked.** A 70 × 56 mm version (parts under the Pico) exists in
   `archive/placement_compact_70x56.py`; copy it over `tools/placement.py` (and set the board size in
   `tools/design.py`) to get it back.

**Build status (what has and has not been checked):** the layout tool's own checker reports
0 clearance / short / edge / hole-to-hole / courtyard violations, 0 open nets, and every GND pad
reaches the one connected pour (raster check). It is *not* KiCad: ERC, KiCad's DRC and the pour fill
have not been run on Rev C. Run `python tools/build.py` on the machine with KiCad 10 - it refills the
pours, runs ERC + DRC, gates on them and only then writes gerbers.

## Files

| Path | What it is |
|---|---|
| `RobotEV.kicad_sch` | Schematic (A2, generated) |
| `RobotEV.kicad_pcb` | PCB — placement, routing, pours, silkscreen |
| `RobotEV.pretty/` | Project footprint library (`Pico2_Socket_2x20_P2.54mm`) |
| `fp-lib-table` | Points KiCad at the project library |
| `../build/drc.rpt` | KiCad DRC report from the last build |
| `../build/erc.rpt` | KiCad ERC report |
| `../build/netlist.xml` | Netlist exported from the schematic |
| `../build/gerbers/` | Gerbers + Excellon drill file |
| `../build/schematic.pdf` | Printable schematic |
| `../build/board_top.png`, `board_bottom.png`, `layout_preview.png` | 2D renders from `tools/render.py` |

Everything in `hardware/` is generated. The circuit and pin map live in `tools/design.py`, the board
placement in `tools/placement.py`; edit those and rerun:

```
# one-time: pip install -r tools/requirements.txt   (numpy, scipy, matplotlib for the layout tool)
python tools/build.py          # schematic, netlist, relayout+route, pour fill, ERC, DRC, gerbers
python tools/relayout.py       # layout only (pure Python, no KiCad): place, route, self-check, write board
python tools/relayout.py --check   # self-check the board file as it stands
python tools/build.py --open   # ...and open pcbnew on the result
```

## Power path

```
J1 (XT30-M) BATTERY ──► F1 15 A ──► VBAT_F ──┬──► J2 (XT30-F)  ESC power (fused)
                                            ├──► D4 SMBJ16A TVS
                                            ├──► C12 100 µF
                                            └──► J3 PWR SW ──► VBAT_SW
                                                                  │
                                          D3 SS34 (reverse polarity)│
                                                                  ▼
                                         VBAT_D ──► C14 470 µF ──► U2 R-78E5.0-0.5 ──► +5V
+5V ──┬──► D5 SS34 ──► VSYS ──► Pico pin 39 (C5 100 nF)
      └──► WT901, U3 AMS1117-3.3 (C13 22 µF) ──► +3V3 (LCD, encoders)
```

* The switch header `J3` only carries the logic-side current (< 250 mA) — the
  ESC is powered directly from the battery. Fit a latching switch, or a jumper
  if you power-cycle by unplugging the pack.
* `J3` is a 2.54 mm 2-pin header on purpose: use whatever panel switch you have.
* The ESC's own +5 V BEC is **not** used; leave its 5 V wire unconnected.
* Protection fitted: **F1 15 A fuse**, **D4 SMBJ16A TVS** and **C12 100 µF** on
  the fused battery rail, **D3 SS34** reverse-polarity protection on the logic
  branch, and **C14 470 µF** holding up the buck input through a sag. The ESC
  tap (J2) is fused; the ESC's own BEC is still not used.

Load budget (measured requirements from the parts in `Goal.md`):
Pico 2 ≈ 100 mA on VSYS, WT901 ≈ 30 mA, LCD 3.3 V ≈ 90 mA max,
encoders ≈ 15 mA, LEDs ≈ 8 mA → ~250 mA from the 5 V buck (0.5 A rating).

## Pin map

| Pico pin | GPIO | Net | Goes to |
|---|---|---|---|
| 1 | GP0 | IMU_TX | J6.2 — WT901 RX |
| 2 | GP1 | IMU_RX | J6.3 — WT901 TX |
| 4 | GP2 | ESC_L | J10.1 PWM |
| 5 | GP3 | ESC_R | J10.2 PWM |
| 6 | GP4 | ENC_L_SDA | J4.3 (I2C0) |
| 7 | GP5 | ENC_L_SCL | J4.4 |
| 9 | GP6 | ENC_R_SDA | J5.3 (I2C1) |
| 10 | GP7 | ENC_R_SCL | J5.4 |
| 12 | GP9 | LCD_CS | J7.5 |
| 14 | GP10 | LCD_SCK | J7.4 |
| 15 | GP11 | LCD_MOSI | J7.3 |
| 16 | GP12 | LCD_DC | J7.6 |
| 17 | GP13 | LCD_RST | J7.7 |
| 19 | GP14 | LCD_BL | J7.8 |
| 20 | GP15 | BTN_START | J8, pull-up R4, 100 nF C9 |
| 21 | GP16 | BTN_MODE | J9, pull-up R5, 100 nF C10 |
| 22 | GP17 | LED_STAT | R7 100 Ω → D2 |
| 31 | GP26/ADC0 | VBAT_ADC | 100k/22k divider, 1k + 100 nF filter |
| 39 | VSYS | VSYS | via D5 SS34 from the buck output, C5 100 nF |

The two AS5600 modules share the fixed I²C address 0x36, so they are on
**separate buses** (I2C0 / I2C1) rather than behind a mux.

The GY-AS5600 breakouts supply their own 4.7 kΩ pull-ups to 3V3, so the board
does not fit a second set (parallel 2.35 kΩ is legal but pointless). If you use
a bare AS5600 on a carrier without pull-ups, add 4.7 kΩ from SDA and SCL to the
3V3 pin at J4/J5 — that is the one part of the bus to check before the first
power-up.

Battery sense: 13.2 V → 2.36 V, 8.0 V → 1.43 V at the ADC pin.

## Connector pinouts

| Ref | Part | Pin 1 … n |
|---|---|---|
| J1 | XT30 male | 1 = VBAT (unfused), 2 = GND |
| J2 | XT30 female | 1 = VBAT_F (fused), 2 = GND |
| J3 | 2.54 header | 1 = VBAT_F, 2 = VBAT_SW |
| J4 / J5 | JST-PH 4 | 1 = 3V3, 2 = GND, 3 = SDA, 4 = SCL |
| J6 | JST-PH 4 | 1 = 5V, 2 = GP0 → WT901 RX, 3 = WT901 TX → GP1, 4 = GND |
| J7 | 2.54 mm male 2×4 | 1 = 3V3, 2 = GND, 3 = DIN, 4 = CLK, 5 = CS, 6 = DC, 7 = RST, 8 = BL |
| J8 / J9 | JST-XH 2 | 1 = signal, 2 = GND (button to GND) |
| J10 | 2.54 mm male 3 | 1 = ESC_L, 2 = ESC_R, 3 = GND |

J7 (LCD) and J10 (ESC PWM) are male pin headers: female Dupont/jumper
connectors push straight on, and both are labelled on the silkscreen. J7 is a
2×4 block laid out odd/even and **rotated 180° in Rev C** (this routes the LCD with no vias): pin 1
(+3V3, square pad) is now the *bottom-right* corner; odd pins run up the right-hand column
(3V3, MOSI, CS, RST) and even pins up the left-hand column (GND, SCK, DC, BL). Go by the pin-1
square pad, not the old drawing. J10 is a horizontal row (pin 1 = ESC_L at the west end) and is
PWM only — the Weka ESC's BEC is not used, so there is no +5 V pin there.
The WT901's own 4-pin header is VCC/RX/TX/GND, so its TX lands on J6.3 and its
RX on J6.2 (the Pico's GP1/GP0 respectively).
LCD pin order follows the Waveshare 1.69" module wiring; check your module's
cable before plugging in.
Encoder connectors are 2.0 mm JST-PH (hand-solderable) rather than 1.0 mm —
check your AS5600 breakout and swap the footprint if it ships with a different plug.

## Bill of materials

| Ref | Value | Footprint |
|---|---|---|
| U1 | RPi Pico 2 module | 2× socket strip 1×20, 2.54 mm, 17.78 mm rows |
| U2 | Recom R-78E5.0-0.5 | SIP-3 (Converter_DCDC R-78E) |
| U3 | AMS1117-3.3 | SOT-223 |
| J1 | XT30PW-M | AMASS XT30 horizontal |
| J2 | XT30PW-F | AMASS XT30 horizontal |
| J3 | 2-pin header | PinHeader 1×02 2.54 mm |
| J4, J5, J6 | JST-PH 4 | JST PH B4B-PH-K vertical |
| J7 | 8-pin header | PinHeader 2×04 2.54 mm vertical |
| J8, J9 | JST-XH 2 | JST XH B2B-XH-A vertical |
| J10 | 3-pin header | PinHeader 1×03 2.54 mm vertical |
| R1 / R2 / R3 | 100k / 22k / 1k | 0805 |
| R4 / R5 | 10k | 0805 |
| R6 / R7 | 1k / 100 | 0805 |
| C1 | 10 µF 25 V | 1206 |
| C2, C3 | 10 µF | 0805 |
| C4–C11 | 100 nF | 0805 |
| C13 | 22 µF (AMS1117 output) | 1206 |
| D1 | green LED | 0805 |
| D2 | blue LED | 0805 |
| D5 | SS34 Schottky (+5 V → VSYS) | SMB |
| D3 | SS34 Schottky (reverse polarity) | SMB |
| D4 | SMBJ16A TVS | SMB |
| F1 | 15 A fuse | 2920 (7451 metric) |
| C12 | 100 µF 16 V | radial 5 mm / 2 mm pitch |
| C14 | 470 µF 16 V | radial 8 mm / 3.5 mm pitch |
| TP1–TP4 | +5V, +3V3, GND, VBAT_SW | 1.5 mm test pad |
| H1–H4 | M3 | 3.2 mm hole |

## Design rules used

| Rule | Value |
|---|---|
| Clearance | 0.2 mm |
| Signal track | 0.25 mm |
| +5 V / +3 V3 / GND track | 0.5 mm |
| VBAT_SW / VBAT_D | 0.8 mm |
| VBAT / VBAT_F | 1.2 mm (raise / double up if you pull > 5 A continuously) |
| Via | 0.8 / 0.4 mm |
| Copper to edge | 0.7 mm |
| Ground | poured on F.Cu and B.Cu, stitched with vias |

Verify before ordering (KiCad's DRC is the authority - this is what `build.py` runs):

```
"C:/Program Files/KiCad/10.0/bin/kicad-cli.exe" pcb drc hardware/RobotEV.kicad_pcb
```

`tools/relayout.py` has its own checker (exact copper-to-copper clearance 0.2 mm, shorts, board edge
0.3 mm, via/pad hole spacing, courtyards, connectivity of every non-GND net, and a raster check that
all 38 GND pads sit in one connected pour). It found 0 problems on Rev C, but it does not replace KiCad.
`build.py` treats `tracks_crossing`, `courtyards_overlap`, open nets, shorts and clearance as blocking.

The GND pours are written *unfilled*; `tools/fill_zones.py` (run by `build.py` with KiCad's Python)
fills them. If you open the board in pcbnew before running the build, press **B** to fill zones
before checking anything.

### How routing works

`tools/router.py` is a two-layer grid router (0.1 mm grid, 0.2 mm clearance + 0.02 mm margin, A* with
turn and via penalties). Net classes: VBAT / VBAT_F 2.5-3.0 mm (falls back to narrower only if it must),
VBAT_SW / VBAT_D 0.8 mm, +5V / +3V3 / VSYS 0.5 mm, signals 0.25 mm. +3V3 and +5V prefer B.Cu so
signals on F.Cu never cross them. Same placement always gives the same copper. If a future edit makes
a net unroutable the tool tries 12 net orders before giving up and exits non-zero.

## Assembly notes

1. Solder the 0805 passives and the SOT-223 LDO first, then the connectors.
2. J7 (2×4) and J10 (1×3) are 2.54 mm male headers — fit them with the pins pointing up, flush to the board, and note J7's rotated odd/even pin order (pin 1 = square pad) before crimping the LCD lead.
3. Fit the two 20-pin sockets for the Pico; the module's USB faces the **bottom** edge (leave the area below it free).
4. Check VBAT/5 V/3.3 V on TP4/TP1/TP2 before plugging in the Pico. **3.3 V must read 3.3 V** - on Rev B it could not, because U3 was unwired.
5. Mount with M3 × 6 screws; keep ~6 mm clearance under the board for the Pico's pins.
6. Check C12/C14 polarity and fit F1 before the first power-up; the fuse is in
   the battery lead, so a short on VBAT_F is cleared by it.
