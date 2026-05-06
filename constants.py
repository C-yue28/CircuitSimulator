BG_DARK = "#0f1117"
BG_PANEL = "#1a1d27"
BG_TOOLBAR = "#13151f"
ACCENT = "#00d4aa"
ACCENT2 = "#6c63ff"
DANGER = "#ff4f5e"
WARNING = "#ffb347"
TEXT_PRI = "#e8eaf0"
TEXT_SEC = "#7b8099"
GRID_COLOR = "#1e2130"
WIRE_COLOR = "#00d4aa"
WIRE_PEND = "#ffb347"
NODE_COLOR = "#6c63ff"
SEL_COLOR = "#ffb347"
COMP_BG = "#242840"
COMP_BORDER = "#3a3f5c"

GRID = 20  # grid snap size
NODE_R = 5  # node handle radius

COMPONENTS = {
    "Resistor": {"color": "#ffd166", "nodes": [(-30, 0), (30, 0)]},
    "Capacitor": {"color": "#06d6a0", "nodes": [(-25, 0), (25, 0)]},
    "Inductor": {"color": "#118ab2", "nodes": [(-30, 0), (30, 0)]},
    "Voltage Src": {"color": "#ef476f", "nodes": [(0, -30), (0, 30)]},
    "Current Src": {"color": "#f77f00", "nodes": [(0, -30), (0, 30)]},
    "Ground": {"color": "#8ecae6", "nodes": [(0, -20)]},
    "Wire Node": {"color": "#a8dadc", "nodes": [(0, 0)]},
    "Diode": {"color": "#c77dff", "nodes": [(-25, 0), (25, 0)]},
    "NPN BJT": {"color": "#48cae4", "nodes": [(-20, 0), (20, -20), (20, 20)]},
    "Op-Amp": {"color": "#f4a261", "nodes": [(-30, -15), (-30, 15), (30, 0)]},
}