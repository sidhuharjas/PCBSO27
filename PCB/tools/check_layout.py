"""Quick layout sanity report: courtyard overlaps and part positions.

    "C:/Program Files/KiCad/10.0/bin/python.exe" tools/check_layout.py
"""
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(os.path.dirname(HERE), "hardware", "RobotEV.kicad_pcb")

board = pcbnew.LoadBoard(PCB)
fps = list(board.GetFootprints())
print("%d footprints on a %.1f x %.1f mm board\n" %
      (len(fps), pcbnew.ToMM(board.GetBoardEdgesBoundingBox().GetWidth()),
       pcbnew.ToMM(board.GetBoardEdgesBoundingBox().GetHeight())))

rects = []
for fp in fps:
    bb = fp.GetBoundingBox(False, False)
    rects.append((fp.GetReference(), pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()),
                  pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())))

overlaps = 0
for i in range(len(rects)):
    for j in range(i + 1, len(rects)):
        a, b = rects[i], rects[j]
        if a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4]:
            print("OVERLAP %-4s %-4s  (%.1f,%.1f)-(%.1f,%.1f) vs (%.1f,%.1f)-(%.1f,%.1f)" %
                  (a[0], b[0], a[1], a[2], a[3], a[4], b[1], b[2], b[3], b[4]))
            overlaps += 1

print("\n%d gross overlaps" % overlaps)
print("tracks: %d, vias: %d, zones: %d" % (len(board.GetTracks()), 0, len(board.Zones())))
