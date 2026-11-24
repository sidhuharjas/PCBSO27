"""Pure-python board model + DRC-lite for KiCad .kicad_pcb files (no KiCad needed)."""
import math, sx

def rot(x, y, a):
    """KiCad rotation (y down, +angle = CCW on screen)."""
    r = math.radians(a); c, s = math.cos(r), math.sin(r)
    return x * c + y * s, -x * s + y * c

def num(v): return float(v)

class Pad:
    def __init__(s, ref, fp, node):
        s.ref = ref; s.num = node[1]; s.kind = node[2]; s.shape = node[3]
        at = sx.first(node, 'at'); s.rx, s.ry = num(at[1]), num(at[2])
        s.ra = num(at[3]) if len(at) > 3 else 0.0
        sz = sx.first(node, 'size'); s.w, s.h = num(sz[1]), num(sz[2])
        dr = sx.first(node, 'drill'); s.drill = None
        if dr:
            if len(dr) > 2 and dr[1] == 'oval': s.drill = (num(dr[2]), num(dr[3]))
            else: s.drill = (num(dr[1]), num(dr[1]))
        ly = sx.first(node, 'layers'); s.layers = list(ly[1:])
        n = sx.first(node, 'net'); s.net = n[1] if n else None
        s.node = node
        s.thru = s.kind in ('thru_hole', 'np_thru_hole')
        s.on_f = s.thru or 'F.Cu' in s.layers
        s.on_b = s.thru or 'B.Cu' in s.layers
        s.update(fp)
    def update(s, fp):
        fx, fy, fa = fp.x, fp.y, fp.a
        ox, oy = rot(s.rx, s.ry, fa)
        s.x, s.y = fx + ox, fy + oy
        at = sx.first(s.node, 'at'); s.ra = num(at[3]) if len(at) > 3 else 0.0   # file pad angle includes footprint rotation
        ang = s.ra % 180
        if abs(ang - 90) < 1e-6: s.W, s.H = s.h, s.w
        else: s.W, s.H = s.w, s.h
    def prim(s):
        """copper primitive: ('rect',x0,y0,x1,y1) or ('cap',x1,y1,x2,y2,r)"""
        if s.shape == 'circle':
            return ('cap', s.x, s.y, s.x, s.y, s.W / 2)
        if s.shape == 'oval':
            if s.W >= s.H:
                d = (s.W - s.H) / 2; return ('cap', s.x - d, s.y, s.x + d, s.y, s.H / 2)
            d = (s.H - s.W) / 2; return ('cap', s.x, s.y - d, s.x, s.y + d, s.W / 2)
        return ('rect', s.x - s.W / 2, s.y - s.H / 2, s.x + s.W / 2, s.y + s.H / 2)

class FP:
    def __init__(s, node):
        s.node = node
        at = sx.first(node, 'at'); s.x, s.y = num(at[1]), num(at[2]); s.a = num(at[3]) if len(at) > 3 else 0.0
        props = {p[1]: p[2] for p in sx.find(node, 'property')}
        s.ref = props.get('Reference', '?'); s.value = props.get('Value', '')
        s.name = node[1]
        s.pads = [Pad(s.ref, s, p) for p in sx.find(node, 'pad')]

class Board:
    def __init__(s, path):
        s.root = sx.parse(open(path, encoding='utf-8').read())
        s.fps = {}
        for n in sx.find(s.root, 'footprint'):
            f = FP(n); s.fps[f.ref] = f
        s.segs = []; s.vias = []
        for n in sx.find(s.root, 'segment'):
            st, en = sx.first(n, 'start'), sx.first(n, 'end')
            s.segs.append(dict(x1=num(st[1]), y1=num(st[2]), x2=num(en[1]), y2=num(en[2]),
                               w=num(sx.first(n, 'width')[1]), layer=sx.first(n, 'layer')[1], net=sx.first(n, 'net')[1]))
        for n in sx.find(s.root, 'via'):
            a = sx.first(n, 'at')
            s.vias.append(dict(x=num(a[1]), y=num(a[2]), d=num(sx.first(n, 'size')[1]),
                               drill=num(sx.first(n, 'drill')[1]), net=sx.first(n, 'net')[1]))
    def pads(s):
        for f in s.fps.values():
            for p in f.pads: yield p

# ---------------- distance helpers -----------------
def seg_pt(ax, ay, bx, by, px, py):
    dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)
def _ccw(ax, ay, bx, by, cx, cy): return (cy - ay) * (bx - ax) > (by - ay) * (cx - ax)
def seg_seg(a, b):
    ax, ay, bx, by = a; cx, cy, dx, dy = b
    if _ccw(ax, ay, cx, cy, dx, dy) != _ccw(bx, by, cx, cy, dx, dy) and _ccw(ax, ay, bx, by, cx, cy) != _ccw(ax, ay, bx, by, dx, dy):
        return 0.0
    return min(seg_pt(ax, ay, bx, by, cx, cy), seg_pt(ax, ay, bx, by, dx, dy),
               seg_pt(cx, cy, dx, dy, ax, ay), seg_pt(cx, cy, dx, dy, bx, by))
def rect_edges(r):
    x0, y0, x1, y1 = r[1:5]
    return [(x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)]
def inside(r, x, y): return r[1] <= x <= r[3] and r[2] <= y <= r[4]
def prim_dist(p, q):
    """edge-to-edge distance between two primitives (0 if touching/overlapping)."""
    if p[0] == 'cap' and q[0] == 'cap':
        return max(0.0, seg_seg(p[1:5], q[1:5]) - p[5] - q[5])
    if p[0] == 'rect' and q[0] == 'rect':
        dx = max(q[1] - p[3], p[1] - q[3], 0); dy = max(q[2] - p[4], p[2] - q[4], 0)
        return math.hypot(dx, dy)
    if p[0] == 'rect': p, q = q, p
    # p cap, q rect
    if inside(q, p[1], p[2]) or inside(q, p[3], p[4]): return 0.0
    d = min(seg_seg(p[1:5], e) for e in rect_edges(q))
    return max(0.0, d - p[5])
