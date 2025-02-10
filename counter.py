import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import csv
import time
import winsound
import platform

class AdvancedCounter(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Advanced Counter")
        self.geometry("800x600")
        self.configure(padx=20, pady=20)
        # State management
        self.counters = []
        self.key_states = {}
        self.is_running = False
        self.is_paused = False
        self.start_time = 0
        self.elapsed_time = 0
        self.timer_speed = 1.0  # Default speed
        self.target_duration = 900  # Default: 15 minutes
        self.last_key_pressed = None
        self.show_results = False
        # Load previous config if available
        self.load_config()
        # Create UI elements
        self.create_widgets()
        self.bind_keys()
        # Font size adjustment
        self.font_size = 12  # Default font size
        self.add_font_size_control()
        self.update_counters_display()  # Ensure font size is applied

    def create_widgets(self):
        # Control panel
        control_frame = ttk.Frame(self)
        control_frame.grid(row=0, column=0, sticky="ew", pady=10)
        # Start Button
        self.start_btn = ttk.Button(control_frame, text="Start", command=self.start_timer)
        self.start_btn.grid(row=0, column=0, padx=5)
        # Stop Button
        self.stop_btn = ttk.Button(control_frame, text="Stop", command=self.stop_timer, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=5)
        # Pause Button
        self.pause_btn = ttk.Button(control_frame, text="Pause", command=self.pause_timer, state=tk.DISABLED)
        self.pause_btn.grid(row=0, column=2, padx=5)
        # Resume Button
        self.resume_btn = ttk.Button(control_frame, text="Resume", command=self.resume_timer, state=tk.DISABLED)
        self.resume_btn.grid(row=0, column=3, padx=5)
        # Reset Button
        ttk.Button(control_frame, text="Reset All", command=self.reset_all).grid(row=0, column=4, padx=5)
        # Speed control using Scale
        speed_frame = ttk.Frame(control_frame)
        speed_frame.grid(row=0, column=5, padx=20)
        ttk.Label(speed_frame, text="Speed:").pack(side=tk.LEFT)
        self.speed_scale = ttk.Scale(speed_frame, from_=0.1, to=3.0, orient='horizontal', command=self.update_speed)
        self.speed_scale.set(1.0)  # Default speed
        self.speed_scale.pack(side=tk.LEFT)
        self.speed_value_label = ttk.Label(speed_frame, text="1.0x")
        self.speed_value_label.pack(side=tk.LEFT, padx=(5, 0))
        # Timer display
        self.timer_label = ttk.Label(control_frame, text="0:00 / 15:00", font=('Helvetica', 14))
        self.timer_label.grid(row=0, column=6, padx=5)
        # Duration input
        duration_frame = ttk.Frame(self)
        duration_frame.grid(row=1, column=0, sticky="ew", padx=10)
        ttk.Label(duration_frame, text="Duration (min):").pack(side=tk.LEFT)
        self.duration_entry = ttk.Entry(duration_frame, width=5)
        self.duration_entry.insert(0, "15")  # Default value
        self.duration_entry.pack(side=tk.LEFT)
        self.duration_entry.bind("<Return>", self.update_duration)  # Corrected event binding
        # Reminder label with word wrap
        self.reminder_label = ttk.Label(
            duration_frame,
            text="Enter the number of minutes and then press enter.",
            foreground="red",
            wraplength=110
        )  # Set a wrap length
        self.reminder_label.pack(side=tk.LEFT, padx=(5, 0))
        # Configuration controls
        config_frame = ttk.Frame(self)
        config_frame.grid(row=2, column=0, sticky="ew", pady=10)
        ttk.Button(config_frame, text="Save Config", command=self.export_config).grid(row=0, column=0, padx=5)
        ttk.Button(config_frame, text="Load Config", command=self.import_config).grid(row=0, column=1, padx=5)
        # Add object controls
        add_frame = ttk.Frame(self)
        add_frame.grid(row=3, column=0, sticky="ew", pady=10)
        self.key_entry = ttk.Entry(add_frame, width=3)
        self.key_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(add_frame, text="Key (A-Z)").pack(side=tk.LEFT)
        # Instructional label
        ttk.Label(add_frame, text="Object Label/Name:").pack(side=tk.LEFT, padx=(5, 0))
        self.name_entry = ttk.Entry(add_frame)
        self.name_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(add_frame, text="Add Object", command=self.add_counter).pack(side=tk.LEFT, padx=5)
        # Scrollable frame for counters
        self.counters_frame = ttk.Frame(self)
        self.counters_frame.grid(row=4, column=0, sticky="nsew")
        
        # Create a canvas for scrolling
        self.canvas = tk.Canvas(self.counters_frame)
        self.scrollbar = ttk.Scrollbar(self.counters_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        # Bind mouse wheel event for scrolling
        if platform.system() == "Linux":
            self.canvas.bind("<Button-4>", self.on_mouse_wheel)  # Scroll up
            self.canvas.bind("<Button-5>", self.on_mouse_wheel)  # Scroll down
        else:
            self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows and macOS
        # Ensure focus on the canvas
        self.canvas.bind("<Button-1>", lambda event: self.canvas.focus_set())
        # Configure grid weights for responsive layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)  # Allow counters frame to expand
        # Update the timer display initially
        self.timer_label.config(text=f"0:00 / {self.format_time(self.target_duration)}")
        # Scrollable frame for counters
        self.counters_frame = ttk.Frame(self)
        self.counters_frame.grid(row=4, column=0, sticky="nsew")
        
        # Create a canvas for scrolling
        self.canvas = tk.Canvas(self.counters_frame)
        self.scrollbar = ttk.Scrollbar(self.counters_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # Bind the scrollable frame to update the canvas scrollregion
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        # Link the scrollbar to the canvas
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack the canvas and scrollbar
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind mouse wheel events for scrolling
        if platform.system() == "Linux":
            self.canvas.bind("<Button-4>", self.on_mouse_wheel)  # Scroll up
            self.canvas.bind("<Button-5>", self.on_mouse_wheel)  # Scroll down
        else:
            self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows and macOS
        
        # Ensure focus on the canvas for mouse wheel events
        self.canvas.bind("<Button-1>", lambda event: self.canvas.focus_set())
        
        # Configure grid weights for responsive layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)  # Allow counters frame to expand

    def on_mouse_wheel(self, event):
        """Handle mouse wheel scrolling for the canvas."""
        if platform.system() == "Windows":
            # On Windows, the delta value is usually larger (e.g., 120)
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif platform.system() == "Darwin":  # macOS
            # On macOS, the delta value is smaller (e.g., 1 or -1)
            self.canvas.yview_scroll(-1 * event.delta, "units")
        else:  # Linux
            # On Linux, Button-4 is scroll up, Button-5 is scroll down
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")

    def update_counters_display(self):
        """Redesign the layout of counters in a grid format with Remove buttons."""
        # Clear all existing widgets in the scrollable_frame
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Loop through each counter and create its UI representation
        for idx, counter in enumerate(self.counters):
            # Create a frame for each counter
            frame = ttk.Frame(self.scrollable_frame, relief="solid", padding=10)
            frame.grid(row=idx // 3, column=idx % 3, padx=5, pady=5, sticky="nsew")

            # Object Name (Bold, size based on self.font_size)
            ttk.Label(
                frame,
                text=counter['name'],
                font=('Helvetica', self.font_size, 'bold')
            ).pack()

            # Key Instruction (Regular font, slightly smaller than self.font_size)
            ttk.Label(
                frame,
                text=f"Press '{counter['key']}'",
                font=('Helvetica', max(self.font_size - 2, 8))  # Ensure minimum size of 8
            ).pack()

            # Count (Bold, larger than self.font_size)
            ttk.Label(
                frame,
                text=str(counter['count']),
                font=('Helvetica', self.font_size + 12, 'bold')  # Larger font for count
            ).pack()

            # Remove Button (Underneath the labels)
            remove_btn = ttk.Button(frame, text="Remove", command=lambda c=counter: self.remove_counter(c))
            remove_btn.pack(pady=(5, 0))  # Add padding above the button

        # Update the scrollregion of the canvas
        self.scrollable_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def bind_keys(self):
        self.bind_all("<KeyPress>", self.handle_key_press)
        self.bind_all("<KeyRelease>", self.handle_key_release)
        self.duration_entry.bind("<Return>", self.update_duration)

    def handle_key_press(self, event):
        if not self.is_running or self.is_paused or event.keysym.upper() in self.key_states:
            return
        key = event.keysym.upper()
        self.key_states[key] = True
        self.last_key_pressed = key
        for counter in self.counters:
            if counter['key'] == key:
                counter['count'] += 1
                self.update_counters_display()
                break

    def handle_key_release(self, event):
        key = event.keysym.upper()
        if key in self.key_states:
            del self.key_states[key]

    def start_timer(self):
        if not self.is_running:
            self.is_running = True
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.pause_btn.config(state=tk.NORMAL)
            self.resume_btn.config(state=tk.DISABLED)
            self.elapsed_time = 0  # Reset elapsed time for new start
            # Set target_duration from entry
            try:
                minutes = int(self.duration_entry.get())
                self.target_duration = minutes * 60  # Convert to seconds
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a valid number for duration.")
                self.is_running = False
                return
            self.start_time = time.time() - self.elapsed_time
            self.update_timer()
        else:
            messagebox.showerror("Error", "Timer is already running.")

    def stop_timer(self):
        """Stop the timer and reset the counter."""
        self.is_running = False
        self.elapsed_time = 0
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.DISABLED)
        self.resume_btn.config(state=tk.DISABLED)
        self.timer_label.config(text=f"0:00 / {self.format_time(self.target_duration)}")
        self.show_results = True
        self.update_results_display()

    def pause_timer(self):
        if self.is_running and not self.is_paused:
            self.is_paused = True
            self.pause_btn.config(state=tk.DISABLED)
            self.resume_btn.config(state=tk.NORMAL)
            self.start_btn.config(state=tk.DISABLED)  # Disable start button while paused

    def resume_timer(self):
        if self.is_paused:
            self.is_paused = False
            self.resume_btn.config(state=tk.DISABLED)
            self.pause_btn.config(state=tk.NORMAL)
            self.start_btn.config(state=tk.DISABLED)  # Disable start button while running
            self.start_time = time.time() - self.elapsed_time  # Update start time to continue from current elapsed time
            self.update_timer()

    def update_timer(self):
        if self.is_running and not self.is_paused:
            self.elapsed_time = (time.time() - self.start_time) * self.timer_speed
            if self.elapsed_time >= self.target_duration:
                self.is_running = False
                self.show_results = True
                self.show_notification("Timer completed!", "info")
                self.update_results_display()
                self.start_btn.config(state=tk.NORMAL)  # Enable start button after completion
                self.stop_btn.config(state=tk.DISABLED)
            self.timer_label.config(text=f"{self.format_time(self.elapsed_time)} / {self.format_time(self.target_duration)}")
            self.after(100, self.update_timer)

    def format_time(self, seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def update_duration(self, event=None):
        """Update the timer display based on the duration entry."""
        try:
            minutes = int(self.duration_entry.get())
            self.target_duration = minutes * 60  # Convert to seconds
            self.timer_label.config(text=f"0:00 / {self.format_time(self.target_duration)}")
        except ValueError:
            pass  # Ignore invalid input

    def update_speed(self, value):
        """Update the timer speed based on the scale value."""
        self.timer_speed = float(value)
        self.speed_value_label.config(text=f"{self.timer_speed:.1f}x")  # Update displayed speed

    def add_counter(self):
        key = self.key_entry.get().upper()
        name = self.name_entry.get()
        if not key or not name:
            self.show_notification("Both key and name are required!", "warning")
            return
        if any(c['key'] == key for c in self.counters):
            self.show_notification("Key already exists!", "warning")
            return
        # Create a new counter object and add it to the list
        counter = {'key': key, 'name': name, 'count': 0}
        self.counters.append(counter)
        self.key_entry.delete(0, tk.END)
        self.name_entry.delete(0, tk.END)
        self.update_counters_display()
        self.save_config()

    def remove_counter(self, counter):
        """Remove a counter from the list."""
        self.counters.remove(counter)
        self.update_counters_display()
        self.save_config()

    def update_counters_display(self):
        """Redesign the layout of counters in a grid format with Remove buttons."""
        # Clear all existing widgets in the counters_frame
        for widget in self.counters_frame.winfo_children():
            widget.destroy()

        # Loop through each counter and create its UI representation
        for idx, counter in enumerate(self.counters):
            # Create a frame for each counter
            frame = ttk.Frame(self.counters_frame, relief="solid", padding=10)
            frame.grid(row=idx // 3, column=idx % 3, padx=5, pady=5, sticky="nsew")

            # Object Name (Bold, size 12)
            ttk.Label(frame, text=counter['name'], font=('Helvetica', 12, 'bold')).pack()

            # Key Instruction (Regular font)
            ttk.Label(frame, text=f"Press '{counter['key']}'").pack()

            # Count (Bold, size 24)
            ttk.Label(frame, text=str(counter['count']), font=('Helvetica', 24, 'bold')).pack()

            # Remove Button (Underneath the labels)
            remove_btn = ttk.Button(frame, text="Remove", command=lambda c=counter: self.remove_counter(c))
            remove_btn.pack(pady=(5, 0))  # Add padding above the button

        # Configure column weights to ensure proper resizing
        self.counters_frame.grid_columnconfigure(0, weight=1)
        self.counters_frame.grid_columnconfigure(1, weight=1)
        self.counters_frame.grid_columnconfigure(2, weight=1)

        # Update the layout and scroll region if needed
        self.counters_frame.update_idletasks()

    def update_results_display(self):
        if self.show_results:
            self.results_frame = ttk.Frame(self)
            self.results_frame.pack(fill=tk.BOTH, expand=True)
            tree = ttk.Treeview(self.results_frame, columns=('name', 'count'), show='headings')
            tree.heading('name', text='Object Name')
            tree.heading('count', text='Total Count')
            for counter in self.counters:
                tree.insert('', tk.END, values=(counter['name'], counter['count']))
            tree.pack(fill=tk.BOTH, expand=True)
            # Option to save results
            save_button = ttk.Button(self.results_frame, text="Save Results as CSV", command=self.export_csv)
            save_button.pack(pady=10)

    def export_csv(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv")
        if filename:
            with open(filename, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Object Name', 'Total Count'])
                for counter in self.counters:
                    writer.writerow([counter['name'], counter['count']])

    def reset_all(self):
        self.is_running = False
        self.elapsed_time = 0
        self.show_results = False
        self.start_btn.config(text="Start", state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.DISABLED)
        self.resume_btn.config(state=tk.DISABLED)
        self.timer_label.config(text=f"0:00 / {self.format_time(self.target_duration)}")
        for counter in self.counters:
            counter['count'] = 0
        self.update_counters_display()
        if hasattr(self, 'results_frame'):  # Check if results_frame exists before destroying it
            self.results_frame.destroy()

    def export_config(self):
        config = {
            'counters': [{'key': c['key'], 'name': c['name']} for c in self.counters],
            'duration': self.target_duration
        }
        filename = filedialog.asksaveasfilename(defaultextension=".json")
        if filename:
            with open(filename, 'w') as f:
                json.dump(config, f)

    def import_config(self):
        filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filename:
            try:
                with open(filename) as f:
                    config = json.load(f)
                    self.counters = [{'key': c['key'], 'name': c['name'], 'count': 0} for c in config.get('counters', [])]
                    self.target_duration = config.get('duration', 900)
                    self.update_counters_display()
                    self.timer_label.config(text=f"0:00 / {self.format_time(self.target_duration)}")  # Update display
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load config: {str(e)}")

    def load_config(self):
        try:
            with open('config.json') as f:
                config = json.load(f)
                self.counters = [{'key': c['key'], 'name': c['name'], 'count': 0} for c in config.get('counters', [])]
                self.target_duration = config.get('duration', 900)
        except FileNotFoundError:
            pass

    def save_config(self):
        config = {
            'counters': [{'key': c['key'], 'name': c['name']} for c in self.counters],
            'duration': self.target_duration
        }
        with open('config.json', 'w') as f:
            json.dump(config, f)

    def show_notification(self, message, type_="info"):
        if platform.system() == "Windows":
            winsound.MessageBeep()
            if type_ == "warning":
                winsound.Beep(1000, 500)
            else:
                winsound.Beep(500, 500)
        else:
            print(f"Notification: {message}")  # Fallback for non-Windows systems
        messagebox.showinfo("Notification", message)

    def add_font_size_control(self):
        """Adds a control for adjusting the font size."""
        font_frame = ttk.Frame(self)
        font_frame.grid(row=5, column=0, sticky="ew", pady=10)
        ttk.Label(font_frame, text="Font Size:").pack(side=tk.LEFT)
        self.font_scale = ttk.Scale(font_frame, from_=8, to=24, orient='horizontal', command=self.update_font_size)
        self.font_scale.set(self.font_size)  # Default font size
        self.font_scale.pack(side=tk.LEFT)
        self.font_size_label = ttk.Label(font_frame, text=f"{self.font_size}pt")
        self.font_size_label.pack(side=tk.LEFT, padx=5)

    def update_font_size(self, value):
        """Updates the font size of all counter labels."""
        # Update the font size variable
        self.font_size = int(float(value))
        self.font_size_label.config(text=f"{self.font_size}pt")
        
        # Re-render the counters display with the new font size
        self.update_counters_display()


    def update_counters_display(self):
        """Redesign the layout of counters in a grid format with Remove buttons."""
        # Clear all existing widgets in the counters_frame
        for widget in self.counters_frame.winfo_children():
            widget.destroy()

        # Loop through each counter and create its UI representation
        for idx, counter in enumerate(self.counters):
            # Create a frame for each counter
            frame = ttk.Frame(self.counters_frame, relief="solid", padding=10)
            frame.grid(row=idx // 3, column=idx % 3, padx=5, pady=5, sticky="nsew")

            # Object Name (Bold, size based on self.font_size)
            ttk.Label(
                frame,
                text=counter['name'],
                font=('Helvetica', self.font_size, 'bold')
            ).pack()

            # Key Instruction (Regular font, slightly smaller than self.font_size)
            ttk.Label(
                frame,
                text=f"Press '{counter['key']}'",
                font=('Helvetica', max(self.font_size - 2, 8))  # Ensure minimum size of 8
            ).pack()

            # Count (Bold, larger than self.font_size)
            ttk.Label(
                frame,
                text=str(counter['count']),
                font=('Helvetica', self.font_size + 12, 'bold')  # Larger font for count
            ).pack()

            # Remove Button (Underneath the labels)
            remove_btn = ttk.Button(frame, text="Remove", command=lambda c=counter: self.remove_counter(c))
            remove_btn.pack(pady=(5, 0))  # Add padding above the button

        # Configure column weights to ensure proper resizing
        self.counters_frame.grid_columnconfigure(0, weight=1)
        self.counters_frame.grid_columnconfigure(1, weight=1)
        self.counters_frame.grid_columnconfigure(2, weight=1)

        # Update the layout and scroll region if needed
        self.counters_frame.update_idletasks()

    def on_mouse_wheel(self, event):
        """Handle mouse wheel scrolling for the canvas."""
        if platform.system() == "Windows":
            # On Windows, the delta value is usually larger (e.g., 120)
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif platform.system() == "Darwin":  # macOS
            # On macOS, the delta value is smaller (e.g., 1 or -1)
            self.canvas.yview_scroll(-1 * event.delta, "units")
        else:  # Linux
            # On Linux, Button-4 is scroll up, Button-5 is scroll down
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")

if __name__ == "__main__":
    app = AdvancedCounter()
    app.mainloop()