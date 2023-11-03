import customtkinter as ctk
from tkcalendar import Calendar
from datetime import datetime, date, time
import sys
sys.path.insert(0, "../utils")
from common import LatitudeRef, LongitudeRef, FloatEntry, IntSpinbox, Corner

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
