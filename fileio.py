from components import *
from constants import *
import os

def write_to_file(circuit: Circuit, file: TextIO):
    file.write(str(len(circuit.components))+"\n")
    for component in circuit.components:
        file.write(component.convert())
    file.write(str(len(circuit.nodes))+"\n")
    for node in circuit.nodes:
        file.write(node.convert())

def read_from_file(file: TextIO):
    circuit = Circuit()
    for i in range(int(file.readline())):
        fields = file.readline().split(",")
        if fields[0] == "R":
            circuit.add_component_from_file_fields(RESISTOR, start=int(fields[1]), end=int(fields[2]), identifier=fields[3], value=int(fields[4]), x=int(fields[5]), y=int(fields[6]), orientation=int(fields[7]))
        elif fields[0] == "V":
            circuit.add_component_from_file_fields(VOLTAGE_SOURCE, start=int(fields[1]), end=int(fields[2]), identifier=fields[3], index=int(fields[4]), value=int(fields[5], x=int(fields[6]), y=int(fields[7])), orientation=int(fields[8]))
    for i in range(int(file.readline())):
        nodevals = file.readline().split(",")
        points = []
        for i in range(int((len(nodevals)-1)/2)):
            points.append((nodevals[i+1], nodevals[i+2]))
        circuit.add_node(points)
    return circuit

def create_new(obj, newpath):
    if not obj.file == None and obj.circuit.size() > 0:
        write_to_file(obj.circuit, obj.file)

    obj.file.close()

    if os.path.exists(newpath):
        os.remove(newpath)
    obj.file = open(newpath, "w")
    obj.circuit = Circuit()

def open_existing(obj, path):
    if not obj.file == None and obj.circuit.size() > 0:
        write_to_file(obj.circuit, obj.file)

    obj.file.close()
    obj.file = open(path, "r+")

    if os.path.getsize(path) > 0:
        obj.circuit = read_from_file(obj.file)
    else:
        obj.circuit = Circuit()

def rename(obj, oldpath, newpath):
    obj.file.close()

    if os.path.exists(newpath):
        os.remove(newpath)

    os.rename(oldpath, newpath)
    obj.file = open(newpath, "a+")