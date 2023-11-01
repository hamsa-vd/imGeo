import tkinter as tk
import customtkinter as ctk
from tkinterdnd2 import TkinterDnD
import sys
sys.path.insert(0, "./frames")
sys.path.insert(1, "./utils")
from home import HomeFrame
from details import DetailsFrame
from store import Store
from common import Screen
class App(ctk.CTk, TkinterDnD.DnDWrapper):
    
    store: Store = Store()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

        self.title("Britian Energy Image")
        self.minsize(480, 640)
        self.geometry("480x640")
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
        
        if self.store.current_screen != Screen.HOME:
            self.render_home_btn()

    def next_screen(self):
        if self.store.current_screen == Screen.HOME:
            self.details_screen()

    def home_screen(self):
        self.store.current_screen = Screen.HOME
        self.clear_screen()
        
        self.home_frame = HomeFrame(self, border_width=2)
        self.home_frame.pack(expand=True, fill="both", padx=40, pady=40)

    def details_screen(self):
        self.store.current_screen = Screen.DETAILS
        self.clear_screen()
        
        self.details_frame = DetailsFrame(self, fg_color='transparent')
        self.details_frame.pack(expand=True, fill="both", padx=40, pady=40)

if __name__ == "__main__":
    app = App()
    app.mainloop()