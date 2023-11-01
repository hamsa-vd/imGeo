import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from tkcalendar import Calendar
from datetime import datetime, date, time
import sys
sys.path.insert(0, "../utils")
from common import LatitudeRef, LongitudeRef, FloatEntry

class DetailsFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.render_widgets()
        
    def init_vars(self):
        current_timestamp = datetime.now()
        date = current_timestamp.strftime("%d %b %Y")
        hour = current_timestamp.time().hour
        minute = current_timestamp.time().minute
        self.date_label = ctk.StringVar(value=self.format_datetime(date=date, hour=hour, minute=minute))
        
    def render_widgets(self):
        
        self.init_vars()
        self.render_date_entry_widget()
        self.render_latitude_widget()
        self.render_longitude_widget()
        self.render_address_widget()
        self.render_process_btn()
    
    def render_process_btn(self):
        self.process_btn = ctk.CTkButton(
            master=self,
            text="Process Images",
            state=ctk.DISABLED
        )
        self.process_btn.grid(row = 7, column=0, columnspan=2, pady=(20, 0))
    
    def render_address_widget(self):
        ctk.CTkLabel(
            master=self,
            text="Enter the address",
            anchor="w"
        ).grid(row=5, column=0, sticky="W", pady=(20, 0))
        self.address = ctk.CTkTextbox(master=self)
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
            self.address.get("1.0", "end-1c").strip() and
            self.latitude_ref.get() and
            self.longitude_ref.get()):
            self.process_btn.configure(state=ctk.NORMAL)
        else:
            self.process_btn.configure(state=ctk.DISABLED)
    
    def process_images(self):
        self.master.store.latitude_deg = self.latitude_deg.getdouble()
        self.master.store.latitude_ref = self.latitude_ref.get()
        self.master.store.longitude_deg = self.longitude_deg.getdouble()
        self.master.store.longitude_ref = self.longitude_ref.get()
        self.master.store.address = self.address.get()
        self.master.next_screen()


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