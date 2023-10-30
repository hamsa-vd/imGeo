import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from tkinterdnd2 import TkinterDnD
import sys
sys.path.insert(0, "./frames")
from home import HomeFrame
class App(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

        self.title("Britian Energy Image")
        self.minsize(480, 760)
        self.geometry("480x760")
        self.maxsize(480, 760)
        
        self.home_screen()
        
    def render_home_btn(self):
        self.home_btn = ctk.CTkButton(
                master=self, 
                corner_radius=5, 
                text= "Home",
                command=self.home_screen
            )
        self.home_btn.pack(padx=10, pady=10, anchor=tk.NW)

    def clear_screen(self):
        for widget in self.winfo_children():
            widget.destroy()


    def home_screen(self):
        self.clear_screen()
        
        self.home_frame = HomeFrame(self, border_width=2)
        self.home_frame.pack(expand=True, fill="both", padx=40, pady=40)

if __name__ == "__main__":
    app = App()
    app.mainloop()