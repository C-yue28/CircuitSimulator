WIRE = 0
VOLTAGE_SOURCE = 1
RESISTOR = 2
SWITCH = 3
LED = 4
TRANSISTOR = 5
CAPACITOR = 6
DIODE = 7

FONT = ("Roboto", 18)

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700

# file format will be .circuit
# data stored will simply be:
# # components
# first: component data (identifier, x, y, start, end, type, value)
# # wires
# then (simply denote with some random identifier like a long string of dashes or something):
# wire data - each will be a straight line - startx, starty, endx, endy, node_number
