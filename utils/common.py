from enum import Enum
import customtkinter as ctk
from PIL import Image, ExifTags
import sys

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
