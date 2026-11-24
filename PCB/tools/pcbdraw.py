"""Placement model: re-place footprints from an existing board, preview with matplotlib."""
import copy, math, sx, geom
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle

import placement as _PL
BOARD_W, BOARD_H, CR = _PL.BOARD_W, _PL.BOARD_H, _PL.CORNER_R

def local_bbox(fp):
    """bbox of pads (+ courtyard if any) in the footprint's local (unrotated) frame."""
    xs = []; ys = []
    a0 = fp.a
    for p in fp.pads:
        # local pad centre is rx,ry ; size depends on file angle relative to fp angle
        rel = (p.ra - a0) % 180
        w, h = (p.h, p.w) if abs(rel - 90) < 1e-6 else (p.w, p.h)
        xs += [p.rx - w / 2, p.rx + w / 2]; ys += [p.ry - h / 2, p.ry + h / 2]
    return min(xs), min(ys), max(xs), max(ys)

def courtyard(fp):
    xs = []; ys = []
    for g in sx.find(fp.node, 'fp_rect') + sx.find(fp.node, 'fp_line'):
        l = sx.first(g, 'layer')
        if l and l[1] == 'F.CrtYd':
            s, e = sx.first(g, 'start'), sx.first(g, 'end')
            xs += [float(s[1]), float(e[1])]; ys += [float(s[2]), float(e[2])]
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None

def courtyards(fp):
    """all F.CrtYd rectangles of a footprint (local frame): each fp_rect on its own, fp_lines merged"""
    rects = []; xs = []; ys = []
    for g in sx.find(fp.node, 'fp_rect'):
        l = sx.first(g, 'layer')
        if l and l[1] == 'F.CrtYd':
            s, e = sx.first(g, 'start'), sx.first(g, 'end')
            rects.append((min(float(s[1]), float(e[1])), min(float(s[2]), float(e[2])), max(float(s[1]), float(e[1])), max(float(s[2]), float(e[2]))))
    for g in sx.find(fp.node, 'fp_line'):
        l = sx.first(g, 'layer')
        if l and l[1] == 'F.CrtYd':
            s, e = sx.first(g, 'start'), sx.first(g, 'end')
            xs += [float(s[1]), float(e[1])]; ys += [float(s[2]), float(e[2])]
    for g in sx.find(fp.node, 'fp_circle'):
        l = sx.first(g, 'layer')
        if l and l[1] == 'F.CrtYd':
            c, e = sx.first(g, 'center'), sx.first(g, 'end')
            r = math.hypot(float(e[1]) - float(c[1]), float(e[2]) - float(c[2]))
            rects.append((float(c[1]) - r, float(c[2]) - r, float(c[1]) + r, float(c[2]) + r))
    if xs: rects.append((min(xs), min(ys), max(xs), max(ys)))
    return rects

def apply_rot(node, delta):
    """add delta to every absolute angle stored in a footprint (pads, text)."""
    if abs(delta) < 1e-9: return
    for p in sx.find(node, 'pad') + sx.find(node, 'property') + sx.find(node, 'fp_text'):
        at = sx.first(p, 'at')
        a = float(at[3]) if len(at) > 3 else 0.0
        a = (a + delta) % 360
        if len(at) > 3: at[3] = a if a != int(a) else int(a)
        else: at.append(int(a) if a == int(a) else a)

def set_pos(fp, x, y, a):
    """position footprint so its *pad bbox centre* sits at (x,y) with angle a."""
    da = a - fp.a
    apply_rot(fp.node, da)
    at = sx.first(fp.node, 'at')
    fp.a = a % 360
    bx0, by0, bx1, by1 = local_bbox_after(fp)
    cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
    ox, oy = geom.rot(cx, cy, fp.a)
    fp.x, fp.y = x - ox, y - oy
    at[1], at[2] = round(fp.x, 4), round(fp.y, 4)
    if len(at) > 3: at[3] = fp.a if fp.a != int(fp.a) else int(fp.a)
    elif fp.a: at.append(int(fp.a))
    for p in fp.pads:
        p.update(fp)

def local_bbox_after(fp):
    xs = []; ys = []
    for p in fp.pads:
        rel = (p.ra - fp.a) % 180
        w, h = (p.h, p.w) if abs(rel - 90) < 1e-6 else (p.w, p.h)
        xs += [p.rx - w / 2, p.rx + w / 2]; ys += [p.ry - h / 2, p.ry + h / 2]
    return min(xs), min(ys), max(xs), max(ys)

NETCOL = {}
def draw(board, path, tracks=None, vias=None, title='', scale=14, zones=True, labels=True, extra=None):
    fig, ax = plt.subplots(figsize=(BOARD_W * scale / 100, BOARD_H * scale / 100), dpi=100)
    ax.set_xlim(-1, BOARD_W + 1); ax.set_ylim(BOARD_H + 1, -1); ax.set_aspect('equal')
    ax.add_patch(FancyBboxPatch((CR, CR), BOARD_W - 2 * CR, BOARD_H - 2 * CR, boxstyle='round,pad=%g,rounding_size=%g' % (CR, CR), fc='#1d4b2b', ec='#d9c26a', lw=1.2))
    for fp in board.fps.values():
        for c in courtyards(fp):
            pts = [geom.rot(*q, fp.a) for q in ((c[0], c[1]), (c[2], c[1]), (c[2], c[3]), (c[0], c[3]))]
            xs = [fp.x + q[0] for q in pts]; ys = [fp.y + q[1] for q in pts]
            ax.add_patch(Rectangle((min(xs), min(ys)), max(xs) - min(xs), max(ys) - min(ys), fc='none', ec='#8fd', lw=0.5, ls=':'))
    if tracks:
        for s in tracks:
            col = '#c33' if s['layer'] == 'F.Cu' else '#36c'
            ax.plot([s['x1'], s['x2']], [s['y1'], s['y2']], color=col, lw=s['w'] * scale * 0.72, solid_capstyle='round', alpha=0.85, zorder=3)
    for p in board.pads():
        pr = p.prim()
        if pr[0] == 'rect':
            ax.add_patch(Rectangle((pr[1], pr[2]), pr[3] - pr[1], pr[4] - pr[2], fc='#e8c34a', ec='none', zorder=4))
        else:
            if abs(pr[1] - pr[3]) + abs(pr[2] - pr[4]) < 1e-9:
                ax.add_patch(Circle((pr[1], pr[2]), pr[5], fc='#e8c34a', ec='none', zorder=4))
            else:
                ax.plot([pr[1], pr[3]], [pr[2], pr[4]], color='#e8c34a', lw=pr[5] * 2 * scale * 0.72, solid_capstyle='round', zorder=4)
        if p.drill:
            ax.add_patch(Circle((p.x, p.y), p.drill[0] / 2, fc='#111', ec='none', zorder=5))
    if vias:
        for v in vias:
            ax.add_patch(Circle((v['x'], v['y']), v['d'] / 2, fc='#bbb', ec='#444', lw=0.3, zorder=6))
            ax.add_patch(Circle((v['x'], v['y']), v['drill'] / 2, fc='#111', ec='none', zorder=7))
    if labels:
        for r, fp in board.fps.items():
            bb = local_bbox_after(fp)
            cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
            ox, oy = geom.rot(cx, cy, fp.a)
            ax.text(fp.x + ox, fp.y + oy, r, color='white', fontsize=7, ha='center', va='center', zorder=9, weight='bold',
                    bbox=dict(fc='#0008', ec='none', pad=0.5))
    if extra: extra(ax)
    ax.set_title(title); ax.set_xticks(range(0, 86, 5)); ax.set_yticks(range(0, 66, 5)); ax.grid(alpha=0.15)
    fig.savefig(path, bbox_inches='tight'); plt.close(fig)
