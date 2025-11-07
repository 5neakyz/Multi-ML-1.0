import tkinter as tk

class my_button (tk.Frame):
    def __init__(self, parent=None, **configs):
        tk.Frame.__init__(self, parent, **configs)
        self.button_var=tk.StringVar()
        self.create_btn()

    def create_btn(self):
        self.hiButton=tk.Button(self, textvariable=self.button_var, command=self.change)
        self.hiButton.grid(row=0, column=0)
        self.button_var.set("Hi World!")

    def change(self):
        self.var=self.hiButton["text"]
        if self.var=="Hi World!":
            self.button_var.set("Hello World!")
            # self.master is the Main class instance
            self.master.gui1.new_text(self.var)
        elif self.var=="Hello World!":
            self.button_var.set("Hi World!")
            self.master.gui1.new_text(self.var)
        else:
            print ("NO")

class my_label (tk.Frame):
    def __init__(self, parent=None, **configs):
        tk.Frame.__init__(self, parent, **configs)
        self.label_var=tk.StringVar()
        self.create_text()

    def create_text(self):
        self.helloText=tk.Label(self, height=10, textvariable=self.label_var)
        self.helloText.grid(row=0, column=0)
        self.label_var.set("Hello World!")

    def new_text(self, message):
        self.label_var.set(message)

class Main(tk.LabelFrame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, text='Hi', bd=2, **kwargs)

        # use instance variables (names start with "self") to keep the reference for later
        self.gui = my_button(self)
        self.gui.grid(row=0, column=0)
        self.gui1 = my_label(self)
        self.gui1.grid(row=1, column=0)

if __name__ == '__main__':
    root = tk.Tk()
    portFrame = Main(root)
    portFrame.grid(row=0, column=0, padx=10)
    root.mainloop()