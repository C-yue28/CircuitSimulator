import tkinter as tk
import numpy as np
from constants import *
from typing import TextIO

# using a grid, we apply nodal analysis method and Kirchoff's law to calculate currents/resistances

class Component(tk.Frame):
    def __init__(self, start, end, identifier="", orientation=UP, position=(0,0), parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.start = start
        self.end = end
        self.id = identifier
        self.orientation = orientation
        self.position = position

        self.width = GUI_COMPONENT_WIDTH
        self.height = GUI_COMPONENT_HEIGHT

        self.config(width=self.width, height=self.height)

        self.canvas = tk.Canvas(self, width=self.width, height=self.height)
        self.canvas.pack()

    def stamp(self, G, I):
        pass

    def convert(self):
        pass

    def draw(self):
        pass

class Resistor(Component):
    def __init__(self, start=None, end=None, identifier="", resistance=0, orientation=UP, position=(0,0), parent=None, *args, **kwargs):
        super().__init__(start=start, end=end, identifier=identifier, orientation=orientation, position=position, parent=parent, *args, **kwargs)
        self.R = resistance
        self.draw()

    def stamp(self, G, I):
        self.g = 1/self.R
        G[self.start][self.start] += self.g
        if not self.end == -1:
            G[self.end][self.end] += self.g
            G[self.start][self.end] -= self.g
            G[self.end][self.start] -= self.g
    
    def convert(self):
        return "R," + str(self.start) + "," + str(self.end) + "," + self.id + "," + str(self.R) + "," + str(self.position[0]) + "," + str(self.position[1]) + "," + str(self.orientation) + "\n"

    def draw(self):
        center_x = self.width/2
        amplitude = self.width/4
        count = 4
        y = self.height/4
        increment = (self.height - 2*y) / (2 + (count**2))

        self.canvas.create_line(center_x, 0, center_x, y, width=LINE_WIDTH)
        self.canvas.create_line(center_x, self.height, center_x, self.height-y, width=LINE_WIDTH)

        self.canvas.create_line(center_x, y, center_x+amplitude, y+increment, width=LINE_WIDTH)

        for i in range(count):
            self.canvas.create_line(center_x+amplitude, y+(4*i+1)*increment, center_x-amplitude, y+(4*i+3)*increment, width=LINE_WIDTH)
            self.canvas.create_line(center_x-amplitude, y+(4*i+3)*increment, center_x+amplitude, y+(4*i+5)*increment, width=LINE_WIDTH)

        self.canvas.create_line(center_x+amplitude, y+increment*(1+count**2), center_x, self.height-y, width=LINE_WIDTH)

# so for voltages, what we solve for is different - the G matrix will instead be coefficients of the current "through" the battery, and the last equation will be Vstart-Vend=Vsrc

class VoltageSource(Component):
    def __init__(self, start=None, end=None, identifier="", index=0, voltage=0, orientation=UP, position=(0,0), parent=None, *args, **kwargs): # index is from the back
        super().__init__(start=start, end=end, identifier=identifier, orientation=orientation, position=position, parent=parent, *args, **kwargs)
        self.V = voltage
        self.index = index
        self.draw()

    def stamp(self, G, I):
        idx = len(G)-1-self.index
        G[self.start][idx] -= 1
        G[self.end][idx] -= 1
        G[idx][self.start] += 1
        G[idx][self.end] -= 1
        I[idx] += self.V

    def convert(self):
        return "V," + str(self.start) + "," + str(self.end) + "," + self.id + "," + str(self.index) + "," + str(self.V) + "," + str(self.position[0]) + "," + str(self.position[1]) + "," + str(self.orientation) + "\n"

    def draw(self):
        center_x = self.width/2
        amplitude = self.width/4
        count = 4
        y=self.height/4
        increment = (self.height - 2*y) / count

        self.canvas.create_line(center_x, 0, center_x, y, width=LINE_WIDTH)
        self.canvas.create_line(center_x, self.height, center_x, self.height-y, width=LINE_WIDTH)

        for i in range(int(count/2)):
            self.canvas.create_line(center_x-amplitude, y+i*2*increment, center_x+amplitude, y+i*2*increment, width=LINE_WIDTH)
            self.canvas.create_line(center_x-amplitude/3, y+(i*2+1)*increment, center_x+amplitude/3, y+(i*2+1)*increment, width=LINE_WIDTH)

# in the physical canvas, a node consists of any position on the wire that connects one component to another; we simply store x and y of each 
# "focus" point - start, end, joints (in order)
class Node:
    def __init__(self, points: list[tuple[int,int]], idx):
        self.focus_points = points # array of tuples
        self.idx = idx

    def convert(self):
        return str(self.idx) + "," + "".join(str(point[0]) + "," + str(point[1]) for point in self.focus_points) + "\n"

class Circuit:
    def __init__(self):
        self.components = []
        self.component_counts = [0, 0, 0, 0, 0, 0, 0, 0]
        self.nodes = [] # map x and y coordinates to nodes

    def size(self):
        return len(self.components)

    def calculate(self):
        size = len(self.components)
        I = np.zeros(size, dtype=np.longdouble)
        G = np.zeros([size, size], dtype=np.longdouble)
        result = np.linalg.solve(G, I)
        return np.insert(result, result[-1], 0)

    def _add_component(self, start, end, _type, value, position):
        if _type == VOLTAGE_SOURCE:
            self.components.append(VoltageSource(start, end, "V"+str(self.component_counts[VOLTAGE_SOURCE]+1), self.component_counts[VOLTAGE_SOURCE], value, position=position))
            self.component_counts[VOLTAGE_SOURCE]+=1
        elif _type == RESISTOR:
            self.components.append(Resistor(start, end, "R"+str(self.component_counts[RESISTOR]+1), value, position=position))
            self.component_counts[RESISTOR]+=1

    def add_component(self, x, middle_y, symbol):
        top_y = middle_y - GUI_COMPONENT_HEIGHT/2
        btm_y = middle_y + GUI_COMPONENT_HEIGHT/2

        self.nodes.append(Node([(x, top_y)], len(self.nodes)))
        self.nodes.append(Node([(x, btm_y)], len(self.nodes)))

        self._add_component(len(self.nodes)-2, len(self.nodes)-1, symbol, DEFAULT_VALUES[symbol], (x, middle_y))

    def add_component_from_file_fields(self, symbol, **kwargs):
        if symbol == RESISTOR:
            self.components.append(Resistor(kwargs["start"], kwargs["end"], kwargs["identifier"], kwargs["value"], kwargs["orientation"], (kwargs["x"], kwargs["y"])))
        elif symbol == VOLTAGE_SOURCE:
            self.components.append(VoltageSource(kwargs["start"], kwargs["end"], kwargs["identifier"], kwargs["index"], kwargs["value"], kwargs["orientation"], (kwargs["x"], kwargs["y"])))

    def add_node(self, points: list[tuple[int,int]]):
        self.nodes.append(Node(points, len(self.nodes)))        
