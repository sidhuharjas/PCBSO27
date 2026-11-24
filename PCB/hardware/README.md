# EV Controller Board — Rev D (100% Through-Hole, Zero SMD)

Custom 2-layer carrier PCB for a **Science Olympiad Electric Vehicle (Division C, 2027)** built around a **Raspberry Pi Pico 2 (RP2350)**, an **8xAA battery pack**, a **Weka dual 20 A brushed ESC**, **two AS5600 magnetic wheel encoders**, a **WitMotion WT901 UART IMU**, and a **Waveshare 1.69" ST7789V2 IPS LCD**.

**Board geometry:** `85 × 65 mm`, 4 mm rounded corners, 4× M3 mounting holes on a `77 × 57 mm` pattern (100% drop-in chassis-compatible with Rev B/C).

---

## What Changed in Rev D (vs. Rev C)

| Metric / Feature | Rev C | **Rev D** | Improvement |
|---|---|---|---|
| **Soldered SMD components** | **26** | **0** | **100% through-hole — standard iron only** |
| **Electrical components to solder** | 29 | **12** | **59% fewer electrical parts** |
| **Total soldered parts (incl. connectors)** | 40 | **23** | **43% fewer solder joints** |
| **XT30 polarity (`J1` / `J2`)** | Reversed (`+` on GND!) | **Fixed (`Pin 1 = -`, `Pin 2 = +`)** | **Prevented dead short on plug-in** |
| **15 A main fuse (`F1`)** | Soldered 2920 SMD | **Keystone 3568 mini blade holder** | **Tool-free 2-second competition swap** |
| **15 A power bus copper** | Single-sided 3.0 mm | **Double-sided 3.0 mm (`F.Cu + B.Cu`)** | **2× copper cross-section (6 mm eff.)** |
| **3.3 V rail regulator** | External `AMS1117-3.3` + MLCC | **Pico 2 onboard `RT6154A` SMPS** | **Zero oscillation risk + USB-only bench testing** |
| **Hold-up cap `C14` rating** | 470 µF 16 V | **470 µF 25 V** | **Proper derating for 13.2 V fresh 8×AA** |
| **Routed signal/power vias** | 8 | **1** (0 on signals!) | **Cleaner 2-layer routing + solid GND planes** |

### Critical Bug Fixed from Rev C
- **Reversed XT30 polarity on `J1` and `J2`:** Official KiCad `AMASS_XT30PW-M` and `AMASS_XT30PW-F` footprints map **Pin 1 (square pad, `-` silk)** to negative and **Pin 2 (round pad, `+` silk)** to positive. Rev C wired Pin 1 to `VBAT`/`VBAT_F` and Pin 2 to `GND`, which would have dead-shorted the battery pack through `D4` and blown the fuse (or damaged the ESC) on first connection. Rev D corrects both connectors to `Pin 1 = GND (-)`, `Pin 2 = VBAT / VBAT_F (+)`, which also places `J1 (+)` and `J2 (+)` directly facing each other (`9.85 mm` apart) right beside the Keystone 3568 blade fuse holder (`9.92 mm` pitch).

### 17 Eliminated Components (Why Every Removal Makes the Board Better)
1. **`U3` (`AMS1117-3.3`) + `C13` + `C3` removed:** The Pico 2's built-in RT6154A buck-boost regulator (`Pin 36: 3V3`) is rated for **300 mA** external load. Total worst-case 3.3 V draw on this board is **≤128 mA** (LCD ≤90 mA + 2× AS5600 ~13 mA + WT901 <25 mA — >2.3× safety margin). Removing `U3` eliminates AMS1117's notorious low-ESR MLCC oscillation risk, eliminates back-powering hazards when plugged into USB, and lets you bench-test **the LCD, IMU, and encoders over USB alone without a battery**.
2. **`J6` (WT901 IMU) moved from `+5V` to `+3V3`:** The WT901 datasheet specifies `3.3–5 V` supply (`<25 mA`, `11.5 mA` typ.) and 3.3 V-only UART I/O. Running it on `+3V3` guarantees its UART stays powered in sync with the RP2350 on both battery and USB.
3. **`C12` (100 µF) removed:** Redundant with `C2` (`10 µF` low-ESR ceramic) and the Pico 2's onboard `47 µF` `VSYS` capacitor; keeps capacitive load well within RECOM `R-78E5.0-0.5`'s `≤100 µF` output-cap limit.
4. **`C5`, `C6`, `C7`, `C8` removed (kept shared `C4` 100 nF on east `+3V3` bus):** All four off-board breakouts (LCD, WT901, 2× AS5600) already carry their own onboard decoupling capacitors.
5. **`R3` (1 kΩ) removed:** The `100 kΩ / 22 kΩ` divider (`R1 || R2 = 18 kΩ`) already limits fault current into `GP26/ADC0` to `<0.2 mA` and forms an `88 Hz` low-pass filter directly with `C11` (`100 nF`).
6. **`R4`, `R5`, `C9`, `C10` removed:** The RP2350 has built-in programmable pull-ups (~50–80 kΩ) on `GP15`/`GP16` and handles button debounce in 5 lines of firmware.
7. **`D1`, `R6`, `D2`, `R7` removed:** Use the Pico 2's onboard `GP25` LED, the 1.69" IPS LCD, and test pads `TP1`–`TP4` for status and power verification (also frees `GP17` for future expansion).

---

## Power Architecture

```text
8xAA Pack (9.6–13.2 V)
  │
  ▼  J1 (XT30PW-M: Pin 1 '-' GND, Pin 2 '+' VBAT)
  ├──[ 3.0 mm F.Cu + 3.0 mm B.Cu bus ]──► F1 (Keystone 3568 + 15 A Mini Blade Fuse)
  │                                         │ VBAT_F
  │                                         ├──[ 3.0 mm F.Cu + 3.0 mm B.Cu ]──► J2 (XT30PW-F -> Weka Dual 20A ESC)
  │                                         ├──► D4 (P6KE18A 600 W TVS -> GND, clamps brushed-motor spikes)
  │                                         └──► J3 (Logic Power Switch, <250 mA)
  │                                                │ VBAT_SW (TP4)
  │                                                ▼
  │                                              D3 (1N5822 40V 3A Schottky: reverse-polarity + hold-up isolator)
  │                                                │ VBAT_D
  │                                                ├──► C14 (470 µF 25V hold-up) + C1 (10 µF 50V ceramic)
  │                                                ├──► R1 (100k) / R2 (22k) + C11 (100nF) ──► Pico GP26/ADC0
  │                                                └──► U2 (RECOM R-78E5.0-0.5, 5 V 500 mA buck)
  │                                                       │ +5V (TP1) + C2 (10 µF 50V ceramic)
  │                                                       ▼
  │                                                     D5 (1N5822 40V 3A Schottky OR-ing diode)
  │                                                       │ VSYS
  │                                                       ▼
  │                                              U1 (Raspberry Pi Pico 2, Pin 39 VSYS — USB-safe!)
  │                                                       │ Pin 36: +3V3 (onboard RT6154A SMPS, 300 mA max)
  │                                                       └──► C4 (100nF), TP2, J4 (ENC_L), J5 (ENC_R), J6 (WT901), J7 (LCD)
```

### Battery Voltage Sense Math (`GP26 / ADC0`)
- Divider ratio: `V_ADC = VBAT_D × 22k / (100k + 22k) = VBAT_D × 0.18033`
- Account for ~0.30 V drop across `D3` (`1N5822` at ~150 mA):
  `V_BATT ≈ (V_ADC / 0.18033) + 0.30 V`
- Fresh 8×AA alkaline (`13.2 V` → `VBAT_D ≈ 12.9 V`): `V_ADC = 2.33 V` (safe margin below `3.3 V` ADC max; survives up to `18.6 V` input!).

---

## RP2350 Pin Map (`U1` — Raspberry Pi Pico 2)

| Pico Pin | GPIO | Net | Destination | Firmware Notes |
|---|---|---|---|---|
| 1 | GP0 | `IMU_TX` | `J6.2` (WT901 RX) | UART0 TX (3.3 V logic) |
| 2 | GP1 | `IMU_RX` | `J6.3` (WT901 TX) | UART0 RX (3.3 V logic) |
| 4 | GP2 | `ESC_L` | `J10.1` | 50 Hz servo PWM (left motor) |
| 5 | GP3 | `ESC_R` | `J10.2` | 50 Hz servo PWM (right motor) |
| 6 | GP4 | `ENC_L_SDA` | `J4.3` | I2C0 SDA (AS5600 `0x36`, breakout has 4.7k pull-up) |
| 7 | GP5 | `ENC_L_SCL` | `J4.4` | I2C0 SCL |
| 9 | GP6 | `ENC_R_SDA` | `J5.3` | I2C1 SDA (AS5600 `0x36`, breakout has 4.7k pull-up) |
| 10 | GP7 | `ENC_R_SCL` | `J5.4` | I2C1 SCL |
| 12 | GP9 | `LCD_CS` | `J7.5` | SPI1 CS |
| 14 | GP10 | `LCD_SCK` | `J7.4` | SPI1 SCK |
| 15 | GP11 | `LCD_MOSI` | `J7.3` | SPI1 TX |
| 16 | GP12 | `LCD_DC` | `J7.6` | LCD Data/Command |
| 17 | GP13 | `LCD_RST` | `J7.7` | LCD Reset |
| 19 | GP14 | `LCD_BL` | `J7.8` | LCD Backlight (PWM dimmable) |
| 20 | GP15 | `BTN_START` | `J8.1` | **Enable internal pull-up** + 20 ms software debounce |
| 21 | GP16 | `BTN_MODE` | `J9.1` | **Enable internal pull-up** + 20 ms software debounce |
| 22 | GP17 | *(spare)* | — | Freed in Rev D (use Pico onboard `GP25` LED for status) |
| 31 | GP26 | `VBAT_ADC` | `R1`/`R2`/`C11` | ADC0 battery monitor (`88 Hz` LPF) |
| 36 | 3V3 | `+3V3` | `J4, J5, J6, J7, C4, TP2` | Onboard RT6154A SMPS output (≤128 mA / 300 mA max) |
| 39 | VSYS | `VSYS` | `D5.1 (K)` | OR-ed 5 V rail (~4.7 V after D5; USB-safe) |
| 3,8,13,18,23,28,33,38 | GND | `GND` | Solid top + bottom pours | Connected to 85 stitching vias |

---

## Connector Pinouts (Pin 1 = Square Pad on PCB)

| Ref | Label | Connector | Pinout |
|---|---|---|---|
| `J1` | `BATT 8xAA` | `AMASS XT30PW-M` | `1 = GND (-)` · `2 = VBAT (+)` |
| `J2` | `ESC PWR` | `AMASS XT30PW-F` | `1 = GND (-)` · `2 = VBAT_F (+)` |
| `J3` | `PWR SW` | `1×2 2.54 mm` header | `1 = VBAT_F` · `2 = VBAT_SW` |
| `J4` | `ENC L` | `JST-PH 4-pin` (2.0 mm) | `1 = +3V3` · `2 = GND` · `3 = SDA (GP4)` · `4 = SCL (GP5)` |
| `J5` | `ENC R` | `JST-PH 4-pin` (2.0 mm) | `1 = +3V3` · `2 = GND` · `3 = SDA (GP6)` · `4 = SCL (GP7)` |
| `J6` | `WT901` | `JST-PH 4-pin` (2.0 mm) | `1 = +3V3` · `2 = IMU_TX (→WT901 RX)` · `3 = IMU_RX (←WT901 TX)` · `4 = GND` |
| `J7` | `LCD` | `2×4 2.54 mm` header | Odd: `1=+3V3, 3=MOSI, 5=CS, 7=RST` · Even: `2=GND, 4=SCK, 6=DC, 8=BL` |
| `J8` | `START` | `JST-XH 2-pin` (2.5 mm) | `1 = BTN_START (GP15)` · `2 = GND` |
| `J9` | `MODE` | `JST-XH 2-pin` (2.5 mm) | `1 = BTN_MODE (GP16)` · `2 = GND` |
| `J10` | `ESC SIG` | `1×3 2.54 mm` header | `1 = ESC_L (GP2)` · `2 = ESC_R (GP3)` · `3 = GND` *(do NOT connect ESC BEC +5V)* |

---

## Complete PCB BOM (100% Through-Hole — 0 SMD, 23 Soldered Parts)

See `hardware/BOM.xlsx` for clickable vendor/cost rollups and off-board parts.

### 12 Electrical Components (9 Unique Part Types)
| Ref(s) | Qty | Value | Package / Footprint | Example Part Number |
|---|---|---|---|---|
| `F1` | 1 | 15 A Mini Blade | `Fuseholder_Blade_Mini_Keystone_3568` | Keystone `3568` + Littelfuse `0297015.WXNV` |
| `D4` | 1 | `P6KE18A` TVS | `D_DO-15_P10.16mm_Horizontal` | Littelfuse `P6KE18A` |
| `D3, D5` | 2 | `1N5822` 40V 3A | `D_DO-201AD_P12.70mm_Horizontal` | ON Semi / Vishay `1N5822` |
| `C14` | 1 | `470 µF 25 V` | `CP_Radial_D8.0mm_P3.50mm` | Nichicon `UPW1E471MPD` |
| `C1, C2` | 2 | `10 µF 50 V` X7R/S | `C_Disc_D6.0mm_W4.4mm_P5.00mm` | TDK `FG20X7R1H106KRT00` / Murata `RDEC71H106K3K1H03B` |
| `U2` | 1 | `R-78E5.0-0.5` | `Converter_DCDC_RECOM_R-78E-0.5_THT` | RECOM `R-78E5.0-0.5` |
| `C4, C11` | 2 | `100 nF 50 V` X7R | `C_Disc_D5.0mm_W2.5mm_P5.00mm` | KEMET `C320C104K5R5TA` |
| `R1` | 1 | `100 kΩ 1%` 1/4 W | `R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm` | Yageo `MFR-25FBF52-100K` |
| `R2` | 1 | `22 kΩ 1%` 1/4 W | `R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm` | Yageo `MFR-25FBF52-22K` |

### 11 Connectors & Sockets (All THT)
- `U1`: 2× 1×20 female 2.54 mm headers (Pico 2 socket)
- `J1`: AMASS `XT30PW-M` · `J2`: AMASS `XT30PW-F`
- `J4, J5, J6`: 3× JST `B4B-PH-K-S` (4-pin JST-PH)
- `J8, J9`: 2× JST `B2B-XH-A` (2-pin JST-XH)
- `J3`: 1×2 2.54 mm male header · `J10`: 1×3 2.54 mm male header · `J7`: 2×4 2.54 mm male header

---

## Soldering & Bring-Up Checklist (Shortest-to-Tallest Order)

1. **Solder lowest parts first:** `R1`, `R2`, `D4` (`K` band to square pad / `VBAT_F`), `D3` (`K` band to square pad / west), `D5` (`K` band to square pad / east).
2. **Ceramic caps:** `C1`, `C2`, `C4`, `C11` (non-polarized).
3. **Headers & sockets:** `J3`, `J7`, `J10`, `J4`–`J6`, `J8`–`J9`, and `U1` (plug a spare Pico 2 into the two 1×20 female strips temporarily while tacking the corner pins so the sockets stay dead parallel!).
4. **Tall & heavy power parts last:** `C14` (`+` long lead into square pad on west), `U2` (Pin 1 into square pad on west), `F1` (`Keystone 3568` — solder all 4 legs generously), `J1` (`XT30PW-M`), `J2` (`XT30PW-F`).
5. **Pre-power continuity check (NO Pico, NO battery, NO fuse):**
   - Check resistance `GND` ↔ `VBAT`, `GND` ↔ `VBAT_F`, `GND` ↔ `+5V`, `GND` ↔ `+3V3` — none should read dead short (`<10 Ω`).
   - Verify battery pack XT30-F polarity with a multimeter (`+` on rounded side, `-` on flat/beveled side).
6. **Power-up test (NO Pico plugged in yet):**
   - Insert 15 A mini blade fuse into `F1`, plug in 8×AA battery, close `J3` power switch.
   - Probe `TP4 (VSW)` → ~9.6–13.2 V; probe `TP1 (+5V)` vs `TP3 (GND)` → `5.0 V ± 0.1 V`; probe `U1` Pin 39 (`VSYS`) → `~4.65–4.75 V`.
7. **Install Pico 2** (USB port facing the south board edge as marked `USB`), plug in USB or turn on battery, and verify `TP2 (+3V3)` = `3.30 V ± 0.05 V`.

---

## Regenerating Files / Preparing Fab Gerbers

- Edit `tools/design.py` or `tools/placement.py`, then run:
  ```bash
  python tools/gen_sch.py     # regenerates hardware/RobotEV.kicad_sch
  python tools/relayout.py    # syncs footprints, places, routes, stitches GND, checks DRC
  python tools/make_bom.py    # regenerates hardware/BOM.xlsx
  python tools/render.py      # renders build/ & renders/ board_top.png + board_bottom.png
  ```
- **Before ordering PCBs:** Open `hardware/RobotEV.kicad_pcb` in **KiCad 10**, press **`B`** to fill the top & bottom GND copper pours, run **Inspect → Design Rules Checker**, and export Gerbers + Drill (or run `python tools/build.py` on a machine with KiCad 10 installed).
- Recommended fab settings: **2-layer, 1.6 mm FR-4, 1 oz Cu** (double-sided 3.0 mm `VBAT`/`VBAT_F` bars already deliver 6.0 mm effective copper width for 15 A peaks).
