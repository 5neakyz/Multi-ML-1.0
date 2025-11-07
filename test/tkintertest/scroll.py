import customtkinter as ctk
class MyFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # add widgets onto the frame...
        self.label = ctk.CTkLabel(self)
        self.label.grid(row=0, column=0, padx=20)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.my_frame = MyFrame(master=self, width=50, height=50)
        self.my_frame.grid(row=0, column=0, padx=20, pady=20)


app = App()
app.geometry(f"{500}x{200}")
app.mainloop()