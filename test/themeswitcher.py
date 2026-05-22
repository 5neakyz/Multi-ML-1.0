import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

def change_theme():
    """Switch to the selected theme."""
    selected = theme_var.get()
    try:
        style.theme_use(selected)
    except tk.TclError:
        messagebox.showerror("Error", f"Theme '{selected}' is not available.")

# Create main window
root = tk.Tk()
root.title("Tkinter Theme Switcher")
root.geometry("300x200")

# Create a ttk Style object
style = ttk.Style()

# Get available themes
available_themes = style.theme_names()

# Variable to store selected theme
theme_var = tk.StringVar(value=style.theme_use())

# Dropdown to select theme
theme_label = ttk.Label(root, text="Select Theme:")
theme_label.pack(pady=10)

theme_menu = ttk.Combobox(root, textvariable=theme_var, values=available_themes, state="readonly")
theme_menu.pack(pady=5)

# Button to apply theme
apply_btn = ttk.Button(root, text="Apply Theme", command=change_theme)
apply_btn.pack(pady=10)

# Example widgets to see theme effect
ttk.Label(root, text="Sample Label").pack(pady=5)
ttk.Entry(root).pack(pady=5)
ttk.Button(root, text="Sample Button").pack(pady=5)

root.mainloop()