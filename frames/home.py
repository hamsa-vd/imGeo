import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from tkinterdnd2 import DND_FILES

class HomeFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.drop)

        self.label = ctk.CTkLabel(self, text="Drag and Drop here")
        self.label.place(relx=0.5, rely=0.54, anchor=tk.CENTER)

        self.or_label = ctk.CTkLabel(self, text="(Or)", text_color="#71797E")
        self.or_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.upload_button = ctk.CTkButton(self, text="Upload", command=self.upload_images)
        self.upload_button.place(relx=0.5, rely=0.45, anchor=tk.CENTER)

    def drop(self, event):
        self.master.store.images = event.data
        self.master.next_screen()

    def upload_images(self):
        image = filedialog.askopenfilename(
                title="Select Images",
                filetypes=[("Image files", "*.jpg;*.jpeg;*.png")]
            )
        if image:
            self.master.store.images = image
            self.master.next_screen()