from enum import Enum
import customtkinter as ctk
from PIL import Image

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