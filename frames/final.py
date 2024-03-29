import customtkinter as ctk
from customtkinter import filedialog
from PIL import Image, ImageDraw, ImageFont, ImageTk
import piexif
import os
import sys
sys.path.insert(0, "../utils")
from common import FinalImage,Corner, open_image
from datetime import timedelta
import secrets

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
