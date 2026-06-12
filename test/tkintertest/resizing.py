import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

class simpleapp_tk(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.parent = master
        self.initialize()

    def initialize(self):
        self.pack(expand=True,fill="both")

        labels = []
        for x in range (9):
            colors = ["green","black","red","purple","yellow","pink","blue","gray","orange"]
            label = ctk.CTkLabel(self,anchor="center",bg_color=colors[x])
            labels.append(label)

        col = 0
        row = 0
        cols = []
        rows = []
        for label in labels:
            print(f'col:{col} row:{row}')
            cols.append(col)
            rows.append(row)
            label.grid(column=col,row=row,padx=1,pady=1,sticky="NESW")
            col += 1
            if col > 1:
                col = 0
                row += 1

        print(f'cols: {cols}')
        print(f'rows: {rows}')
        print(f'cols unique: {set(cols)}')
        print(f'rows unique: {set(rows)}')
        self.grid_columnconfigure(list(set(cols)),minsize=200,weight=1)
        #self.grid_columnconfigure(1,minsize=200,weight=1)
        #self.grid_columnconfigure(2,minsize=200,weight=1)
        self.grid_rowconfigure(list(set(rows)),minsize=200,weight=1)
        #self.grid_rowconfigure(1,minsize=200,weight=1)
        #self.grid_rowconfigure(2,minsize=200,weight=1)


if __name__ == "__main__":
    app = simpleapp_tk(None)
    app.mainloop()