import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import math
import uuid

from helpers import *
from constants import *
from solver import *

DRAW_FN = {
    "Resistor": draw_resistor,
    "Capacitor": draw_capacitor,
    "Inductor": draw_inductor,
    "Voltage Src": draw_voltage_src,
    "Current Src": draw_current_src,
    "Ground": draw_ground,
    "Wire Node": draw_wire_node,
    "Diode": draw_diode,
    "NPN BJT": draw_npn,
    "Op-Amp": draw_opamp,
}

class CircuitForge(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Circuit Editor")
        self.configure(bg=BG_DARK)
        self.geometry("1280x800")
        self.minsize(900, 600)

        self.components = {}  # {id: {type, x, y, nodes:[]}}
        self.connections = []  # [{from_id, from_node, to_id, to_node, wire_id}]
        self.mode = tk.StringVar(value="insert")
        self.active_comp = tk.StringVar(value="Resistor")
        self.selected_id = None
        self.wire_start = None  # (comp_id, node_index, canvas_x, canvas_y)
        self.pending_wire = None  # canvas line id
        self.drag_data = {}
        self.sim_running = False
        self.filepath = None

        self.build_ui()
        self.draw_grid()


    def build_ui(self):
        # Top toolbar
        self.build_toolbar()
        # Main area - sidebar + canvas
        main = tk.Frame(self, bg=BG_DARK)
        main.pack(fill=tk.BOTH, expand=True)
        self.build_sidebar(main)
        self.build_canvas(main)
        # Bottom status bar
        self.build_statusbar()

    def build_toolbar(self):
        tb = tk.Frame(self, bg=BG_TOOLBAR, height=48)
        tb.pack(fill=tk.X, side=tk.TOP)
        tb.pack_propagate(False)

        # App title
        tk.Label(tb, text="CircuitForge", bg=BG_TOOLBAR, fg=ACCENT, font=("Courier New", 14, "bold"), padx=16).pack(side=tk.LEFT, pady=8)

        sep = tk.Frame(tb, bg=COMP_BORDER, width=1)
        sep.pack(side=tk.LEFT, fill=tk.Y, padx=4, pady=8)

        # Mode buttons
        mode_frame = tk.Frame(tb, bg=BG_TOOLBAR)
        mode_frame.pack(side=tk.LEFT, padx=8)

        self.btn_insert = self.tb_btn(mode_frame, "Insert", self.mode_insert, ACCENT)
        self.btn_insert.pack(side=tk.LEFT, padx=3)
        self.btn_delete = self.tb_btn(mode_frame, "Delete", self._mode_delete, DANGER)
        self.btn_delete.pack(side=tk.LEFT, padx=3)
        self.btn_wire = self.tb_btn(mode_frame, "Wire", self._mode_wire, ACCENT2)
        self.btn_wire.pack(side=tk.LEFT, padx=3)

        sep2 = tk.Frame(tb, bg=COMP_BORDER, width=1)
        sep2.pack(side=tk.LEFT, fill=tk.Y, padx=4, pady=8)

        # File ops
        file_frame = tk.Frame(tb, bg=BG_TOOLBAR)
        file_frame.pack(side=tk.LEFT, padx=8)
        self.tb_btn(file_frame, "Open", self.file_open, TEXT_PRI).pack(side=tk.LEFT, padx=3)
        self.tb_btn(file_frame, "Save", self.file_save, TEXT_PRI).pack(side=tk.LEFT, padx=3)
        self.tb_btn(file_frame, "Export", self.file_export, TEXT_PRI).pack(side=tk.LEFT, padx=3)

        sep3 = tk.Frame(tb, bg=COMP_BORDER, width=1)
        sep3.pack(side=tk.LEFT, fill=tk.Y, padx=4, pady=8)

        # Simulation
        self.btn_sim = self.tb_btn(tb, "Run Sim", self.toggle_simulation, "#00ff99")
        self.btn_sim.pack(side=tk.LEFT, padx=8)

        # Clear canvas (right side)
        self.tb_btn(tb, "Clear All", self.clear_all, DANGER).pack(side=tk.RIGHT, padx=12)

        self._update_mode_buttons()

    def tb_btn(self, parent, text, cmd, fg=TEXT_PRI):
        return tk.Button(parent, text=text, command=cmd, bg=BG_PANEL, fg=fg, activebackground=COMP_BORDER, activeforeground=fg, relief=tk.FLAT, font=("Courier New", 10, "bold"), padx=10, pady=4, cursor="hand2", bd=0)

    def build_sidebar(self, parent):
        sb = tk.Frame(parent, bg=BG_PANEL, width=190)
        sb.pack(side=tk.LEFT, fill=tk.Y)
        sb.pack_propagate(False)

        tk.Label(sb, text="COMPONENTS", bg=BG_PANEL, fg=TEXT_SEC, font=("Courier New", 9, "bold"), pady=10).pack()

        for name, meta in COMPONENTS.items():
            color = meta["color"]
            btn = tk.Button(sb, text=name, command=lambda n=name: self._select_component(n), bg=COMP_BG, fg=color, activebackground=COMP_BORDER, activeforeground=color, relief=tk.FLAT, font=("Courier New", 10), anchor=tk.W, padx=14, pady=6, bd=0, cursor="hand2", width=18)
            btn.pack(fill=tk.X, padx=8, pady=2)
            # highlight selected
            btn.bind("<Enter>", lambda e, b=btn, c=color: b.config(bg=COMP_BORDER))
            btn.bind("<Leave>", lambda e, b=btn, n=name: b.config(bg=COMP_BORDER if self.active_comp.get() == n else COMP_BG))
            setattr(self, f"_cmp_btn_{name.replace(' ','_')}", btn)

        # Info panel
        sep = tk.Frame(sb, bg=COMP_BORDER, height=1)
        sep.pack(fill=tk.X, padx=8, pady=10)

        tk.Label(sb, text="SELECTION INFO", bg=BG_PANEL, fg=TEXT_SEC, font=("Courier New", 9, "bold")).pack()
        self.info_text = tk.Text(sb, bg=COMP_BG, fg=ACCENT, font=("Courier New", 9), relief=tk.FLAT, height=10, padx=8, pady=6, state=tk.DISABLED, wrap=tk.WORD)
        self.info_text.pack(fill=tk.X, padx=8, pady=6)

        # State summary
        sep2 = tk.Frame(sb, bg=COMP_BORDER, height=1)
        sep2.pack(fill=tk.X, padx=8, pady=4)
        self.stats_label = tk.Label(sb, text="", bg=BG_PANEL, fg=TEXT_SEC, font=("Courier New", 8), justify=tk.LEFT, padx=12)
        self.stats_label.pack(fill=tk.X)
        self.update_stats()

    def build_canvas(self, parent):
        wrap = tk.Frame(parent, bg=BG_DARK)
        wrap.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(wrap, bg=BG_DARK, highlightthickness=0, cursor="crosshair")
        hbar = tk.Scrollbar(wrap, orient=tk.HORIZONTAL, command=self.canvas.xview)
        vbar = tk.Scrollbar(wrap, orient=tk.VERTICAL, command=self.canvas.yview)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set, scrollregion=(-2000, -2000, 2000, 2000))

        # Bindings
        self.canvas.bind("<Button-1>", self._canvas_click)
        self.canvas.bind("<B1-Motion>", self._canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._canvas_release)
        self.canvas.bind("<Motion>", self._canvas_motion)
        self.canvas.bind("<Button-3>", self._canvas_right_click)
        # Pan with middle mouse
        self.canvas.bind("<Button-2>", self._pan_start)
        self.canvas.bind("<B2-Motion>", self._pan_move)

    def build_statusbar(self):
        sb = tk.Frame(self, bg=BG_TOOLBAR, height=24)
        sb.pack(fill=tk.X, side=tk.BOTTOM)
        sb.pack_propagate(False)
        self.status_var = tk.StringVar(value="Ready — Insert mode")
        tk.Label(sb, textvariable=self.status_var, bg=BG_TOOLBAR, fg=TEXT_SEC, font=("Courier New", 9), anchor=tk.W, padx=12).pack(side=tk.LEFT)
        self.coord_var = tk.StringVar(value="x: 0  y: 0")
        tk.Label(sb, textvariable=self.coord_var, bg=BG_TOOLBAR, fg=TEXT_SEC, font=("Courier New", 9), padx=12).pack(side=tk.RIGHT)

    def draw_grid(self):
        self.canvas.delete("grid")
        for x in range(-2000, 2001, GRID):
            self.canvas.create_line(x, -2000, x, 2000, fill=GRID_COLOR, tags="grid")
        for y in range(-2000, 2001, GRID):
            self.canvas.create_line(-2000, y, 2000, y, fill=GRID_COLOR, tags="grid")
        self.canvas.tag_lower("grid")

    def mode_insert(self):
        self.mode.set("insert")
        self.wire_start = None
        if self.pending_wire:
            self.canvas.delete(self.pending_wire)
            self.pending_wire = None
        self._deselect()
        self._update_mode_buttons()
        self.status_var.set(f"Insert mode — placing: {self.active_comp.get()}")

    def _mode_delete(self):
        self.mode.set("delete")
        self._deselect()
        self._update_mode_buttons()
        self.status_var.set("Delete mode — click a component or wire to remove")

    def _mode_wire(self):
        self.mode.set("wire")
        self._deselect()
        self._update_mode_buttons()
        self.status_var.set("Wire mode — click a node to start drawing")

    def _select_component(self, name):
        self.active_comp.set(name)
        if self.mode.get() != "insert":
            self.mode_insert()
        self.status_var.set(f"Insert mode — placing: {name}")
        # Update sidebar button highlights
        for n in COMPONENTS:
            btn = getattr(self, f"_cmp_btn_{n.replace(' ','_')}", None)
            if btn:
                btn.config(bg=COMP_BORDER if n == name else COMP_BG)

    def _update_mode_buttons(self):
        m = self.mode.get()
        self.btn_insert.config(
            relief=tk.SUNKEN if m == "insert" else tk.FLAT,
            bg=COMP_BORDER if m == "insert" else BG_PANEL,
        )
        self.btn_delete.config(
            relief=tk.SUNKEN if m == "delete" else tk.FLAT,
            bg=COMP_BORDER if m == "delete" else BG_PANEL,
        )
        self.btn_wire.config(
            relief=tk.SUNKEN if m == "wire" else tk.FLAT,
            bg=COMP_BORDER if m == "wire" else BG_PANEL,
        )

    def _snap(self, v):
        return round(v / GRID) * GRID
    
    def _canvas_coords(self, event):
        return self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)

    def _canvas_click(self, event):
        cx, cy = self._canvas_coords(event)
        m = self.mode.get()

        if m == "insert":
            # Check not clicking existing comp
            hit = self._hit_component(cx, cy)
            if hit:
                self._select_comp(hit)
            else:
                self._place_component(self._snap(cx), self._snap(cy))

        elif m == "delete":
            # Check wire first
            wire_hit = self._hit_wire(cx, cy)
            if wire_hit is not None:
                self._delete_wire(wire_hit)
            else:
                hit = self._hit_component(cx, cy)
                if hit:
                    self._delete_component(hit)

        elif m == "wire":
            node = self._hit_node(cx, cy)
            if node:
                comp_id, node_idx, nx, ny = node
                if self.wire_start is None:
                    self.wire_start = (comp_id, node_idx, nx, ny)
                    self.status_var.set("Wire: click destination node to complete")
                else:
                    s = self.wire_start
                    if not (s[0] == comp_id and s[1] == node_idx):
                        self._add_connection(s[0], s[1], comp_id, node_idx)
                    self.wire_start = None
                    if self.pending_wire:
                        self.canvas.delete(self.pending_wire)
                        self.pending_wire = None
                    self.status_var.set("Wire mode — click a node to start")
            else:
                # cancel
                if self.wire_start and not node:
                    hit = self._hit_component(cx, cy)
                    if not hit:
                        self.wire_start = None
                        if self.pending_wire:
                            self.canvas.delete(self.pending_wire)
                            self.pending_wire = None

    def _canvas_drag(self, event):
        cx, cy = self._canvas_coords(event)
        if self.mode.get() == "insert" and self.drag_data.get("id"):
            cid = self.drag_data["id"]
            nx = self._snap(cx - self.drag_data.get("ox", 0))
            ny = self._snap(cy - self.drag_data.get("oy", 0))
            self._move_component(cid, nx, ny)

    def _canvas_release(self, event):
        self.drag_data = {}

    def _canvas_motion(self, event):
        cx, cy = self._canvas_coords(event)
        self.coord_var.set(f"x: {int(cx)}  y: {int(cy)}")
        # Update pending wire
        if self.mode.get() == "wire" and self.wire_start:
            if self.pending_wire:
                self.canvas.delete(self.pending_wire)
            sx, sy = self.wire_start[2], self.wire_start[3]
            self.pending_wire = self.canvas.create_line(sx, sy, cx, cy, fill=WIRE_PEND, width=2, dash=(6, 4), tags="pending_wire")
        # Highlight hovered node
        self.canvas.delete("node_hover")
        if self.mode.get() == "wire":
            node = self._hit_node(cx, cy)
            if node:
                _, _, nx, ny = node
                self.canvas.create_oval(nx - NODE_R - 3, ny - NODE_R - 3, nx + NODE_R + 3, ny + NODE_R + 3, outline=ACCENT, width=2, tags="node_hover")

    def _canvas_right_click(self, event):
        self.wire_start = None
        if self.pending_wire:
            self.canvas.delete(self.pending_wire)
            self.pending_wire = None
        self._deselect()
        self.status_var.set(f"{self.mode.get().capitalize()} mode")

    def _pan_start(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def _pan_move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def _place_component(self, x, y):
        name = self.active_comp.get()
        cid = str(uuid.uuid4())[:8]
        meta = COMPONENTS[name]
        nodes_abs = [(x + dx, y + dy) for dx, dy in meta["nodes"]]
        self.components[cid] = {"type": name, "x": x, "y": y, "nodes": nodes_abs}
        self._render_component(cid)
        self.update_stats()
        self.status_var.set(f"Placed {name} [{cid}] at ({x}, {y})")

    def _render_component(self, cid):
        comp = self.components[cid]
        tag = f"comp_{cid}"
        self.canvas.delete(tag)

        cx, cy = comp["x"], comp["y"]
        name = comp["type"]
        color = COMPONENTS[name]["color"]

        # Draw symbol
        if name in DRAW_FN:
            DRAW_FN[name](self.canvas, cx, cy, color, tag)
        else:
            self.canvas.create_rectangle(cx - 20, cy - 12, cx + 20, cy + 12, outline=color, fill=COMP_BG, tags=tag)

        # Label
        self.canvas.create_text(cx, cy - 28, text=f"{name}\n[{cid}]", fill=TEXT_SEC, font=("Courier New", 7), tags=tag, justify=tk.CENTER)

        # Node handles
        for i, (nx, ny) in enumerate(comp["nodes"]):
            self.canvas.create_oval(nx - NODE_R, ny - NODE_R, nx + NODE_R, ny + NODE_R, fill=NODE_COLOR, outline=ACCENT2, width=1, tags=(tag, f"node_{cid}_{i}"))

        # Click/drag binding
        #self.canvas.tag_bind(tag, "<Button-1>", lambda e, c=cid: self._comp_click(e, c))
        self.canvas.tag_bind(tag, "<B1-Motion>", lambda e, c=cid: self._comp_drag(e, c))

    def _comp_click(self, event, cid):
        cx, cy = self._canvas_coords(event)
        m = self.mode.get()
        if m == "insert":
            comp = self.components[cid]
            self.drag_data = {"id": cid, "ox": cx - comp["x"], "oy": cy - comp["y"]}
            self._select_comp(cid)
        elif m == "delete":
            self._delete_component(cid)
        elif m == "wire":
            node = self._hit_node(cx, cy)
            if node:
                self._canvas_click(event)

    def _comp_drag(self, event, cid):
        if self.mode.get() == "insert":
            cx, cy = self._canvas_coords(event)
            if not self.drag_data.get("id"):
                comp = self.components[cid]
                self.drag_data = {"id": cid, "ox": cx - comp["x"], "oy": cy - comp["y"]}
            nx = self._snap(cx - self.drag_data.get("ox", 0))
            ny = self._snap(cy - self.drag_data.get("oy", 0))
            self._move_component(cid, nx, ny)

    def _move_component(self, cid, x, y):
        comp = self.components[cid]
        name = comp["type"]
        offsets = COMPONENTS[name]["nodes"]
        comp["x"] = x
        comp["y"] = y
        comp["nodes"] = [(x + dx, y + dy) for dx, dy in offsets]
        self._render_component(cid)
        self._redraw_wires_for(cid)

    def _delete_component(self, cid):
        # Remove connections
        to_remove = [c for c in self.connections if c["from_id"] == cid or c["to_id"] == cid]
        for conn in to_remove:
            self.canvas.delete(conn["wire_id"])
            self.connections.remove(conn)
        # Remove canvas items
        self.canvas.delete(f"comp_{cid}")
        del self.components[cid]
        if self.selected_id == cid:
            self._deselect()
        self.update_stats()
        self.status_var.set(f"Deleted component [{cid}]")

    def _select_comp(self, cid):
        self._deselect()
        self.selected_id = cid
        tag = f"comp_{cid}"
        # Draw selection outline
        comp = self.components[cid]
        self.canvas.create_rectangle(comp["x"] - 38, comp["y"] - 38, comp["x"] + 38, comp["y"] + 38, outline=SEL_COLOR, dash=(4, 3), width=2, tags="selection_rect")
        self._update_info(cid)

    def _deselect(self):
        self.canvas.delete("selection_rect")
        self.selected_id = None
        self._update_info(None)

    def _add_connection(self, from_id, from_node, to_id, to_node):
        fn = self.components[from_id]["nodes"][from_node]
        tn = self.components[to_id]["nodes"][to_node]
        wire_id = self.canvas.create_line(
            fn[0], fn[1], tn[0], tn[1], fill=WIRE_COLOR, width=2.5, tags="wire"
        )
        self.canvas.tag_lower("wire")
        self.canvas.tag_lower("grid")
        conn = {"from_id": from_id, "from_node": from_node, "to_id": to_id, "to_node": to_node, "wire_id": wire_id}
        self.connections.append(conn)
        self.update_stats()
        self.status_var.set(f"Connected [{from_id}] node {from_node} → [{to_id}] node {to_node}")

    def _redraw_wires_for(self, cid):
        for conn in self.connections:
            if conn["from_id"] == cid or conn["to_id"] == cid:
                fn = self.components[conn["from_id"]]["nodes"][conn["from_node"]]
                tn = self.components[conn["to_id"]]["nodes"][conn["to_node"]]
                self.canvas.coords(conn["wire_id"], fn[0], fn[1], tn[0], tn[1])

    def _delete_wire(self, idx):
        conn = self.connections[idx]
        self.canvas.delete(conn["wire_id"])
        self.connections.pop(idx)
        self.update_stats()
        self.status_var.set("Wire deleted")

    def _hit_component(self, cx, cy, radius=36):
        for cid, comp in self.components.items():
            if abs(cx - comp["x"]) < radius and abs(cy - comp["y"]) < radius:
                return cid
        return None

    def _hit_node(self, cx, cy, radius=10):
        for cid, comp in self.components.items():
            for i, (nx, ny) in enumerate(comp["nodes"]):
                if math.hypot(cx - nx, cy - ny) < radius:
                    return (cid, i, nx, ny)
        return None

    def _hit_wire(self, cx, cy, tol=6):
        for i, conn in enumerate(self.connections):
            fn = self.components[conn["from_id"]]["nodes"][conn["from_node"]]
            tn = self.components[conn["to_id"]]["nodes"][conn["to_node"]]
            # point to line distance
            dx, dy = tn[0] - fn[0], tn[1] - fn[1]
            if dx == 0 and dy == 0:
                continue
            t = max(0, min(1, ((cx - fn[0]) * dx + (cy - fn[1]) * dy) / (dx * dx + dy * dy)))
            px, py = fn[0] + t * dx, fn[1] + t * dy
            if math.hypot(cx - px, cy - py) < tol:
                return i
        return None

    def _update_info(self, cid):
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        if cid and cid in self.components:
            comp = self.components[cid]
            lines = [f"ID: {cid}", f"Type: {comp['type']}", f"x: {comp['x']}", f"y: {comp['y']}", f"Nodes:"]
            for i, (nx, ny) in enumerate(comp["nodes"]):
                lines.append(f"  [{i}] ({nx}, {ny})")
            # connections
            conns = [c for c in self.connections if c["from_id"] == cid or c["to_id"] == cid]
            if conns:
                lines.append(f"Wires: {len(conns)}")
            self.info_text.insert(tk.END, "\n".join(lines))
        self.info_text.config(state=tk.DISABLED)

    def update_stats(self):
        self.stats_label.config(text=f"Components : {len(self.components)}\nConnections: {len(self.connections)}")

    def file_open(self):
        path = filedialog.askopenfilename(title="Open circuit", filetypes=[("JSON", "*.json"), ("All", "*.*")])
        if not path:
            return
        try:
            with open(path) as f:
                data = json.load(f)
            self._load_state(data)
            self.filepath = path
            self.status_var.set(f"Opened: {path}")
        except Exception as e:
            messagebox.showerror("Open failed", str(e))

    def file_save(self):
        if not self.filepath:
            self.filepath = filedialog.asksaveasfilename(title="Save circuit", defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not self.filepath:
            return
        try:
            with open(self.filepath, "w") as f:
                json.dump(self._get_state(), f, indent=2)
            self.status_var.set(f"Saved: {self.filepath}")
        except Exception as e:
            messagebox.showerror("Save failed", str(e))

    def file_export(self):
        path = filedialog.asksaveasfilename(title="Export netlist", defaultextension=".json", filetypes=[("JSON", "*.json"), ("Text", "*.txt")])
        if not path:
            return
        try:
            with open(path, "w") as f:
                json.dump(self._get_state(), f, indent=2)
            self.status_var.set(f"Exported: {path}")
        except Exception as e:
            messagebox.showerror("Export failed", str(e))

    def _get_state(self):
        comps = {}
        for cid, comp in self.components.items():
            comps[cid] = {"type": comp["type"], "x": comp["x"], "y": comp["y"], "nodes": comp["nodes"]}
        conns = []
        for c in self.connections:
            conns.append({"from_id": c["from_id"], "from_node": c["from_node"], "to_id": c["to_id"], "to_node": c["to_node"]})
        return {"components": comps, "connections": conns}

    def _load_state(self, data):
        self.clear_all(confirm=False)
        for cid, comp in data.get("components", {}).items():
            self.components[cid] = {"type": comp["type"], "x": comp["x"], "y": comp["y"], "nodes": [tuple(n) for n in comp["nodes"]]}
            self._render_component(cid)
        for conn in data.get("connections", []):
            self._add_connection(conn["from_id"], conn["from_node"], conn["to_id"], conn["to_node"])
        self.update_stats()

    def toggle_simulation(self):
        self.sim_running = not self.sim_running
        if self.sim_running:
            self.btn_sim.config(text="Stop Sim", fg=DANGER)
            self.status_var.set("Simulation running…")
            self._run_simulation()
        else:
            self.btn_sim.config(text="Run Sim", fg="#00ff99")
            self.status_var.set("Simulation stopped")

    def _run_simulation(self):
        
        if not self.sim_running:
            return
        state = self._get_state()
        
        self.status_var.set(f"Sim tick — {len(state['components'])} nodes, {len(state['connections'])} branches")
        self.after(500, self._run_simulation)

    def clear_all(self, confirm=True):
        if confirm and not messagebox.askyesno(
            "Clear", "Remove all components and wires?"
        ):
            return
        self.canvas.delete("all")
        self.components.clear()
        self.connections.clear()
        self.selected_id = None
        self.wire_start = None
        self.pending_wire = None
        self.drag_data = {}
        self.draw_grid()
        self.update_stats()
        self._update_info(None)
        self.status_var.set("Canvas cleared")