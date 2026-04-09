APPLICATION_NAME = "Smart Circuit Simulator"

# component types + defaults
VOLTAGE_SOURCE = 0
RESISTOR = 1
SWITCH = 2
LED = 3
TRANSISTOR = 4
CAPACITOR = 5
DIODE = 6

DEFAULT_VALUES = [5, 5, 0, 0, 0, 0, 0]

# GUI stuff
FONT = ("Roboto", 18)

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700

GUI_COMPONENT_WIDTH = 40
GUI_COMPONENT_HEIGHT = 80
LINE_WIDTH = 2.5

UP = 0
LEFT = 1
DOWN = 2
RIGHT = 3

# file stuff
DEFAULT_FILE = "circuits/new_circuit.circuit"

# file format will be .circuit
# data stored will simply be:
# # components
# first: component data (identifier, x, y, start, end, type, value)
# # wires
# then (simply denote with some random identifier like a long string of dashes or something):
# wire data - each will be a straight line - startx, starty, endx, endy, node_number
