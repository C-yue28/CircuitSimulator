import numpy as np
from constants import *
from typing import TextIO

# using a grid, we apply nodal analysis method and Kirchoff's law to calculate currents/resistances

class Component:
    def __init__(self, start, end, identifier=""):
        self.start = start
        self.end = end
        self.id = identifier

    def stamp(self, G, I):
        pass

class Resistor(Component):
    def __init__(self, start=None, end=None, identifier="", resistance=0):
        super().__init__(start=start, end=end, identifier=identifier)
        self.R = resistance
        self.g = 1/resistance

    def stamp(self, G, I):
        G[self.start][self.start] += self.g
        if not self.end == -1:
            G[self.end][self.end] += self.g
            G[self.start][self.end] -= self.g
            G[self.end][self.start] -= self.g

# so for voltages, what we solve for is different - the G matrix will instead be coefficients of the current "through" the battery, and the last equation will be Vstart-Vend=Vsrc

class VoltageSource():
    def __init__(self, connections=[], identifier="", index=0, voltage=0): # index is from the back
        self.connections=connections
        self.id = identifier
        self.V = voltage
        self.index = index

    def stamp(self, G, I):
        idx = len(G)-1-self.index
        for c in self.connections:
            G[c][idx] -= 1
            G[idx][c] += 1
            I[idx] += self.V

class Circuit:
    def __init__(self):
        self.components = []
        self.size = 0
        self.component_counts = [0, 0, 0, 0, 0, 0, 0, 0]

    def calculate(self):
        I = np.zeros(self.size, dtype=np.longdouble)
        G = np.zeros([self.size, self.size], dtype=np.longdouble)
        result = np.linalg.solve(G, I)
        return np.insert(result, result[-1], 0)

    def add_component(self, start, end, type, value):
        if type == VOLTAGE_SOURCE:
            self.components.append(VoltageSource(start, "V"+str(self.component_counts[VOLTAGE_SOURCE]+1), self.component_counts[VOLTAGE_SOURCE], value))
            self.component_counts[VOLTAGE_SOURCE]+=1
        elif type == RESISTOR:
            self.components.append(Resistor(start, end, "R"+str(self.component_counts[RESISTOR]+1), value))
            self.component_counts[RESISTOR]+=1
        self.size+=1

    def convert(self, c: Resistor):
        return str(c.start) + "," + str(c.end) + "," + c.id + "," + str(c.R) + "\n"

    def convert(self, c: VoltageSource):
        return (str(connection) + "," for connection in c.connections) + c.id + "," + c.V + "," + str(c.index) + "\n"

    def write_to_file(self, file: TextIO):
        file.write(str(self.size)+"\n")
        for component in self.components:
            file.write(self.convert(component))
