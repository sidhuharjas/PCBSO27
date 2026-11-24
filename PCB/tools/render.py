"""Render top/bottom copper + silkscreen (including footprint outlines) of RobotEV.kicad_pcb to PNG."""
import math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
import sx, geom, router, design as D, pcbdraw, placement as PL
D.BOARD_W, D.BOARD_H, D.CORNER_R = PL.BOARD_W, PL.BOARD_H, PL.CORNER_R


def render(path_pcb, out_dirs, scale=16):
    if isinstance(out_dirs, str):
        out_dirs = [out_dirs]
    for d in out_dirs:
        os.makedirs(d, exist_ok=True)
    b = geom.Board(path_pcb)
    W, H, R = D.BOARD_W, D.BOARD_H, D.CORNER_R
    res = 0.1
    nx, ny = int(W / res) + 1, int(H / res) + 1
    X, Y = np.meshgrid(np.arange(nx) * res, np.arange(ny) * res)
    rt = router.Router.__new__(router.Router); rt.nx, rt.ny, rt.X, rt.Y, rt.W, rt.H, rt.R = nx, ny, X, Y, W, H, R
    router.G = res
    edge = router.Router._edge_distance(rt)
    objs = []
    for fp in b.fps.values():
        for p in fp.pads: objs.append((p.prim(), p.net, {0, 1} if p.thru else ({0} if p.on_f else {1})))
    for s in b.segs: objs.append((('cap', s['x1'], s['y1'], s['x2'], s['y2'], s['w'] / 2), s['net'], {0 if s['layer'] == 'F.Cu' else 1}))
    for v in b.vias: objs.append((('cap', v['x'], v['y'], v['x'], v['y'], v['d'] / 2), v['net'], {0, 1}))
    texts = []
    for n in sx.find(b.root, 'gr_text'):
        if sx.first(n, 'layer')[1] != 'F.SilkS': continue
        a = sx.first(n, 'at')
        ang = float(a[3]) if len(a) > 3 else 0.0
        texts.append((n[1], float(a[1]), float(a[2]), float(sx.first(sx.first(sx.first(n, 'effects'), 'font'), 'size')[1]), ang))
    for fp in b.fps.values():
        for pr in sx.find(fp.node, 'property'):
            if pr[1] == 'Reference' and not sx.first(pr, 'hide'):
                a = sx.first(pr, 'at'); q = geom.rot(float(a[1]), float(a[2]), fp.a)
                texts.append((pr[2], fp.x + q[0], fp.y + q[1], 0.8, 0.0))
        for t in sx.find(fp.node, 'fp_text'):
            if sx.first(t, 'layer')[1] == 'F.SilkS':
                a = sx.first(t, 'at'); q = geom.rot(float(a[1]), float(a[2]), fp.a)
                sz = float(sx.first(sx.first(sx.first(t, 'effects'), 'font'), 'size')[1])
                texts.append((t[2], fp.x + q[0], fp.y + q[1], sz, 0.0))
    for side, name in ((0, 'top'), (1, 'bottom')):
        m = np.zeros((ny, nx), bool)
        for pr, net, L in objs:
            if side in L and net != 'GND': router.Router._stamp(rt, m, pr, 0.22)
        fill = ~m & (edge > 0.6)
        fig, ax = plt.subplots(figsize=(W * scale / 100, H * scale / 100), dpi=100)
        if side == 0:
            ax.set_xlim(-1, W + 1); ax.set_ylim(H + 1, -1)
        else:
            ax.set_xlim(W + 1, -1); ax.set_ylim(H + 1, -1)
        ax.set_aspect('equal')
        ax.add_patch(FancyBboxPatch((R, R), W - 2 * R, H - 2 * R, boxstyle='round,pad=%g,rounding_size=%g' % (R, R), fc='#17402a', ec='#d9c26a', lw=1.2))
        img = np.zeros((ny, nx, 4)); img[fill] = (0.78, 0.35, 0.30, 0.55) if side == 0 else (0.30, 0.45, 0.80, 0.55)
        ax.imshow(img, extent=(-res / 2, W + res / 2, H + res / 2, -res / 2), zorder=2, interpolation='nearest')
        for s in b.segs:
            if (0 if s['layer'] == 'F.Cu' else 1) != side: continue
            ax.plot([s['x1'], s['x2']], [s['y1'], s['y2']], color='#e05a4f' if side == 0 else '#4f78e0', lw=s['w'] * scale * 0.72, solid_capstyle='round', zorder=3)
        for p in b.pads():
            if side == 0 and not p.on_f or side == 1 and not p.on_b: continue
            pr = p.prim()
            if pr[0] == 'rect': ax.add_patch(Rectangle((pr[1], pr[2]), pr[3] - pr[1], pr[4] - pr[2], fc='#e8c34a', ec='none', zorder=4))
            elif abs(pr[1] - pr[3]) + abs(pr[2] - pr[4]) < 1e-9: ax.add_patch(Circle((pr[1], pr[2]), pr[5], fc='#e8c34a', ec='none', zorder=4))
            else: ax.plot([pr[1], pr[3]], [pr[2], pr[4]], color='#e8c34a', lw=pr[5] * 2 * scale * 0.72, solid_capstyle='round', zorder=4)
            if p.drill: ax.add_patch(Circle((p.x, p.y), p.drill[0] / 2, fc='#0a0a0a', ec='none', zorder=5))
        for v in b.vias:
            ax.add_patch(Circle((v['x'], v['y']), v['d'] / 2, fc='#c9c9c9', ec='none', zorder=5)); ax.add_patch(Circle((v['x'], v['y']), v['drill'] / 2, fc='#0a0a0a', ec='none', zorder=6))
        silk = 'B.SilkS' if side == 1 else 'F.SilkS'
        # Draw footprint silkscreen outlines on front side (component bodies, diode bands, XT30 outlines)
        if side == 0:
            for fp in b.fps.values():
                for g in sx.find(fp.node, 'fp_line'):
                    if sx.first(g, 'layer')[1] != 'F.SilkS': continue
                    s_, e_ = sx.first(g, 'start'), sx.first(g, 'end')
                    q1 = geom.rot(float(s_[1]), float(s_[2]), fp.a)
                    q2 = geom.rot(float(e_[1]), float(e_[2]), fp.a)
                    ax.plot([fp.x + q1[0], fp.x + q2[0]], [fp.y + q1[1], fp.y + q2[1]],
                            color='#eaeaea', lw=0.14 * scale * 0.72, solid_capstyle='round', zorder=6.5, alpha=0.88)
                for g in sx.find(fp.node, 'fp_rect'):
                    if sx.first(g, 'layer')[1] != 'F.SilkS': continue
                    s_, e_ = sx.first(g, 'start'), sx.first(g, 'end')
                    corners = [(float(s_[1]), float(s_[2])), (float(e_[1]), float(s_[2])),
                               (float(e_[1]), float(e_[2])), (float(s_[1]), float(e_[2])), (float(s_[1]), float(s_[2]))]
                    wc = [geom.rot(x, y, fp.a) for x, y in corners]
                    ax.plot([fp.x + c[0] for c in wc], [fp.y + c[1] for c in wc],
                            color='#eaeaea', lw=0.14 * scale * 0.72, solid_capstyle='round', zorder=6.5, alpha=0.88)
                for g in sx.find(fp.node, 'fp_circle'):
                    if sx.first(g, 'layer')[1] != 'F.SilkS': continue
                    c_, e_ = sx.first(g, 'center'), sx.first(g, 'end')
                    q = geom.rot(float(c_[1]), float(c_[2]), fp.a)
                    rad = math.hypot(float(e_[1]) - float(c_[1]), float(e_[2]) - float(c_[2]))
                    ax.add_patch(Circle((fp.x + q[0], fp.y + q[1]), rad, fc='none', ec='#eaeaea', lw=0.14 * scale * 0.72, zorder=6.5, alpha=0.88))
        for n in sx.find(b.root, 'gr_line'):
            if sx.first(n, 'layer')[1] != silk: continue
            p, q = sx.first(n, 'start'), sx.first(n, 'end')
            ax.plot([float(p[1]), float(q[1])], [float(p[2]), float(q[2])], color='#f2f2f2', lw=0.2 * scale * 0.72, solid_capstyle='round', zorder=7)
        for n in sx.find(b.root, 'gr_circle'):
            if sx.first(n, 'layer')[1] != silk: continue
            c = sx.first(n, 'center'); e = sx.first(n, 'end')
            ax.add_patch(Circle((float(c[1]), float(c[2])), float(e[1]) - float(c[1]), fc='#f2f2f2', ec='none', zorder=7))
        for n in (sx.find(b.root, 'gr_text') if side == 1 else []):
            if sx.first(n, 'layer')[1] != silk: continue
            a = sx.first(n, 'at'); sz = float(sx.first(sx.first(sx.first(n, 'effects'), 'font'), 'size')[1])
            ax.text(float(a[1]), float(a[2]), n[1], color='#f2f2f2', fontsize=sz * scale * 0.62, ha='center', va='center', zorder=8, family='monospace', weight='bold')
        if side == 0:
            for t, x, y, sz, ang in texts:
                ax.text(x, y, t, color='white', fontsize=sz * scale * 0.62, ha='center', va='center',
                        rotation=ang, zorder=8, family='monospace', weight='bold')
        ax.set_title('RobotEV Rev D (All-THT, 0 SMD) - %s (%s)' % (name, 'F.Cu + silk' if side == 0 else 'B.Cu, viewed from bottom'))
        ax.axis('off')
        for d in out_dirs:
            fig.savefig(os.path.join(d, 'board_%s.png' % name), bbox_inches='tight')
        plt.close(fig)


if __name__ == '__main__':
    root = os.path.dirname(HERE)
    render(os.path.join(root, 'hardware', 'RobotEV.kicad_pcb'),
           [os.path.join(root, 'build'), os.path.join(root, 'renders')])
