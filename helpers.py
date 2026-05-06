from constants import *
import tkinter as tk

def draw_resistor(canvas, cx, cy, color, tag):
    w, h = 30, 12
    canvas.create_line(cx-30, cy, cx-w//2, cy, fill=color, width=2, tags=tag)
    canvas.create_rectangle(cx-w//2, cy-h//2, cx+w//2, cy+h//2,
                            outline=color, fill=COMP_BG, width=2, tags=tag)
    canvas.create_line(cx+w//2, cy, cx+30, cy, fill=color, width=2, tags=tag)
 
def draw_capacitor(canvas, cx, cy, color, tag):
    canvas.create_line(cx-25, cy, cx-6, cy, fill=color, width=2, tags=tag)
    canvas.create_line(cx-6, cy-14, cx-6, cy+14, fill=color, width=2, tags=tag)
    canvas.create_line(cx+6, cy-14, cx+6, cy+14, fill=color, width=2, tags=tag)
    canvas.create_line(cx+6, cy, cx+25, cy, fill=color, width=2, tags=tag)
 
def draw_inductor(canvas, cx, cy, color, tag):
    canvas.create_line(cx-30, cy, cx-22, cy, fill=color, width=2, tags=tag)
    for i, x in enumerate(range(-22, 18, 10)):
        canvas.create_arc(cx+x, cy-8, cx+x+10, cy+8,
                          start=0, extent=180, style="arc",
                          outline=color, width=2, tags=tag)
    canvas.create_line(cx+18, cy, cx+30, cy, fill=color, width=2, tags=tag)
 
def draw_voltage_src(canvas, cx, cy, color, tag):
    canvas.create_oval(cx-18, cy-18, cx+18, cy+18,
                       outline=color, fill=COMP_BG, width=2, tags=tag)
    canvas.create_line(cx, cy-30, cx, cy-18, fill=color, width=2, tags=tag)
    canvas.create_line(cx, cy+18, cx, cy+30, fill=color, width=2, tags=tag)
    canvas.create_text(cx-6, cy, text="+", fill=color, font=("Courier", 12, "bold"), tags=tag)
    canvas.create_text(cx+6, cy, text="−", fill=color, font=("Courier", 12, "bold"), tags=tag)
 
def draw_current_src(canvas, cx, cy, color, tag):
    canvas.create_oval(cx-18, cy-18, cx+18, cy+18,
                       outline=color, fill=COMP_BG, width=2, tags=tag)
    canvas.create_line(cx, cy-30, cx, cy-18, fill=color, width=2, tags=tag)
    canvas.create_line(cx, cy+18, cx, cy+30, fill=color, width=2, tags=tag)
    canvas.create_line(cx, cy-10, cx, cy+10, fill=color, width=2, arrow=tk.LAST, tags=tag)
 
def draw_ground(canvas, cx, cy, color, tag):
    canvas.create_line(cx, cy-20, cx, cy, fill=color, width=2, tags=tag)
    for i, (w, y_off) in enumerate([(20, 0),(13, 5),(6, 10)]):
        canvas.create_line(cx-w, cy+y_off, cx+w, cy+y_off, fill=color, width=2, tags=tag)
 
def draw_wire_node(canvas, cx, cy, color, tag):
    canvas.create_oval(cx-6, cy-6, cx+6, cy+6,
                       fill=color, outline=color, tags=tag)
 
def draw_diode(canvas, cx, cy, color, tag):
    canvas.create_line(cx-25, cy, cx-10, cy, fill=color, width=2, tags=tag)
    canvas.create_polygon(cx-10, cy-12, cx-10, cy+12, cx+10, cy,
                           outline=color, fill=COMP_BG, width=2, tags=tag)
    canvas.create_line(cx+10, cy-12, cx+10, cy+12, fill=color, width=2, tags=tag)
    canvas.create_line(cx+10, cy, cx+25, cy, fill=color, width=2, tags=tag)
 
def draw_npn(canvas, cx, cy, color, tag):
    canvas.create_line(cx-20, cy, cx, cy, fill=color, width=2, tags=tag)
    canvas.create_line(cx, cy-24, cx, cy+24, fill=color, width=3, tags=tag)
    canvas.create_line(cx, cy-12, cx+20, cy-20, fill=color, width=2, tags=tag)
    canvas.create_line(cx, cy+12, cx+20, cy+20, fill=color, width=2,
                       arrow=tk.LAST, tags=tag)
    canvas.create_line(cx+20, cy-20, cx+20, cy-20, fill=color, width=2, tags=tag)
 
def draw_opamp(canvas, cx, cy, color, tag):
    pts = [cx-30, cy-25, cx-30, cy+25, cx+30, cy]
    canvas.create_polygon(*pts, outline=color, fill=COMP_BG, width=2, tags=tag)
    canvas.create_line(cx-30, cy-15, cx-18, cy-15, fill=color, width=2, tags=tag)
    canvas.create_line(cx-30, cy+15, cx-18, cy+15, fill=color, width=2, tags=tag)
    canvas.create_text(cx-22, cy-15, text="−", fill=color, font=("Courier", 10), tags=tag)
    canvas.create_text(cx-22, cy+15, text="+", fill=color, font=("Courier", 10), tags=tag)
    canvas.create_line(cx+30, cy, cx+30, cy, fill=color, width=2, tags=tag)
