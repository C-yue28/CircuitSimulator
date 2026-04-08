import tkinter as tk
from tkinter import filedialog

import os
from numpy import delete, place

from circuits import *
from constants import *
from fileio import *

class CircuitSim:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Smart Circuit Simulator: " + os.path.abspath(DEFAULT_FILE))
        self.root.geometry(str(WINDOW_WIDTH) + "x" + str(WINDOW_HEIGHT))

        self.canvas = tk.Canvas(self.root, width=WINDOW_WIDTH, height=WINDOW_HEIGHT-100)
        self.canvas.place(relx=0, rely=100/WINDOW_HEIGHT, anchor="nw")
        self.canvas.create_rectangle(50, 100, 200, 300)

        self.file = open(os.path.abspath(DEFAULT_FILE), "w")
        self.circuit = Circuit()

        self.display()
        
    def add_button(self, frame, text, onclick, _relx, _rely, anchor):
        btn = tk.Button(frame, text=text, command=onclick)
        btn.place(relx=_relx, rely=_rely, anchor=anchor)

    def create_new_circuit(self):
        self.canvas.delete("all")
        create_new(self, filedialog.asksaveasfilename(initialdir="C:/Users/Chris Yue/source/repos/CS50 Final Project", filetypes=[("Circuit files", "*.circuit")], defaultextension=".circuit"))
        self.root.title(self.file.name)

    def open_circuit(self):
        # then clear canvas & open the new circuit
        self.canvas.delete("all")
        open_existing(self, self.circuit, filedialog.askopenfilename(initialdir="C:/Users/Chris Yue/source/repos/CS50 Final Project", filetypes=[("Circuit files", "*.circuit")], defaultextension=".circuit"))

    def rename_circuit(self):
        oldpath = os.path.abspath(self.file.name)
        rename(self, oldpath, filedialog.asksaveasfilename(initialfile=oldpath, filetypes=[("Circuit files", "*.circuit")], defaultextension=".circuit")) # temporarily set file to a name instead of an actual file

    def init_toolbar(self):
        self.toolbar = tk.Frame(self.root, bd=1, relief='raised', width=WINDOW_WIDTH, height=100)

        menubar_parent = tk.Menu(self.root)

        # File -> New/Open/Rename
        file_menu = tk.Menu(menubar_parent, tearoff=0)
        file_menu.add_command(label="Create...", command=self.create_new_circuit)
        file_menu.add_command(label="Open...", command=self.open_circuit)
        file_menu.add_command(label="Rename/Save as...", command=self.rename_circuit)

        menubar_parent.add_cascade(label="File", menu=file_menu)

        self.root.config(menu=menubar_parent)

        self.toolbar.place(x=0, y=0, anchor="nw")
        self.toolbar.tkraise()

    def display(self):
        self.init_toolbar()

    def run(self):
        self.root.mainloop()