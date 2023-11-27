import customtkinter as ctk
from customtkinter import ThemeManager
from PIL import Image, ImageTk
from tkinter import Canvas, Scrollbar, PhotoImage
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
            pil_img = Image.open(img_path)
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
