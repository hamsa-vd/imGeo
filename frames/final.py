import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont, ImageTk
import os

class FinalFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.process_images()
        self.render_widgets()
    
    def process_images(self):
        image = Image.open(self.master.store.images)
        date = self.master.store.datetime.strftime("%d %b %Y %H:%M:%S")
        latitude = f"{self.master.store.latitude_deg} {self.master.store.latitude_ref}"
        longitude = f"{self.master.store.longitude_deg} {self.master.store.longitude_ref}"
        self.imprint_info_on_image(
            image=image,
            date=date,
            latitude=latitude,
            longitude=longitude,
            address=self.master.store.address,
            filepath=self.master.store.images
        )
        
    
    def imprint_info_on_image(self, image, date, latitude, longitude, address, filepath):
        text = f"{date}\n{latitude} {longitude}\n{address}"
        width, height = image.size

        long_line = max(text.split("\n"), key=len)
        font_size = int(width / len(long_line))
        font = ImageFont.truetype("arial.ttf", font_size)
        
        draw = ImageDraw.Draw(image)
        text_width = draw.textlength(long_line, font=font)
        
        while text_width > width - 20:  
            font_size -= 1
            font = ImageFont.truetype("arial.ttf", font_size)
            text_width = draw.textlength(long_line, font=font)

        position = ((width - text_width) / 2, height - (font.size * len(text.split("\n"))) - 10)
        draw.text(position, text, font=font, fill="white")
        
        top = ctk.CTkToplevel(self.master)
        top.title("Final Image")
        label = ctk.CTkLabel(top, text="", image=ctk.CTkImage(light_image=image, size=(width, height)))
        label.pack(padx=10, pady=10)
    
    def render_widgets(self):
        self.download_btn = ctk.CTkButton(
            master=self,
            text="Download Images",
            state=ctk.DISABLED
        )
        self.download_btn.place(relx=0.5, rely=0.5, anchor= ctk.CENTER)