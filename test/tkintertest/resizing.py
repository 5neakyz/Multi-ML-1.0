import tkinter

class simpleapp_tk(tkinter.Tk):
    def __init__(self,parent):
        tkinter.Tk.__init__(self,parent)
        self.parent = parent
        self.initialize()

    def initialize(self):
        self.grid()

        label = tkinter.Label(self,anchor="center",bg="green")
        label.grid(column=0,row=0,sticky='NSEW')

        label2 = tkinter.Label(self,anchor="center",bg="black")
        label2.grid(column=1,row=0,sticky='NSEW')

        label3 = tkinter.Label(self,anchor="center",bg="red")
        label3.grid(column=2,row=0,sticky='NSEW')

        label4 = tkinter.Label(self,anchor="center",bg="purple")
        label4.grid(column=0,row=1,sticky='NSEW')

        label5 = tkinter.Label(self,anchor="center",bg="blue")
        label5.grid(column=1,row=1,sticky='NSEW')

        label6 = tkinter.Label(self,anchor="center",bg="yellow")
        label6.grid(column=2,row=1,sticky='NSEW')


        self.grid_columnconfigure(0,weight=1)
        self.grid_columnconfigure(1,weight=1)
        self.grid_columnconfigure(2,weight=1)
        self.grid_rowconfigure(0,weight=1)
        self.grid_rowconfigure(1,weight=1)


if __name__ == "__main__":
    app = simpleapp_tk(None)
    app.title("Test App")
    app.mainloop()