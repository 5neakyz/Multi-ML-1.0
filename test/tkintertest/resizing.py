import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

class simpleapp_tk(ctk.CTkScrollableFrame):
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

        x = 0
        y = 0
        for label in labels:
            label.grid(column=x,row=y,padx=1,pady=1,sticky="NESW")
            y += 1
            if y > 2:
                y = 0
                x += 1
            print(f'Y:{y} X:{x}')
                
        self.grid_columnconfigure(0,minsize=200,weight=1)
        self.grid_columnconfigure(1,minsize=200,weight=1)
        self.grid_columnconfigure(2,minsize=200,weight=1)
        self.grid_rowconfigure(0,minsize=200,weight=1)
        self.grid_rowconfigure(1,minsize=200,weight=1)
        self.grid_rowconfigure(2,minsize=200,weight=1)


if __name__ == "__main__":
    app = simpleapp_tk(None)
    app.mainloop()