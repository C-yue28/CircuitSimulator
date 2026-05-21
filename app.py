from signal import valid_signals
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ctypes import windll
import json
import math
import uuid

from helpers import *
from constants import *
from solver import *
from solver import _SUFFIXES

# better quality
windll.shcore.SetProcessDpiAwareness(1)

class CircuitForge(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Circuit Forge")
        self.configure(bg=BG_DARK)
        self.geometry("1280x800")
        self.minsize(900, 600)

        self.components = {}  # {id: {type, x, y, nodes:[]}}
        # structural choice of storing connections taken from AI suggestions
        self.connections = []  # [{from_id, from_node, to_id, to_node, wire_id}]
        self.mode = tk.StringVar(value="insert")
        self.active_comp = tk.StringVar(value="Resistor")
        self.selected_id = None
        self.wire_start = None  # (comp_id, node_index, canvas_x, canvas_y)
        self.pending_wire = None  # canvas line id
        self.drag_data = {}
        self.sim_running = False
        self.filepath = None
        self.place_angle = 0
        self.zoom = 1
        self.pan_x = 0
        self.pan_y = 0
        self.pan_anchor = None

        self.build_ui()
        self.draw_grid()

        self.bind("<r>", lambda e: self.rotate_selected(90))
        self.bind("<e>", lambda e: self.rotate_selected(-90))

        self.canvas.bind("<MouseWheel>", self.on_zoom)
        self.bind("<Control-0>", lambda e: self.reset_zoom())
        self.full_redraw()

    # fixes for zooming/panning implemented with AI assistance
    def w2s(self, wx, wy):
        return wx * self.zoom + self.pan_x, wy * self.zoom + self.pan_y

    def s2w(self, sx, sy):
        return (sx - self.pan_x) / self.zoom, (sy - self.pan_y) / self.zoom

    def snap(self, v):
        return round(v / GRID) * GRID

    def event_world(self, event):
        return self.s2w(event.x, event.y)

    def full_redraw(self):
        self.canvas.delete("all")
        self.draw_grid()
        for conn in self.connections:
            self.draw_wire(conn)
        for cid in self.components:
            self.render_component(cid)
        if self.selected_id and self.selected_id in self.components:
            self.draw_selection_rect(self.selected_id)
        if self.sim_running:
            self.display_results()

    def build_ui(self):
        # Top toolbar
        self.build_toolbar()
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

        tk.Label(
            tb,
            text="Circuit Forge",
            bg=BG_TOOLBAR,
            fg=ACCENT,
            font=("Courier New", 14, "bold"),
            padx=16,
        ).pack(side=tk.LEFT, pady=8)
        self.sep(tb)

        mf = tk.Frame(tb, bg=BG_TOOLBAR)
        mf.pack(side=tk.LEFT, padx=8)
        self.btn_select = self.tbtn(mf, "Select", self.mode_select, ACCENT)
        self.btn_select.pack(side=tk.LEFT, padx=3)
        self.btn_insert = self.tbtn(mf, "Insert", self.mode_insert, ACCENT)
        self.btn_insert.pack(side=tk.LEFT, padx=3)
        self.btn_delete = self.tbtn(mf, "Delete", self.mode_delete, DANGER)
        self.btn_delete.pack(side=tk.LEFT, padx=3)
        self.btn_wire = self.tbtn(mf, "Wire", self.mode_wire, ACCENT2)
        self.btn_wire.pack(side=tk.LEFT, padx=3)
        self.sep(tb)

        ff = tk.Frame(tb, bg=BG_TOOLBAR)
        ff.pack(side=tk.LEFT, padx=8)
        self.tbtn(ff, "Open", self.file_open, TEXT_PRI).pack(side=tk.LEFT, padx=3)
        self.tbtn(ff, "Save", self.file_save, TEXT_PRI).pack(side=tk.LEFT, padx=3)
        self.tbtn(ff, "Export", self.file_export, TEXT_PRI).pack(side=tk.LEFT, padx=3)
        self.sep(tb)

        self.btn_sim = self.tbtn(tb, "Run Sim", self.toggle_simulation, "#00ff99")
        self.btn_sim.pack(side=tk.LEFT, padx=8)
        self.tbtn(tb, "Clear All", self.clear_all, DANGER).pack(side=tk.RIGHT, padx=12)
        self.update_mode_buttons()

    def sep(self, parent):
        tk.Frame(parent, bg=COMP_BORDER, width=1).pack(
            side=tk.LEFT, fill=tk.Y, padx=4, pady=8
        )

    def tbtn(self, parent, text, cmd, fg=TEXT_PRI):
        return tk.Button(
            parent,
            text=text,
            command=cmd,
            bg=BG_PANEL,
            fg=fg,
            activebackground=COMP_BORDER,
            activeforeground=fg,
            relief=tk.FLAT,
            font=("Courier New", 10, "bold"),
            padx=10,
            pady=4,
            cursor="hand2",
            bd=0,
        )

    def build_sidebar(self, parent):
        sb = tk.Frame(parent, bg=BG_PANEL, width=200)
        sb.pack(side=tk.LEFT, fill=tk.Y)
        sb.pack_propagate(False)

        tk.Label(
            sb,
            text="COMPONENTS",
            bg=BG_PANEL,
            fg=TEXT_SEC,
            font=("Courier New", 9, "bold"),
            pady=10,
        ).pack()

        for name, meta in COMPONENTS.items():
            c = meta["color"]
            btn = tk.Button(
                sb,
                text=name,
                command=lambda n=name: self.select_component(n),
                bg=COMP_BG,
                fg=c,
                activebackground=COMP_BORDER,
                activeforeground=c,
                relief=tk.FLAT,
                font=("Courier New", 10),
                anchor=tk.W,
                padx=14,
                pady=6,
                bd=0,
                cursor="hand2",
                width=18,
            )
            btn.pack(fill=tk.X, padx=8, pady=2)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=COMP_BORDER))
            btn.bind(
                "<Leave>",
                lambda e, b=btn, n=name: b.config(
                    bg=COMP_BORDER if self.active_comp.get() == n else COMP_BG
                ),
            )
            setattr(self, f"_cmpbtn_{name.replace(' ','_')}", btn)

        tk.Frame(sb, bg=COMP_BORDER, height=1).pack(fill=tk.X, padx=8, pady=10)
        tk.Label(
            sb,
            text="SELECTION INFO",
            bg=BG_PANEL,
            fg=TEXT_SEC,
            font=("Courier New", 9, "bold"),
        ).pack()
        self.info_text = tk.Text(
            sb,
            bg=COMP_BG,
            fg=ACCENT,
            font=("Courier New", 9),
            relief=tk.FLAT,
            height=9,
            padx=8,
            pady=6,
            state=tk.DISABLED,
            wrap=tk.WORD,
        )
        self.info_text.pack(fill=tk.X, padx=8, pady=4)

        self.btn_edit_val = tk.Button(
            sb,
            text="Edit Values",
            command=self.open_value_editor,
            bg=COMP_BG,
            fg=WARNING,
            activebackground=COMP_BORDER,
            activeforeground=WARNING,
            relief=tk.FLAT,
            font=("Courier New", 9, "bold"),
            padx=10,
            pady=4,
            bd=0,
            cursor="hand2",
            state=tk.DISABLED,
        )
        self.btn_edit_val.pack(fill=tk.X, padx=8, pady=2)

        tk.Frame(sb, bg=COMP_BORDER, height=1).pack(fill=tk.X, padx=8, pady=6)
        self.stats_label = tk.Label(
            sb,
            text="",
            bg=BG_PANEL,
            fg=TEXT_SEC,
            font=("Courier New", 8),
            justify=tk.LEFT,
            padx=12,
        )
        self.stats_label.pack(fill=tk.X)
        self.update_stats()

    def build_canvas(self, parent):
        wrap = tk.Frame(parent, bg=BG_DARK)
        wrap.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(
            wrap, bg=BG_DARK, highlightthickness=0, cursor="crosshair"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", lambda e: self.full_redraw())
        self.canvas.bind("<Button-1>", self.canvas_click)
        self.canvas.bind("<B1-Motion>", self.canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.canvas_release)
        self.canvas.bind("<Motion>", self.canvas_motion)
        self.canvas.bind("<Button-3>", self.canvas_right_click)
        self.canvas.bind("<Button-2>", self.pan_start)
        self.canvas.bind("<B2-Motion>", self.pan_move)
        self.canvas.bind("<Double-Button-1>", self.canvas_double_click)

    def build_statusbar(self):
        sb = tk.Frame(self, bg=BG_TOOLBAR, height=24)
        sb.pack(fill=tk.X, side=tk.BOTTOM)
        sb.pack_propagate(False)
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(
            sb,
            textvariable=self.status_var,
            bg=BG_TOOLBAR,
            fg=TEXT_SEC,
            font=("Courier New", 9),
            anchor=tk.W,
            padx=12,
        ).pack(side=tk.LEFT)
        self.coord_var = tk.StringVar(value="x:0 y:0  zoom:100%")
        tk.Label(
            sb,
            textvariable=self.coord_var,
            bg=BG_TOOLBAR,
            fg=TEXT_SEC,
            font=("Courier New", 9),
            padx=12,
        ).pack(side=tk.RIGHT)

    def draw_grid(self):
        W = self.canvas.winfo_width() or 1280
        H = self.canvas.winfo_height() or 760
        wx0, wy0 = self.s2w(0, 0)
        wx1, wy1 = self.s2w(W, H)
        gx0 = int(wx0 // GRID) * GRID
        gy0 = int(wy0 // GRID) * GRID
        for wx in range(gx0, int(wx1) + GRID, GRID):
            sx, _ = self.w2s(wx, 0)
            self.canvas.create_line(sx, 0, sx, H, fill=GRID_COLOR, tags="grid")
        for wy in range(gy0, int(wy1) + GRID, GRID):
            _, sy = self.w2s(0, wy)
            self.canvas.create_line(0, sy, W, sy, fill=GRID_COLOR, tags="grid")
        self.canvas.tag_lower("grid")

    def mode_select(self):
        self.mode.set("select")
        self.wire_start = None
        if self.pending_wire:
            self.canvas.delete(self.pending_wire)
            self.pending_wire = None
        self.deselect()
        self.update_mode_buttons()
        self.status_var.set(f"Select mode - click on a component to select")

    def mode_insert(self):
        self.mode.set("insert")
        self.wire_start = None
        if self.pending_wire:
            self.canvas.delete(self.pending_wire)
            self.pending_wire = None
        self.deselect()
        self.update_mode_buttons()
        self.status_var.set(f"Insert mode — placing: {self.active_comp.get()}")

    def mode_delete(self):
        self.mode.set("delete")
        self.deselect()
        self.update_mode_buttons()
        self.status_var.set("Delete mode — click a component or wire to remove")

    def mode_wire(self):
        self.mode.set("wire")
        self.deselect()
        self.update_mode_buttons()
        self.status_var.set("Wire mode — click a node to start drawing")

    def select_component(self, name):
        self.active_comp.set(name)
        if self.mode.get() != "insert":
            self.mode_insert()
        # Update sidebar button
        for n in COMPONENTS:
            btn = getattr(self, f"_cmp_btn_{n.replace(' ','_')}", None)
            if btn:
                btn.config(bg=COMP_BORDER if n == name else COMP_BG)

    def update_mode_buttons(self):
        m = self.mode.get()
        self.btn_select.config(
            relief=tk.SUNKEN if m == "select" else tk.FLAT,
            bg=COMP_BORDER if m == "select" else BG_PANEL,
        )
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

    def canvas_click(self, event):
        wx, wy = self.event_world(event)
        m = self.mode.get()

        if m == "insert":
            hit = self.hit_component(wx, wy)
            if hit:
                self.select_comp(hit)
            else:
                self.place_component(self.snap(wx), self.snap(wy))

        elif m == "delete":
            wi = self.hit_wire(wx, wy)
            if wi is not None:
                self.delete_wire(wi)
            else:
                hit = self.hit_component(wx, wy)
                if hit:
                    self.delete_component(hit)

        elif m == "wire":
            node = self.hit_node(wx, wy)
            if node:
                cid, nidx, nx, ny = node
                if self.wire_start is None:
                    self.wire_start = (cid, nidx, nx, ny)
                    self.status_var.set("Wire — click node / canvas / wire to route")
                else:
                    s = self.wire_start
                    if not (s[0] == cid and s[1] == nidx):
                        self.add_connection(s[0], s[1], cid, nidx)
                    self.cancel_wire()
                    self.status_var.set("Wire — click a node to start")
            elif self.wire_start is not None:
                sx, sy = self.snap(wx), self.snap(wy)
                wi = self.hit_wire(wx, wy)
                new_cid, new_nidx = (
                    self.split_wire(wi, sx, sy)
                    if wi is not None
                    else self.place_wire_node(sx, sy)
                )
                s = self.wire_start
                self.add_connection(s[0], s[1], new_cid, new_nidx)
                self.wire_start = None
                if wi is None:
                    nx, ny = self.components[new_cid]["nodes"][new_nidx]
                    self.wire_start = (new_cid, new_nidx, nx, ny)
                self.cancel_pending_wire()
                self.status_var.set("Wire routed — continue or right click to stop")

        elif m == "select":
            hit = self.hit_component(wx, wy)
            if hit:
                self.select_comp(hit)

    def canvas_double_click(self, event):
        if self.mode.get() != "insert" and self.mode.get() != "select":
            return
        wx, wy = self.event_world(event)
        hit = self.hit_component(wx, wy)
        if hit:
            self.open_value_editor(hit)

    def canvas_drag(self, event):
        wx, wy = self.event_world(event)
        if (
            self.mode.get() == "insert" or self.mode.get() == "select"
        ) and self.drag_data.get("id"):
            cid = self.drag_data["id"]
            nx = self.snap(wx - self.drag_data["ox"])
            ny = self.snap(wy - self.drag_data["oy"])
            self.move_component(cid, nx, ny)
            self.draw_selection_rect(cid)

    def canvas_release(self, event):
        self.drag_data = {}

    def canvas_motion(self, event):
        wx, wy = self.event_world(event)
        self.update_coord_bar(event.x, event.y)

        if self.mode.get() == "wire" and self.wire_start:
            if self.pending_wire:
                self.canvas.delete(self.pending_wire)
            sx0, sy0 = self.w2s(self.wire_start[2], self.wire_start[3])
            self.pending_wire = self.canvas.create_line(
                sx0,
                sy0,
                event.x,
                event.y,
                fill=WIRE_PEND,
                width=2,
                dash=(6, 4),
                tags="pending_wire",
            )

        self.canvas.delete("node_hover")
        if self.mode.get() == "wire":
            node = self.hit_node(wx, wy)
            if node:
                _, _, nx, ny = node
                sx, sy = self.w2s(nx, ny)
                r = max(4, (NODE_R + 3) * self.zoom)
                self.canvas.create_oval(
                    sx - r,
                    sy - r,
                    sx + r,
                    sy + r,
                    outline=ACCENT,
                    width=2,
                    tags="node_hover",
                )

    def canvas_right_click(self, event):
        self.wire_start = None
        if self.pending_wire:
            self.canvas.delete(self.pending_wire)
            self.pending_wire = None
        self.deselect()
        self.status_var.set(f"{self.mode.get().capitalize()} mode")

    def on_zoom(self, event):
        if event.num == 4 or event.delta > 0:
            factor = 1.1
        else:
            factor = 1 / 1.1

        new_zoom = max(0.1, min(8.0, self.zoom * factor))
        if new_zoom == self.zoom:
            return

        wx, wy = self.s2w(event.x, event.y)
        self.zoom = new_zoom
        self.pan_x = event.x - wx * self.zoom
        self.pan_y = event.y - wy * self.zoom
        self.full_redraw()
        self.update_coord_bar(event.x, event.y)

    def reset_zoom(self):
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.full_redraw()

    def pan_start(self, event):
        self.pan_anchor = (event.x, event.y, self.pan_x, self.pan_y)

    def pan_move(self, event):
        if not self.pan_anchor:
            return
        ax, ay, apx, apy = self.pan_anchor
        self.pan_x = apx + (event.x - ax)
        self.pan_y = apy + (event.y - ay)
        self.full_redraw()

    def preset_rotate(self, delta):
        self.place_angle = (self.place_angle + delta) % 360
        self.status_var.set(
            f"Place angle set to {self.place_angle}° — next component will be rotated"
        )

    def rotate_selected(self, delta):
        cid = self.selected_id
        if not cid or cid not in self.components:
            return

        comp = self.components[cid]
        comp["angle"] = (comp.get("angle", 0) + delta) % 360
        comp["nodes"] = rotate_nodes(comp["type"], comp["x"], comp["y"], comp["angle"])

        self.render_component(cid)
        self.redraw_wires_for(cid)
        self.select_comp(cid)
        self.update_info(cid)
        self.status_var.set(f"Rotated [{cid}] to {comp['angle']}° (R=CW, E=CCW)")

    def place_wire_node(self, x, y):
        cid = str(uuid.uuid4())[:8]
        self.components[cid] = {
            "type": "Wire Node",
            "x": x,
            "y": y,
            "angle": 0,
            "nodes": [(x, y)],
        }
        self.render_component(cid)
        self.update_stats()
        return cid, 0

    def split_wire(self, conn_idx, x, y):
        conn = self.connections[conn_idx]
        from_id, from_node = conn["from_id"], conn["from_node"]
        to_id, to_node = conn["to_id"], conn["to_node"]
        self.delete_wire(conn_idx)
        new_cid, new_nidx = self.place_wire_node(x, y)
        self.add_connection(from_id, from_node, new_cid, new_nidx)
        self.add_connection(new_cid, new_nidx, to_id, to_node)
        return new_cid, new_nidx

    def canvas_right_click(self, event):
        self.cancel_wire()
        self.deselect()

    def update_coord_bar(self, sx, sy):
        wx, wy = self.s2w(sx, sy)
        self.coord_var.set(f"x:{int(wx)} y:{int(wy)}  zoom:{self.zoom*100:.0f}%")

    def cancel_wire(self):
        self.wire_start = None
        self.cancel_pending_wire()

    def cancel_pending_wire(self):
        if self.pending_wire:
            self.canvas.delete(self.pending_wire)
            self.pending_wire = None

    def place_component(self, x, y):
        if self.sim_running: 
            self.sim_running = False
        name = self.active_comp.get()
        cid = str(uuid.uuid4())[:8]
        angle = self.place_angle

        identifiers = [
            int(comp["identifier"][1:])
            for comp in self.components.values()
            if comp["type"] == name
        ]
        identifier_idx = 0
        while identifier_idx in identifiers:
            identifier_idx += 1

        if not (name == "Ground" or name == "Wire Node"):
            identifier = COMPONENTS[name]["params"][0][0] + str(identifier_idx)
        else:
            identifier = None

        self.components[cid] = {
            "type": name,
            "x": x,
            "y": y,
            "angle": angle,
            "nodes": rotate_nodes(name, x, y, angle),
            "values": self.default_values(name),
            "identifier": identifier,
        }

        self.select_comp(cid)

        self.render_component(cid)
        self.update_stats()
        self.status_var.set(f"Placed {name} [{cid}] at ({x}, {y})")

    def render_component(self, cid):
        comp = self.components[cid]
        tag = f"comp_{cid}"
        self.canvas.delete(tag)
        name = comp["type"]
        color = COMPONENTS[name]["color"]
        angle = comp.get("angle", 0)
        wx, wy = comp["x"], comp["y"]
        sx, sy = self.w2s(wx, wy)
        identifier = comp.get("identifier")
        z = self.zoom

        def ws(dx, dy):
            return rotate_point(sx, sy, dx * z, dy * z, angle)

        c = self.canvas
        lw = max(1, 2 * z)

        if not name == "Wire Node":
            draw_fn = DRAW_FN.get(name, draw_unknown)
            draw_fn(
                c,
                ws,
                color,
                tag,
                lw,
                z,
                sx,
                sy,
                (
                    COMPONENTS[name]["selection_radii"][0] * self.zoom,
                    COMPONENTS[name]["selection_radii"][1] * self.zoom,
                ),
            )

        if not self.sim_running:

            vals = comp.get("values", {})
            val_str = ""
            if vals:
                val_str = list(vals.values())[0]
            label = ""
            if len(val_str) > 0:
                label += f"\n{val_str}"
            label += f"\n{identifier}" if identifier is not None else ""
            lx, ly = (sx, sy)
            c.tag_raise(
                c.create_text(
                    lx,
                    ly + 34 * z,
                    text=label,
                    fill=TEXT_SEC,
                    font=("Courier New", max(6, int(7 * z))),
                    tags=tag,
                    justify=tk.CENTER,
                    anchor="center",
                )
            )

        for i, (nwx, nwy) in enumerate(comp["nodes"]):
            self.draw_node(nwx, nwy, tag, cid, i)

        self.canvas.tag_bind(tag, "<Button-1>", lambda e, c=cid: self.comp_click(e, c))
        self.canvas.tag_bind(tag, "<B1-Motion>", lambda e, c=cid: self.comp_drag(e, c))

    def comp_click(self, event, cid):
        wx, wy = self.event_world(event)
        m = self.mode.get()
        if m == "insert" or m == "select":
            comp = self.components[cid]
            self.drag_data = {"id": cid, "ox": wx - comp["x"], "oy": wy - comp["y"]}
            self.select_comp(cid)
        elif m == "delete":
            self.delete_component(cid)
        # was causing bugs
        # elif m == "wire":
        #     node = self.hit_node(wx, wy)
        #     if node:
        #         self.canvas_click(event)

    def comp_drag(self, event, cid):
        if self.mode.get() == "insert" or self.mode.get() == "select":
            wx, wy = self.event_world(event)
            if not self.drag_data.get("id"):
                comp = self.components[cid]
                self.drag_data = {"id": cid, "ox": wx - comp["x"], "oy": wy - comp["y"]}
            new_x = self.snap(wx - self.drag_data.get("ox", 0))
            new_y = self.snap(wy - self.drag_data.get("oy", 0))
            self.move_component(
                cid,
                new_x,
                new_y,
            )
            self.draw_selection_rect(cid)

    def move_component(self, cid, x, y):
        comp = self.components[cid]
        name = comp["type"]
        offsets = COMPONENTS[name]["nodes"]
        comp["x"] = x
        comp["y"] = y
        comp["nodes"] = rotate_nodes(name, x, y, comp.get("angle", 0))
        self.render_component(cid)
        self.redraw_wires_for(cid)

    def delete_component(self, cid):
        if self.sim_running: 
            self.sim_running = False

        # Remove connections
        to_remove = [
            c for c in self.connections if c["from_id"] == cid or c["to_id"] == cid
        ]
        for conn in to_remove:
            self.canvas.delete(conn["wire_id"])
            self.connections.remove(conn)
        # Remove canvas items
        self.canvas.delete(f"comp_{cid}")
        del self.components[cid]
        if self.selected_id == cid:
            self.deselect()
        self.update_stats()
        self.status_var.set(f"Deleted component [{cid}]")

    def select_comp(self, cid):
        self.deselect()
        self.selected_id = cid
        self.draw_selection_rect(cid)
        self.update_info(cid)

    def draw_selection_rect(self, cid):
        self.canvas.delete("selection_rect")
        comp = self.components[cid]
        sx, sy = self.w2s(comp["x"], comp["y"])
        rx, ry = COMPONENTS[comp["type"]]["selection_radii"]
        rotation = comp["angle"]
        rx *= self.zoom
        ry *= self.zoom
        x1, y1 = rotate_point(sx, sy, -rx, -ry, rotation)
        x2, y2 = rotate_point(sx, sy, rx, ry, rotation)
        self.canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            outline=SEL_COLOR,
            dash=(4, 3),
            width=2,
            tags="selection_rect",
        )

    def deselect(self):
        self.canvas.delete("selection_rect")
        self.selected_id = None
        self.update_info(None)

    def add_connection(self, from_id, from_node, to_id, to_node):
        conn = {
            "from_id": from_id,
            "from_node": from_node,
            "to_id": to_id,
            "to_node": to_node,
            "wire_id": None,
        }
        self.connections.append(conn)
        self.draw_wire(conn)
        self.update_stats()
        self.status_var.set(f"Connected [{from_id}]:{from_node} -> [{to_id}]:{to_node}")

    def draw_node(self, nwx, nwy, tag, cid, i):
        nsx, nsy = self.w2s(nwx, nwy)
        r = NODE_R * self.zoom
        self.canvas.create_oval(
            nsx - r,
            nsy - r,
            nsx + r,
            nsy + r,
            fill=NODE_COLOR,
            outline=ACCENT2,
            width=1,
            tags=(tag, f"node_{cid}_{i}"),
        )

    def draw_wire(self, conn):
        fn = self.components[conn["from_id"]]["nodes"][conn["from_node"]]
        tn = self.components[conn["to_id"]]["nodes"][conn["to_node"]]
        sfx, sfy = self.w2s(*fn)
        stx, sty = self.w2s(*tn)
        wid = self.canvas.create_line(
            sfx,
            sfy,
            stx,
            sty,
            fill=WIRE_COLOR,
            width=max(1, 2 * self.zoom),
            tags="wire",
        )
        conn["wire_id"] = wid
        self.canvas.tag_lower("wire")
        self.canvas.tag_lower("grid")
        return wid

    def redraw_wires_for(self, cid):
        for conn in self.connections:
            if conn["from_id"] == cid or conn["to_id"] == cid:
                self.canvas.delete(conn["wire_id"])
                self.draw_wire(conn)

    def delete_wire(self, idx):
        conn = self.connections[idx]
        self.canvas.delete(conn["wire_id"])
        self.connections.pop(idx)
        self.update_stats()
        self.status_var.set("Wire deleted")

    def hit_component(self, wx, wy):
        for cid, comp in self.components.items():
            if (
                abs(wx - comp["x"]) < COMPONENTS[comp["type"]]["selection_radii"][0]
                and abs(wy - comp["y"]) < COMPONENTS[comp["type"]]["selection_radii"][1]
            ):
                return cid
        return None

    def hit_node(self, wx, wy):
        r = max(7, 8 / self.zoom)
        for cid, comp in self.components.items():
            for i, (nx, ny) in enumerate(comp["nodes"]):
                if math.hypot(wx - nx, wy - ny) < r:
                    return (cid, i, nx, ny)
        return None

    def hit_wire(self, wx, wy):
        tol = max(4, 6 / self.zoom)
        for i, conn in enumerate(self.connections):
            fn = self.components[conn["from_id"]]["nodes"][conn["from_node"]]
            tn = self.components[conn["to_id"]]["nodes"][conn["to_node"]]
            dx, dy = tn[0] - fn[0], tn[1] - fn[1]
            if dx == 0 and dy == 0:
                continue
            t = max(
                0, min(1, ((wx - fn[0]) * dx + (wy - fn[1]) * dy) / (dx * dx + dy * dy))
            )
            if math.hypot(wx - fn[0] - t * dx, wy - fn[1] - t * dy) < tol:
                return i
        return None

    def open_value_editor(self, cid=None):
        target = cid or self.selected_id
        if not target or target not in self.components:
            return
        comp = self.components[target]
        if not COMPONENTS[comp["type"]]["params"]:
            self.status_var.set(f"{comp['type']} has no editable values")
            return
        dlg = ValueDialog(self, comp)
        if dlg.result is not None:
            comp["values"] = dlg.result
            self.render_component(target, True)
            self.update_info(target)
            self.status_var.set(f"Values updated for [{target}]")

    def default_values(self, name):
        return {label: default for label, default, unit in COMPONENTS[name]["params"]}

    def update_info(self, cid):
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        has_params = False
        if cid and cid in self.components:
            comp = self.components[cid]
            name = comp["type"]
            lines = [f"ID:    {comp["identifier"]}"]
            vals = comp.get("values", {})
            if vals:
                lines.append("Value(s):")
                for k, v in vals.items():
                    unit = next(
                        (u for l, d, u in COMPONENTS[name]["params"] if l == k), ""
                    )
                    lines.append(f"  {k} = {v}")
            if self.sim_running and cid in self.results["element_currents"].keys():
                lines.append("Simulation Results:")
                lines.append(self.format_val(self.results["element_currents"][cid]))

            lines.extend(
                [
                    f"Type:  {name}",
                    f"x:     {comp['x']}",
                    f"y:     {comp['y']}",
                    f"Angle: {comp.get('angle',0)}",
                ]
            )

            lines.append("Nodes:")
            for i, (nx, ny) in enumerate(comp["nodes"]):
                lines.append(f"  [{i}]({nx},{ny})")
            conns = [
                c for c in self.connections if c["from_id"] == cid or c["to_id"] == cid
            ]
            if conns:
                lines.append(f"Wires: {len(conns)}")

            lines.append(f"CODE: {cid}")

            self.info_text.insert(tk.END, "\n".join(lines))
            has_params = bool(COMPONENTS[name]["params"])

        self.info_text.config(state=tk.DISABLED)
        self.btn_edit_val.config(state=tk.NORMAL if has_params else tk.DISABLED)

    def update_stats(self):
        self.stats_label.config(
            text=f"Components : {len(self.components)}\nConnections: {len(self.connections)}"
        )

    def file_open(self):
        path = filedialog.askopenfilename(
            title="Open circuit", filetypes=[("JSON", "*.json"), ("All", "*.*")]
        )
        if not path:
            return
        try:
            with open(path) as f:
                data = json.load(f)
            self.load_state(data)
            self.filepath = path
            self.status_var.set(f"Opened: {path}")
        except Exception as e:
            messagebox.showerror("Open failed", str(e))

    def file_save(self):
        if not self.filepath:
            self.filepath = filedialog.asksaveasfilename(
                title="Save circuit",
                defaultextension=".json",
                filetypes=[("JSON", "*.json")],
            )
        if not self.filepath:
            return
        try:
            with open(self.filepath, "w") as f:
                json.dump(self.get_state(), f, indent=2)
            self.status_var.set(f"Saved: {self.filepath}")
        except Exception as e:
            messagebox.showerror("Save failed", str(e))

    def file_export(self):
        path = filedialog.asksaveasfilename(
            title="Export netlist",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Text", "*.txt")],
        )
        if not path:
            return
        try:
            with open(path, "w") as f:
                json.dump(self.get_state(), f, indent=2)
            self.status_var.set(f"Exported: {path}")
        except Exception as e:
            messagebox.showerror("Export failed", str(e))

    def get_state(self):
        comps = {}
        for cid, comp in self.components.items():
            comps[cid] = {
                "type": comp["type"],
                "x": comp["x"],
                "y": comp["y"],
                "angle": comp.get("angle", 0),
                "nodes": comp["nodes"],
                "values": comp.get("values", {}),
                "identifier": comp.get("identifier"),
            }
        conns = [
            {
                "from_id": c["from_id"],
                "from_node": c["from_node"],
                "to_id": c["to_id"],
                "to_node": c["to_node"],
            }
            for c in self.connections
        ]
        return {"components": comps, "connections": conns}

    def load_state(self, data):
        self.clear_all(confirm=False)
        for cid, comp in data.get("components", {}).items():
            self.components[cid] = {
                "type": comp["type"],
                "x": comp["x"],
                "y": comp["y"],
                "angle": comp.get("angle", 0),
                "nodes": [tuple(n) for n in comp["nodes"]],
                "values": comp.get("values", self.default_values(comp["type"])),
                "identifier": comp.get("identifier"),
            }
        for conn in data.get("connections", []):
            self.connections.append(
                {
                    "from_id": conn["from_id"],
                    "from_node": conn["from_node"],
                    "to_id": conn["to_id"],
                    "to_node": conn["to_node"],
                    "wire_id": None,
                }
            )
        self.full_redraw()
        self.update_stats()

    def toggle_simulation(self):
        self.sim_running = not self.sim_running
        if self.sim_running:
            self.btn_sim.config(text="Stop Sim", fg=DANGER)
            self.status_var.set("Simulation running…")
            self.run_simulation()
        else:
            self.btn_sim.config(text="Run Sim", fg="#00ff99")
            self.status_var.set("Simulation stopped")
        self.full_redraw()

    def format_val(self, val: float):
        if val < 0:
            return ""
        elif val == 0:
            return "0"
        magnitude = math.floor(math.log10(val))
        suffix = 10 ** (3 * math.floor(magnitude / 3))
        temp = {}
        if suffix in SUFFIXES.keys():
            return str(val / suffix) + SUFFIXES[suffix] + "A"

    def display_results(self):
        for cid in self.results["element_currents"].keys():
            comp = self.components[cid]
            x, y = self.w2s(comp["x"], comp["y"])
            self.canvas.tag_raise(
                self.canvas.create_text(
                    x,
                    y + 34 * self.zoom,
                    text=self.format_val(self.results["element_currents"][cid]),
                    fill=TEXT_SOLVE,
                    font=("Courier New", max(6, int(7 * self.zoom))),
                    tags=f"result_{cid}",
                    justify=tk.CENTER,
                    anchor="center",
                )
            )

    def run_simulation(self):
        if not self.sim_running:
            return
        state = self.get_state()
        summary, self.results = CircuitSolver(state).solve_and_format()
        if self.results["error"]:
            self.status_var.set(f"Sim error: {self.results['error']}")
        else:
            nv = len(self.results["node_voltages"])
            ni = len(self.results["element_currents"])
            self.status_var.set(f"Solved: {nv} node voltages, {ni} element currents")
        print(summary)

    def clear_all(self, confirm=True):
        if confirm and not messagebox.askyesno(
            "Clear", "Remove all components and wires?"
        ):
            return
        if self.sim_running: 
            self.sim_running = False
        self.components.clear()
        self.connections.clear()
        self.selected_id = None
        self.wire_start = None
        self.pending_wire = None
        self.drag_data = {}
        self.full_redraw()
        self.update_stats()
        self.update_info(None)
        self.status_var.set("Canvas cleared")