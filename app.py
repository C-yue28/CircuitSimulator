import tkinter as tk
from tkinter import filedialog

import os
from numpy import delete, place

from components import *
from constants import *
from fileio import *

class CircuitSim:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APPLICATION_NAME + " - " + os.path.abspath(DEFAULT_FILE))
        self.root.geometry(str(WINDOW_WIDTH) + "x" + str(WINDOW_HEIGHT))

        self.canvas = tk.Canvas(self.root, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
        self.canvas.place(relx=0, rely=0, anchor="nw")

        self.file = open(os.path.abspath(DEFAULT_FILE), "w")
        self.circuit = Circuit()

        self.display()
        
    def add_button(self, frame, text, onclick, _relx, _rely, anchor):
        btn = tk.Button(frame, text=text, command=onclick)
        btn.place(relx=_relx, rely=_rely, anchor=anchor)

    def create_new_circuit(self):
        new_filename = filedialog.asksaveasfilename(initialdir=self.file.name, filetypes=[("Circuit files", "*.circuit")], defaultextension=".circuit")
        if len(new_filename) <= 0:
            return
        create_new(self, new_filename)
        self.canvas.delete("all")
        self.root.title(APPLICATION_NAME + " - " + self.file.name)

    def open_circuit(self):
        open_filename = filedialog.askopenfilename(initialdir=self.file.name, filetypes=[("Circuit files", "*.circuit")], defaultextension=".circuit")
        if len(open_filename) <= 0:
            return
        open_existing(self, open_filename)
        self.canvas.delete("all")
        self.root.title(APPLICATION_NAME + " - " + self.file.name)
        self.draw_circuit()

    def rename_circuit(self):
        newpath = filedialog.asksaveasfilename(initialfile=self.file.name, filetypes=[("Circuit files", "*.circuit")], defaultextension=".circuit")
        if len(newpath) <= 0:
            return
        rename(self, self.file.name, newpath) # temporarily set file to a name instead of an actual file
        self.root.title(APPLICATION_NAME + " - " + self.file.name)

    def hovering_symbol(self, event):
        if event.widget == self.symbol_obj or event.widget == self.symbol_obj.canvas:
            x = self.symbol_obj.winfo_x() + event.x
            y = self.symbol_obj.winfo_y() + event.y
        else:
            x = event.x
            y = event.y
        self.canvas.coords(self.symbol_obj_id, x, y)

    def confirm_add_component(self, event, symbol):
        if event.widget == self.symbol_obj or event.widget == self.symbol_obj.canvas:
            x = self.symbol_obj.winfo_x() + event.x
            y = self.symbol_obj.winfo_y() + event.y
        else:
            x = event.x
            y = event.y
        self.circuit.add_component(x, y, symbol)
        self.root.unbind('<Motion>')
        self.root.unbind('<Button-1>')

        self.symbol_obj = None
        self.symbol_obj_id = None

    def adding_symbol(self, symbol):
        if symbol == RESISTOR:
            self.symbol_obj = Resistor()
        elif symbol == VOLTAGE_SOURCE:
            self.symbol_obj = VoltageSource()
        self.symbol_obj_id = self.canvas.create_window(0, 0, window=self.symbol_obj)
        self.root.bind('<Motion>', self.hovering_symbol)
        self.root.bind('<Button-1>', lambda event: self.confirm_add_component(event, symbol))

    def draw_circuit(self):
        for component in self.circuit.components:
            print(component.position[1])
            self.canvas.create_window(component.position[0], component.position[1], tags=component.id, window=component)
            component.draw()

    def display(self):
        self.toolbar = tk.Frame(self.root, bd=0, width=WINDOW_WIDTH, height=30)

        menubar_parent = tk.Menu(self.root)

        # File -> New/Open/Rename
        file_menu = tk.Menu(menubar_parent, tearoff=0)
        file_menu.add_command(label="Create...", command=self.create_new_circuit)
        file_menu.add_command(label="Open...", command=self.open_circuit)
        file_menu.add_command(label="Rename/Save as...", command=self.rename_circuit)

        # Edit
        edit_menu = tk.Menu(menubar_parent, tearoff=0)
        add_symbol_menu = tk.Menu(edit_menu, tearoff=0)
        add_symbol_menu.add_command(label="Voltage Source", command=lambda: self.adding_symbol(VOLTAGE_SOURCE))
        add_symbol_menu.add_command(label="Resistor", command=lambda: self.adding_symbol(RESISTOR))

        edit_menu.add_cascade(label="Add...", menu=add_symbol_menu)

        menubar_parent.add_cascade(label="File", menu=file_menu)
        menubar_parent.add_cascade(label="Edit", menu=edit_menu)

        self.root.config(menu=menubar_parent)

        self.toolbar.place(x=0, y=0, anchor="nw")
        self.toolbar.tkraise()

    def run(self):
        self.root.mainloop()