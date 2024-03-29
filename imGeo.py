import customtkinter as ctk
from customtkinter import filedialog, ThemeManager
from tkinterdnd2 import TkinterDnD, DND_FILES
from tkcalendar import Calendar
from PIL import Image, ImageDraw, ImageFont, ImageTk, ExifTags
import piexif
from datetime import datetime, date, time, timedelta
from typing import List
from enum import Enum
import os
import sys
import secrets

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

def open_image(image_path):
    
    image = Image.open(image_path)
    
    try:
        exif = image._getexif()
        if exif is not None:
            orientation_key = next(key for key, value in ExifTags.TAGS.items() if value == 'Orientation')

            if orientation_key in exif:
                if exif[orientation_key] == 3:
                    image = image.rotate(180, expand=True)
                elif exif[orientation_key] == 6:
                    image = image.rotate(270, expand=True)
                elif exif[orientation_key] == 8:
                    image = image.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        pass

    return image

class Store:
    _instance = None
    current_screen: Screen = Screen.HOME
    images: List[str] = []
    _final_images: List[FinalImage] = []
    datetime: datetime = None
    latitude_deg: float = None
    latitude_ref: str = LatitudeRef.N.value
    longitude_deg: float = None
    longitude_ref: str = LongitudeRef.E.value
    address: str = None
    pic_name: str = None
    from_minutes: int = 0
    to_minutes: int = 0
    corner: Corner = Corner.BOTTOM_RIGHT
    font_size: int = 0
    
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
        self.images = []
        self._final_images = []
        self.datetime = None
        self.latitude_deg = None
        self.latitude_ref = LatitudeRef.N.value
        self.longitude_deg = None
        self.longitude_ref = LongitudeRef.E.value
        self.address = None
        self.pic_name = None
        self.from_minutes = 0
        self.to_minutes = 0
        self.corner = Corner.BOTTOM_RIGHT
        self.font_size = 0

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
        
        if len(self.master.store.images) != 0:
            self.update_count_label(len(self.master.store.images))
            self.show_go_btn()


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
        self.validate_inputs()
        # self.set_values()
    
    def render_process_btn(self):
        
        self.arrage_image_btn = ctk.CTkButton(
            master=self,
            text="Reorder Images",
            command=self.reorder_images
        )
        self.arrage_image_btn.grid(row= self.current_row, column=0, pady=(20, 0))
        
        self.process_btn = ctk.CTkButton(
            master=self,
            text="Process Images",
            command=self.process_images,
            state=ctk.DISABLED
        )
        self.process_btn.grid(row = self.current_row, column=1, pady=(20, 0))

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
        if self.master.store.pic_name is not None:
            self.pic_name.insert(0, self.master.store.pic_name)
        
        ctk.CTkLabel(
            master=self,
            text="Select Corner",
            anchor="w"
        ).grid(row=self.current_row, column=1, sticky="W", pady=(20, 0), padx=(10, 0))
        self.corner = ctk.CTkComboBox(master=self, values=Corner.values(), state='readonly')
        self.corner.set(self.master.store.corner.value)
        self.corner.grid(row=self.current_row+1, column=1, sticky="W", padx=(10, 0))
        self.current_row += 2
    
    def render_address_widget(self):
        ctk.CTkLabel(
            master=self,
            text="Enter the address",
            anchor="w"
        ).grid(row=self.current_row, column=0, sticky="W", pady=(20, 0))
        self.address = ctk.CTkEntry(master=self, placeholder_text="Adress here...")
        self.address.grid(row=self.current_row + 1, column=0, sticky="EW")
        self.address.bind("<KeyRelease>", lambda e: self.validate_inputs())
        if self.master.store.address is not None:
            self.address.insert(0, self.master.store.address)
        
        initial_font_size = 0
        if self.master.store.font_size != 0:
            initial_font_size = self.master.store.font_size 
        ctk.CTkLabel(
            master=self,
            text="Font Size",
            anchor="w"
        ).grid(row=self.current_row, column=1, sticky="W", pady=(20, 0), padx=(10, 0))
        self.font_size = IntSpinbox(master=self, from_=0, to=200, initial_val=initial_font_size)
        self.font_size.grid(row=self.current_row+1, column=1, sticky="W", padx=(10, 0))
        
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
        if self.master.store.longitude_deg is not None:
            self.longitude_deg.insert(0, self.master.store.longitude_deg)

        
        self.longitude_ref = ctk.CTkComboBox(master=self, values=LongitudeRef.values(), width=80, state='readonly')
        self.longitude_ref.set(self.master.store.longitude_ref)
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
        if self.master.store.latitude_deg is not None:
            self.latitude_deg.insert(0, self.master.store.latitude_deg)
        
        self.latitude_ref = ctk.CTkComboBox(master=self, values=LatitudeRef.values(), width=80, state='readonly')
        self.latitude_ref.set(self.master.store.latitude_ref)
        self.latitude_ref.grid(row=self.current_row+1, column=1, padx=(10, 0), sticky="W")
        self.current_row += 2
    
    def render_from_to_minutes_widget(self):
        from_minute_frame = ctk.CTkFrame(self, fg_color='transparent')
        from_minute_frame.grid(row=self.current_row, column=0, pady=(20, 0), sticky="EW")
        
        from_min_initial_val = 1
        if self.master.store.from_minutes != 0:
            minute_initial_val = self.master.store.from_minutes
        ctk.CTkLabel(master=from_minute_frame, text="From mins").pack(padx=(0, 10), side=ctk.LEFT)
        self.from_minutes_box = IntSpinbox(master=from_minute_frame, from_=0, to=2, initial_val=from_min_initial_val, command=self.from_minutes_updated)
        self.from_minutes_box.pack(side=ctk.LEFT)
        
        to_minute_frame = ctk.CTkFrame(self, fg_color='transparent')
        to_minute_frame.grid(row=self.current_row, column=1, pady=(20, 0), sticky='W')
        
        to_min_initial_val = 2
        if self.master.store.to_minutes != 0:
            to_min_initial_val = self.master.store.to_minutes
        ctk.CTkLabel(master=to_minute_frame, text="To mins").pack(padx=10, side=ctk.LEFT)
        self.to_minutes_box = IntSpinbox(master=to_minute_frame, from_=1, to=60, initial_val=to_min_initial_val, command=self.to_minutes_updated)
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
    
    def save(self):
        if self.latitude_deg.get() and self.latitude_deg.get() != "":
            self.master.store.latitude_deg = float(self.latitude_deg.get())
        self.master.store.latitude_ref = self.latitude_ref.get()
        if self.longitude_deg.get() and self.longitude_deg.get() != "":
            self.master.store.longitude_deg = float(self.longitude_deg.get())
        self.master.store.longitude_ref = self.longitude_ref.get()
        if self.address.get() and self.address.get().strip() != "":
            self.master.store.address = self.address.get().strip()
        if self.pic_name.get() and self.pic_name.get().strip() != "":
            self.master.store.pic_name = self.pic_name.get().strip()
        self.master.store.font_size = int(self.font_size.get())
        self.master.store.corner = Corner.from_string(self.corner.get())
        self.master.store.from_minutes = int(self.from_minutes_box.get())
        self.master.store.to_minutes = int(self.to_minutes_box.get())
    
    def process_images(self):
        self.master.configure(cursor="watch")
        self.save()
        self.master.next_screen()
    
    def reorder_images(self):
        ImagesGrid(parent=self.master)
    
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

class ImagesGrid(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.attributes('-topmost', True)
        self.minsize(width=750, height=600)
        
        self.master = parent
        self.img_indices_order = list(range(len(parent.store.images)))
        
        self.image_labels = []
        self.image_number_labels = []
        self.selected_image_label = None
        self.filled_col = None
        self.selected_image_idx = None
        
        self.selected_image_labels = set()
        self.selected_image_indices = set()
        
        appearance_mode = ctk.get_appearance_mode()
        fg_color = ThemeManager().theme['CTkFrame']['fg_color'][1 if appearance_mode == 'Dark' else 0]

        self.canvas = ctk.CTkCanvas(master=self, bg=fg_color, borderwidth=0, highlightthickness=0)
        self.scrollbar = ctk.CTkScrollbar(master=self, orientation="vertical", command=self.canvas.yview)
        self.scrollable_frame = ctk.CTkFrame(master=self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        self.bind("<MouseWheel>", self.on_mouse_wheel)
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.scrollbar.pack(side="right", fill="y")

        self.bind("<Configure>", self.on_resize)
        self.canvas.bind("<Configure>", self.on_canvas_resize)

        self.render_actions(master=self.scrollable_frame)
        self.load_images(parent.store.images)
    
    def on_mouse_wheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def get_label(self, frame):
        return frame.children['!label']

    def select_label(self, sel_idx):
        self.get_label(self.image_labels[sel_idx]).configure(borderwidth=5, relief=ctk.RIDGE)
        self.selected_image_indices.add(sel_idx)
        
    def deselect_label(self, sel_idx):
        self.selected_image_indices.remove(sel_idx)
        self.get_label(self.image_labels[sel_idx]).configure(borderwidth=5, relief=ctk.FLAT)
    
    def deselect_all(self):
        for sel_idx in list(self.selected_image_indices):
            self.deselect_label(sel_idx)
        self.selected_image_indices = set()
    
    def render_actions(self, master):
        self.action_frame = ctk.CTkFrame(master=master, fg_color='transparent')
        self.action_frame.grid(row=0,column=0, pady=10)
        
        self.start_index_entry = IntSpinbox(master=self.action_frame)
        self.start_index_entry.pack(side=ctk.LEFT)
        
        self.rearrange_btn = ctk.CTkButton(master=self.action_frame, text="Rearrange", command=self.rearrange)
        self.rearrange_btn.pack(side=ctk.LEFT, padx=10)
        
        self.done_btn = ctk.CTkButton(master=self.action_frame, text="Done", command=self.on_done)
        self.done_btn.pack(side=ctk.RIGHT)
        
        self.reverse_btn = ctk.CTkButton(master=self.action_frame, text="Reverse", command=self.reverse_images)
        self.reverse_btn.pack(side=ctk.RIGHT, padx=10)
        
        self.deselect_all_btn = ctk.CTkButton(master=self.action_frame, text="Deselect All", command=self.deselect_all)
        self.deselect_all_btn.pack(side=ctk.RIGHT, padx=(10,0))
        
        self.delete_btn = ctk.CTkButton(master=self.action_frame, text='Delete', command=self.delete_images)
        self.delete_btn.pack(side=ctk.RIGHT)
        
    
    def rearrange(self):
        to_index = self.start_index_entry.get()
        if to_index == 0 or len(self.selected_image_indices) == 0:
            return
        
        final_indices_order = []
        final_image_labels = []
        final_indices = set()
        sorted_indices = sorted(self.selected_image_indices)
        current_image_len = len(self.image_labels)
        
        def addFromIndices(current_idx):
            new_idx = current_idx
            for i in sorted_indices:
                final_indices_order.append(self.img_indices_order[i])
                final_image_labels.append(self.image_labels[i])
                final_indices.add(new_idx)
                new_idx += 1
        
        for idx in range(0, current_image_len):
            if to_index - 1 == idx:
                addFromIndices(len(final_image_labels))
            if idx in sorted_indices:
                continue
            final_indices_order.append(self.img_indices_order[idx])
            final_image_labels.append(self.image_labels[idx])
            
        if len(final_indices) == 0:
            addFromIndices(len(final_image_labels))
        
        self.img_indices_order = final_indices_order
        self.image_labels = final_image_labels
        self.selected_image_indices = final_indices
        self.display_images()
    
    def delete_images(self):
        deleted_images_count = 0
        for sel_idx in list(self.selected_image_indices):
            self.img_indices_order.pop(sel_idx - deleted_images_count)
            self.image_labels.pop(sel_idx - deleted_images_count).grid_forget()
            self.image_number_labels.pop(sel_idx - deleted_images_count).grid_forget()
            deleted_images_count += 1
        
        self.start_index_entry.configure(to=len(self.image_labels)+1)
        self.selected_image_indices = set()
        self.display_images()
    
    def reverse_images(self):
        if len(self.selected_image_indices) in [0,1] :
            self.img_indices_order.reverse()
            self.image_labels.reverse()
            self.display_images()
            return
        sorted_list = sorted(self.selected_image_indices)
        required_order = []
        check = sorted_list[-2]
        for idx in range(len(self.image_labels)):
            if idx in sorted_list:
                required_order.append(sorted_list[-(sorted_list.index(idx)+1)])
            else:
                required_order.append(idx)
        self.img_indices_order = [self.img_indices_order[idx] for idx in required_order]
        self.image_labels = [self.image_labels[idx] for idx in required_order]
        self.display_images()
    
    def on_done(self):
        self.master.store.images = [ self.master.store.images[idx] for idx in self.img_indices_order ]
        self.destroy()
    
    def on_canvas_resize(self, event):
        canvas_width = event.width
        self.canvas.itemconfig(1, width=canvas_width)
    
    def load_images(self, images):
        for index, img_path in enumerate(images):
            pil_img = open_image(img_path)
            pil_img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(pil_img)
            label = ctk.CTkLabel(master=self.scrollable_frame, image=tk_img, text="")
            label.image = tk_img
            label.bind("<Button-1>", lambda event, idx=index: self.on_click_image(event, idx))
            # label.bind("<B1-Motion>", self.on_drag_image)
            # label.bind("<ButtonRelease-1>", self.on_drop_image)
            self.image_labels.append(label)
            
            num_label = ctk.CTkLabel(master=self.scrollable_frame, text=str(index + 1))
            self.image_number_labels.append(num_label)
        
        self.start_index_entry.configure(to=index+2)
        self.display_images()

    def on_click_image(self, event, idx): 
        ctrl_pressed = event.state & 0x0004 != 0
        shift_pressed = event.state & 0x0001 != 0
        if event.widget.widgetName != 'label':
            return
        
        if idx in self.selected_image_indices:
            self.deselect_label(idx)
            return
        
        if shift_pressed: 
            range_start = None
            if len(self.selected_image_indices) == 0:
                indices_range = range(0, idx+1)
            elif min(self.selected_image_indices) > idx:
                indices_range = range(idx, min(self.selected_image_indices))
            else:
                for selected_idx in range(idx, -1, -1):
                    if selected_idx in list(self.selected_image_indices):
                        indices_range = range(selected_idx, idx+1)
                        break
            for sel_idx in indices_range:
                self.select_label(sel_idx)
        elif ctrl_pressed:
            self.select_label(idx)
        else:
            for sel_idx in list(self.selected_image_indices):
                self.deselect_label(sel_idx)
            self.selected_image_indices = {idx}
            self.select_label(idx)


    def display_images(self):
        for label in self.image_labels:
            label.grid_forget()
        for num_label in self.image_number_labels:
            num_label.grid_forget()
        
        row, col = 1, 0
        for idx, label in enumerate(self.image_labels):
            label.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            current_label = self.get_label(label)
            current_label.bind("<Button-1>", lambda event, idx=idx: self.on_click_image(event, idx))
            current_label.configure(borderwidth=5)
            self.image_number_labels[idx].grid(row=row + 1, column=col, padx=5, pady=5)
            self.image_number_labels[idx].configure(text=str(idx + 1))
            col += 1
            if (col * 300 + 150) >= self.winfo_width():
                self.filled_col = col
                col = 0
                row += 2  # Increment by 2 to account for image number labels
        if self.filled_col is None or col > self.filled_col:
            self.filled_col = col
        self.action_frame.grid(row=0, column=0, columnspan=self.filled_col, padx=10, pady=20, sticky=ctk.EW)

    def on_resize(self, event):
        
        if ( self.filled_col is None or 
            ((self.filled_col) * 300 < self.winfo_width()) or
            ((self.filled_col - 1) * 300 > self.winfo_width())
            ):
            self.display_images()

class FinalFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.render_widgets()
        self.process_images()

    def secure_random_number(self, start, end):
        return secrets.randbelow(end - start) + start
    
    def process_images(self):
        last_datetime = self.master.store.datetime.replace(second=self.secure_random_number(0, 60))
        for image_path in self.master.store.images:
            image = open_image(image_path)
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
                corner=self.master.store.corner,
                font_s=self.master.store.font_size
            )
            exif_bytes = self.build_exif_bytes(dt=date, latitude=latitude, longitude=longitude)
            self.master.store.insert_final_image(image_path=image_path, image=image, exif_bytes=exif_bytes)
        self.master.configure(cursor="")
        self.download_btn.configure(state=ctk.NORMAL)
    
    def randomize_last_three_decimals(self, value):
        value_str = f"{value:.8f}"
        whole_part, decimal_part = value_str.split('.')
        first_five_decimals = decimal_part[:5]
        last_three_random = f"{self.secure_random_number(0, 999):03d}"
        new_value_str = f"{whole_part}.{first_five_decimals}{last_three_random}"
        return float(new_value_str)
    
    def get_rand_datetime(self, last):
        random_minutes = self.secure_random_number(self.master.store.from_minutes, self.master.store.to_minutes)
        random_seconds = self.secure_random_number(0, 60)
        return last.replace(second=random_seconds) + timedelta(minutes=random_minutes)
    
    def imprint_info_on_image(self, image, date, latitude, longitude, address, filepath, pic_name, corner, font_s):
        text = f"{date}\n{latitude} {longitude}\n{address}"
        if pic_name is not None and pic_name != "":
            text += f"\n{pic_name}"
        width, height = image.size

        ratio = 8 / 7
        if (width / height) > 1.25:
            ratio = 5 / 7
        if (height / width) > 1.4:
            ratio = 10 / 7

        long_line = max(text.split("\n"), key=len)
        font_size = int((width / len(long_line)) * ratio)
        font = ImageFont.truetype("arial.ttf", font_size)
        
        draw = ImageDraw.Draw(image)
        text_width = draw.textlength(long_line, font=font)
        
        while text_width > width - 20:  
            font_size -= 1
            font = ImageFont.truetype("arial.ttf", font_size)
            text_width = draw.textlength(long_line, font=font)
        
        if(font_s != 0):
            font = ImageFont.truetype("arial.ttf", font_s)

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

        self.title("imGeo")
        # self.iconbitmap("./assets/imGeo.ico")
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
        if self.store.current_screen == Screen.DETAILS:
            self.details_frame.save()
        if self.store.current_screen == Screen.FINAL:
            self.store.reset()
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