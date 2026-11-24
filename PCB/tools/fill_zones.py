"""Refill the GND pours with KiCad's own zone filler and save the board.

    "C:/Program Files/KiCad/10.0/bin/python.exe" tools/fill_zones.py

relayout.py writes the pours unfilled (it cannot run KiCad's filler); this step fills them so the
DRC and the gerbers see real copper.  Same call gen_pcb.py used for Rev B.
"""
import os
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(os.path.dirname(HERE), "hardware", "RobotEV.kicad_pcb")

board = pcbnew.LoadBoard(PCB)
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(PCB, board)
print("filled %d zone(s)" % len(list(board.Zones())))
