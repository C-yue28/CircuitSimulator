from circuits import *

FILE = None

def make_new(name):
    global FILE
    if FILE == None:
        FILE = open("circuits/" + name + ".circuit", "w")
        
    return Circuit()