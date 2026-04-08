from circuits import *
import os

def convert(c: Resistor):
        return "R," + str(c.start) + "," + str(c.end) + "," + c.id + "," + str(c.R) + "\n"

def convert(c: VoltageSource):
    return "V," + str(len(c.connections)) + "," + (str(connection) + "," for connection in c.connections) + c.id + "," + str(c.index) + "," + c.V + "\n"

def write_to_file(circuit: Circuit, file: TextIO):
    file.write(str(circuit.size)+"\n")
    for component in circuit.components:
        file.write(convert(component))

def read_from_file(circuit: Circuit, file: TextIO):
    circuit = Circuit()
    circuit.size = int(file.readline()[0:-2])
    for i in range(circuit.size):
        fields = file.readline()[0:-2].split(",")
        if fields[0] == "R":
            new_component = Resistor(fields[1], fields[2], fields[3], fields[4])
        elif fields[0] == "V":
            conn_count = int(fields[1])
            new_component = VoltageSource((fields[i+2] for i in range(conn_count)), fields[conn_count+2], fields[conn_count+3], fields[conn_count+4])

def create_new(obj, newpath):
    if not obj.file == None and obj.circuit.size > 0:
        write_to_file(obj.circuit, obj.file)

    obj.file.close()

    if os.path.exists(newpath):
        os.remove(newpath)
    obj.file = open(newpath, "w")
    obj.circuit = Circuit()

def open_existing(obj, circuit: Circuit, path):
    if not obj.file == None and obj.circuit.size > 0:
        write_to_file(obj.circuit, obj.file)

    obj.file.close()
    obj.file = open(path, "w")

def rename(obj, oldpath, newpath):
    obj.file.close()
    if os.path.exists(newpath):
        os.remove(newpath)
    os.rename(oldpath, newpath)
    obj.file = open(newpath, "w")

    if os.path.getsize(newpath) > 0:
        read_from_file(circuit, file)
    else:
        circuit = Circuit()