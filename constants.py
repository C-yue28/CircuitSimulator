BG_DARK = "#0f1117"
BG_PANEL = "#1a1d27"
BG_TOOLBAR = "#13151f"
ACCENT = "#00d4aa"
ACCENT2 = "#6c63ff"
DANGER = "#ff4f5e"
WARNING = "#ffb347"
TEXT_PRI = "#e8eaf0"
TEXT_SEC = "#7b8099"
TEXT_SOLVE = "#ffffff"
GRID_COLOR = "#1e2130"
WIRE_COLOR = "#00d4aa"
WIRE_PEND = "#ffb347"
NODE_COLOR = "#6c63ff"
SEL_COLOR = "#ffb347"
COMP_BG = "#242840"
COMP_BORDER = "#3a3f5c"

GRID = 20  # grid snap size
NODE_R = 2  # node handle radius

COMPONENTS = {
    "Resistor": {
        "color": "#ffd166",
        "nodes": [(-40, 0), (40, 0)],
        "selection_radii": (18, 10),
        "params": [("R", "1k", "Ohm")],
    },
    "Capacitor": {
        "color": "#06d6a0",
        "nodes": [(-40, 0), (40, 0)],
        "selection_radii": (15, 15),
        "params": [("C", "0.1u", "F")],
    },
    "Inductor": {
        "color": "#118ab2",
        "nodes": [(-40, 0), (40, 0)],
        "selection_radii": (18, 6),
        "params": [("L", "10m", "H")],
    },
    "Voltage Src": {
        "color": "#ef476f",
        "nodes": [(0, -40), (0, 40)],
        "selection_radii": (18, 18),
        "params": [("V", "5", "V")],
    },
    "Ground": {
        "color": "#8ecae6",
        "nodes": [(0, -20)],
        "selection_radii": (18, 18),
        "params": [],
    },
    "Wire Node": {
        "color": "#a8dadc",
        "nodes": [(0, 0)],
        "selection_radii": (4, 4),
        "params": [],
    },
    "Diode": {
        "color": "#c77dff",
        "nodes": [(-40, 0), (40, 0)],
        "selection_radii": (15, 12),
        "params": [("D", "0.7", "V")],
    },
    "NPN BJT": {
        "color": "#48cae4",
        "nodes": [(-20, 0), (20, -20), (20, 20)],
        "selection_radii": (20, 24),
        "params": [("Q", "100", "")],
    },
    "Op-Amp": {
        "color": "#f4a261",
        "nodes": [(-40, -20), (-40, 20), (40, 0)],
        "selection_radii": (22, 20),
        "params": [("U", "inf", "")],
    },
}