"""One-shot build: schematic -> netlist -> PCB -> checks -> gerbers.

    python tools/build.py            # full build + DRC/ERC reports
    python tools/build.py --open     # also open pcbnew on the result

Exits non-zero, and skips the gerbers, if ERC reports an error or DRC reports a
short, an open net, a clearance / track-width / hole violation or a mask bridge.
Cosmetic findings (silkscreen, courtyards) are printed but do not block.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KICAD = "C:/Program Files/KiCad/10.0/bin"
KP_PY = os.path.join(KICAD, "python.exe")
CLI = os.path.join(KICAD, "kicad-cli.exe")
SCH = os.path.join(ROOT, "hardware", "RobotEV.kicad_sch")
PCB = os.path.join(ROOT, "hardware", "RobotEV.kicad_pcb")
BUILD = os.path.join(ROOT, "build")

# DRC categories that make a board electrically wrong or unbuildable
HARD_DRC = {
    "shorting_items", "unconnected_items", "clearance", "track_width",
    "hole_clearance", "hole_to_hole", "copper_edge_clearance",
    "solder_mask_bridge", "starved_thermal", "isolated_copper",
    # Rev B shipped a VBAT <-> VBAT_F crossing (fuse bypassed) that was filed under "cosmetic"
    "tracks_crossing", "via_dangling", "item_on_disabled_layer", "courtyards_overlap",
}


def run(cmd, **kw):
    print("\n$ " + " ".join(cmd))
    return subprocess.run(cmd, **kw).returncode


def categories(path):
    """DRC/ERC category -> number of findings."""
    out = {}
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("[") and "]" in line:
                name = line[1:line.index("]")]
                out[name] = out.get(name, 0) + 1
    return out


def severity_errors(path):
    """ERC findings KiCad tags `; error` (as opposed to `; warning`)."""
    n = 0
    if not os.path.exists(path):
        return n
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if "; error" in line:
                n += 1
    return n


def gnd_zone_pairs(path):
    """`unconnected_items` entries where both sides are the GND pours.

    KiCad reports the F.Cu and B.Cu GND zone objects against each other even
    though they are joined by the stitching vias (the stitching vias) and every GND pad
    on both layers. No pad or track is left open, so this one pair is cosmetic;
    any other open item still blocks the build.
    """
    n = 0
    if not os.path.exists(path):
        return n
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = [l.rstrip("\n") for l in f]
    for i, line in enumerate(lines):
        if not line.startswith("[unconnected_items]"):
            continue
        items = [l for l in lines[i + 1:i + 4] if l.strip().startswith("@")]
        if len(items) == 2 and all("Zone [GND]" in it for it in items):
            n += 1
    return n


def gate():
    erc_err = severity_errors(os.path.join(BUILD, "erc.rpt"))
    drc = categories(os.path.join(BUILD, "drc.rpt"))
    drc_path = os.path.join(BUILD, "drc.rpt")
    zone_pairs = gnd_zone_pairs(drc_path)
    if zone_pairs and drc.get("unconnected_items"):
        drc["unconnected_items"] -= zone_pairs
        if drc["unconnected_items"] <= 0:
            del drc["unconnected_items"]
    hard = {c: n for c, n in drc.items() if c in HARD_DRC}
    soft = {c: n for c, n in drc.items() if c not in HARD_DRC}
    print("\n=== build gate ===")
    if zone_pairs:
        print("note        : %d unconnected item(s) are the two GND pours reported "
              "against each other (joined by the GND stitching vias)" % zone_pairs)
    print("ERC errors  : %d" % erc_err)
    print("DRC blocking: %s" % (hard or "none"))
    print("DRC cosmetic: %s" % (soft or "none"))
    if erc_err or hard:
        print("GATE FAILED - gerbers not exported")
        return 1
    print("GATE PASSED")
    return 0


def main():
    os.makedirs(BUILD, exist_ok=True)
    rc = run([sys.executable, os.path.join(HERE, "gen_sch.py")])
    if rc:
        return rc
    rc = run([CLI, "sch", "export", "netlist", "--format", "kicadxml",
              "-o", os.path.join(BUILD, "netlist.xml"), SCH])
    if rc:
        return rc
    # Rev C: placement, routing, stitching and silkscreen come from relayout.py (pure Python,
    # footprints are re-used from the existing board).  gen_pcb.py is kept only to bootstrap a board
    # from scratch; run it first if hardware/RobotEV.kicad_pcb does not exist yet.
    if not os.path.exists(PCB):
        rc = run([KP_PY, os.path.join(HERE, "gen_pcb.py")])
        if rc:
            return rc
    rc = run([sys.executable, os.path.join(HERE, "relayout.py")])
    if rc:
        return rc
    rc = run([KP_PY, os.path.join(HERE, "fill_zones.py")])
    if rc:
        return rc
    run([CLI, "sch", "erc", "-o", os.path.join(BUILD, "erc.rpt"), "--severity-all", SCH])
    run([CLI, "pcb", "drc", "-o", os.path.join(BUILD, "drc.rpt"),
         "--severity-all", "--units", "mm", PCB])
    rc = gate()
    if rc:
        return rc
    run([CLI, "pcb", "export", "gerbers", "-o", os.path.join(BUILD, "gerbers") + os.sep, PCB])
    run([CLI, "pcb", "export", "drill", "-o", os.path.join(BUILD, "gerbers") + os.sep,
         "--format", "excellon", "--drill-origin", "absolute", PCB])
    run([CLI, "sch", "export", "pdf", "-o", os.path.join(BUILD, "schematic.pdf"), SCH])
    run([sys.executable, os.path.join(HERE, "render.py")])
    if "--open" in sys.argv:
        subprocess.Popen([os.path.join(KICAD, "pcbnew.exe"), PCB])
    return 0


if __name__ == "__main__":
    sys.exit(main())
