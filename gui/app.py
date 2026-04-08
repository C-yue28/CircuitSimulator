import tkinter as tk
from numpy import place
from circuits import *
from constants import *
from file_system import *

class CircuitSim:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Smart Circuit Simulator")
        self.root.geometry(str(WINDOW_WIDTH) + "x" + str(WINDOW_HEIGHT))

        self.canvas = tk.Canvas(self.root, width=WINDOW_WIDTH, height=WINDOW_HEIGHT-100)
        self.canvas.place(relx=0, rely=100/WINDOW_HEIGHT, anchor="nw")
        self.canvas.create_rectangle(50, 100, 200, 300)

        self.display()
        
    def add_button(self, frame, text, onclick, _relx, _rely, anchor):
        btn = tk.Button(frame, text=text, command=onclick)
        btn.place(relx=_relx, rely=_rely, anchor=anchor)

    def create_new_circuit(self):
        txt = self.new_circuit_entry.get()
        self.circuit = make_new(txt)

    def new_circuit_interface(self):
        self.canvas.delete("all")

        input_frame = tk.Frame(self.root, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="gray")
        input_frame.place(relx=0.5, rely=0.5, anchor="center")
        input_frame.tkraise()
        
        self.new_circuit_entry = tk.Entry(input_frame, width=20)
        self.new_circuit_entry.place(relx=0.5, rely=0.45, anchor="center")
        self.add_button(input_frame, "Testing", self.create_new_circuit, 0.5, 0.55, "center")

    def init_toolbar(self):
        self.toolbar = tk.Frame(self.root, bd=1, relief='raised', width=WINDOW_WIDTH, height=100)
        self.add_button(self.toolbar, "New circuit", self.new_circuit_interface, 0, 0, "nw")
        self.toolbar.place(x=0, y=0, anchor="nw")
        self.toolbar.tkraise()

    def display(self):
        self.init_toolbar()

    def run(self):
        self.root.mainloop()