"""Generate hardware/RobotEV.kicad_sch from tools/design.py.

Symbols are copied verbatim out of the installed KiCad symbol libraries and
embedded in the schematic (lib_symbols), so the file opens anywhere without
needing a project symbol table.  Every pin gets a short wire and a global
label - that keeps the generated schematic electrically explicit and
ERC-friendly without hand-routing a rat's nest of wires.
"""
import os
import re
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D  # noqa: E402

# ----------------------------------------------------------------- s-expr ast
class Str(str):
    """Quoted string atom (kept distinct from bare symbols)."""


def parse(text):
    toks = re.findall(r'"(?:[^"\\]|\\.)*"|\(|\)|[^\s()]+', text)
    stack = [[]]
    for t in toks:
        if t == "(":
            stack.append([])
        elif t == ")":
            node = stack.pop()
            stack[-1].append(node)
        elif t.startswith('"'):
            body = t[1:-1].replace('\\"', '"').replace("\\\\", "\\")
            stack[-1].append(Str(body))
        else:
            stack[-1].append(t)
    return stack[0][0]


def emit(node, depth=0):
    pad = "\t" * depth
    if isinstance(node, Str):
        return '"' + node.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if not isinstance(node, list):
        return str(node)
    if all(not isinstance(c, list) for c in node):
        return "(" + " ".join(emit(c, 0) for c in node) + ")"
    out = ["(" + emit(node[0], 0)]
    i = 1
    while i < len(node) and not isinstance(node[i], list):
        out[0] += " " + emit(node[i], 0)
        i += 1
    for c in node[i:]:
        out.append(emit(c, depth + 1))
    return "\n".join([out[0]] + [pad + "\t" + l for l in out[1:]]) + "\n" + pad + ")"


def uid():
    return str(uuid.uuid4())


# --------------------------------------------------------------- symbol cache
_sym_cache = {}


def symbol_node(lib, name):
    path = os.path.join(D.SYM_LIB, lib + ".kicad_sym")
    if not os.path.exists(path):
        raise SystemExit("symbol library not found: " + path)
    tree = parse(open(path, encoding="utf-8").read())
    for child in tree[1:]:
        if isinstance(child, list) and child[0] == "symbol" and child[1] == name:
            return child
    raise SystemExit("symbol %s:%s not found" % (lib, name))


def lib_key(lib_id):
    lib, name = lib_id.split(":", 1)
    return lib, name


def collect_symbols(lib_ids):
    """Embed each symbol plus any parent it `extends`, namespaced as 'Lib:Name'."""
    out = {}
    todo = list(lib_ids)
    while todo:
        lib_id = todo.pop()
        if lib_id in out:
            continue
        lib, name = lib_key(lib_id)
        node = symbol_node(lib, name)
        node[1] = Str(lib_id)
        out[lib_id] = node
        for c in node:
            if isinstance(c, list) and c[0] == "extends":
                todo.append(lib + ":" + str(c[1]))
    return _flatten(out, set(lib_ids))


def _flatten(out, wanted):
    """Inline `extends` parents into their children.

    KiCad resolves (extends "Parent") by bare name inside the embedded lib_symbols, but
    here the parent is namespaced ('Lib:Parent'), so the link breaks and a derived symbol
    such as AMS1117-3.3 ends up with NO pins.  The netlist then has no node for it and the
    part is silently unwired (ERC cannot see it either).  Copy the parent's body into the
    child instead and drop the now-unused parents.
    """
    import copy

    def flat(lib_id):
        node = out[lib_id]
        ext = next((c for c in node if isinstance(c, list) and c[0] == "extends"), None)
        if ext is None:
            return node
        lib, name = lib_key(lib_id)
        pname = str(ext[1])
        parent = copy.deepcopy(flat(lib + ":" + pname))
        parent[1] = Str(lib_id)
        for c in parent:
            if isinstance(c, list) and c[0] == "symbol":
                c[1] = Str(str(c[1]).replace(lib_key(lib + ":" + pname)[1] + "_", name + "_", 1))
        child_props = {str(p[1]): p for p in node if isinstance(p, list) and p[0] == "property"}
        for i, c in enumerate(parent):
            if isinstance(c, list) and c[0] == "property" and str(c[1]) in child_props:
                parent[i] = child_props[str(c[1])]
        out[lib_id] = parent
        return parent

    for lib_id in list(out):
        flat(lib_id)
    return {k: v for k, v in out.items() if k in wanted}


def _raw_pins(node):
    pins = []
    for c in node:
        if not (isinstance(c, list) and c[0] == "symbol"):
            continue
        for p in c:
            if not (isinstance(p, list) and p[0] == "pin"):
                continue
            etype, style = p[1], p[2]
            at = next(x for x in p if isinstance(x, list) and x[0] == "at")
            num = next(x for x in p if isinstance(x, list) and x[0] == "number")
            nm = next(x for x in p if isinstance(x, list) and x[0] == "name")
            pins.append((str(num[1]), str(nm[1]), float(at[1]), float(at[2]),
                         int(float(at[3])), str(etype)))
    return pins


def pins_of(lib_id):
    """[(number, name, x, y, angle, etype)] for a symbol definition.

    Symbols such as AMS1117-3.3 only `extends` a parent and carry no pins of
    their own, so walk up the inheritance chain until pins are found.
    """
    lib, _name = lib_key(lib_id)
    node = _sym_cache[lib_id]
    pins = _raw_pins(node)
    if not pins:
        for c in node:
            if isinstance(c, list) and c[0] == "extends":
                pins = pins_of(lib + ":" + str(c[1]))
                break
    return pins


# -------------------------------------------------------------- custom symbol
def make_box_symbol(lib_id, ref_prefix, value, pin_rows, width_mm=None):
    """Build a rectangular module symbol.

    pin_rows: list of (number, name, side, etype); side 'L' or 'R'.
    Left pins are numbered top-down, right pins bottom-up (like the Pico).
    """
    left = [p for p in pin_rows if p[2] == "L"]
    right = [p for p in pin_rows if p[2] == "R"]
    pitch = 2.54
    n = max(len(left), len(right))
    half_h = (n + 1) * pitch / 2
    half_w = width_mm or 12.7
    body = [
        "symbol", Str(lib_id.split(":")[1] + "_0_1"),
        ["rectangle", ["start", -half_w, half_h], ["end", half_w, -half_h],
         ["stroke", ["width", 0.254], ["type", "default"]],
         ["fill", ["type", "background"]]],
    ]
    pins = ["symbol", Str(lib_id.split(":")[1] + "_1_1")]
    for i, (num, name, side, etype) in enumerate(left):
        y = (half_h - pitch) - i * pitch
        pins.append(["pin", etype, "line", ["at", -half_w - 2.54, y, 0], ["length", 2.54],
                     ["name", Str(name), ["effects", ["font", ["size", 1.27, 1.27]]]],
                     ["number", Str(num), ["effects", ["font", ["size", 1.27, 1.27]]]]])
    for i, (num, name, side, etype) in enumerate(right):
        y = (-half_h + pitch) + i * pitch
        pins.append(["pin", etype, "line", ["at", half_w + 2.54, y, 180], ["length", 2.54],
                     ["name", Str(name), ["effects", ["font", ["size", 1.27, 1.27]]]],
                     ["number", Str(num), ["effects", ["font", ["size", 1.27, 1.27]]]]])
    node = ["symbol", Str(lib_id),
            ["pin_names", ["offset", 1.016]],
            ["exclude_from_sim", "no"], ["in_bom", "yes"], ["on_board", "yes"],
            ["in_pos_files", "yes"], ["duplicate_pin_numbers_are_jumpers", "no"],
            ["property", Str("Reference"), Str(ref_prefix), ["at", 0, half_h + 2.54, 0],
             ["effects", ["font", ["size", 1.27, 1.27]]]],
            ["property", Str("Value"), Str(value), ["at", 0, -half_h - 2.54, 0],
             ["effects", ["font", ["size", 1.27, 1.27]]]],
            ["property", Str("Footprint"), Str(""), ["at", 0, 0, 0], ["hide", "yes"],
             ["effects", ["font", ["size", 1.27, 1.27]]]],
            ["property", Str("Datasheet"), Str(""), ["at", 0, 0, 0], ["hide", "yes"],
             ["effects", ["font", ["size", 1.27, 1.27]]]],
            ["property", Str("Description"), Str(D.TITLE), ["at", 0, 0, 0], ["hide", "yes"],
             ["effects", ["font", ["size", 1.27, 1.27]]]],
            body, pins,
            ["embedded_fonts", "no"]]
    return node


PICO_PINS = [
    (1, "GP0", "L", "bidirectional"), (2, "GP1", "L", "bidirectional"),
    (3, "GND", "L", "power_in"), (4, "GP2", "L", "bidirectional"),
    (5, "GP3", "L", "bidirectional"), (6, "GP4", "L", "bidirectional"),
    (7, "GP5", "L", "bidirectional"), (8, "GND", "L", "power_in"),
    (9, "GP6", "L", "bidirectional"), (10, "GP7", "L", "bidirectional"),
    (11, "GP8", "L", "bidirectional"), (12, "GP9", "L", "bidirectional"),
    (13, "GND", "L", "power_in"), (14, "GP10", "L", "bidirectional"),
    (15, "GP11", "L", "bidirectional"), (16, "GP12", "L", "bidirectional"),
    (17, "GP13", "L", "bidirectional"), (18, "GND", "L", "power_in"),
    (19, "GP14", "L", "bidirectional"), (20, "GP15", "L", "bidirectional"),
    (21, "GP16", "R", "bidirectional"), (22, "GP17", "R", "bidirectional"),
    (23, "GND", "R", "power_in"), (24, "GP18", "R", "bidirectional"),
    (25, "GP19", "R", "bidirectional"), (26, "GP20", "R", "bidirectional"),
    (27, "GP21", "R", "bidirectional"), (28, "GND", "R", "power_in"),
    (29, "GP22", "R", "bidirectional"), (30, "RUN", "R", "input"),
    (31, "GP26/ADC0", "R", "bidirectional"), (32, "GP27/ADC1", "R", "bidirectional"),
    (33, "GND", "R", "power_in"), (34, "GP28/ADC2", "R", "bidirectional"),
    (35, "ADC_VREF", "R", "power_in"), (36, "3V3", "R", "power_out"),
    (37, "3V3_EN", "R", "input"), (38, "GND", "R", "power_in"),
    (39, "VSYS", "R", "power_in"), (40, "VBUS", "R", "power_in"),
]

CUSTOM = {"RobotEV:Pico2": lambda: make_box_symbol("RobotEV:Pico2", "U",
                                                   "RPi Pico 2 (RP2350)", PICO_PINS, 12.7)}


# ------------------------------------------------------------------- placement
CELL_W, CELL_H = 76.2, 71.12     # multiples of 1.27 -> everything stays on grid
COLS = 8
ORIGIN = (25.4, 25.4)


def sch_sheet():
    return ["paper", Str("A2")]


def main():
    global _sym_cache
    out_dir = os.path.join(os.path.dirname(HERE), "hardware")
    os.makedirs(out_dir, exist_ok=True)

    lib_ids = sorted({p["sym"] for p in D.PARTS} | {"power:PWR_FLAG"})
    _sym_cache = collect_symbols([x for x in lib_ids if not x.startswith("RobotEV:")])
    for k, f in CUSTOM.items():
        _sym_cache[k] = f()

    body = []
    # ---- sheet header
    root = ["kicad_sch", ["version", 20250610], ["generator", Str("eeschema")],
            ["generator_version", Str("10.0")], ["uuid", Str(uid())],
            ["paper", Str("A2")],
            ["title_block", ["title", Str(D.TITLE)], ["date", Str(D.DATE)],
             ["rev", Str(D.REV)],
             ["comment", 1, Str("Generated by tools/gen_sch.py - edit tools/design.py")]]]

    # ---- lib_symbols
    libs = ["lib_symbols"]
    for lib_id in sorted(_sym_cache):
        libs.append(_sym_cache[lib_id])
    root.append(libs)

    # ---- instances, one grid cell each
    for idx, part in enumerate(D.PARTS):
        col, row = idx % COLS, idx // COLS
        cx = ORIGIN[0] + col * CELL_W
        cy = ORIGIN[1] + row * CELL_H
        sym = part["sym"]
        node_pins = {p[0]: p for p in pins_of(sym)}
        inst = ["symbol", ["lib_id", Str(sym)], ["at", cx, cy, 0], ["unit", 1],
                ["exclude_from_sim", "no"], ["in_bom", "yes"], ["on_board", "yes"],
                ["dnp", "no"], ["uuid", Str(uid())],
                ["property", Str("Reference"), Str(part["ref"]),
                 ["at", cx + 2.54, cy - 2.54, 0],
                 ["effects", ["font", ["size", 1.27, 1.27]], ["justify", "left"]]],
                ["property", Str("Value"), Str(part["value"]),
                 ["at", cx + 2.54, cy, 0],
                 ["effects", ["font", ["size", 1.27, 1.27]], ["justify", "left"]]],
                ["property", Str("Footprint"), Str(part["fp"]), ["at", cx, cy, 0],
                 ["hide", "yes"], ["effects", ["font", ["size", 1.27, 1.27]]]],
                ["property", Str("Datasheet"), Str(""), ["at", cx, cy, 0],
                 ["hide", "yes"], ["effects", ["font", ["size", 1.27, 1.27]]]],
                ["property", Str("Description"), Str(part["desc"]), ["at", cx, cy, 0],
                 ["hide", "yes"], ["effects", ["font", ["size", 1.27, 1.27]]]]]

        # pin fan-out: short wire + global label (or no-connect for unused pins)
        for num in sorted(node_pins, key=lambda s: int(s) if s.isdigit() else 0):
            node_pin = node_pins[num]
            px, py, ang = node_pin[2], node_pin[3], node_pin[4]
            ax, ay = cx + px, cy - py
            dirs = {0: (-1, 0), 90: (0, 1), 180: (1, 0), 270: (0, -1)}
            dx, dy = dirs.get(int(ang) % 360, (0, 1))
            ex, ey = ax + dx * 3.81, ay + dy * 3.81
            inst.append(["pin", Str(num), ["uuid", Str(uid())]])
            net = part["pins"].get(int(num) if num.isdigit() else num)
            if net is None:
                body.append(["no_connect", ["at", ax, ay], ["uuid", Str(uid())]])
                continue
            body.append(["wire", ["pts", ["xy", ax, ay], ["xy", ex, ey]],
                         ["stroke", ["width", 0], ["type", "default"]],
                         ["uuid", Str(uid())]])
            rot = 180 if dx < 0 else 0 if dx > 0 else 90 if dy < 0 else 270
            just = "right" if dx < 0 else "left" if dx > 0 else None
            eff = ["effects", ["font", ["size", 1.27, 1.27]]]
            if just:
                eff.append(["justify", just])
            body.append(["global_label", Str(net), ["shape", "input"], ["at", ex, ey, rot],
                         ["fields_autoplaced", "yes"], eff, ["uuid", Str(uid())],
                         ["property", Str("Intersheetrefs"), Str("${INTERSHEET_REFS}"),
                          ["at", ex, ey, 0], ["hide", "yes"],
                          ["effects", ["font", ["size", 1.27, 1.27]]]]])

        inst.append(["instances", ["project", Str(D.PROJECT),
                                   ["path", Str("/" + ROOT_UUID),
                                    ["reference", Str(part["ref"])], ["unit", 1]]]])
        root.append(inst)

    # ---- power flags so ERC is happy about all five rails
    flag_y = 15.0          # top margin of the sheet, clear of the part grid
    # only rails without a power_out driver need a flag (+5V/+3V3 are driven
    # by U2/U3, and two power outputs on one net is an ERC error)
    for i, net in enumerate(["GND", "VBAT", "VBAT_F", "VBAT_SW", "VBAT_D", "VSYS"]):
        fx = ORIGIN[0] + i * 40.64
        ref = "#FLG%02d" % (i + 1)
        root.append(["symbol", ["lib_id", Str("power:PWR_FLAG")], ["at", fx, flag_y, 0],
                     ["unit", 1], ["exclude_from_sim", "no"], ["in_bom", "yes"],
                     ["on_board", "yes"], ["dnp", "no"], ["uuid", Str(uid())],
                     ["property", Str("Reference"), Str(ref), ["at", fx, flag_y + 5.08, 0],
                      ["hide", "yes"], ["effects", ["font", ["size", 1.27, 1.27]]]],
                     ["property", Str("Value"), Str("PWR_FLAG"), ["at", fx, flag_y - 2.54, 0],
                      ["effects", ["font", ["size", 1.27, 1.27]]]],
                     ["property", Str("Footprint"), Str(""), ["at", fx, flag_y, 0],
                      ["hide", "yes"], ["effects", ["font", ["size", 1.27, 1.27]]]],
                     ["property", Str("Datasheet"), Str(""), ["at", fx, flag_y, 0],
                      ["hide", "yes"], ["effects", ["font", ["size", 1.27, 1.27]]]],
                     ["pin", Str("1"), ["uuid", Str(uid())]],
                     ["instances", ["project", Str(D.PROJECT),
                                    ["path", Str("/" + ROOT_UUID),
                                     ["reference", Str(ref)], ["unit", 1]]]]])
        body.append(["wire", ["pts", ["xy", fx, flag_y], ["xy", fx, flag_y + 5.08]],
                     ["stroke", ["width", 0], ["type", "default"]], ["uuid", Str(uid())]])
        body.append(["global_label", Str(net), ["shape", "input"],
                     ["at", fx, flag_y + 5.08, 270], ["fields_autoplaced", "yes"],
                     ["effects", ["font", ["size", 1.27, 1.27]]], ["uuid", Str(uid())],
                     ["property", Str("Intersheetrefs"), Str("${INTERSHEET_REFS}"),
                      ["at", fx, flag_y, 0], ["hide", "yes"],
                      ["effects", ["font", ["size", 1.27, 1.27]]]]])

    head = ["kicad_sch", ["version", 20250610], ["generator", Str("eeschema")],
            ["generator_version", Str("10.0")], ["uuid", Str(ROOT_UUID)],
            ["paper", Str("A2")],
            ["title_block", ["title", Str(D.TITLE)], ["date", Str(D.DATE)],
             ["rev", Str(D.REV)],
             ["comment", 1, Str("Generated by tools/gen_sch.py - edit tools/design.py")]],
            libs]
    # KiCad expects every symbol before the loose wires/labels on the sheet
    syms = [n for n in root[6:] if isinstance(n, list) and n[0] == "symbol"]
    text = emit(head + syms + body +
                [["sheet_instances", ["path", Str("/"), ["page", Str("1")]]],
                 ["embedded_fonts", "no"]]) + "\n"

    path = os.path.join(out_dir, D.PROJECT + ".kicad_sch")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("wrote", path, "(%d bytes, %d parts)" % (len(text), len(D.PARTS)))


ROOT_UUID = uid()

if __name__ == "__main__":
    main()
