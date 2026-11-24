"""Generate hardware/RobotEV.kicad_pcb from tools/design.py + the netlist.

Run with the KiCad Python (it imports pcbnew):
    "C:/Program Files/KiCad/10.0/bin/python.exe" tools/gen_pcb.py

What it does
  1. builds every footprint at the floorplan position from design.py
  2. assigns pads to nets straight from the schematic netlist (no guessing)
  3. draws the board outline, ground pours and stitching vias
  4. routes the board with a small grid autorouter (wide power nets first)
  5. saves the board and the two custom footprints into hardware/RobotEV.pretty
"""
import heapq
import math
import os
import sys
from array import array

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import design as D  # noqa: E402

G = 0.15           # routing grid, mm
CLEAR = 0.2        # design rule clearance, mm
EDGE_MARGIN = 0.7  # copper keep-out from board edge, mm
VIA_D, VIA_DRILL = 0.8, 0.4
SIGNAL_W = 0.25
DEBUG = True       # print a grid map around nets that fail to route
FANOUT = True      # pre-reserve pad escapes (only helps on much denser boards)
FANOUT_REFS = {"U1", "J4", "J5", "J6", "J7", "J8", "J9", "J10",
               "J1", "J2", "J3", "F1", "D4", "C12"}
NETLIST = os.path.join(ROOT, "build", "netlist.xml")
OUT_PCB = os.path.join(ROOT, "hardware", D.PROJECT + ".kicad_pcb")
OUT_PRETTY = os.path.join(ROOT, "hardware", "RobotEV.pretty")


def mm(v):
    return int(round(pcbnew.FromMM(v)))


def V(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def rad_for(width):
    """Grid cells to reserve around a track this wide (min centre spacing)."""
    need = width / 2.0 + SIGNAL_W / 2.0 + CLEAR
    return max(1, int(math.ceil(need / G)) - 1)


# a via only has to clear a neighbouring track edge, not reserve a whole pad-sized
# disc: the old (VIA_D + CLEAR) rule sealed 0.9 mm around every via
VIA_MARK_R = max(1, int(math.ceil((VIA_D / 2.0 + SIGNAL_W / 2.0 + CLEAR) / G)) - 1)


# --------------------------------------------------------------------- netlist
def load_netlist(path):
    import xml.etree.ElementTree as ET
    root = ET.parse(path).getroot()
    padnet = {}
    bynet = {}
    for net in root.find("nets"):
        name = net.get("name")
        for node in net:
            key = (node.get("ref"), node.get("pin"))
            padnet[key] = name
            bynet.setdefault(name, []).append(key)
    return padnet, bynet


# ------------------------------------------------------------ custom footprints
def _shape(fp, layer, x1, y1, x2, y2, w=0.12):
    s = pcbnew.PCB_SHAPE(fp)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetLayer(layer)
    s.SetStart(V(x1, y1))
    s.SetEnd(V(x2, y2))
    s.SetWidth(mm(w))
    fp.Add(s)


def _rect(fp, layer, x1, y1, x2, y2, w=0.12):
    _shape(fp, layer, x1, y1, x2, y1, w)
    _shape(fp, layer, x2, y1, x2, y2, w)
    _shape(fp, layer, x2, y2, x1, y2, w)
    _shape(fp, layer, x1, y2, x1, y1, w)


def make_pico_footprint(board, ref, value):
    """40 pads in two 1x20 rows, 17.78 mm apart - a Pico 2 in header sockets."""
    fp = pcbnew.FOOTPRINT(board)
    fp.SetFPID(pcbnew.LIB_ID("RobotEV", "Pico2_Socket_2x20_P2.54mm"))
    for i in range(20):
        y = -24.13 + i * 2.54
        for num, x in ((i + 1, -8.89), (40 - i, 8.89)):
            pad = pcbnew.PAD(fp)
            pad.SetNumber(str(num))
            pad.SetShape(pcbnew.PAD_SHAPE_OVAL)
            pad.SetSize(pcbnew.VECTOR2I(mm(1.7), mm(1.7)))
            pad.SetDrillSize(pcbnew.VECTOR2I(mm(1.0), mm(1.0)))
            pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
            pad.SetLayerSet(pad.PTHMask())
            pad.SetPosition(V(x, y))
            fp.Add(pad)
    # body + pin 1 marker
    _rect(fp, pcbnew.F_SilkS, -10.5, -25.5, 10.5, 25.5)
    _rect(fp, pcbnew.F_CrtYd, -11.5, -26.5, 11.5, 26.5, 0.05)
    _shape(fp, pcbnew.F_SilkS, -10.5, 25.2, -7.5, 25.2, 0.3)   # thick edge near pin 1
    _shape(fp, pcbnew.F_SilkS, -8.89, -26.2, -8.89, -25.5, 0.3)  # pin 1 tick
    txt = pcbnew.PCB_TEXT(fp)
    txt.SetText("RPI PICO 2")
    txt.SetLayer(pcbnew.F_SilkS)
    txt.SetPosition(V(0, 22.0))
    txt.SetTextSize(pcbnew.VECTOR2I(mm(1.2), mm(1.2)))
    txt.SetTextThickness(mm(0.2))
    fp.Add(txt)
    fp.SetReference(ref)
    fp.SetValue(value)
    return fp


CUSTOM_FPS = {"RobotEV:Pico2": make_pico_footprint}


# ---------------------------------------------------------------------- router
class Router:
    def __init__(self, board, edges, holes):
        self.NX = int(D.BOARD_W / G) + 1
        self.NY = int(D.BOARD_H / G) + 1
        n = self.NX * self.NY
        self.own = [array("h", [-1]) * n, array("h", [-1]) * n]
        self.hard = [bytearray(n), bytearray(n)]
        self.ispad = [bytearray(n), bytearray(n)]
        self.novia = bytearray(n)
        self.vias = set()
        self.last_seen = 0
        self.last_end = ""
        self._edge_keepout()
        for hx, hy in holes:
            self._block_circle(hx, hy, 1.6 + EDGE_MARGIN + 0.3)

    # -- helpers
    def _edge_keepout(self):
        W, H, R, m = D.BOARD_W, D.BOARD_H, D.CORNER_R, EDGE_MARGIN
        for j in range(self.NY):
            for i in range(self.NX):
                x, y = i * G, j * G
                inside = (m <= x <= W - m and m <= y <= H - m)
                if inside:
                    cx = R if x < R else (W - R if x > W - R else None)
                    cy = R if y < R else (H - R if y > H - R else None)
                    if cx is not None and cy is not None:
                        inside = math.hypot(x - cx, y - cy) <= R - m
                if not inside:
                    k = j * self.NX + i
                    self.hard[0][k] = 1
                    self.hard[1][k] = 1

    def _block_circle(self, cx, cy, r):
        i0, j0 = int((cx - r) / G), int((cy - r) / G)
        i1, j1 = int((cx + r) / G) + 1, int((cy + r) / G) + 1
        for j in range(max(0, j0), min(self.NY, j1 + 1)):
            for i in range(max(0, i0), min(self.NX, i1 + 1)):
                if math.hypot(i * G - cx, j * G - cy) <= r:
                    k = j * self.NX + i
                    self.hard[0][k] = 1
                    self.hard[1][k] = 1

    def mark(self, layer, i, j, net, r=0):
        for jj in range(max(0, j - r), min(self.NY, j + r + 1)):
            for ii in range(max(0, i - r), min(self.NX, i + r + 1)):
                k = jj * self.NX + ii
                if self.own[layer][k] == -1:
                    self.own[layer][k] = net

    def _paint(self, x0, y0, x1, y1, layers, net, ispad=False):
        for j in range(max(0, int(y0 / G)), min(self.NY, int(y1 / G) + 1)):
            for i in range(max(0, int(x0 / G)), min(self.NX, int(x1 / G) + 1)):
                if not (x0 <= i * G <= x1 and y0 <= j * G <= y1):
                    continue
                k = j * self.NX + i
                for l in layers:
                    if net < 0:
                        self.hard[l][k] = 1
                    elif ispad:
                        self.own[l][k] = net
                        self.ispad[l][k] = 1
                    elif self.ispad[l][k]:
                        continue                       # never steal real pad copper
                    elif self.own[l][k] == -1:
                        self.own[l][k] = net
                    elif self.own[l][k] != net:
                        # inside two different pads' halos: no legal track fits here
                        self.hard[l][k] = 1

    def blocked_pads(self, pad, net, expand=0.3, rad=1):
        ls = pad.GetLayerSet()
        layers = [l for l in (0, 1) if ls.Contains(pcbnew.F_Cu if l == 0 else pcbnew.B_Cu)]
        bb = pad.GetBoundingBox()
        bx0, by0 = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop())
        bx1, by1 = pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())
        if net < 0:                                    # NPTH / mechanical pad
            self._paint(bx0 - expand, by0 - expand, bx1 + expand, by1 + expand,
                        layers, -1)
        else:
            self._paint(bx0, by0, bx1, by1, layers, net, ispad=True)
            r = expand + rad * G
            self._paint(bx0 - r, by0 - r, bx1 + r, by1 + r, layers, net)
        # keep vias away from drilled holes (hole-to-hole spacing)
        if pad.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
            px = pcbnew.ToMM(pad.GetPosition().x)
            py = pcbnew.ToMM(pad.GetPosition().y)
            r = pcbnew.ToMM(pad.GetDrillSize().x) / 2.0 + VIA_DRILL / 2.0 + 0.55
            for j in range(max(0, int((py - r) / G)), min(self.NY, int((py + r) / G) + 1)):
                for i in range(max(0, int((px - r) / G)), min(self.NX, int((px + r) / G) + 1)):
                    if math.hypot(i * G - px, j * G - py) <= r:
                        self.novia[j * self.NX + i] = 1

    def ok(self, layer, i, j, net, extra):
        if not (0 <= i < self.NX and 0 <= j < self.NY):
            return False
        for jj in range(max(0, j - extra), min(self.NY, j + extra + 1)):
            for ii in range(max(0, i - extra), min(self.NX, i + extra + 1)):
                if self.hard[layer][jj * self.NX + ii]:
                    return False
                o = self.own[layer][jj * self.NX + ii]
                if o != -1 and o != net:
                    return False
        return True

    def via_ok(self, i, j, net):
        if self.novia[j * self.NX + i]:
            return False
        for layer in (0, 1):
            if not self.ok(layer, i, j, net, VIA_MARK_R):
                return False
        return (i, j) not in self.vias

    # -- A*
    def astar(self, net, sources, targets, width):
        extra = rad_for(width) - 1
        targets = set(targets)
        tlist = list(targets)
        heap = []
        cnt = 0
        g = {}
        prev = {}
        for s in sources:
            g[s] = 0
            heapq.heappush(heap, (0, cnt, s))
            cnt += 1

        def hh(i, j):
            return min(abs(i - t[1]) + abs(j - t[2]) for t in tlist)

        seen = set()
        limit = 600000                    # bound a hopeless search in time
        while heap:
            if len(seen) > limit:
                self.last_seen, self.last_end = len(seen), "limit"
                return None
            f, _, st = heapq.heappop(heap)
            if st in seen:
                continue
            seen.add(st)
            if st in targets:
                path = [st]
                while path[-1] in prev:
                    path.append(prev[path[-1]])
                return path[::-1]
            layer, i, j = st
            base = g[st]
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ni, nj = i + di, j + dj
                nst = (layer, ni, nj)
                # landing on the pad's own copper only needs to touch it; a full
                # corridor is not required for that last cell
                if not self.ok(layer, ni, nj, net, 1 if nst in targets else extra):
                    continue
                cost = base + 1
                if layer == 1 and dj != 0:      # keep B.Cu mostly vertical
                    cost += 0.35
                if layer == 0 and di != 0:
                    cost += 0.35
                if nst in g and cost >= g[nst]:
                    continue
                g[nst] = cost
                prev[nst] = st
                heapq.heappush(heap, (cost + hh(ni, nj), cnt, nst))
                cnt += 1
            # via down/up
            other = 1 - layer
            if self.via_ok(i, j, net):
                nst = (other, i, j)
                cost = base + 34
                if nst not in g or cost < g[nst]:
                    g[nst] = cost
                    prev[nst] = st
                    heapq.heappush(heap, (cost + hh(i, j), cnt, nst))
                    cnt += 1
        self.last_seen, self.last_end = len(seen), "exhausted"
        return None

    def component(self, cells, net, extra, cap=80000):
        """Flood fill with A*'s own legality rule: how much board can this reach?"""
        seen = set(cells)
        stack = list(cells)
        x0 = y0 = 10 ** 9
        x1 = y1 = -10 ** 9
        while stack and len(seen) < cap:
            layer, i, j = stack.pop()
            x0, x1 = min(x0, i), max(x1, i)
            y0, y1 = min(y0, j), max(y1, j)
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ni, nj = i + di, j + dj
                if not (0 <= ni < self.NX and 0 <= nj < self.NY):
                    continue
                nst = (layer, ni, nj)
                if nst in seen or not self.ok(layer, ni, nj, net, extra):
                    continue
                seen.add(nst)
                stack.append(nst)
        return len(seen), (x0, y0, x1, y1)

    # -- path -> copper
    def commit(self, board, net, neti, path, width, pad_positions=None):
        rad = rad_for(width)
        segs = []
        vias = []
        run_layer = path[0][0]
        run = [path[0][1:3]]
        d0 = None
        for cur, nxt in zip(path, path[1:]):
            if nxt[0] != cur[0]:                      # layer change -> via
                segs.append((run_layer, run[0], run[-1]))
                vias.append(cur[1:3])
                run_layer = nxt[0]
                run = [nxt[1:3]]
                d0 = None
                continue
            d = (nxt[1] - cur[1], nxt[2] - cur[2])
            if d == d0:
                run.append(nxt[1:3])
            else:                                     # turn -> flush straight run
                segs.append((run_layer, run[0], run[-1]))
                run = [cur[1:3], nxt[1:3]]
                d0 = d
        segs.append((run_layer, run[0], run[-1]))
        segs = [(l, a, b) for l, a, b in segs if a != b]
        for layer, a, b in segs:
            t = pcbnew.PCB_TRACK(board)
            t.SetLayer(pcbnew.F_Cu if layer == 0 else pcbnew.B_Cu)
            t.SetWidth(mm(width))
            t.SetStart(V(a[0] * G, a[1] * G))
            t.SetEnd(V(b[0] * G, b[1] * G))
            t.SetNet(net)
            board.Add(t)
        for i, j in vias:
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(V(i * G, j * G))
            v.SetWidth(mm(VIA_D))
            v.SetDrill(mm(VIA_DRILL))
            v.SetViaType(pcbnew.VIATYPE_THROUGH)
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            v.SetNet(net)
            board.Add(v)
            self.vias.add((i, j))
        for layer, i, j in path:
            self.mark(layer, i, j, neti, rad)
        for i, j in vias:
            self.mark(0, i, j, neti, VIA_MARK_R)
            self.mark(1, i, j, neti, VIA_MARK_R)

    def free_cells(self, i, j, layer, net, d, maxn):
        n = 0
        di, dj = d
        for k in range(1, maxn + 1):
            ii, jj = i + di * k, j + dj * k
            if not (0 <= ii < self.NX and 0 <= jj < self.NY):
                break
            if self.hard[layer][jj * self.NX + ii]:
                break
            o = self.own[layer][jj * self.NX + ii]
            if o != -1 and o != net:
                break
            n += 1
        return n

    def fanout(self, board, pad, net, nid, width, reach=1.8):
        """Claim a short escape track from a pad before any net is routed.

        Without this, neighbouring tracks seal dense pad columns and the pads
        become unreachable. Returns the grid node the pad now connects to.
        """
        ls = pad.GetLayerSet()
        layers = [l for l in (0, 1) if ls.Contains(pcbnew.F_Cu if l == 0 else pcbnew.B_Cu)]
        if not layers:
            return None
        px = pcbnew.ToMM(pad.GetPosition().x)
        py = pcbnew.ToMM(pad.GetPosition().y)
        ci, cj = int(round(px / G)), int(round(py / G))
        if not (0 <= ci < self.NX and 0 <= cj < self.NY):
            return None
        rad = rad_for(width)
        best = None
        for layer in layers:
            if self.hard[layer][cj * self.NX + ci]:
                continue
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = self.free_cells(ci, cj, layer, nid, d, int(reach / G))
                if n < 3:
                    continue
                if best is None or n > best[0]:
                    best = (n, layer, d)
        if best is None:
            return None
        n, layer, (di, dj) = best
        ei, ej = ci + di * n, cj + dj * n
        t = pcbnew.PCB_TRACK(board)
        t.SetLayer(pcbnew.F_Cu if layer == 0 else pcbnew.B_Cu)
        t.SetWidth(mm(width))
        t.SetStart(V(px, py))
        t.SetEnd(V(ei * G, ej * G))
        t.SetNet(net)
        board.Add(t)
        for k in range(n + 1):
            self.mark(layer, ci + di * k, cj + dj * k, nid, rad)
        return (layer, ei, ej)

    def access_all(self, pad, net):
        """Every grid cell of this pad's own copper region - any of them is a
        legal place for a track to arrive, which keeps fine-pitch pads usable."""
        ls = pad.GetLayerSet()
        layers = [l for l in (0, 1) if ls.Contains(pcbnew.F_Cu if l == 0 else pcbnew.B_Cu)] or [0, 1]
        px = pcbnew.ToMM(pad.GetPosition().x)
        py = pcbnew.ToMM(pad.GetPosition().y)
        ci, cj = int(round(px / G)), int(round(py / G))
        out = []
        for layer in layers:
            for dj in range(-2, 3):
                for di in range(-2, 3):
                    i, j = ci + di, cj + dj
                    if not (0 <= i < self.NX and 0 <= j < self.NY):
                        continue
                    k = j * self.NX + i
                    if self.hard[layer][k] or self.own[layer][k] != net:
                        continue
                    out.append((layer, i, j))
        return out

    def freedom(self, cell, net):
        layer, i, j = cell
        return sum(1 for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1))
                   if self.ok(layer, i + di, j + dj, net, 0))

    def access(self, pad, net):
        cx = pcbnew.ToMM(pad.GetPosition().x)
        cy = pcbnew.ToMM(pad.GetPosition().y)
        ci, cj = int(round(cx / G)), int(round(cy / G))
        for r in range(0, 3):
            for dj in range(-r, r + 1):
                for di in range(-r, r + 1):
                    i, j = ci + di, cj + dj
                    if not (0 <= i < self.NX and 0 <= j < self.NY):
                        continue
                    for layer in (0, 1):
                        if self.own[layer][j * self.NX + i] == net and \
                                not self.hard[layer][j * self.NX + i]:
                            return (layer, i, j)
        return None


def board_polygon(inset, seg=14):
    """Outline polygon (rounded corners) inset from the board edge."""
    W, H, R = D.BOARD_W, D.BOARD_H, D.CORNER_R
    rr = R - inset
    pts = []
    for c, a0, a1 in [((R, R), 180, 270), ((W - R, R), 270, 360),
                      ((W - R, H - R), 0, 90), ((R, H - R), 90, 180)]:
        for k in range(seg + 1):
            a = math.radians(a0 + (a1 - a0) * k / seg)
            pts.append((c[0] + rr * math.cos(a), c[1] + rr * math.sin(a)))
    return pts


def export_pretty(board_path):
    """Write the project's custom footprints out as .kicad_mod files."""
    from gen_sch import parse, emit, Str
    tree = parse(open(board_path, encoding="utf-8").read())
    ver = None
    for c in tree[1:]:
        if isinstance(c, list) and c[0] == "version":
            ver = c[1]
    os.makedirs(OUT_PRETTY, exist_ok=True)
    for node in tree[1:]:
        if isinstance(node, list) and node[0] == "footprint" and \
                str(node[1]).startswith("RobotEV:"):
            name = str(node[1]).split(":", 1)[1]
            node[1] = Str(name)
            if ver is not None:
                node[2:2] = [["version", ver], ["generator", Str("pcbnew")]]
            with open(os.path.join(OUT_PRETTY, name + ".kicad_mod"), "w",
                      encoding="utf-8", newline="\n") as f:
                f.write(emit(node) + "\n")
            print("  saved footprint %s" % name)


def write_fp_lib_table():
    txt = ('(fp_lib_table\n'
           '  (version 7)\n'
           '  (lib (name "RobotEV")(type "KiCad")(uri "${KIPRJMOD}/RobotEV.pretty")'
           '(options "")(descr "Project footprints (generated)"))\n'
           ')\n')
    path = os.path.join(ROOT, "hardware", "fp-lib-table")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(txt)


# ---------------------------------------------------------------------- build
def main():
    os.makedirs(OUT_PRETTY, exist_ok=True)
    board = pcbnew.BOARD()
    tb = board.GetTitleBlock()
    tb.SetTitle(D.TITLE)
    tb.SetRevision(D.REV)
    tb.SetDate(D.DATE)
    tb.SetCompany("Science Olympiad - Electric Vehicle")

    # nets -----------------------------------------------------------------
    padnet, bynet = load_netlist(NETLIST)
    nets = {}
    for idx, name in enumerate(sorted(bynet)):
        n = pcbnew.NETINFO_ITEM(board, name)
        n.SetNetCode(idx + 1)
        board.Add(n)
        nets[name] = n
    netidx = {name: i for i, name in enumerate(sorted(bynet))}

    # footprints -----------------------------------------------------------
    byref = {}
    for part in D.PARTS:
        sym = part["sym"]
        if sym in CUSTOM_FPS:
            fp = CUSTOM_FPS[sym](board, part["ref"], part["value"])
        else:
            lib, name = part["fp"].split(":", 1)
            fp = pcbnew.FootprintLoad(os.path.join(D.FP_LIB, lib + ".pretty"), name)
            if fp is None:
                raise SystemExit("missing footprint %s" % part["fp"])
            fp.SetReference(part["ref"])
            fp.SetValue(part["value"])
        x, y, rot = part["at"]
        # design.py positions are footprint *centres*, not library origins
        fp.SetPosition(V(0, 0))
        if rot:
            fp.SetOrientationDegrees(rot)
        bb = fp.GetBoundingBox(False, False)
        cget = getattr(bb, "GetCenter", None) or bb.GetCentre
        c = cget()
        fp.SetPosition(V(x - pcbnew.ToMM(c.x), y - pcbnew.ToMM(c.y)))
        board.Add(fp)
        byref[part["ref"]] = fp

    # pad -> net, from the schematic netlist
    for ref, fp in byref.items():
        for pad in fp.Pads():
            key = (ref, pad.GetNumber())
            if key in padnet:
                pad.SetNet(nets[padnet[key]])

    # silk labels ----------------------------------------------------------
    pad_rects = []
    for fp in byref.values():
        try:
            fp.Value().SetVisible(False)      # values are in the BOM, not on silk
            if fp.GetFPID().GetLibItemName().startswith("MountingHole"):
                fp.Reference().SetVisible(False)
        except Exception:
            pass
        for pad in fp.Pads():
            bb = pad.GetBoundingBox()
            pad_rects.append((pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()),
                              pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())))
        rb = fp.Reference().GetBoundingBox()
        for item in fp.GraphicalItems():        # existing silk: keep labels clear
            if item.GetLayer() != pcbnew.F_SilkS:
                continue
            sb = item.GetBoundingBox()
            if sb.GetWidth() > 0 and sb.GetHeight() > 0:
                pad_rects.append((pcbnew.ToMM(sb.GetLeft()), pcbnew.ToMM(sb.GetTop()),
                                  pcbnew.ToMM(sb.GetRight()), pcbnew.ToMM(sb.GetBottom())))

    def rect_free(x0, y0, x1, y1):
        if x0 < 0.3 or y0 < 0.3 or x1 > D.BOARD_W - 0.3 or y1 > D.BOARD_H - 0.3:
            return False
        for a0, b0, a1, b1 in pad_rects:
            if x0 < a1 + 0.2 and a0 - 0.2 < x1 and y0 < b1 + 0.2 and b0 - 0.2 < y1:
                return False
        return True

    for part in D.PARTS:
        if part["ref"] not in D.SILK_LABELS:
            continue
        text, dx, dy = D.SILK_LABELS[part["ref"]]
        x, y, _ = part["at"]
        size = 0.8
        w = len(text) * size * 0.8
        for cx, cy in ((x + dx, y + dy), (x, y - dy), (x + dx, y + dy - 3.0),
                       (x, y - dy + 3.0), (x - w, y), (x + w, y)):
            if rect_free(cx - w / 2, cy - size * 0.9, cx + w / 2, cy + size * 0.9):
                t = pcbnew.PCB_TEXT(byref[part["ref"]])
                t.SetText(text)
                t.SetLayer(pcbnew.F_SilkS)
                t.SetPosition(V(cx, cy))
                t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
                t.SetTextThickness(mm(0.15))
                byref[part["ref"]].Add(t)
                pad_rects.append((cx - w / 2, cy - size * 0.9, cx + w / 2, cy + size * 0.9))
                break

    # title block: two short lines in the free strip at the bottom left. Added
    # before the designator fit so references are placed around it, not through it
    for line, ty in (("EV CONTROLLER REV %s" % D.REV, 60.4), ("RP2350 / 8xAA", 62.6)):
        t = pcbnew.PCB_TEXT(board)
        t.SetText(line)
        t.SetLayer(pcbnew.F_SilkS)
        t.SetPosition(V(15.0, ty))
        t.SetTextSize(pcbnew.VECTOR2I(mm(0.9), mm(0.9)))
        t.SetTextThickness(mm(0.16))
        board.Add(t)
        tw = len(line) * 0.9 * 0.85
        pad_rects.append((15.0 - tw / 2, ty - 0.6, 15.0 + tw / 2, ty + 0.6))

    # reference designators: keep the library position if it is clear, else
    # step outwards / shrink, and hide the text rather than leave a clash
    for part in D.PARTS:
        fp = byref[part["ref"]]
        ref = fp.Reference()
        if not ref.IsVisible() or not ref.GetText():
            continue
        x, y, _ = part["at"]
        text = ref.GetText()
        rb = ref.GetBoundingBox()
        home = ((pcbnew.ToMM(rb.GetLeft()) + pcbnew.ToMM(rb.GetRight())) / 2.0,
                (pcbnew.ToMM(rb.GetTop()) + pcbnew.ToMM(rb.GetBottom())) / 2.0)
        placed = False
        for size in (0.9, 0.8):     # below 0.8 mm KiCad flags text_height
            ref.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
            ref.SetTextThickness(mm(size * 0.16))
            w, h = len(text) * size * 0.85, size * 1.3
            spots = [home, (x, y - 4.2), (x, y + 4.2), (x - 4.2, y), (x + 4.2, y),
                     (x, y - 6.0), (x, y + 6.0), (x - 6.0, y), (x + 6.0, y)]
            for cx, cy in spots:
                r = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
                if rect_free(*r):
                    ref.SetPosition(V(cx, cy))
                    pad_rects.append(r)
                    placed = True
                    break
            if placed:
                break
        if not placed:
            ref.SetVisible(False)

    # board outline: straight edges between four corner arcs ----------------
    R = D.CORNER_R
    arcs = [((R, R), 180, 270), ((D.BOARD_W - R, R), 270, 360),
            ((D.BOARD_W - R, D.BOARD_H - R), 0, 90), ((R, D.BOARD_H - R), 90, 180)]

    def arc_pt(c, deg):
        a = math.radians(deg)
        return (c[0] + R * math.cos(a), c[1] + R * math.sin(a))

    for idx, (c, a0, a1) in enumerate(arcs):
        s, m, e = arc_pt(c, a0), arc_pt(c, (a0 + a1) / 2.0), arc_pt(c, a1)
        arc = pcbnew.PCB_SHAPE(board)
        arc.SetShape(pcbnew.SHAPE_T_ARC)
        arc.SetLayer(pcbnew.Edge_Cuts)
        try:
            arc.SetStart(V(*s))
            arc.SetMid(V(*m))
            arc.SetEnd(V(*e))
        except AttributeError:
            arc.SetArcGeometry(V(*s), V(*m), V(*e))
        arc.SetWidth(mm(0.1))
        board.Add(arc)
        nc, na0, _ = arcs[(idx + 1) % 4]
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetStart(V(*e))
        seg.SetEnd(V(*arc_pt(nc, na0)))
        seg.SetWidth(mm(0.1))
        board.Add(seg)

    # router ---------------------------------------------------------------
    holes = [(x, y) for _, x, y in D.MOUNTING_HOLES]
    R = Router(board, None, holes)

    pads_by_net = {}
    for ref, fp in byref.items():
        for pad in fp.Pads():
            num = pad.GetNumber()
            if not num:                      # NPTH / mechanical pad: hard keep-out
                R.blocked_pads(pad, -1)
                continue
            name = padnet.get((ref, num))
            if name is None:
                R.blocked_pads(pad, -1)          # unconnected / mechanical pad
                continue
            pads_by_net.setdefault(name, []).append(pad)
            R.blocked_pads(pad, netidx[name])

    # Every pad's own copper belongs to its own net: overlapping fan-out halos
    # from a neighbour must never claim it (that is how tracks ended up shorting
    # the neighbouring pin of 1.25 mm pitch connectors).
    for ref, fp in byref.items():
        for pad in fp.Pads():
            num = pad.GetNumber()
            name = padnet.get((ref, num)) if num else None
            if not name:
                continue
            bb = pad.GetBoundingBox()
            x0 = pcbnew.ToMM(bb.GetLeft()) - 0.2
            y0 = pcbnew.ToMM(bb.GetTop()) - 0.2
            x1 = pcbnew.ToMM(bb.GetRight()) + 0.2
            y1 = pcbnew.ToMM(bb.GetBottom()) + 0.2
            ls = pad.GetLayerSet()
            for j in range(max(0, int(y0 / G)), min(R.NY, int(y1 / G) + 1)):
                for i in range(max(0, int(x0 / G)), min(R.NX, int(x1 / G) + 1)):
                    if x0 <= i * G <= x1 and y0 <= j * G <= y1:
                        k = j * R.NX + i
                        for l, lay in ((0, pcbnew.F_Cu), (1, pcbnew.B_Cu)):
                            if ls.Contains(lay):
                                R.own[l][k] = netidx[name]

    order = [n for n in D.ROUTE_ORDER if n in pads_by_net and n != "GND"]
    rest = [n for n in pads_by_net if n not in order and n != "GND"]

    def span(name):
        ps = pads_by_net[name]
        xs = [pcbnew.ToMM(p.GetPosition().x) for p in ps]
        ys = [pcbnew.ToMM(p.GetPosition().y) for p in ps]
        return max(max(xs) - min(xs), max(ys) - min(ys))

    # Local nets first (they get boxed in easily), then long nets get the
    # remaining wide-open channels.
    rest.sort(key=lambda n: (span(n) > 12.0, span(n) if span(n) <= 12.0 else -span(n)))

    def add_stub(pad, acc, net, nid, width):
        """Tie an off-grid pad centre to the routing grid."""
        px, py = pcbnew.ToMM(pad.GetPosition().x), pcbnew.ToMM(pad.GetPosition().y)
        gx, gy = acc[1] * G, acc[2] * G
        if abs(px - gx) < 0.01 and abs(py - gy) < 0.01:
            return
        t = pcbnew.PCB_TRACK(board)
        t.SetLayer(pcbnew.F_Cu if acc[0] == 0 else pcbnew.B_Cu)
        t.SetWidth(mm(width))
        t.SetStart(V(px, py))
        t.SetEnd(V(gx, gy))
        t.SetNet(net)
        board.Add(t)
        R.mark(acc[0], acc[1], acc[2], nid, 1)

    def route_net(name, flip=False):
        """Connect every pad of one net (spanning-tree style). Returns failures."""
        pads = pads_by_net[name]
        if len(pads) < 2:
            return []
        net = nets[name]
        nid = netidx[name]
        width = D.NET_WIDTH.get(name, SIGNAL_W)

        def node_of(pad):
            return fanout_node.get(id(pad)) or R.access(pad, nid)

        def connect(pad, acc):
            if id(pad) not in fanout_node:
                add_stub(pad, acc, net, nid, width)

        def far(p):
            return (abs(pcbnew.ToMM(p.GetPosition().x) - D.BOARD_W / 2) +
                    abs(pcbnew.ToMM(p.GetPosition().y) - D.BOARD_H / 2))

        seed = (min if flip else max)(pads, key=far)
        todo = [p for p in pads if p is not seed]
        todo.sort(key=lambda p: math.hypot(
            pcbnew.ToMM(p.GetPosition().x) - pcbnew.ToMM(seed.GetPosition().x),
            pcbnew.ToMM(p.GetPosition().y) - pcbnew.ToMM(seed.GetPosition().y)))
        seed_cells = ([fanout_node[id(seed)]] if id(seed) in fanout_node
                      else R.access_all(seed, nid))
        if not seed_cells:
            return ["%s: no access" % name]
        start = max(seed_cells, key=lambda c: R.freedom(c, nid))
        R.mark(start[0], start[1], start[2], nid, rad_for(width))
        connect(seed, start)
        connected = [start]
        fails = []
        pending = []
        for pad in todo:
            tgt = ([fanout_node[id(pad)]] if id(pad) in fanout_node
                   else R.access_all(pad, nid))
            if not tgt:
                fails.append("%s: no access to %s" % (name, pad.GetNumber()))
                continue
            path = R.astar(nid, connected, tgt, width)
            if path is None:
                pending.append(pad)          # maybe reachable after retries
                continue
            R.commit(board, net, nid, path, width)
            connected.extend(path)
            connect(pad, path[-1])
        id2name = {v: k for k, v in netidx.items()}

        def blockers_of(pad):
            counts = {}
            for layer, i, j in R.access_all(pad, nid):
                for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ii, jj = i + di, j + dj
                    if not (0 <= ii < R.NX and 0 <= jj < R.NY):
                        continue
                    o = R.own[layer][jj * R.NX + ii]
                    if o >= 0 and o != nid:
                        nm = id2name.get(o, "?")
                        counts[nm] = counts.get(nm, 0) + 1
            return sorted(counts.items(), key=lambda kv: -kv[1])[:3]

        for pad in pending:
            # a fan-out stub can itself end up sealed in, so try its end first
            # and then fall back to the pad's own copper
            tries = []
            if id(pad) in fanout_node:
                tries.append([fanout_node[id(pad)]])
            tries.append(R.access_all(pad, nid))
            path = None
            for tgt in tries:
                if tgt:
                    path = R.astar(nid, connected, tgt, width)
                    if path:
                        break
            if path is None:
                fails.append("%s: failed to %s (blocked by %s)" %
                             (name, pad.GetNumber(), blockers_of(pad)))
                if DEBUG:
                    ci = int(round(pcbnew.ToMM(pad.GetPosition().x) / G))
                    cj = int(round(pcbnew.ToMM(pad.GetPosition().y) / G))
                    print("--- %s pad %s at (%d,%d) layer0" % (name, pad.GetNumber(), ci, cj))
                    for jj in range(cj + 20, cj - 21, -1):
                        row = ""
                        for ii in range(ci - 20, ci + 21):
                            if not (0 <= ii < R.NX and 0 <= jj < R.NY):
                                row += "#"
                            else:
                                k = jj * R.NX + ii
                                if R.hard[0][k]:
                                    row += "h"
                                elif R.own[0][k] == nid:
                                    row += "*"
                                elif R.own[0][k] < 0:
                                    row += "."
                                else:
                                    row += "x"
                        print("   " + row)
                    nreach, bb = R.component(connected, nid, rad_for(width) - 1)
                    print("  DIAG %s pad %s targets=%d seen=%d end=%s reach=%d "
                          "box=%s" % (name, pad.GetNumber(), len(tgt or []), R.last_seen,
                                       R.last_end, nreach, bb))
                continue
            R.commit(board, net, nid, path, width)
            connected.extend(path)
            connect(pad, path[-1])
        return fails

    # optional pre-reserved pad escapes; off by default (it only pays off on
    # very dense boards where every pad would otherwise be sealed in)
    # the escape list has to exist before the optional fan-out pass
    escapes = getattr(D, "ESCAPES", {})
    fanout_node = {}
    if FANOUT:
        for name, pads in pads_by_net.items():
            width = D.NET_WIDTH.get(name, SIGNAL_W)
            for pad in pads:
                try:
                    ref = pad.GetParent().GetReference()
                except Exception:
                    ref = ""
                if ref not in FANOUT_REFS or (ref, pad.GetNumber()) in escapes:
                    continue
                node = R.fanout(board, pad, nets[name], netidx[name], width, reach=2.6)
                if node is not None:
                    fanout_node[id(pad)] = node

    # Explicit per-pad escapes (see D.ESCAPES): a short track from the pad centre
    # into open board, which unseals pads the grid cannot leave on its own.
    escapes = getattr(D, "ESCAPES", {})
    for (eref, enum), dest in escapes.items():
        efp = byref.get(eref)
        pad = next((p for p in efp.Pads() if p.GetNumber() == enum), None) if efp else None
        if pad is None or (eref, enum) not in padnet:
            print("  escape %s.%s: no such pad or net" % (eref, enum))
            continue
        ename = padnet[(eref, enum)]
        ew = D.NET_WIDTH.get(ename, SIGNAL_W)
        px = pcbnew.ToMM(pad.GetPosition().x)
        py = pcbnew.ToMM(pad.GetPosition().y)
        t = pcbnew.PCB_TRACK(board)
        t.SetLayer(pcbnew.F_Cu)
        t.SetWidth(mm(ew))
        t.SetStart(V(px, py))
        t.SetEnd(V(dest[0], dest[1]))
        t.SetNet(nets[ename])
        board.Add(t)
        steps = max(1, int(max(abs(dest[0] - px), abs(dest[1] - py)) / G))
        for k in range(steps + 1):
            x = px + (dest[0] - px) * k / steps
            y = py + (dest[1] - py) * k / steps
            R.mark(0, int(round(x / G)), int(round(y / G)), netidx[ename], rad_for(ew))
        fanout_node[id(pad)] = (0, int(round(dest[0] / G)), int(round(dest[1] / G)))
        print("  escape %s.%s %s -> (%.2f, %.2f)" % (eref, enum, ename, dest[0], dest[1]))

    # Whole nets placed explicitly (power rails that do not fit the grid's rules);
    # drawn before anything is autorouted so the rest routes around them.
    manual = getattr(D, "MANUAL_ROUTES", {})
    for mname, polys in manual.items():
        if mname not in nets:
            continue
        mnet, mid = nets[mname], netidx[mname]
        for pts, mwidth in polys:
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                t = pcbnew.PCB_TRACK(board)
                t.SetLayer(pcbnew.F_Cu)
                t.SetWidth(mm(mwidth))
                t.SetStart(V(x0, y0))
                t.SetEnd(V(x1, y1))
                t.SetNet(mnet)
                board.Add(t)
                steps = max(1, int(max(abs(x1 - x0), abs(y1 - y0)) / G))
                for k in range(steps + 1):
                    x = x0 + (x1 - x0) * k / steps
                    y = y0 + (y1 - y0) * k / steps
                    R.mark(0, int(round(x / G)), int(round(y / G)), mid, rad_for(mwidth))
        print("  manual route %s (%d polyline%s)" %
              (mname, len(polys), "" if len(polys) == 1 else "s"))

    priority = [n for n in getattr(D, "ROUTE_FIRST", []) if n in pads_by_net]
    plan = priority + order + [n for n in rest if n not in priority]
    only = getattr(D, "MANUAL_ONLY", set())
    plan = [n for n in plan if n not in only]

    failures = []
    for k, name in enumerate(plan):
        print("  [%d/%d] %s" % (k + 1, len(plan), name), flush=True)
        failures.extend(route_net(name))
    # One pass only: re-routing a net that is already partly connected stacks a
    # second set of tracks on the first, which DRC reports as duplicate copper
    # and hole-to-hole hits even though both halves are the same net.
    for f in failures:
        print("  ROUTE FAIL " + f)

    # ground pours + stitching vias ---------------------------------------
    gnd = nets["GND"]
    inset = 0.6
    poly = board_polygon(inset)
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(gnd)
        o = z.Outline()
        o.NewOutline()
        for x, y in poly:
            o.Append(V(x, y))
        z.SetLocalClearance(mm(CLEAR))
        z.SetMinThickness(mm(0.25))
        try:
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        except Exception:
            pass
        try:                       # drop islands that no via/pad can reach
            z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        except Exception:
            pass
        board.Add(z)

    gi = netidx["GND"]
    stitched = 0
    for x in [6.5 + 5.0 * k for k in range(15)]:
        for y in [6.5 + 5.0 * k for k in range(11)]:
            i, j = int(round(x / G)), int(round(y / G))
            if R.via_ok(i, j, gi):
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(V(i * G, j * G))
                v.SetWidth(mm(VIA_D))
                v.SetDrill(mm(VIA_DRILL))
                v.SetViaType(pcbnew.VIATYPE_THROUGH)
                v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                v.SetNet(gnd)
                board.Add(v)
                R.mark(0, i, j, gi, VIA_MARK_R)
                R.mark(1, i, j, gi, VIA_MARK_R)
                stitched += 1

    # a ring just inside the outline ties the edge of both pours together, where
    # the 5 mm grid lands on mounting holes and connector keep-outs
    for x, y in board_polygon(2.4, seg=6):
        i, j = int(round(x / G)), int(round(y / G))
        if not (0 <= i < R.NX and 0 <= j < R.NY) or not R.via_ok(i, j, gi):
            continue
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(V(i * G, j * G))
        v.SetWidth(mm(VIA_D))
        v.SetDrill(mm(VIA_DRILL))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(gnd)
        board.Add(v)
        R.mark(0, i, j, gi, VIA_MARK_R)
        R.mark(1, i, j, gi, VIA_MARK_R)
        stitched += 1

    # fill the ground pours so the board ships with copper already poured
    try:
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    except Exception as exc:  # pragma: no cover
        print("  (zone fill skipped: %s)" % exc)

    pcbnew.SaveBoard(OUT_PCB, board)

    # ship the custom footprints so KiCad can re-link them
    export_pretty(OUT_PCB)
    write_fp_lib_table()

    print("wrote %s" % OUT_PCB)
    print("routed %d nets, %d stitching vias, %d failures" %
          (len(plan), stitched, len(failures)))
    for f in failures:
        print("  ROUTE FAIL %s" % f)


if __name__ == "__main__":
    main()
