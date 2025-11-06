import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
import threading

class NavBar(tk.Menu):
    def __init__(self, parent):
        tk.Menu.__init__(self, parent)
        self.menu_settings = tk.Menu(self, tearoff=0)
        self.menu_file = tk.Menu(self)
        self.menu_help = tk.Menu(self)
        
        #self.add_cascade(menu=self.menu_file, label='File')
        self.add_cascade(menu=self.menu_settings, label='Settings')
        self.add_cascade(menu=self.menu_help, label='Help')
        self.menu_settings.add_command(label="Test",command = lambda: threading.Thread(daemon=True,target=parent.close_window()).start())

    def testprint(self):
        print("you called?")

class Footer(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self,parent)
        pass

class MyApp(tk.Tk):
    def __init__(self):
        super().__init__() 
        self.title("ML Multi Stager v2.0.0")
        self.geometry(f"{800}x{600}")
        self.option_add("*tearOff", False)
        self.protocol("WM_DELETE_WINDOW",self.close_window)

        self.menu_bar = NavBar(self)
        self.config(menu=self.menu_bar)
        self.select_firmware_btn  = tk.Button(self,text="Firmware",command=lambda: threading.Thread(daemon=True,target=self.menu_bar.testprint(),args=("firm",)).start())
        self.select_firmware_btn.pack()
        self.mainloop()
    
    def close_window(self):
        self.destroy()


if __name__ == "__main__":
    MyApp()