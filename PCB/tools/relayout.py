"""Re-place, route and finish hardware/RobotEV.kicad_pcb  --  pure Python, no KiCad needed.

    python tools/relayout.py            # place + route + stitch + silkscreen, writes the board
    python tools/relayout.py --check    # only run the built-in DRC on the current board file

Footprints are taken from the board file itself (they are KiCad's own, as exported by gen_pcb.py);
nets come from tools/design.py; positions from tools/placement.py.  Existing tracks, vias and
silkscreen text are discarded and regenerated, so the result is deterministic.
KiCad is still the final authority: build.py runs KiCad's DRC and refills the GND pours afterwards.
"""
import copy, itertools, math, os, random, sys, uuid
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sx, geom, pcbdraw, router, placement as PL
import design as D
D.BOARD_W, D.BOARD_H, D.CORNER_R = PL.BOARD_W, PL.BOARD_H, PL.CORNER_R

ROOT = os.path.dirname(HERE)
PCB = os.path.join(ROOT, 'hardware', 'RobotEV.kicad_pcb')
BUILD = os.path.join(ROOT, 'build')

POWER_W = {'VBAT': [3.0, 2.0, 1.2, 0.8], 'VBAT_F': [2.5, 2.0, 1.2, 0.8],
           'VBAT_SW': [0.8, 0.5, 0.3], 'VBAT_D': [0.8, 0.5, 0.3],
           '+5V': [0.5, 0.4, 0.3, 0.25], '+3V3': [0.5, 0.4, 0.3, 0.25], 'VSYS': [0.5, 0.4, 0.3]}
SIG_W = [0.25, 0.2]
# layer-cost per net: (F.Cu, B.Cu).  Power spines live on B.Cu, signals on F.Cu.
LCOST = {'+5V': (1.6, 1.0), '+3V3': (1.6, 1.0)}
ORDER = ['VBAT', 'VBAT_F', 'VBAT_SW', 'VBAT_D', 'VSYS', '+5V', '+3V3']

def uid(): return str(uuid.uuid4())

# ------------------------------------------------------------------ board load / place
def thin_pico_courtyard(fp):
    """Pico courtyard = the two socket strips only, so small SMD parts may sit under the module."""
    for g in sx.find(fp.node, 'fp_line'):
        if sx.first(g, 'layer')[1] == 'F.CrtYd': fp.node.remove(g)
    for g in sx.find(fp.node, 'fp_rect'):
        if sx.first(g, 'layer')[1] == 'F.CrtYd': fp.node.remove(g)
    last = max(i for i, c in enumerate(fp.node) if isinstance(c, list) and c[0] in ('fp_line', 'fp_rect', 'fp_circle'))
    for xc in (-8.89, 8.89):
        r = [sx.Sym('fp_rect'), [sx.Sym('start'), round(xc - 1.4, 3), -25.4], [sx.Sym('end'), round(xc + 1.4, 3), 25.4],
             [sx.Sym('stroke'), [sx.Sym('width'), 0.05], [sx.Sym('type'), sx.Sym('default')]], [sx.Sym('fill'), sx.Sym('no')],
             [sx.Sym('layer'), 'F.CrtYd'], [sx.Sym('uuid'), uid()]]
        fp.node.insert(last + 1, r)

def load_and_place():
    b = geom.Board(PCB)
    # nets from design.py (single source of truth); fixes parts whose pads were left unconnected
    for part in D.PARTS:
        fp = b.fps[part['ref']]
        for p in fp.pads:
            net = part['pins'].get(int(p.num)) if p.num.isdigit() else None
            p.net = net
            nn = sx.first(p.node, 'net')
            if nn: p.node.remove(nn)
            if net:
                # keep KiCad's element order: net goes after layers / roundrect_rratio
                idx = max(i for i, c in enumerate(p.node) if isinstance(c, list) and c[0] in ('layers', 'roundrect_rratio', 'remove_unused_layers'))
                p.node.insert(idx + 1, [sx.Sym('net'), net])
    thin_pico_courtyard(b.fps['U1'])
    PL.PLACE.update({'H%d' % (i + 1): (x, y, 0) for i, (x, y) in enumerate(PL.HOLES)})
    for r, (x, y, a) in PL.PLACE.items():
        pcbdraw.set_pos(b.fps[r], x, y, a)
    for r, (x, y, a) in PL.ORIGIN.items():
        fp = b.fps[r]; da = a - fp.a; pcbdraw.apply_rot(fp.node, da); fp.a = a; fp.x, fp.y = x, y
        at = sx.first(fp.node, 'at'); at[1], at[2] = x, y
        if len(at) > 3: at[3] = a
        else: at.append(a)
        for p in fp.pads: p.update(fp)
    return b

# ------------------------------------------------------------------ routing
def route_all(b, seed=0, verbose=True):
    W, H, R = D.BOARD_W, D.BOARD_H, D.CORNER_R
    rt = router.Router(W, H, R)
    nets = {}
    for ref, fp in b.fps.items():
        for p in fp.pads:
            o = rt.add_pad(p, ref + '.' + p.num)
            if p.net: nets.setdefault(p.net, []).append(rt.objs[-1])
    nets.pop('GND', None)
    def mstlen(pads):
        pts = [(p.prim[1], p.prim[2]) for p in pads]
        import preview as pv
        return sum(d for _, _, d in pv.mst(pts))
    sigs = sorted([n for n in nets if n not in ORDER], key=lambda n: mstlen(nets[n]))
    rnd = random.Random(seed)
    if seed: 
        # keep short nets first but jitter
        sigs.sort(key=lambda n: mstlen(nets[n]) * rnd.uniform(0.7, 1.4))
    result = {}; fails = []
    for n in ORDER + sigs:
        if n not in nets: continue
        widths = POWER_W.get(n, SIG_W)
        lc = LCOST.get(n, (1.0, 1.5))
        res = rt.route_net(n, nets[n], widths, lc)
        if res is None:
            fails.append(n); 
            if verbose: print('  FAIL', n)
        else:
            segs, vias, w = res
            result[n] = (segs, vias, w)
            if verbose: print('  ok  %-10s w=%.2f  %3d seg %d via' % (n, w, len(segs), len(vias)))
    return rt, result, fails

def stitch_vias(rt, b, result):
    """GND stitching vias on a loose grid wherever both layers are free; returns via list"""
    blocked, near, via_ok = rt.masks('GND', 0.25)
    vias = []
    step = 7.5
    gx = 4.0
    while gx < D.BOARD_W - 3:
        gy = 3.5
        while gy < D.BOARD_H - 3:
            # search a small neighbourhood for a legal spot
            best = None
            for dx in np.arange(-1.5, 1.51, 0.1):
                for dy in np.arange(-1.5, 1.51, 0.1):
                    i = int(round((gx + dx) / router.G)); j = int(round((gy + dy) / router.G))
                    if 0 <= i < rt.nx and 0 <= j < rt.ny and via_ok[j, i]:
                        d = math.hypot(dx, dy)
                        if best is None or d < best[0]: best = (d, i * router.G, j * router.G)
            if best:
                x, y = round(best[1], 4), round(best[2], 4)
                # do not stack vias closer than 2.5 mm
                if all(math.hypot(x - v[0], y - v[1]) > 5.0 for v in vias):
                    vias.append((x, y)); rt.add_via(x, y, 'GND')
                    blocked, near, via_ok = rt.masks('GND', 0.25)
            gy += step
        gx += step
    return vias

# ------------------------------------------------------------------ built-in DRC
def drc(b, segs, vias, verbose=True):
    """exact geometry check: clearance, shorts, edge, hole-to-hole, connectivity of non-GND nets"""
    objs = []
    for fp in b.fps.values():
        for p in fp.pads:
            L = 'FB' if (p.thru or not (p.on_f ^ p.on_b)) else ('F' if p.on_f else 'B')
            objs.append(dict(k='pad', net=p.net, prim=p.prim(), L=L, name='%s.%s' % (fp.ref, p.num), fp=fp.ref))
    for s in segs:
        objs.append(dict(k='trk', net=s['net'], prim=('cap', s['x1'], s['y1'], s['x2'], s['y2'], s['w'] / 2), L='F' if s['layer'] == 'F.Cu' else 'B', name='trk', fp=None))
    for v in vias:
        objs.append(dict(k='via', net=v['net'], prim=('cap', v['x'], v['y'], v['x'], v['y'], v['d'] / 2), L='FB', name='via@%.2f,%.2f' % (v['x'], v['y']), fp=None))
    errs = []
    # bucket by 3 mm cells
    cell = 3.0; buckets = {}
    for i, o in enumerate(objs):
        pr = o['prim']
        if pr[0] == 'cap': x0, y0, x1, y1 = min(pr[1], pr[3]) - pr[5], min(pr[2], pr[4]) - pr[5], max(pr[1], pr[3]) + pr[5], max(pr[2], pr[4]) + pr[5]
        else: x0, y0, x1, y1 = pr[1:5]
        o['bb'] = (x0, y0, x1, y1)
        for cx in range(int((x0 - 0.5) // cell), int((x1 + 0.5) // cell) + 1):
            for cy in range(int((y0 - 0.5) // cell), int((y1 + 0.5) // cell) + 1):
                buckets.setdefault((cx, cy), []).append(i)
    seen = set()
    for lst in buckets.values():
        for i, j in itertools.combinations(sorted(lst), 2):
            if (i, j) in seen: continue
            seen.add((i, j))
            a, c = objs[i], objs[j]
            if a['net'] is not None and a['net'] == c['net']: continue
            if a['k'] == 'pad' and c['k'] == 'pad' and a['fp'] == c['fp']: continue
            if not (set(a['L']) & set(c['L'])): continue
            d = geom.prim_dist(a['prim'], c['prim'])
            if d < router.CLR - 1e-6:
                kind = 'SHORT' if d <= 0 else 'clearance'
                errs.append((kind, a['name'], a['net'], c['name'], c['net'], round(d, 3)))
    # edge
    W, H, R = D.BOARD_W, D.BOARD_H, D.CORNER_R
    def edge_d(x, y):
        qx = abs(x - W / 2) - (W / 2 - R); qy = abs(y - H / 2) - (H / 2 - R)
        sd = math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - R
        return -sd
    for o in objs:
        if o['k'] == 'pad' and o['name'].split('.')[0].startswith('H'): continue
        pr = o['prim']
        pts = [(pr[1], pr[2]), (pr[3], pr[4])] if pr[0] == 'cap' else [(pr[1], pr[2]), (pr[3], pr[2]), (pr[3], pr[4]), (pr[1], pr[4])]
        rad = pr[5] if pr[0] == 'cap' else 0
        for x, y in pts:
            if edge_d(x, y) - rad < 0.3 - 1e-6:
                errs.append(('edge', o['name'], o['net'], '', '', round(edge_d(x, y) - rad, 3))); break
    # courtyard overlaps (KiCad reports these as errors on this project)
    rects = {}
    for fp in b.fps.values():
        for k, c in enumerate(pcbdraw.courtyards(fp)):
            pts = [geom.rot(*q, fp.a) for q in ((c[0], c[1]), (c[2], c[1]), (c[2], c[3]), (c[0], c[3]))]
            xs = [fp.x + q[0] for q in pts]; ys = [fp.y + q[1] for q in pts]
            rects['%s#%d' % (fp.ref, k) if k else fp.ref] = (min(xs), min(ys), max(xs), max(ys))
    for (ra, a), (rb, c) in itertools.combinations(rects.items(), 2):
        if ra.split('#')[0] == rb.split('#')[0]: continue
        if a[0] < c[2] - 1e-6 and c[0] < a[2] - 1e-6 and a[1] < c[3] - 1e-6 and c[1] < a[3] - 1e-6:
            errs.append(('courtyard', ra, '', rb, '', 0))
    for ref, r in rects.items():
        if r[0] < 0.2 or r[1] < 0.2 or r[2] > D.BOARD_W - 0.2 or r[3] > D.BOARD_H - 0.2:
            errs.append(('courtyard_outside', ref, '', '', '', 0))
    # tall parts must stay out from under the Pico module (it floats ~8.5 mm above the board)
    u1 = b.fps['U1']; mod = (u1.x - 10.6, u1.y - 25.6, u1.x + 10.6, u1.y + 25.6)
    for ref in PL.TALL:
        r = None
        for k, v in rects.items():
            if k.split('#')[0] == ref: r = v if r is None else (min(r[0], v[0]), min(r[1], v[1]), max(r[2], v[2]), max(r[3], v[3]))
        if r and r[0] < mod[2] and mod[0] < r[2] and r[1] < mod[3] and mod[1] < r[3]:
            errs.append(('tall_under_pico', ref, '', 'U1', '', 0))
    # via drill to pad drill
    drills = [(p.x, p.y, max(p.drill) / 2, '%s.%s' % (fp.ref, p.num)) for fp in b.fps.values() for p in fp.pads if p.drill]
    for v in vias:
        for (x, y, r, nm) in drills:
            if math.hypot(v['x'] - x, v['y'] - y) - r - v['drill'] / 2 < 0.25:
                errs.append(('hole_to_hole', 'via@%.2f,%.2f' % (v['x'], v['y']), v['net'], nm, '', 0)); break
    # connectivity of every routed net (non-GND): union-find over touching copper
    nets = {}
    for i, o in enumerate(objs):
        if o['net'] and o['net'] != 'GND': nets.setdefault(o['net'], []).append(i)
    opens = []
    for n, idxs in nets.items():
        par = {i: i for i in idxs}
        def f(x):
            while par[x] != x: par[x] = par[par[x]]; x = par[x]
            return x
        for i, j in itertools.combinations(idxs, 2):
            a, c = objs[i], objs[j]
            if not (set(a['L']) & set(c['L'])): continue
            if geom.prim_dist(a['prim'], c['prim']) <= 1e-9: par[f(i)] = f(j)
        pads = [i for i in idxs if objs[i]['k'] == 'pad']
        roots = {f(i) for i in pads}
        if len(roots) > 1: opens.append((n, len(roots)))
    if verbose:
        print('DRC: %d violation(s), %d open net(s)' % (len(errs), len(opens)))
        for e in errs[:30]: print('  ', e)
        for o in opens: print('  OPEN', o)
    return errs, opens

def pour_connectivity(b, segs, vias, res=0.1):
    """raster check that every GND pad lands in one connected copper pour (both layers + vias)"""
    from scipy import ndimage
    W, H, R = D.BOARD_W, D.BOARD_H, D.CORNER_R
    nx, ny = int(W / res) + 1, int(H / res) + 1
    X, Y = np.meshgrid(np.arange(nx) * res, np.arange(ny) * res)
    rt = router.Router.__new__(router.Router)
    rt.nx, rt.ny, rt.X, rt.Y, rt.W, rt.H, rt.R = nx, ny, X, Y, W, H, R
    router.G = res
    edge = router.Router._edge_distance(rt)
    masks = []
    objs = []
    for fp in b.fps.values():
        for p in fp.pads:
            L = {0, 1} if (p.thru) else ({0} if p.on_f else {1})
            objs.append((p.prim(), p.net, L, p))
    for s in segs: objs.append((('cap', s['x1'], s['y1'], s['x2'], s['y2'], s['w'] / 2), s['net'], {0 if s['layer'] == 'F.Cu' else 1}, None))
    for v in vias: objs.append((('cap', v['x'], v['y'], v['x'], v['y'], v['d'] / 2), v['net'], {0, 1}, None))
    fills = []
    for l in (0, 1):
        m = np.zeros((ny, nx), bool)
        for pr, net, L, p in objs:
            if l in L and net != 'GND': rt._stamp(m, pr, 0.2 + 0.02)
        fills.append(~m & (edge > 0.6 + 0.02))
    lab = [ndimage.label(f)[0] for f in fills]
    # union labels of F and B through GND vias / thru pads
    par = {}
    def f(x):
        par.setdefault(x, x)
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    def at(l, x, y):
        i, j = int(round(x / res)), int(round(y / res))
        return lab[l][j, i] if 0 <= i < nx and 0 <= j < ny else 0
    pad_nodes = []
    for pr, net, L, p in objs:
        if net != 'GND': continue
        nodes = set()
        cx, cy = (pr[1], pr[2]) if pr[0] == 'cap' else ((pr[1] + pr[3]) / 2, (pr[2] + pr[4]) / 2)
        for l in L:
            # any filled pixel inside / touching the pad
            sub = np.zeros((ny, nx), bool); rt._stamp(sub, pr, 0.15)
            ls = np.unique(lab[l][sub & fills[l]]); 
            for v in ls:
                if v: nodes.add((l, int(v)))
        if p is not None or True:
            nodes = list(nodes)
            for a in nodes[1:]: par[f(nodes[0])] = f(a)
            if p is not None: pad_nodes.append((p.ref + '.' + p.num, nodes))
    # tracks of net GND are none; vias & THT pads already unify via nodes above (thru pads give both layers)
    for v in vias:
        if v['net'] == 'GND':
            a, c = (0, int(at(0, v['x'], v['y']))), (1, int(at(1, v['x'], v['y'])))
            if a[1] and c[1]: par[f(a)] = f(c)
    comps = {}
    bad = []
    for nm, nodes in pad_nodes:
        if not nodes: bad.append(nm); continue
        comps.setdefault(f(nodes[0]), []).append(nm)
    return comps, bad

# ------------------------------------------------------------------ silkscreen
NAME = 'HARJAS SIDHU'
MANUAL_LABELS = [  # (text, x, y, angle, size): placed at the nearest free spot to (x, y)
    ('BATT 8xAA', 20.2, 14.7, 90, 0.8), ('ESC PWR', 20.2, 29.5, 90, 0.8),
    ('RPI PICO 2', 50.0, 21.0, 0, 1.2), ('USB', 50.0, 60.6, 0, 1.0),
    (NAME, 79.0, 32.0, 90, 1.2),
]
LABELS = [  # (text, anchor ref, preferred sides)
    ('PWR SW', 'J3', ('below', 'above')),
    ('ENC L', 'J4', ('above',)), ('ENC R', 'J5', ('above',)), ('WT901', 'J6', ('above',)),
    ('LCD', 'J7', ('above', 'right')), ('START', 'J8', ('below',)), ('MODE', 'J9', ('below',)),
    ('ESC SIG', 'J10', ('above',)),
]

def fp_world_bbox(fp):
    xs, ys = [], []
    for p in fp.pads:
        pr = p.prim()
        if pr[0] == 'cap': xs += [pr[1] - pr[5], pr[3] + pr[5]]; ys += [pr[2] - pr[5], pr[4] + pr[5]]
        else: xs += [pr[1], pr[3]]; ys += [pr[2], pr[4]]
    for c in pcbdraw.courtyards(fp):
        pts = [geom.rot(*q, fp.a) for q in ((c[0], c[1]), (c[2], c[1]), (c[2], c[3]), (c[0], c[3]))]
        xs += [fp.x + q[0] for q in pts]; ys += [fp.y + q[1] for q in pts]
    return min(xs), min(ys), max(xs), max(ys)

def do_silk(b, root):
    """strip old silk labels, hide fp reference text, add gr_text refs/labels placed clear of pads"""
    # remove old board texts
    for n in sx.find(root, 'gr_text'): root.remove(n)
    obstacles = []
    for fp in b.fps.values():
        for t in list(sx.find(fp.node, 'fp_text')):
            ly = sx.first(t, 'layer')[1]
            if ly == 'F.SilkS' and t[2] not in ('+', '-'): fp.node.remove(t)
        for p in fp.pads:
            pr = p.prim()
            if pr[0] == 'cap': obstacles.append((pr[1] - pr[5] - .3, pr[2] - pr[5] - .3, pr[3] + pr[5] + .3, pr[4] + pr[5] + .3))
            else: obstacles.append((pr[1] - .3, pr[2] - .3, pr[3] + .3, pr[4] + .3))
        # silk outlines of this footprint (world bbox of each segment)
        for g in sx.find(fp.node, 'fp_line') + sx.find(fp.node, 'fp_rect'):
            if sx.first(g, 'layer')[1] != 'F.SilkS': continue
            s_, e_ = sx.first(g, 'start'), sx.first(g, 'end')
            q1 = geom.rot(float(s_[1]), float(s_[2]), fp.a); q2 = geom.rot(float(e_[1]), float(e_[2]), fp.a)
            obstacles.append((min(q1[0], q2[0]) + fp.x - .15, min(q1[1], q2[1]) + fp.y - .15, max(q1[0], q2[0]) + fp.x + .15, max(q1[1], q2[1]) + fp.y + .15))
        for g in sx.find(fp.node, 'fp_circle'):
            if sx.first(g, 'layer')[1] != 'F.SilkS': continue
            c_, e_ = sx.first(g, 'center'), sx.first(g, 'end')
            q = geom.rot(float(c_[1]), float(c_[2]), fp.a); r = math.hypot(float(e_[1]) - float(c_[1]), float(e_[2]) - float(c_[2]))
            obstacles.append((fp.x + q[0] - r, fp.y + q[1] - r, fp.x + q[0] + r, fp.y + q[1] + r))
    # +/- marks inside footprints are obstacles too
    for fp in b.fps.values():
        for t in sx.find(fp.node, 'fp_text'):
            if t[2] in ('+', '-') and sx.first(t, 'layer')[1] == 'F.SilkS':
                a = sx.first(t, 'at'); q = geom.rot(float(a[1]), float(a[2]), fp.a)
                obstacles.append((fp.x + q[0] - .9, fp.y + q[1] - .9, fp.x + q[0] + .9, fp.y + q[1] + .9))
    W, H = D.BOARD_W, D.BOARD_H
    def free(r):
        x0, y0, x1, y1 = r
        if x0 < 1.0 or y0 < 1.0 or x1 > W - 1.0 or y1 > H - 1.0: return False
        # keep out of the rounded corners
        for cx, cy in ((D.CORNER_R, D.CORNER_R), (W - D.CORNER_R, D.CORNER_R), (D.CORNER_R, H - D.CORNER_R), (W - D.CORNER_R, H - D.CORNER_R)):
            if (x0 < D.CORNER_R and y0 < D.CORNER_R) or (x1 > W - D.CORNER_R and y0 < D.CORNER_R) or (x0 < D.CORNER_R and y1 > H - D.CORNER_R) or (x1 > W - D.CORNER_R and y1 > H - D.CORNER_R):
                if math.hypot(max(abs((x0 + x1) / 2 - cx) - (x1 - x0) / 2, 0), max(abs((y0 + y1) / 2 - cy) - (y1 - y0) / 2, 0)) > D.CORNER_R - 1.0: pass
        for o in obstacles:
            if x0 < o[2] and o[0] < x1 and y0 < o[3] and o[1] < y1: return False
        return True
    def add_text(text, x, y, size=0.8, thick=0.15, angle=0):
        n = [sx.Sym('gr_text'), text, [sx.Sym('at'), round(x, 3), round(y, 3), angle], [sx.Sym('layer'), 'F.SilkS'],
             [sx.Sym('uuid'), uid()], [sx.Sym('effects'), [sx.Sym('font'), [sx.Sym('size'), size, size], [sx.Sym('thickness'), thick]]]]
        root.append(n)
    def tsize(text, size): return len(text) * size * 0.78 + 0.2, size * 1.1
    def place_text(text, bb, sides, size=0.8, gap=0.6):
        w, h = tsize(text, size)
        cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
        cands = []
        for s in sides:
            if s == 'above': cands += [(cx + k, bb[1] - gap - h / 2) for k in (0, -3, 3, -6, 6)]
            if s == 'below': cands += [(cx + k, bb[3] + gap + h / 2) for k in (0, -3, 3, -6, 6)]
            if s == 'left': cands += [(bb[0] - gap - w / 2, cy + k) for k in (0, -3, 3)]
            if s == 'right': cands += [(bb[2] + gap + w / 2, cy + k) for k in (0, -3, 3)]
        for k in (1.0, 2.0, 3.0):
            for dx in (-1.5, 0, 1.5):
                cands += [(cx + dx, bb[1] - gap - h / 2 - k), (cx + dx, bb[3] + gap + h / 2 + k)]
            cands += [(bb[0] - gap - w / 2 - k, cy), (bb[2] + gap + w / 2 + k, cy)]
        for (x, y) in cands:
            r = (x - w / 2, y - h / 2, x + w / 2, y + h / 2)
            if free(r):
                obstacles.append(r); return x, y
        return None
    for text, x0, y0, ang, size in MANUAL_LABELS:
        w, h = tsize(text, size)
        if ang == 90: w, h = h, w
        cands = sorted(((dx * 0.5, dy * 0.5) for dx in range(-24, 25) for dy in range(-24, 25)), key=lambda d: d[0] ** 2 + d[1] ** 2)
        for dx, dy in cands:
            r = (x0 + dx - w / 2, y0 + dy - h / 2, x0 + dx + w / 2, y0 + dy + h / 2)
            if free(r):
                add_text(text, x0 + dx, y0 + dy, size=size, thick=0.2 if size > 1 else 0.15, angle=ang); obstacles.append(r); break
        else:
            print('  (no room for silk label %r)' % text)
    placed = {}
    for text, ref, sides in LABELS:
        bb = fp_world_bbox(b.fps[ref])
        pos = place_text(text, bb, sides + ('above', 'below', 'right', 'left'), 0.8, 0.5)
        if pos: add_text(text, pos[0], pos[1]); placed[ref] = pos
    # board name / pico marking
    u = fp_world_bbox(b.fps['U1'])
    for line, dy in (('RPI PICO 2', 0), ):
        pass
    # reference designators
    for ref, fp in b.fps.items():
        if (ref.startswith('H') and ref[1:].isdigit()) or ref in ('J1', 'J2'):
            for pr in sx.find(fp.node, 'property'):
                if pr[1] == 'Reference' and not sx.first(pr, 'hide'): pr.insert(5, [sx.Sym('hide'), sx.Sym('yes')])
            continue
        bb = fp_world_bbox(fp)
        pos = place_text(ref, bb, ('above', 'below', 'right', 'left'), 0.8 if ref != 'U1' else 1.0, 0.25)
        for pr in sx.find(fp.node, 'property'):
            if pr[1] != 'Reference': continue
            at = sx.first(pr, 'at')
            hid = sx.first(pr, 'hide')
            if pos is None:
                if not hid: pr.insert(5, [sx.Sym('hide'), sx.Sym('yes')])
                print('  (no room for silk ref %s - hidden)' % ref); continue
            lx, ly = geom.rot(pos[0] - fp.x, pos[1] - fp.y, -fp.a)
            at[1], at[2] = round(lx, 4), round(ly, 4)
            if len(at) > 3: at[3] = 0
            else: at.append(0)
            if hid: pr.remove(hid)
            ef = sx.first(pr, 'effects'); ft = sx.first(ef, 'font'); sz = sx.first(ft, 'size'); sz[1] = sz[2] = 0.8 if ref != 'U1' else 1.0
            th = sx.first(ft, 'thickness')
            if th: th[1] = 0.13
    # title
    for line, ty in (('EV CONTROLLER REV C', H - 2.2),):
        pass
    return obstacles

# ------------------------------------------------------------------ write
def rebuild_outline(root):
    W, H, R = D.BOARD_W, D.BOARD_H, D.CORNER_R
    for n in sx.find(root, 'gr_line') + sx.find(root, 'gr_arc'):
        if sx.first(n, 'layer')[1] == 'Edge.Cuts': root.remove(n)
    def stroke(): return [sx.Sym('stroke'), [sx.Sym('width'), 0.1], [sx.Sym('type'), sx.Sym('default')]]
    items = []
    for (x1, y1, x2, y2) in ((R, 0, W - R, 0), (W, R, W, H - R), (W - R, H, R, H), (0, H - R, 0, R)):
        items.append([sx.Sym('gr_line'), [sx.Sym('start'), x1, y1], [sx.Sym('end'), x2, y2], stroke(), [sx.Sym('layer'), 'Edge.Cuts'], [sx.Sym('uuid'), uid()]])
    k = R * (1 - math.cos(math.radians(45)))
    for (sx_, sy_), (mx, my), (ex, ey) in (((0, R), (k, k), (R, 0)), ((W - R, 0), (W - k, k), (W, R)), ((W, H - R), (W - k, H - k), (W - R, H)), ((R, H), (k, H - k), (0, H - R))):
        items.append([sx.Sym('gr_arc'), [sx.Sym('start'), sx_, sy_], [sx.Sym('mid'), round(mx, 6), round(my, 6)], [sx.Sym('end'), ex, ey], stroke(), [sx.Sym('layer'), 'Edge.Cuts'], [sx.Sym('uuid'), uid()]])
    last = max(i for i, c in enumerate(root) if isinstance(c, list) and c[0] == 'footprint')
    root[last + 1:last + 1] = items
    # GND pours follow the outline (0.6 mm inset)
    m = 0.6; r = R - m; pts = []
    for (cx, cy, a0) in ((W - R, R, -90), (W - R, H - R, 0), (R, H - R, 90), (R, R, 180)):
        for i in range(0, 13):
            a = math.radians(a0 + i * 7.5); pts.append((round(cx + r * math.cos(a), 6), round(cy + r * math.sin(a), 6)))
    for z in sx.find(root, 'zone'):
        poly = sx.first(z, 'polygon'); old = sx.first(poly, 'pts')
        old[1:] = [[sx.Sym('xy'), x, y] for x, y in pts]

def _voronoi(root, layer, allowed, seed=7, n=78, width=0.2, dot=0.32, min_len=0.3):
    """Voronoi web as silkscreen lines + node dots on `layer`; `allowed(x, y)` is the keep-in test."""
    from scipy.spatial import Voronoi
    W, H = D.BOARD_W, D.BOARD_H
    def uidn(): return [sx.Sym('uuid'), uid()]
    rng = np.random.default_rng(seed)
    n = int(n * (W * H) / (70.0 * 56.0))
    pts = np.column_stack([rng.uniform(0, W, n), rng.uniform(0, H, n)])
    def mirrored(p): return np.vstack([p, p * [-1, 1], p * [1, -1], p * [-1, 1] + [2 * W, 0], p * [1, -1] + [0, 2 * H]])
    for _ in range(2):                      # light Lloyd relaxation -> even but organic cells
        vor = Voronoi(mirrored(pts)); new = pts.copy()
        for i in range(n):
            reg = vor.regions[vor.point_region[i]]
            if -1 in reg or not reg: continue
            poly = vor.vertices[reg]; new[i] = [np.clip(poly[:, 0].mean(), 0, W), np.clip(poly[:, 1].mean(), 0, H)]
        pts = 0.6 * pts + 0.4 * new
    vor = Voronoi(mirrored(pts)); verts = vor.vertices
    lines = 0; dots = set(); ends = set()
    for (i, j), rv in zip(vor.ridge_points, vor.ridge_vertices):
        if -1 in rv or (i >= n and j >= n): continue
        a, c = verts[rv[0]], verts[rv[1]]
        L = float(np.hypot(*(c - a)))
        if L < 0.3: continue
        steps = max(2, int(L / 0.1))
        ok = [allowed(*(a + (c - a) * t / steps)) for t in range(steps + 1)]
        t0 = None
        for t in range(steps + 2):
            good = t <= steps and ok[t]
            if good and t0 is None: t0 = t
            if (not good) and t0 is not None:
                if (t - 1 - t0) * L / steps >= min_len:
                    p0 = a + (c - a) * t0 / steps; p1 = a + (c - a) * (t - 1) / steps
                    root.append([sx.Sym('gr_line'), [sx.Sym('start'), round(float(p0[0]), 3), round(float(p0[1]), 3)], [sx.Sym('end'), round(float(p1[0]), 3), round(float(p1[1]), 3)],
                                 [sx.Sym('stroke'), [sx.Sym('width'), width], [sx.Sym('type'), sx.Sym('default')]], [sx.Sym('layer'), layer], uidn()]); lines += 1
                    if min_len > 1: ends.add((round(float(p0[0]), 3), round(float(p0[1]), 3))); ends.add((round(float(p1[0]), 3), round(float(p1[1]), 3)))
                t0 = None
        if min_len <= 1:
            for k in rv:
                vx, vy = verts[k]
                if allowed(vx, vy): dots.add((round(float(vx), 3), round(float(vy), 3)))
    if min_len > 1: dots = ends
    for vx, vy in sorted(dots):
        root.append([sx.Sym('gr_circle'), [sx.Sym('center'), vx, vy], [sx.Sym('end'), vx + dot, vy], [sx.Sym('stroke'), [sx.Sym('width'), 0.1], [sx.Sym('type'), sx.Sym('default')]],
                     [sx.Sym('fill'), sx.Sym('yes')], [sx.Sym('layer'), layer], uidn()])
    print('  %s voronoi: %d segments, %d node dots' % (layer, lines, len(dots)))

def _inside_board(x, y, inset):
    W, H, R = D.BOARD_W, D.BOARD_H, D.CORNER_R
    qx = abs(x - W / 2) - (W / 2 - R); qy = abs(y - H / 2) - (H / 2 - R)
    d = math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - R
    return -d >= inset

def _hole_list(b, vias):
    holes = []
    for fp in b.fps.values():
        for p in fp.pads:
            if p.thru: holes.append((p.x, p.y, max(p.W, p.H) / 2 + 0.55))
            if fp.ref.startswith('H') and fp.ref[1:].isdigit(): holes[-1] = (p.x, p.y, 3.4)
    for v in vias: holes.append((v['x'], v['y'], v['d'] / 2 + 0.55))
    return holes

def back_art(b, root, vias, seed=7):
    """B.SilkS: title (mirrored) + Voronoi web.  Lines stop short of every hole/via/pad and of the text."""
    for n in sx.find(root, 'gr_line') + sx.find(root, 'gr_circle') + sx.find(root, 'gr_text'):
        ly = sx.first(n, 'layer')
        if ly and ly[1] == 'B.SilkS': root.remove(n)
    u1 = b.fps['U1']
    title = [('EV CONTROLLER', u1.x, u1.y - 13.0, 1.25), ('REV C', u1.x, u1.y - 9.4, 1.25)]
    keep_rects = []
    for text, x, y, sz in title:
        w = len(text) * sz * 0.9 + 0.6
        root.append([sx.Sym('gr_text'), text, [sx.Sym('at'), round(x, 3), round(y, 3), 0], [sx.Sym('layer'), 'B.SilkS'], [sx.Sym('uuid'), uid()],
                     [sx.Sym('effects'), [sx.Sym('font'), [sx.Sym('size'), sz, sz], [sx.Sym('thickness'), 0.2]], [sx.Sym('justify'), sx.Sym('mirror')]]])
        keep_rects.append((x - w / 2 - 1.0, y - sz / 2 - 1.0, x + w / 2 + 1.0, y + sz / 2 + 1.0))
    holes = _hole_list(b, vias)
    def allowed(x, y):
        if not _inside_board(x, y, 1.3): return False
        for (cx, cy, r) in holes:
            if (x - cx) ** 2 + (y - cy) ** 2 < r * r: return False
        for (x0, y0, x1, y1) in keep_rects:
            if x0 < x < x1 and y0 < y < y1: return False
        return True
    _voronoi(root, 'B.SilkS', allowed, seed=seed)

def front_art(b, root, vias, obstacles, seed=11):
    """F.SilkS Voronoi web in the free space: clear of pads, part courtyards, screw heads, text and silk outlines."""
    for n in sx.find(root, 'gr_line') + sx.find(root, 'gr_circle'):
        ly = sx.first(n, 'layer')
        if ly and ly[1] == 'F.SilkS': root.remove(n)
    rects = [(o[0] - 0.25, o[1] - 0.25, o[2] + 0.25, o[3] + 0.25) for o in obstacles]
    for fp in b.fps.values():
        for c in pcbdraw.courtyards(fp):
            pts = [geom.rot(*q, fp.a) for q in ((c[0], c[1]), (c[2], c[3]))]
            xs = [fp.x + q[0] for q in pts]; ys = [fp.y + q[1] for q in pts]
            rects.append((min(xs) - 0.5, min(ys) - 0.5, max(xs) + 0.5, max(ys) + 0.5))
    u1 = b.fps['U1']
    rects.append((u1.x - 10.7, u1.y - 25.7, u1.x + 10.7, u1.y + 25.7))     # under the Pico module
    holes = [(p.x, p.y, 3.6) for fp in b.fps.values() if fp.ref.startswith('H') and fp.ref[1:].isdigit() for p in fp.pads]
    holes += [(v['x'], v['y'], 0.9) for v in vias]
    def allowed(x, y):
        if not _inside_board(x, y, 1.0): return False
        for (cx, cy, r) in holes:
            if (x - cx) ** 2 + (y - cy) ** 2 < r * r: return False
        for (x0, y0, x1, y1) in rects:
            if x0 < x < x1 and y0 < y < y1: return False
        return True
    _voronoi(root, 'F.SilkS', allowed, seed=seed, width=0.18, dot=0.28, min_len=3.0)

def write_board(b, root, segs, vias, path, front_obstacles=()):
    rebuild_outline(root)
    back_art(b, root, vias)
    front_art(b, root, vias, front_obstacles)
    for n in sx.find(root, 'segment') + sx.find(root, 'via'): root.remove(n)
    for z in sx.find(root, 'zone'):
        for fpoly in sx.find(z, 'filled_polygon'): z.remove(fpoly)
    # title block
    tb = sx.first(root, 'title_block')
    for k, v in (('title', 'EV Controller - RP2350 / 8xAA / Weka dual ESC'), ('date', '2026-11-15'), ('rev', 'C')):
        e = sx.first(tb, k)
        if e: e[1] = v
    # insert tracks after the last footprint
    last = max(i for i, c in enumerate(root) if isinstance(c, list) and c[0] == 'footprint')
    new = []
    for s in segs:
        new.append([sx.Sym('segment'), [sx.Sym('start'), s['x1'], s['y1']], [sx.Sym('end'), s['x2'], s['y2']], [sx.Sym('width'), s['w']],
                    [sx.Sym('layer'), s['layer']], [sx.Sym('net'), s['net']], [sx.Sym('uuid'), uid()]])
    for v in vias:
        new.append([sx.Sym('via'), [sx.Sym('at'), v['x'], v['y']], [sx.Sym('size'), v['d']], [sx.Sym('drill'), v['drill']],
                    [sx.Sym('layers'), 'F.Cu', 'B.Cu'], [sx.Sym('net'), v['net']], [sx.Sym('uuid'), uid()]])
    root[last + 1:last + 1] = new
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(sx.dump(root) + '\n')

def to_board_items(result, stitch):
    segs, vias = [], []
    for n, (ss, vv, w) in result.items():
        n = n.split('@')[0]
        for s in ss: segs.append(dict(x1=s[0], y1=s[1], x2=s[2], y2=s[3], w=w, layer='F.Cu' if s[4] == 0 else 'B.Cu', net=n))
        for v in vv: vias.append(dict(x=v[0], y=v[1], d=router.VIA_D, drill=router.VIA_DRILL, net=n))
    for v in stitch: vias.append(dict(x=v[0], y=v[1], d=router.VIA_D, drill=router.VIA_DRILL, net='GND'))
    return segs, vias

def main():
    if '--check' in sys.argv:
        b = geom.Board(PCB); drc(b, b.segs, b.vias); return
    seed = 0
    for a in sys.argv:
        if a.startswith('--seed='): seed = int(a.split('=')[1])
    b = load_and_place()
    best = None
    for attempt in range(seed, seed + 12):
        print('routing attempt (seed %d)' % attempt)
        rt, result, fails = route_all(b, attempt)
        if not fails: best = (rt, result); break
    if best is None:
        print('ROUTING FAILED for', fails); sys.exit(2)
    rt, result = best
    stitch = stitch_vias(rt, b, result)
    segs, vias = to_board_items(result, stitch)
    comps, bad = pour_connectivity(b, segs, vias)
    # any GND pad that ended up on an isolated copper island gets an explicit track to the main pour
    for rnd in range(6):
        if len(comps) <= 1 and not bad: break
        main = max(comps.values(), key=len)
        orphans = [nm for g in comps.values() if g is not main for nm in g] + bad
        gnd_pads = {o.name: o for o in rt.objs if o.kind == 'pad' and o.net == 'GND'}
        for nm in orphans:
            o = gnd_pads[nm]
            tgt = min((gnd_pads[m] for m in main), key=lambda q: math.hypot(q.prim[1] - o.prim[1], q.prim[2] - o.prim[2]))
            r = rt.route_net('GND', [o, tgt], [0.4, 0.3, 0.25], (1.0, 1.0))
            print('  GND fix for %s -> %s: %s' % (nm, tgt.name, 'ok' if r else 'FAILED'))
            if r: result['GND@%s' % nm] = r
        segs, vias = to_board_items(result, stitch)
        comps, bad = pour_connectivity(b, segs, vias)
    errs, opens = drc(b, segs, vias)
    print('GND pour: %d connected group(s); %d pad(s) with no pour contact %s' % (len(comps), len(bad), bad))
    for k, v in comps.items(): print('   group of %d pads' % len(v), v[:6] if len(v) < 6 else '')
    root = b.root
    front_obs = do_silk(b, root)
    os.makedirs(BUILD, exist_ok=True)
    write_board(b, root, segs, vias, PCB, front_obs)
    print('wrote', PCB)
    pcbdraw.draw(b, os.path.join(BUILD, 'layout_preview.png'), tracks=segs, vias=vias, title='RobotEV rev C - routed (red F.Cu, blue B.Cu)', labels=False)
    print('tracks: %.0f mm, %d vias (%d routed + %d GND stitching)' % (sum(math.hypot(s['x2'] - s['x1'], s['y2'] - s['y1']) for s in segs), len(vias), len(vias) - len(stitch), len(stitch)))
    if errs or opens or bad: sys.exit(1)

if __name__ == '__main__':
    main()
