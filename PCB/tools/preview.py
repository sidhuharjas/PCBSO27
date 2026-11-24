import sys, copy, itertools, math
import geom, pcbdraw as layout, placement as P, sx
import matplotlib.pyplot as plt

def load_placed(path='/home/claude/work/PCB/hardware/RobotEV.kicad_pcb'):
    b = geom.Board(path)
    for r, (x, y, a) in P.PLACE.items():
        layout.set_pos(b.fps[r], x, y, a)
    for r, (x, y, a) in P.ORIGIN.items():
        fp = b.fps[r]; da = a - fp.a; layout.apply_rot(fp.node, da); fp.a = a; fp.x, fp.y = x, y
        at = sx.first(fp.node, 'at'); at[1], at[2] = x, y
        if len(at) > 3: at[3] = a
        else: at.append(a)
        for p in fp.pads: p.update(fp)
    return b

def mst(points):
    if len(points) < 2: return []
    inn = [points[0]]; out = list(points[1:]); edges = []
    while out:
        best = None
        for i, p in enumerate(inn):
            for j, q in enumerate(out):
                d = math.hypot(p[0] - q[0], p[1] - q[1])
                if best is None or d < best[0]: best = (d, i, j)
        d, i, j = best; edges.append((inn[i], out[j], d)); inn.append(out.pop(j))
    return edges

def ratsnest(b, skip=('GND',)):
    nets = {}
    for p in b.pads():
        if p.net: nets.setdefault(p.net, []).append((p.x, p.y))
    tot = 0; lines = []
    for n, pts in nets.items():
        if n in skip: continue
        for a, c, d in mst(pts): tot += d; lines.append((n, a, c))
    return tot, lines

if __name__ == '__main__':
    b = load_placed()
    tot, lines = ratsnest(b)
    print('ratsnest (non-GND) %.0f mm' % tot)
    def extra(ax):
        for n, a, c in lines:
            col = {'+3V3': 'orange', '+5V': 'magenta', 'VBAT_F': 'red', 'VBAT': 'red', 'VBAT_SW': 'red', 'VBAT_D': 'red', 'VSYS': 'magenta'}.get(n, 'cyan')
            ax.plot([a[0], c[0]], [a[1], c[1]], color=col, lw=0.8, alpha=0.8, zorder=8)
    layout.draw(b, '/home/claude/work/place_v2.png', title='placement v2 + ratsnest (GND omitted)', extra=extra)
