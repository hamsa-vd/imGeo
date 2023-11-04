from customtkinter import filedialog
import customtkinter as ctk
from tkinterdnd2 import DND_FILES

class HomeFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<DragEnter>>', self.validate_dragged_files)
        self.dnd_bind('<<Drop>>', self.drop)

        self.count_label = ctk.CTkLabel(self, text="0 images uploaded")

        self.label = ctk.CTkLabel(self, text="Drag and Drop here")
        self.label.place(relx=0.5, rely=0.54, anchor=ctk.CENTER)

        self.or_label = ctk.CTkLabel(self, text="(Or)", text_color="#71797E")
        self.or_label.place(relx=0.5, rely=0.5, anchor=ctk.CENTER)

        self.upload_button = ctk.CTkButton(self, text="Upload", command=self.upload_images)
        self.upload_button.place(relx=0.5, rely=0.45, anchor=ctk.CENTER)
        
        self.go_button = ctk.CTkButton(self, text="Go", command=self.on_go, width=75)

    def update_count_label(self, count):
        self.count_label.place(relx=0.0, rely=0.0, x=10, y=10, anchor=ctk.NW)
        self.count_label.configure(text=f"{count} images uploaded")

    def show_go_btn(self):
        self.go_button.place(relx=1.0, rely=1.0, x=-10, y=-10, anchor=ctk.SE)

    def on_go(self):
        self.master.next_screen()

    def is_image_file(self, file_path):
        allowed_extensions = ['.jpg', '.jpeg', '.png']
        return any(file_path.lower().endswith(ext) for ext in allowed_extensions)

    def validate_dragged_files(self, event):
        files = event.data.get_files()
        if all(self.is_image_file(file) for file in files):
            event.allow_drop()
        else:
            event.prevent_drop()
            self.label.configure(text="Only image files are allowed!")

    def drop(self, event):
        files = event.data.strip().split(" ")
        potential_images = []
        wrong_split_file:str = None
        for file in files:
            if wrong_split_file is not None:
                if file.endswith("}"):
                    total_file = wrong_split_file.strip('{') + " " + file.strip('}')
                    potential_images.append(total_file)
                    wrong_split_file = None
                else:
                    wrong_split_file += " " + file
                continue
            if file.startswith("{"):
                wrong_split_file = file
                continue
            potential_images.append(file)
        potential_images = list(filter(lambda x: self.is_image_file(x), potential_images))
        if len(potential_images):
            self.master.store.images += potential_images
            self.show_go_btn()
            self.update_count_label(len(self.master.store.images))
        else:
            self.label.configure(text="Only image files are allowed!")

    def upload_images(self):
        images = filedialog.askopenfilenames(
                title="Select Images",
                filetypes=[("Image files", "*.jpg;*.jpeg;*.png")]
            )
        if images and all(self.is_image_file(file) for file in images):
            self.master.store.images += images
            self.show_go_btn()
            self.update_count_label(len(self.master.store.images))
