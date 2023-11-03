import customtkinter as ctk
from customtkinter import filedialog
from tkinterdnd2 import TkinterDnD, DND_FILES
from tkcalendar import Calendar
from PIL import Image, ImageDraw, ImageFont, ImageTk
import piexif
from datetime import datetime, date, time, timedelta
from typing import List
from enum import Enum
import os
import sys
import random

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

class Corner(Enum):
    TOP_LEFT="Top Left"
    TOP_RIGHT="Top Right"
    BOTTOM_LEFT="Bottom Left"
    BOTTOM_RIGHT="Bottom Right"
    
    @classmethod
    def values(self):
        return [el.value for el in self]
    
    @classmethod
    def from_string(self, val):
        for mem in self:
            if mem.value == val:
                return mem
        return val
class FloatEntry(ctk.CTkEntry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configure(validate="all", validatecommand=(self.register(self.validate),'%P'))

    def validate(self, text):
        if not text:
            return True
        try:
            value = float(text)
        except ValueError:
            return False
        return 0 <= value <= 90

class FinalImage:
    image_path: str
    image: Image.Image
    exif_bytes: bytes
    
    def __init__(self, image_path: str, image: Image.Image, exif_bytes: bytes):
        self.image_path = image_path
        self.image = image
        self.exif_bytes = image

class IntSpinbox(ctk.CTkFrame):
    def __init__(self, *args,
                 width: int = 100,
                 height: int = 32,
                 step_size: int = 1,
                 command = None,
                 from_: int = 0,
                 to: int = sys.maxsize,
                 initial_val: int = 0,
                 **kwargs):
        super().__init__(*args, width=width, height=height, **kwargs)

        self.step_size = step_size
        self.command = command
        self.min = from_
        self.max = to

        self.configure(fg_color=("gray78", "gray28"))  # set frame color

        self.grid_columnconfigure((0, 2), weight=0)  # buttons don't expand
        self.grid_columnconfigure(1, weight=1)  # entry expands

        self.subtract_button = ctk.CTkButton(self, text="-", width=height-6, height=height-6,
                                                       command=self.subtract_button_callback)
        self.subtract_button.grid(row=0, column=0, padx=(3, 0), pady=3)

        self.entry = ctk.CTkEntry(self, width=width-(2*height), height=height-6, border_width=0, justify='center', validate="key", validatecommand=(self.register(self.validate), '%P'))
        self.entry.grid(row=0, column=1, columnspan=1, padx=3, pady=3, sticky="ew")

        self.add_button = ctk.CTkButton(self, text="+", width=height-6, height=height-6,
                                                  command=self.add_button_callback)
        self.add_button.grid(row=0, column=2, padx=(0, 3), pady=3)

        # default value
        self.entry.insert(0, str(initial_val))
    
    def validate(self, inp):
        if not inp:
            return True
        try:
            value = int(inp)
        except ValueError:
            return False
        return self.min <= value <= self.max

    def add_button_callback(self):
        try:
            if self.entry.get() == "":
                value = 0
            else:
                value = int(self.entry.get()) + self.step_size
            if value > self.max:
                self.add_button.configure(state=ctk.DISABLED)
                return
            self.subtract_button.configure(state=ctk.NORMAL)
            self.entry.delete(0, "end")
            self.entry.insert(0, value)
            
            if self.command is not None:
                self.command()
        except ValueError:
            return

    def subtract_button_callback(self):
        try:
            if self.entry.get() == "":
                self.subtract_button.configure(state=ctk.DISABLED)
                value = 0
            else:
                value = int(self.entry.get()) - self.step_size
            if value < self.min:
                self.subtract_button.configure(state=ctk.DISABLED)
                return
            self.add_button.configure(state=ctk.NORMAL)
            self.entry.delete(0, "end")
            self.entry.insert(0, value)
            if self.command is not None:
                self.command()
        except ValueError:
            return

    def get(self):
        try:
            value = int(self.entry.get())
        except ValueError:
            return None
        return value
    
    def set(self, value: int):
        self.entry.delete(0, "end")
        self.entry.insert(0, str(int(value)))
    
    def configure(self, **kwargs):
        from_ = kwargs.pop('from_', None)
        to = kwargs.pop('to', None)
        
        if from_ is not None:
            self.min = from_
            if int(self.entry.get()) > from_:
                self.subtract_button.configure(state=ctk.NORMAL)
        if to is not None:
            self.max = to
            if int(self.entry.get()) < to:
                self.add_button.configure(state=ctk.NORMAL)
        super().configure(**kwargs)

class Store:
    _instance = None
    current_screen: Screen = Screen.HOME
    images: List[str] = []
    _final_images: List[FinalImage] = []
    datetime: datetime = None
    latitude_deg: float = None
    latitude_ref: LatitudeRef = LatitudeRef.N
    longitude_deg: float = None
    longitude_ref: LongitudeRef = LongitudeRef.E
    address: str = None
    pic_name: str = None
    from_minutes: int = 0
    to_minutes: int = 0
    corner: Corner = Corner.BOTTOM_RIGHT
    
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
            },
            "address": self.address
        }
        
    def insert_final_image(self, image_path: str, image: Image.Image, exif_bytes: bytes):
        self._final_images.append(FinalImage(image_path=image_path, image=image, exif_bytes=exif_bytes))
        
    def get_final_images(self):
        return self._final_images

    def __repr__(self):
        return self.get_dict()
    
    def reset(self):
        self._instance = Store()

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
        self.current_row = 0
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
        self.render_from_to_minutes_widget()
        self.render_latitude_widget()
        self.render_longitude_widget()
        self.render_address_widget()
        self.render_pic_name_corner_widget()
        self.render_process_btn()
        # self.set_values()
    
    def render_process_btn(self):
        self.process_btn = ctk.CTkButton(
            master=self,
            text="Process Images",
            command=self.process_images,
            state=ctk.DISABLED
        )
        self.process_btn.grid(row = self.current_row, column=0, columnspan=2, pady=(20, 0))
        self.current_row += 1
    
    def render_pic_name_corner_widget(self):
        ctk.CTkLabel(
            master=self,
            text="Enter the Pic Name",
            anchor="w"
        ).grid(row=self.current_row, column=0, sticky="W", pady=(20, 0))
        self.pic_name = ctk.CTkEntry(master=self, placeholder_text="Pic name here...")
        self.pic_name.grid(row=self.current_row+1, column=0, sticky="EW")
        self.pic_name.bind("<KeyRelease>", lambda e: self.validate_inputs())
        
        ctk.CTkLabel(
            master=self,
            text="Select Corner",
            anchor="w"
        ).grid(row=self.current_row, column=1, sticky="W", pady=(20, 0), padx=(10, 0))
        self.corner = ctk.CTkComboBox(master=self, values=Corner.values(), state='readonly')
        self.corner.set(Corner.BOTTOM_RIGHT.value)
        self.corner.grid(row=self.current_row+1, column=1, sticky="W", padx=(10, 0))
        self.current_row += 2
    
    def render_address_widget(self):
        ctk.CTkLabel(
            master=self,
            text="Enter the address",
            anchor="w"
        ).grid(row=self.current_row, column=0, sticky="W", pady=(20, 0))
        self.address = ctk.CTkEntry(master=self, placeholder_text="Adress here...")
        self.address.grid(row=self.current_row + 1, column=0, columnspan=2, sticky="EW")
        self.address.bind("<KeyRelease>", lambda e: self.validate_inputs())
        self.current_row += 2
    
    
    def render_longitude_widget(self):
        ctk.CTkLabel(
            master=self,
            text="Longitude Details",
            anchor="w"
        ).grid(row=self.current_row, column=0, sticky="W", pady=(20, 0))
        self.longitude_deg = FloatEntry(
            master=self, 
            placeholder_text="Longitude Degree",
            width=200
        )
        self.longitude_deg.grid(row=self.current_row + 1, column=0, sticky="W")
        self.longitude_deg.bind("<KeyRelease>", lambda e: self.validate_inputs())

        
        self.longitude_ref = ctk.CTkComboBox(master=self, values=LongitudeRef.values(), width=80, state='readonly')
        self.longitude_ref.set(LongitudeRef.E.value)
        self.longitude_ref.grid(row=self.current_row + 1, column=1, padx=(10, 0), sticky="W")
        self.current_row += 2
    
    def render_latitude_widget(self):
        ctk.CTkLabel(
            master=self,
            text="Latitude Details",
            anchor="w"
        ).grid(row=self.current_row, column=0, sticky="W", pady=(20, 0))
        self.latitude_deg = FloatEntry(
            master=self, 
            placeholder_text="Latitude Degree",
            width=200
        )
        self.latitude_deg.grid(row=self.current_row+1, column=0, sticky="W")
        self.latitude_deg.bind("<KeyRelease>", lambda e: self.validate_inputs())
        
        self.latitude_ref = ctk.CTkComboBox(master=self, values=LatitudeRef.values(), width=80, state='readonly')
        self.latitude_ref.set(LatitudeRef.N.value)
        self.latitude_ref.grid(row=self.current_row+1, column=1, padx=(10, 0), sticky="W")
        self.current_row += 2
    
    def render_from_to_minutes_widget(self):
        from_minute_frame = ctk.CTkFrame(self, fg_color='transparent')
        from_minute_frame.grid(row=self.current_row, column=0, pady=(20, 0), sticky="EW")
        
        ctk.CTkLabel(master=from_minute_frame, text="From mins").pack(padx=(0, 10), side=ctk.LEFT)
        self.from_minutes_box = IntSpinbox(master=from_minute_frame, from_=0, to=2, initial_val=1, command=self.from_minutes_updated)
        self.from_minutes_box.pack(side=ctk.LEFT)
        
        to_minute_frame = ctk.CTkFrame(self, fg_color='transparent')
        to_minute_frame.grid(row=self.current_row, column=1, pady=(20, 0), sticky='W')
        ctk.CTkLabel(master=to_minute_frame, text="To mins").pack(padx=10, side=ctk.LEFT)
        self.to_minutes_box = IntSpinbox(master=to_minute_frame, from_=1, to=60, initial_val=2, command=self.to_minutes_updated)
        self.to_minutes_box.pack(side= ctk.LEFT)
        self.current_row += 1
    
    def render_date_entry_widget(self):
        ctk.CTkButton(
            master=self,
            corner_radius=5,
            text="Pick date and time", 
            command=self.pick_datetime
        ).grid(row=self.current_row, column=0, pady=10, sticky="W")
        ctk.CTkLabel(master=self, textvariable=self.date_label).grid(row=self.current_row, column=1, padx=10, pady=10, sticky="W")
        self.current_row += 1
        
    def format_datetime(self, date, hour, minute):
        return f"Selected: {date} {hour:02}:{minute:02}"
    
    def pick_datetime(self):
        selected_dt = datetime.now()
        if self.master.store.datetime is not None:
            selected_dt = self.master.store.datetime
        picker = DateTimePicker(parent=self.master, dt=selected_dt)
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
            self.latitude_ref.get() and
            self.longitude_ref.get() and
            self.corner.get()):
            self.process_btn.configure(state=ctk.NORMAL)
        else:
            self.process_btn.configure(state=ctk.DISABLED)
    
    def to_minutes_updated(self):
        to_minutes = self.to_minutes_box.get()
        self.from_minutes_box.configure(to=int(to_minutes))
    
    def from_minutes_updated(self):
        from_minutes = self.from_minutes_box.get()
        self.to_minutes_box.configure(from_=int(from_minutes))
    
    def process_images(self):
        self.master.store.latitude_deg = float(self.latitude_deg.get())
        self.master.store.latitude_ref = self.latitude_ref.get()
        self.master.store.longitude_deg = float(self.longitude_deg.get())
        self.master.store.longitude_ref = self.longitude_ref.get()
        self.master.store.address = self.address.get().strip()
        if self.pic_name.get() and self.pic_name.get().strip() != "":
            self.master.store.pic_name = self.pic_name.get().strip()
        self.master.store.corner = Corner.from_string(self.corner.get())
        self.master.store.from_minutes = int(self.from_minutes_box.get())
        self.master.store.to_minutes = int(self.to_minutes_box.get())
        self.master.next_screen()
    
    def set_values(self):
        self.latitude_deg.insert(0, "51.59760168")
        self.longitude_deg.insert(0, "0.08291295")
        self.address.insert(0, "17 Neville Road, IG6 2LN")
        self.pic_name.insert(0, "Bathroom 1")
        self.validate_inputs()


class DateTimePicker(ctk.CTkToplevel):
    def __init__(self, parent, dt=datetime.now()):
        super().__init__(parent)
        
        self.title("Pick a Data and Time")
        self.attributes("-topmost", True)
        self.minsize(width=360, height=360)
        self.geometry("360x360")
        self.maxsize(width=360, height=360)
        self.bind("<Destroy>", self.on_destroy)
        
        self.dt = dt
        self.date_time = None
        self.current_time = dt.time()
        
        # Date picker
        self.calendar = Calendar(self)
        self.calendar.pack(padx=20, pady=20, fill='both', expand=True)
        self.calendar.selection_set(dt)
        
        # Time picker
        self.time_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.time_frame.pack(padx=10, pady=5)
        
        # self.hour_var = ctk.StringVar(value=self.current_time.hour)
        # self.minute_var = ctk.StringVar(value=self.current_time.minute)
        
        ctk.CTkLabel(self.time_frame, text="Hour:").grid(row=0, column=0, padx=(0, 10))
        
        
        self.hour_box = IntSpinbox(master=self.time_frame, from_=0, to=23, initial_val=self.current_time.hour)
        self.hour_box.grid(row=0, column=1)
        # ttk.Spinbox(self.time_frame, from_=0, to=23, textvariable=self.hour_var, width=5, validate='key', validatecommand=(self.register(self.validate_hours), '%P'))
        
        ctk.CTkLabel(self.time_frame, text="Minute:").grid(row=0, column=2, padx=(20, 10))
        self.minute_box = IntSpinbox(master=self.time_frame, from_=0, to=60, initial_val=self.current_time.minute)
        self.minute_box.grid(row=0, column=3)
        # ttk.Spinbox(self.time_frame, from_=0, to=59, textvariable=self.minute_var, width=5, validate='key', validatecommand=(self.register(self.validate_minutes, '%P'))).grid(row=0, column=3)
        
        ctk.CTkButton(self, text="OK", command=self.on_ok).pack(pady=10)

    def validate_hours(self, P):
        if P.strip() == "" or (P.isdigit() and int(P) in range(0, 24)):
            return True
        else:
            return False
    
    def validate_minutes(self, P):
        if P.strip() == "" or (P.isdigit() and int(P) in range(0, 60)):
            return True
        else:
            return False

    def on_ok(self):
        if self.hour_box.get() == "":
            self.hour_box.set(self.current_time.hour)
        if self.minute_box.get() == "":
            self.minute_box.set(self.current_time.minute)

        self.date_time = (self.calendar.selection_get(), int(self.hour_box.get()), int(self.minute_box.get()))
        self.destroy()
    
    def on_destroy(self, event):
        if self.date_time is None:
            self.date_time = (self.dt.date(), self.dt.time().hour, self.dt.time().minute)

class FinalFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.render_widgets()
        self.process_images()
    
    def process_images(self):
        last_datetime = self.master.store.datetime.replace(second=random.randint(0, 60))
        for image_path in self.master.store.images:
            image = Image.open(image_path)
            date = last_datetime
            last_datetime = self.get_rand_datetime(last_datetime)
            latitude = self.randomize_last_three_decimals(abs(self.master.store.latitude_deg))
            longitude = self.randomize_last_three_decimals(abs(self.master.store.longitude_deg))
            
            self.imprint_info_on_image(
                image=image,
                date=date.strftime("%d %b %Y  %H:%M:%S"),
                latitude=f"{latitude}{self.master.store.latitude_ref}",
                longitude=f"{longitude}{self.master.store.longitude_ref}",
                address=self.master.store.address,
                pic_name=self.master.store.pic_name,
                filepath=image_path,
                corner=self.master.store.corner
            )
            exif_bytes = self.build_exif_bytes(dt=date, latitude=latitude, longitude=longitude)
            self.master.store.insert_final_image(image_path=image_path, image=image, exif_bytes=exif_bytes)
        self.download_btn.configure(state=ctk.NORMAL)
    
    def randomize_last_three_decimals(self, value):
        value_str = f"{value:.8f}"
        whole_part, decimal_part = value_str.split('.')
        first_five_decimals = decimal_part[:5]
        last_three_random = f"{random.randint(0, 999):03d}"
        new_value_str = f"{whole_part}.{first_five_decimals}{last_three_random}"
        return float(new_value_str)
    
    def get_rand_datetime(self, last):
        random_minutes = random.randint(self.master.store.from_minutes, self.master.store.to_minutes)
        random_seconds = random.randint(0, 60)
        return last.replace(second=random_seconds) + timedelta(minutes=random_minutes)
    
    def imprint_info_on_image(self, image, date, latitude, longitude, address, filepath, pic_name, corner):
        text = f"{date}\n{latitude} {longitude}\n{address}"
        if pic_name is not None and pic_name != "":
            text += f"\n{pic_name}"
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
        if corner == Corner.TOP_LEFT:
            position = (10, 10)
        elif corner == Corner.TOP_RIGHT:
            position = (width - text_width - 10, 10)
        elif corner == Corner.BOTTOM_LEFT:
            position = (10, height - text_block_height - 10)
        else:
            position = (width - text_width - 10, height - text_block_height - 10)
        # position = (10, height - text_block_height - 10)
        
        # rectangle_position = (position[0] - 10, position[1] - 10, position[0] + text_width + 10, position[1] + text_block_height + 10)
        # rectangle = Image.new('RGBA', image.size, (0, 0, 0, 0))
        # rectangle_draw = ImageDraw.Draw(rectangle)
        # rectangle_draw.rectangle(rectangle_position, fill=(0, 0, 0, 64)) 
        # image.paste(rectangle, mask=rectangle)
        
        lines = text.split("\n")
        y_text = position[1]
        for line in lines:
            line_width = draw.textlength(line, font=font)
            line_height = font.size
            if corner in [Corner.TOP_RIGHT, Corner.BOTTOM_RIGHT]:
                x_text = width - line_width - 10
            else:
                x_text = position[0]
            draw.text((x_text, y_text), line, font=font, fill="white")
            y_text += line_height
        
        # draw.text(position, text, font=font, fill="white")
    
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
        self.home_btn.pack(padx=10, pady=10, anchor=ctk.NW)

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

if __name__ == "__main__":
    app = App()
    app.mainloop()