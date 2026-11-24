"""2-layer grid router (pure Python + numpy/scipy).  No KiCad needed.

Copper model: every object is a primitive from geom.prim_dist ('cap' = segment+radius, 'rect').
Rules: clearance CLR between different nets, edge clearance EDGE, grid G.
"""
import heapq, math
import numpy as np
import geom

G = 0.1          # grid pitch, mm
CLR = 0.2        # copper clearance
MARGIN = 0.02    # extra margin so grid quantisation never eats the clearance
EDGE = 0.5       # copper to board edge
VIA_D, VIA_DRILL = 0.8, 0.4

class Obj:
    __slots__ = ('prim', 'net', 'layers', 'kind', 'name', 'drill')
    def __init__(s, prim, net, layers, kind, name=''):
        s.prim, s.net, s.layers, s.kind, s.name = prim, net, layers, kind, name; s.drill = None

class Router:
    def __init__(self, W, H, corner_r):
        self.W, self.H, self.R = W, H, corner_r
        self.nx, self.ny = int(round(W / G)) + 1, int(round(H / G)) + 1
        xs = np.arange(self.nx) * G; ys = np.arange(self.ny) * G
        self.X, self.Y = np.meshgrid(xs, ys)          # shape (ny, nx)
        self.objs = []
        self.edge_d = self._edge_distance()
        self.path_log = {}

    def _edge_distance(self):
        cx, cy = self.W / 2, self.H / 2
        qx = np.abs(self.X - cx) - (self.W / 2 - self.R)
        qy = np.abs(self.Y - cy) - (self.H / 2 - self.R)
        outside = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0))
        inside = np.minimum(np.maximum(qx, qy), 0)
        sd = outside + inside - self.R             # signed distance to outline (neg inside)
        return -sd                                 # distance to edge, positive inside

    # ---------------------------------------------------------------- objects
    def add_pad(self, p, name):
        layers = set()
        if p.on_f: layers.add(0)
        if p.on_b: layers.add(1)
        if p.kind == 'np_thru_hole' or not layers: layers = {0, 1}
        self.objs.append(Obj(p.prim(), p.net, layers, 'pad', name)); self.objs[-1].drill = max(p.drill) if p.drill else None
    def add_seg(self, x1, y1, x2, y2, w, layer, net):
        self.objs.append(Obj(('cap', x1, y1, x2, y2, w / 2), net, {layer}, 'trk'))
    def add_via(self, x, y, net, d=VIA_D):
        self.objs.append(Obj(('cap', x, y, x, y, d / 2), net, {0, 1}, 'via'))

    def _stamp(self, mask, prim, R):
        """mark cells whose centre is closer than R to prim"""
        if prim[0] == 'cap':
            x0, y0, x1, y1, r = prim[1:6]
            lo_x, hi_x = min(x0, x1) - r - R, max(x0, x1) + r + R
            lo_y, hi_y = min(y0, y1) - r - R, max(y0, y1) + r + R
        else:
            x0, y0, x1, y1 = prim[1:5]; r = 0
            lo_x, hi_x, lo_y, hi_y = x0 - R, x1 + R, y0 - R, y1 + R
        i0 = max(0, int(math.floor(lo_x / G))); i1 = min(self.nx - 1, int(math.ceil(hi_x / G)))
        j0 = max(0, int(math.floor(lo_y / G))); j1 = min(self.ny - 1, int(math.ceil(hi_y / G)))
        if i0 > i1 or j0 > j1: return
        X = self.X[j0:j1 + 1, i0:i1 + 1]; Y = self.Y[j0:j1 + 1, i0:i1 + 1]
        if prim[0] == 'cap':
            dx, dy = x1 - x0, y1 - y0; L = dx * dx + dy * dy
            if L == 0: d = np.hypot(X - x0, Y - y0)
            else:
                t = np.clip(((X - x0) * dx + (Y - y0) * dy) / L, 0, 1)
                d = np.hypot(X - x0 - t * dx, Y - y0 - t * dy)
            d = d - r
        else:
            ddx = np.maximum(np.maximum(x0 - X, X - x1), 0); ddy = np.maximum(np.maximum(y0 - Y, Y - y1), 0)
            d = np.hypot(ddx, ddy)
        mask[j0:j1 + 1, i0:i1 + 1] |= d < R

    def masks(self, net, w, margin_extra=0.0):
        """blocked[layer] for a track of width w of `net`; via_blocked; near-penalty mask"""
        R = CLR + MARGIN + w / 2
        blocked = [np.zeros((self.ny, self.nx), bool) for _ in range(2)]
        near = [np.zeros((self.ny, self.nx), bool) for _ in range(2)]
        vb = [np.zeros((self.ny, self.nx), bool) for _ in range(2)]
        Rv = CLR + MARGIN + VIA_D / 2
        padarea = np.zeros((self.ny, self.nx), bool)
        for o in self.objs:
            if o.kind == 'pad' and o.prim[0] == 'rect':
                self._stamp(padarea, o.prim, 0.0)
            same = (o.net == net and net is not None)
            for l in o.layers:
                if not same:
                    self._stamp(blocked[l], o.prim, R)
                    self._stamp(near[l], o.prim, R + 0.35)
                    self._stamp(vb[l], o.prim, Rv)
        for l in (0, 1):
            blocked[l] |= self.edge_d < (EDGE + w / 2 + MARGIN)
            vb[l] |= self.edge_d < (EDGE + VIA_D / 2 + MARGIN)
        holes = np.zeros((self.ny, self.nx), bool)
        for o in self.objs:
            if o.kind == 'pad' and getattr(o, 'drill', None):
                self._stamp(holes, ('cap', o.prim[1], o.prim[2], o.prim[1], o.prim[2], o.drill / 2), 0.25 + VIA_DRILL / 2 + MARGIN)
        via_ok = ~(vb[0] | vb[1] | padarea | holes)
        return blocked, near, via_ok

    # ------------------------------------------------------------------ route
    def pad_seeds(self, pobj, blocked):
        """grid cells inside the pad (per layer)"""
        seeds = []
        pr = pobj.prim
        if pr[0] == 'rect': x0, y0, x1, y1 = pr[1:5]
        else:
            r = pr[5]; x0, y0, x1, y1 = min(pr[1], pr[3]) - r, min(pr[2], pr[4]) - r, max(pr[1], pr[3]) + r, max(pr[2], pr[4]) + r
        for j in range(int(math.ceil(y0 / G - 1e-9)), int(math.floor(y1 / G + 1e-9)) + 1):
            for i in range(int(math.ceil(x0 / G - 1e-9)), int(math.floor(x1 / G + 1e-9)) + 1):
                if not (0 <= i < self.nx and 0 <= j < self.ny): continue
                if geom.prim_dist(pr, ('cap', i * G, j * G, i * G, j * G, 0)) > 0: continue
                for l in pobj.layers:
                    if not blocked[l][j, i]: seeds.append((l, j * self.nx + i))
        return seeds

    def astar(self, starts, goals, blocked, near, via_ok, lcost, via_cost=35, turn=5, weight=1.4, limit=900000):
        nx = self.nx
        bl = [b.ravel().tolist() for b in blocked]
        nr = [n.ravel().tolist() for n in near]
        vk = via_ok.ravel().tolist()
        goalset = set(goals)
        gx = [g[1] % nx for g in goals]; gy = [g[1] // nx for g in goals]
        gx0, gx1, gy0, gy1 = min(gx), max(gx), min(gy), max(gy)
        def h(idx):
            x = idx % nx; y = idx // nx
            dx = max(gx0 - x, 0, x - gx1); dy = max(gy0 - y, 0, y - gy1)
            return (dx + dy) * weight
        openq = []; best = {}; parent = {}
        for (l, idx) in starts:
            for d in range(5):
                k = (l, idx, 4)       # dir 4 = none
            best[(l, idx, 4)] = 0
            heapq.heappush(openq, (h(idx), 0, l, idx, 4))
        n = 0
        steps = (1, -1, nx, -nx)
        total = nx * self.ny
        while openq:
            f, g, l, idx, d = heapq.heappop(openq)
            if best.get((l, idx, d), 1e18) < g: continue
            if (l, idx) in goalset:
                path = [(l, idx)]; k = (l, idx, d)
                while k in parent:
                    k = parent[k]; path.append((k[0], k[1]))
                path.reverse(); return path
            n += 1
            if n > limit: return None
            x = idx % nx
            for di, s in enumerate(steps):
                j = idx + s
                if j < 0 or j >= total: continue
                if di < 2:
                    xx = x + s
                    if xx < 0 or xx >= nx: continue
                if bl[l][j]: continue
                c = lcost[l] + (0.35 * lcost[l] if nr[l][j] else 0)
                if d != 4 and d != di: c += turn
                ng = g + c
                k = (l, j, di)
                if ng < best.get(k, 1e18):
                    best[k] = ng; parent[k] = (l, idx, d)
                    heapq.heappush(openq, (ng + h(j), ng, l, j, di))
            # via
            if vk[idx] and not bl[1 - l][idx]:
                k = (1 - l, idx, 4); ng = g + via_cost
                if ng < best.get(k, 1e18):
                    best[k] = ng; parent[k] = (l, idx, d)
                    heapq.heappush(openq, (ng + h(idx), ng, 1 - l, idx, 4))
        return None

    def route_net(self, net, pads, widths, lcost):
        """pads: list of Obj (pad objects of this net). Returns (segments, vias) or None"""
        if len(pads) < 2: return [], []
        for w in widths:
            res = self._route_net_w(net, pads, w, lcost)
            if res: return res + (w,)
        return None

    def _route_net_w(self, net, pads, w, lcost):
        blocked, near, via_ok = self.masks(net, w)
        nx = self.nx
        # order: start from the pad closest to the centroid, then nearest-first
        cen = (sum(p.prim[1] for p in pads) / len(pads), sum(p.prim[2] for p in pads) / len(pads))
        pads = sorted(pads, key=lambda p: math.hypot(p.prim[1] - cen[0], p.prim[2] - cen[1]))
        first = self.pad_seeds(pads[0], blocked)
        if not first: return None
        tree = set(first)
        todo = pads[1:]
        segs, vias = [], []
        tree_pts = [(pads[0].prim[1], pads[0].prim[2])]
        while todo:
            todo.sort(key=lambda p: min(math.hypot(p.prim[1] - q[0], p.prim[2] - q[1]) for q in tree_pts))
            tp = todo.pop(0)
            seeds = self.pad_seeds(tp, blocked)
            if not seeds: return None
            path = self.astar(seeds, tree, blocked, near, via_ok, lcost)
            if path is None: return None
            s2, v2 = self._path_to_geom(path, w, net)
            segs += s2; vias += v2
            for (l, idx) in path: tree.add((l, idx))
            for v in v2:
                i, j = int(round(v[0] / G)), int(round(v[1] / G))
                tree.add((0, j * nx + i)); tree.add((1, j * nx + i))
            for (l, idx) in seeds: tree.add((l, idx))
            tree_pts.append((tp.prim[1], tp.prim[2]))
        # commit objects
        for s in segs: self.add_seg(s[0], s[1], s[2], s[3], w, s[4], net)
        for v in vias: self.add_via(v[0], v[1], net)
        return segs, vias

    def _path_to_geom(self, path, w, net):
        nx = self.nx
        pts = [(l, (idx % nx) * G, (idx // nx) * G) for (l, idx) in path]
        segs, vias = [], []
        i = 0
        # split at layer changes
        runs = []; cur = [pts[0]]
        for p in pts[1:]:
            if p[0] != cur[-1][0]:
                vias.append((cur[-1][1], cur[-1][2])); runs.append(cur); cur = [p]
            else: cur.append(p)
        runs.append(cur)
        for run in runs:
            # compress collinear points
            comp = [run[0]]
            for k in range(1, len(run) - 1):
                a, b, c = comp[-1], run[k], run[k + 1]
                if (b[1] - a[1]) * (c[2] - b[2]) == (b[2] - a[2]) * (c[1] - b[1]) and abs((b[1]-a[1])*(c[1]-b[1]) + (b[2]-a[2])*(c[2]-b[2])) > 0:
                    continue
                comp.append(b)
            if len(run) > 1: comp.append(run[-1])
            for a, b in zip(comp, comp[1:]):
                if abs(a[1] - b[1]) + abs(a[2] - b[2]) < 1e-9: continue
                segs.append((round(a[1], 4), round(a[2], 4), round(b[1], 4), round(b[2], 4), a[0]))
        return segs, vias
