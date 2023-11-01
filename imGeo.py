import tkinter as tk
from tkinter import ttk, filedialog
import customtkinter as ctk
from tkcalendar import Calendar
from datetime import datetime, date, time
from PIL import Image, ImageDraw, ImageFont, ImageTk
from tkinterdnd2 import TkinterDnD, DND_FILES
import piexif
import os
from enum import Enum
from typing import List

class Screen(Enum):
    HOME="home"
    DETAILS="details"
    FINAL="FINAL"

class LatitudeRef(Enum):
    N="N"
    S="S"
    
    @classmethod
    def values(self):
        return [el.value for el in self]

class LongitudeRef(Enum):
    E="E"
    W="W"
    @classmethod
    def values(self):
        return [el.value for el in self]


class FloatEntry(ctk.CTkEntry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        vcmd = (self.register(self.validate),'%P')
        self.configure(validate="all", validatecommand=vcmd)

    def validate(self, text):
        if (
            all(char in "0123456789.-" for char in text) and  # all characters are valid
            "-" not in text[1:] and # "-" is the first character or not present
            text.count(".") <= 1): # only 0 or 1 periods
                return True
        else:
            return False

class FinalImage:
    image_path: str
    image: Image.Image
    exif_bytes: bytes
    
    def __init__(self, image_path: str, image: Image.Image, exif_bytes: bytes):
        self.image_path = image_path
        self.image = image
        self.exif_bytes = image

class Store:
    _instance = None
    current_screen: Screen
    images: List[str]
    _final_images: List[FinalImage]
    datetime: datetime
    latitude_deg: float
    latitude_ref: LatitudeRef
    longitude_deg: float
    longitude_ref: LongitudeRef
    address: str
    pic_name: str
    
    def __init__(self):
        self.current_screen = Screen.HOME
        self.images = []
        self._final_images = []
        self.datetime = None
        self.latitude_deg = None
        self.latitude_ref = None
        self.longitude_deg = None
        self.longitude_ref = None
        self.address = None
        self.pic_name = None
    
    def __new__(self, *args, **kwargs):
        if not self._instance:
            self._instance = super(Store, self).__new__(self, *args, **kwargs)
        return self._instance

    def get_dict(self):
        return {
            "images": self.images,
            "datetime": self.datetime,
            "latitude": {
                "deg": self.latitude_deg,
                "ref": self.latitude_ref
            },
            "longitude": {
                "deg": self.longitude_deg,
                "ref": self.longitude_ref
            }
        }
        
    def insert_final_image(self, image_path: str, image: Image.Image, exif_bytes: bytes):
        self._final_images.append(FinalImage(image_path=image_path, image=image, exif_bytes=exif_bytes))
        
    def get_final_images(self):
        return self._final_images

    def __repr__(self):
        return self.get_dict()
    
    def reset(self):
        self._instance = Store()

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
        elif self.store.current_screen == Screen.DETAILS:
            self.final_screen()
        else:
            self.home_screen()

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
    
    def final_screen(self):
        self.store.current_screen = Screen.FINAL
        self.clear_screen()
        
        self.final_frame = FinalFrame(self, fg_color='transparent')
        self.final_frame.pack(expand=True, fill="both", padx=40, pady=40)

class HomeFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<DragEnter>>', self.validate_dragged_files)
        self.dnd_bind('<<Drop>>', self.drop)

        self.label = ctk.CTkLabel(self, text="Drag and Drop here")
        self.label.place(relx=0.5, rely=0.54, anchor=ctk.CENTER)

        self.or_label = ctk.CTkLabel(self, text="(Or)", text_color="#71797E")
        self.or_label.place(relx=0.5, rely=0.5, anchor=ctk.CENTER)

        self.upload_button = ctk.CTkButton(self, text="Upload", command=self.upload_images)
        self.upload_button.place(relx=0.5, rely=0.45, anchor=ctk.CENTER)

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
            self.master.store.images = potential_images
            self.master.next_screen()
        else:
            self.label.configure(text="Only image files are allowed!")

    def upload_images(self):
        images = filedialog.askopenfilenames(
                title="Select Images",
                filetypes=[("Image files", "*.jpg;*.jpeg;*.png")]
            )
        if images and all(self.is_image_file(file) for file in images):
            self.master.store.images = images
            self.master.next_screen()

class DetailsFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.render_widgets()
        
    def init_vars(self):
        current_timestamp = datetime.now()
        date = current_timestamp.date()
        hour = current_timestamp.time().hour
        minute = current_timestamp.time().minute
        self.date_label = ctk.StringVar(value=self.format_datetime(date=date.strftime("%d %b %Y"), hour=hour, minute=minute))
        self.master.store.datetime = datetime(date.year, date.month, date.day, hour, minute)
        
    def render_widgets(self):
        
        self.init_vars()
        self.render_date_entry_widget()
        self.render_latitude_widget()
        self.render_longitude_widget()
        self.render_address_widget()
        self.render_pic_name_widget()
        self.render_process_btn()
        self.set_values()
    
    def render_process_btn(self):
        self.process_btn = ctk.CTkButton(
            master=self,
            text="Process Images",
            command=self.process_images,
            state=ctk.DISABLED
        )
        self.process_btn.grid(row = 9, column=0, columnspan=2, pady=(20, 0))
    
    def render_pic_name_widget(self):
        ctk.CTkLabel(
            master=self,
            text="Enter the Pic Name",
            anchor="w"
        ).grid(row=7, column=0, sticky="W", pady=(20, 0))
        self.pic_name = ctk.CTkEntry(master=self, placeholder_text="Pic name here...")
        self.pic_name.grid(row=8, column=0, columnspan=2, sticky="EW")
        self.pic_name.bind("<KeyRelease>", lambda e: self.validate_inputs())
    
    def render_address_widget(self):
        ctk.CTkLabel(
            master=self,
            text="Enter the address",
            anchor="w"
        ).grid(row=5, column=0, sticky="W", pady=(20, 0))
        self.address = ctk.CTkEntry(master=self, placeholder_text="Adress here...")
        self.address.grid(row=6, column=0, columnspan=2, sticky="EW")
        self.address.bind("<KeyRelease>", lambda e: self.validate_inputs())
    
    def render_longitude_widget(self):
        ctk.CTkLabel(
            master=self,
            text="Longitude Details",
            anchor="w"
        ).grid(row=3, column=0, sticky="W", pady=(20, 0))
        self.longitude_deg = FloatEntry(
            master=self, 
            placeholder_text="Longitude Degree",
            width=200
        )
        self.longitude_deg.grid(row=4, column=0, sticky="W")
        self.longitude_deg.bind("<KeyRelease>", lambda e: self.validate_inputs())

        
        self.longitude_ref = ctk.CTkComboBox(master=self, values=LongitudeRef.values(), width=80)
        self.longitude_ref.grid(row=4, column=1, padx=(10, 0), sticky="W")
    
    def render_latitude_widget(self):
        ctk.CTkLabel(
            master=self,
            text="Latitude Details",
            anchor="w"
        ).grid(row=1, column=0, sticky="W", pady=(20, 0))
        self.latitude_deg = FloatEntry(
            master=self, 
            placeholder_text="Latitude Degree",
            width=200
        )
        self.latitude_deg.grid(row=2, column=0, sticky="W")
        self.latitude_deg.bind("<KeyRelease>", lambda e: self.validate_inputs())
        
        self.latitude_ref = ctk.CTkComboBox(master=self, values=LatitudeRef.values(), width=80)
        self.latitude_ref.grid(row=2, column=1, padx=(10, 0), sticky="W")
    
    def render_date_entry_widget(self):
        ctk.CTkButton(
            master=self,
            corner_radius=5,
            text="Pick date and time", 
            command=self.pick_datetime
        ).grid(row=0, column=0, pady=10, sticky="W")
        ctk.CTkLabel(master=self, textvariable=self.date_label).grid(row=0, column=1, padx=10, pady=10, sticky="W")
        
    def format_datetime(self, date, hour, minute):
        return f"Selected: {date} {hour:02}:{minute:02}"
    
    def pick_datetime(self):
        picker = DateTimePicker(self.master)
        self.master.wait_window(picker)
        date, hour, minute = picker.date_time
        self.date_label.set(self.format_datetime(date=date, hour=hour, minute=minute))
        self.master.store.datetime = datetime(date.year, date.month, date.day, hour, minute)

    def deg_validator(self, deg_str):
        if deg_str == "":
            return True
        try:
            float(deg_str)
            return True
        except ValueError:
            return False
    
    def validate_inputs(self):
        if (self.latitude_deg.get() and
            self.longitude_deg.get() and
            self.address.get() and
            self.pic_name.get() and
            self.latitude_ref.get() and
            self.longitude_ref.get()):
            self.process_btn.configure(state=ctk.NORMAL)
        else:
            self.process_btn.configure(state=ctk.DISABLED)
    
    def process_images(self):
        self.master.store.latitude_deg = float(self.latitude_deg.get())
        self.master.store.latitude_ref = self.latitude_ref.get()
        self.master.store.longitude_deg = float(self.longitude_deg.get())
        self.master.store.longitude_ref = self.longitude_ref.get()
        self.master.store.address = self.address.get().strip()
        self.master.store.pic_name = self.pic_name.get().strip()
        self.master.next_screen()
    
    def set_values(self):
        self.latitude_deg.insert(0, "51.59760168")
        self.longitude_deg.insert(0, "0.08291295")
        self.address.insert(0, "17 Neville Road, IG6 2LN")
        self.pic_name.insert(0, "Bathroom 1")
        self.validate_inputs()

class FinalFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.render_widgets()
        self.process_images()
    
    def process_images(self):
        for image_path in self.master.store.images:
            image = Image.open(image_path)
            date = self.master.store.datetime
            latitude = abs(self.master.store.latitude_deg)
            longitude = abs(self.master.store.longitude_deg)
            
            self.imprint_info_on_image(
                image=image,
                date=date.strftime("%d %b %Y  %H:%M:%S"),
                latitude=f"{latitude}{self.master.store.latitude_ref}",
                longitude=f"{longitude}{self.master.store.longitude_ref}",
                address=self.master.store.address,
                pic_name=self.master.store.pic_name,
                filepath=image_path
            )
            exif_bytes = self.build_exif_bytes(dt=date, latitude=latitude, longitude=longitude)
            self.master.store.insert_final_image(image_path=image_path, image=image, exif_bytes=exif_bytes)
        self.download_btn.configure(state=ctk.NORMAL)
    
    def imprint_info_on_image(self, image, date, latitude, longitude, address, filepath, pic_name):
        text = f"{date}\n{latitude} {longitude}\n{address}\n{pic_name}"
        width, height = image.size

        long_line = max(text.split("\n"), key=len)
        font_size = int(width / len(long_line)) * (8 / 7)
        font = ImageFont.truetype("arial.ttf", font_size)
        
        draw = ImageDraw.Draw(image)
        text_width = draw.textlength(long_line, font=font)
        
        while text_width > width - 20:  
            font_size -= 1
            font = ImageFont.truetype("arial.ttf", font_size)
            text_width = draw.textlength(long_line, font=font)

        text_block_height = font.size * len(text.split("\n"))
        position = (10, height - text_block_height - 10)
        draw.text(position, text, font=font, fill="white")
    
    def build_exif_bytes(self, dt, latitude, longitude):
        exif_dict = {
            "0th": {},
            "Exif": {},
            "GPS": {}
        }
        def to_deg(value):
            deg = int(value)
            min = int((value - deg) * 60)
            sec = int((value - deg - min/60) * 3600)
            return (deg, min, sec)
        lat = to_deg(latitude)
        lon = to_deg(longitude)
        
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef] = self.master.store.latitude_ref.encode('utf-8')
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = [(lat[0], 1), (lat[1], 1), (lat[2], 1)]
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = self.master.store.longitude_ref.encode('utf-8')
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = [(lon[0], 1), (lon[1], 1), (lon[2], 1)]

        date_str = dt.strftime('%Y:%m:%d %H:%M:%S')
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = date_str.encode('utf-8')
        exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = date_str.encode('utf-8')
        exif_dict["0th"][piexif.ImageIFD.DateTime] = date_str.encode('utf-8')
        
        exif_bytes = piexif.dump(exif_dict)
        return exif_bytes
    
    def display_image(self, image):
        (width, height) = image.size
        top = ctk.CTkToplevel(self.master)
        top.title("Final Image")
        label = ctk.CTkLabel(top, text="", image=ctk.CTkImage(light_image=image, size=(width, height)))
        label.pack(padx=10, pady=10)
    
    def save_images(self):
        selected_folder = filedialog.askdirectory(title="Select Folder to save images")
        if selected_folder:
            for fi in self.master.store.get_final_images():
                save_path = f"{selected_folder}/{os.path.basename(fi.image_path)}"
                fi.image.save(save_path, quality=100, exif_bytes=fi.exif_bytes)
            
            
    
    def render_widgets(self):
        self.download_btn = ctk.CTkButton(
            master=self,
            text="Download Images",
            command=self.save_images,
            state=ctk.DISABLED
        )
        self.download_btn.place(relx=0.5, rely=0.5, anchor= ctk.CENTER)

class DateTimePicker(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("Pick a Data and Time")
        self.attributes("-topmost", True)
        self.bind("<Destroy>", self.on_destroy)
        
        # Date picker
        self.calendar = Calendar(self)
        self.calendar.pack(padx=10, pady=10)
        
        # Time picker
        self.time_frame = ctk.CTkFrame(self)
        self.time_frame.pack(padx=10, pady=5)
        
        self.current_time = datetime.now().time()
        self.hour_var = ctk.StringVar(value=self.current_time.hour)
        self.minute_var = ctk.StringVar(value=self.current_time.minute)
        
        ctk.CTkLabel(self.time_frame, text="Hour:").grid(row=0, column=0, padx=(0, 10))
        ttk.Spinbox(self.time_frame, from_=0, to=23, textvariable=self.hour_var, width=5).grid(row=0, column=1)
        
        ctk.CTkLabel(self.time_frame, text="Minute:").grid(row=0, column=2, padx=(10, 0))
        ttk.Spinbox(self.time_frame, from_=0, to=59, textvariable=self.minute_var, width=5).grid(row=0, column=3)
        
        ctk.CTkButton(self, text="OK", command=self.on_ok).pack(pady=10)

    def on_ok(self):
        self.destroy()
    
    def on_destroy(self, event):
        if self.hour_var.get() == "":
            self.hour_var.set(self.current_time.hour)
        if self.minute_var.get() == "":
            self.minute_var.set(self.current_time.minute)
        self.date_time = (self.calendar.selection_get(), int(self.hour_var.get()), int(self.minute_var.get()))

if __name__ == "__main__":
    app = App()
    app.mainloop()