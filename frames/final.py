import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageDraw, ImageFont, ImageTk
import piexif
import os
import sys
sys.path.insert(0, "../utils")
from common import FinalImage

class FinalFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.render_widgets()
        self.process_images()
    
    def process_images(self):
        image = Image.open(self.master.store.images)
        date = self.master.store.datetime
        latitude = abs(self.master.store.latitude_deg)
        longitude = abs(self.master.store.longitude_deg)
        filepath = self.master.store.images
        
        self.imprint_info_on_image(
            image=image,
            date=date.strftime("%d %b %Y  %H:%M:%S"),
            latitude=f"{latitude}{self.master.store.latitude_ref}",
            longitude=f"{longitude}{self.master.store.longitude_ref}",
            address=self.master.store.address,
            pic_name=self.master.store.pic_name,
            filepath=filepath
        )
        exif_bytes = self.build_exif_bytes(dt=date, latitude=latitude, longitude=longitude)
        self.master.store.insert_final_image(image_path=filepath, image=image, exif_bytes=exif_bytes)
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