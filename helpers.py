import tkinter as tk
import math

from constants import *

# most of these graphics/UI designed using AI except for resistor/voltage source

def rotate_point(cx, cy, dx, dy, angle):
    rad = math.radians(angle % 360)
    cos_a, sin_a = round(math.cos(rad)), round(math.sin(rad))
    rx = cos_a * dx - sin_a * dy
    ry = sin_a * dx + cos_a * dy
    return cx + rx, cy + ry


def rotate_nodes(name, cx, cy, angle):
    offsets = COMPONENTS[name]["nodes"]
    return [rotate_point(cx, cy, dx, dy, angle) for dx, dy in offsets]


def draw_selecton_rect_area(canvas, ws, r, lw, tag):
    rx = r[0]
    ry = r[1]
    canvas.create_polygon(
        *ws(rx, ry),
        *ws(-rx, ry),
        *ws(rx, -ry),
        *ws(-rx, -ry),
        outline="",
        fill="",
        tags=tag,
    )


def draw_resistor(canvas, ws, color, tag, lw, z, sx, sy, r):
    canvas.create_line(*ws(-40, 0), *ws(-15, 0), fill=color, width=lw, tags=tag)
    canvas.create_polygon(
        *ws(-15, -8),
        *ws(15, -8),
        *ws(15, 8),
        *ws(-15, 8),
        outline=color,
        fill=COMP_BG,
        width=lw,
        tags=tag,
    )
    canvas.create_line(*ws(15, 0), *ws(40, 0), fill=color, width=lw, tags=tag)
    draw_selecton_rect_area(canvas, ws, r, lw, tag)


def draw_capacitor(canvas, ws, color, tag, lw, z, sx, sy, r):
    canvas.create_line(*ws(-40, 0), *ws(-8, 0), fill=color, width=lw, tags=tag)
    canvas.create_line(*ws(-8, -14), *ws(-8, 14), fill=color, width=lw, tags=tag)
    canvas.create_line(*ws(8, -14), *ws(8, 14), fill=color, width=lw, tags=tag)
    canvas.create_line(*ws(8, 0), *ws(40, 0), fill=color, width=lw, tags=tag)
    draw_selecton_rect_area(canvas, ws, r, lw, tag)


def draw_inductor(canvas, ws, color, tag, lw, z, sx, sy, r):
    canvas.create_line(*ws(-40, 0), *ws(-20, 0), fill=color, width=lw, tags=tag)
    for hx in range(-20, 20, 10):
        pts = []
        for step in range(9):
            a = math.radians(step * 180 / 8)
            pts.extend(ws(hx + 5 - 5 * math.cos(a), -5 * math.sin(a)))
        canvas.create_line(*pts, fill=color, width=lw, smooth=True, tags=tag)
    canvas.create_line(*ws(20, 0), *ws(40, 0), fill=color, width=lw, tags=tag)
    draw_selecton_rect_area(canvas, ws, r, lw, tag)


def draw_voltage_src(canvas, ws, color, tag, lw, z, sx, sy, r):
    _r = max(4, 20 * z)
    canvas.create_oval(
        sx - _r,
        sy - _r,
        sx + _r,
        sy + _r,
        outline=color,
        fill=COMP_BG,
        width=lw,
        tags=tag,
    )
    canvas.create_line(*ws(0, -40), *ws(0, -20), fill=color, width=lw, tags=tag)
    canvas.create_line(*ws(0, 20), *ws(0, 40), fill=color, width=lw, tags=tag)
    fs = max(7, int(12 * z))
    px, py = ws(0, -10)
    canvas.create_text(
        px, py, text="+", fill=color, font=("Courier", fs, "bold"), tags=tag
    )
    mx, my = ws(0, 10)
    canvas.create_text(
        mx, my, text="-", fill=color, font=("Courier", fs, "bold"), tags=tag
    )
    draw_selecton_rect_area(canvas, ws, r, lw, tag)


def draw_ground(canvas, ws, color, tag, lw, z, sx, sy, r):
    canvas.create_line(*ws(0, -20), *ws(0, 0), fill=color, width=lw, tags=tag)
    for w, off in [(20, 0), (13, 6), (6, 12)]:
        canvas.create_line(*ws(-w, off), *ws(w, off), fill=color, width=lw, tags=tag)
    draw_selecton_rect_area(canvas, ws, r, lw, tag)


def draw_diode(canvas, ws, color, tag, lw, z, sx, sy, r):
    canvas.create_line(*ws(-40, 0), *ws(-12, 0), fill=color, width=lw, tags=tag)
    canvas.create_polygon(
        *ws(-12, -12),
        *ws(-12, 12),
        *ws(12, 0),
        outline=color,
        fill=COMP_BG,
        width=lw,
        tags=tag,
    )
    canvas.create_line(*ws(12, -12), *ws(12, 12), fill=color, width=lw, tags=tag)
    canvas.create_line(*ws(12, 0), *ws(40, 0), fill=color, width=lw, tags=tag)
    draw_selecton_rect_area(canvas, ws, r, lw, tag)


def draw_npn_bjt(canvas, ws, color, tag, lw, z, sx, sy, r):
    canvas.create_line(*ws(-20, 0), *ws(0, 0), fill=color, width=lw, tags=tag)
    canvas.create_line(
        *ws(0, -20), *ws(0, 20), fill=color, width=max(1, 3 * z), tags=tag
    )
    canvas.create_line(*ws(0, -10), *ws(20, -20), fill=color, width=lw, tags=tag)
    canvas.create_line(
        *ws(0, 10), *ws(20, 20), fill=color, width=lw, arrow=tk.LAST, tags=tag
    )
    draw_selecton_rect_area(canvas, ws, r, lw, tag)


def draw_opamp(canvas, ws, color, tag, lw, z, sx, sy, r):
    canvas.create_polygon(
        *ws(-20, -20),
        *ws(-20, 20),
        *ws(20, 0),
        outline=color,
        fill=COMP_BG,
        width=lw,
        tags=tag,
    )
    canvas.create_line(*ws(-40, -20), *ws(-20, -20), fill=color, width=lw, tags=tag)
    canvas.create_line(*ws(-40, 20), *ws(-20, 20), fill=color, width=lw, tags=tag)
    canvas.create_line(*ws(20, 0), *ws(40, 0), fill=color, width=lw, tags=tag)
    fs = max(6, int(9 * z))
    lx, ly = ws(-13, -11)
    canvas.create_text(lx, ly, text="-", fill=color, font=("Courier", fs), tags=tag)
    lx, ly = ws(-13, 11)
    canvas.create_text(lx, ly, text="+", fill=color, font=("Courier", fs), tags=tag)
    draw_selecton_rect_area(canvas, ws, r, lw, tag)


def draw_unknown(canvas, ws, color, tag, lw, z, sx, sy, r):
    r = max(4, 20 * z)
    canvas.create_rectangle(
        sx - r,
        sy - r * 0.6,
        sx + r,
        sy + r * 0.6,
        outline=color,
        fill=COMP_BG,
        width=lw,
        tags=tag,
    )
    draw_selecton_rect_area(canvas, ws, r, lw, tag)


DRAW_FN = {
    "Resistor": draw_resistor,
    "Capacitor": draw_capacitor,
    "Inductor": draw_inductor,
    "Voltage Src": draw_voltage_src,
    "Ground": draw_ground,
    "Diode": draw_diode,
    "NPN BJT": draw_npn_bjt,
    "Op-Amp": draw_opamp,
}

# dialog implemented using AI
class ValueDialog(tk.Toplevel):
    def __init__(self, parent, comp):
        super().__init__(parent)
        self.result = None
        name = comp["type"]
        params_meta = COMPONENTS[name]["params"]
        current_vals = comp.get("values", {})

        self.title(f"Edit {name}")
        self.configure(bg=BG_PANEL)
        self.resizable(False, False)
        self.grab_set()

        tk.Label(
            self,
            text=f"  {name} values",
            bg=BG_PANEL,
            fg=ACCENT,
            font=("Courier New", 11, "bold"),
            pady=10,
        ).pack(fill=tk.X)

        frame = tk.Frame(self, bg=BG_PANEL, padx=16, pady=4)
        frame.pack(fill=tk.X)

        self._entries = {}
        for label, default, unit in params_meta:
            row = tk.Frame(frame, bg=BG_PANEL)
            row.pack(fill=tk.X, pady=4)
            lbl_text = f"{label} ({unit})" if unit else label
            tk.Label(
                row,
                text=lbl_text,
                bg=BG_PANEL,
                fg=TEXT_SEC,
                font=("Courier New", 10),
                width=14,
                anchor=tk.W,
            ).pack(side=tk.LEFT)
            var = tk.StringVar(value=current_vals.get(label, default))
            entry = tk.Entry(
                row,
                textvariable=var,
                bg=COMP_BG,
                fg=TEXT_PRI,
                insertbackground=ACCENT,
                relief=tk.FLAT,
                font=("Courier New", 10),
                width=12,
            )
            entry.pack(side=tk.LEFT, padx=6)
            self._entries[label] = var

        btn_row = tk.Frame(self, bg=BG_PANEL, pady=10)
        btn_row.pack()
        tk.Button(
            btn_row,
            text="OK",
            command=self._ok,
            bg=ACCENT,
            fg=BG_DARK,
            font=("Courier New", 10, "bold"),
            relief=tk.FLAT,
            padx=16,
            pady=4,
        ).pack(side=tk.LEFT, padx=8)
        tk.Button(
            btn_row,
            text="Cancel",
            command=self.destroy,
            bg=COMP_BORDER,
            fg=TEXT_PRI,
            font=("Courier New", 10),
            relief=tk.FLAT,
            padx=16,
            pady=4,
        ).pack(side=tk.LEFT, padx=8)

        self.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width() // 2 - self.winfo_width() // 2
        py = (
            parent.winfo_rooty() + parent.winfo_height() // 2 - self.winfo_height() // 2
        )
        self.geometry(f"+{px}+{py}")
        self.wait_window()

    def _ok(self):
        self.result = {k: v.get().strip() for k, v in self._entries.items()}
        self.destroy()