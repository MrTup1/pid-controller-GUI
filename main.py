import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk  # The new UI library
import serial
import serial.tools.list_ports
import time
import collections

# Global Theme Settings
ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class PIDControllerGUI:
    def __init__(self):
        # Change root to CTk
        self.root = ctk.CTk()
        self.root.title("PID Controller Interface")
        self.root.geometry("900x650") # Increased slightly for comfortable spacing

        # Serial Connection
        self.serial_port = None
        self.is_connected = False
        self.data_buffer = collections.deque(maxlen=200) 

        # GUI Layout
        self._setup_connection_frame()
        self._setup_control_frame()
        self._setup_visualization_frame()

        # Start Serial Polling Loop
        self.root.after(10, self._read_serial)

    def _setup_connection_frame(self):
        # CTkFrame doesn't have 'text' for a border title like ttk.LabelFrame
        # So we create a Frame and add a Label inside to act as the header.
        frame = ctk.CTkFrame(self.root)
        frame.pack(fill="x", padx=10, pady=5)
        
        # Section Title
        lbl_title = ctk.CTkLabel(frame, text="Connection Settings", font=("Roboto", 12, "bold"))
        lbl_title.pack(anchor="w", padx=10, pady=(5, 0))

        # Inner container for the controls to keep them aligned
        inner_frame = ctk.CTkFrame(frame, fg_color="transparent")
        inner_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(inner_frame, text="Port:").pack(side="left", padx=5)
        
        self.port_combo = ctk.CTkComboBox(inner_frame, width=150)
        self.port_combo.pack(side="left", padx=5)
        self.refresh_ports()

        self.btn_refresh = ctk.CTkButton(inner_frame, text="↻", width=40, command=self.refresh_ports)
        self.btn_refresh.pack(side="left", padx=2)

        self.btn_connect = ctk.CTkButton(inner_frame, text="Connect", command=self.toggle_connection)
        self.btn_connect.pack(side="left", padx=10)

        self.status_lbl = ctk.CTkLabel(inner_frame, text="Status: Disconnected", text_color="red")
        self.status_lbl.pack(side="left", padx=10)

    def _setup_control_frame(self):
        frame = ctk.CTkFrame(self.root)
        frame.pack(fill="x", padx=10, pady=5)

        # Section Title
        ctk.CTkLabel(frame, text="PID Controls", font=("Roboto", 12, "bold")).grid(row=0, column=0, columnspan=10, sticky="w", padx=10, pady=(5,5))

        # Setpoint Control
        # Note: CTk width is in pixels, not characters. Adjusted accordingly.
        ctk.CTkLabel(frame, text="Target (0-1023):").grid(row=1, column=0, padx=5, pady=5)

        slider_container = ctk.CTkFrame(frame, fg_color="transparent") #Transparent box that fits both the slider and slider value
        slider_container.grid(row=1, column=1, padx=5, pady=5)

        def slider_event(value):
            self.value_label.configure(text=str(int(value)))

        # 1. The Value Label (Packed Top)
        self.value_label = ctk.CTkLabel(slider_container, text="0", font=("Roboto", 14, "bold"))
        self.value_label.pack(side="top", pady=(0, 2))

        # 2. The Slider (Packed Bottom)
        self.ent_setpoint = ctk.CTkSlider(slider_container, from_=0, to=1024, number_of_steps=1024, command=slider_event)
        self.ent_setpoint.set(0) # Ensure slider and label match start values
        self.ent_setpoint.pack(side="top")
        
        ctk.CTkButton(frame, text="Set Target", width=100, command=self.send_setpoint).grid(row=1, column=2, padx=5, pady=5)
        
        # PID Constants
        ctk.CTkLabel(frame, text="Kp:").grid(row=1, column=3, padx=5)
        self.ent_kp = ctk.CTkEntry(frame, width=60)
        self.ent_kp.insert(0, "0.6")
        self.ent_kp.grid(row=1, column=4, padx=5)

        ctk.CTkLabel(frame, text="Ki:").grid(row=1, column=5, padx=5)
        self.ent_ki = ctk.CTkEntry(frame, width=60)
        self.ent_ki.insert(0, "0.05")
        self.ent_ki.grid(row=1, column=6, padx=5)

        ctk.CTkLabel(frame, text="Kd:").grid(row=1, column=7, padx=5)
        self.ent_kd = ctk.CTkEntry(frame, width=60)
        self.ent_kd.insert(0, "0.02")
        self.ent_kd.grid(row=1, column=8, padx=5)

        ctk.CTkButton(frame, text="Update Gains", width=100, command=self.send_gains).grid(row=1, column=9, padx=10)

    def _setup_visualization_frame(self):
        frame = ctk.CTkFrame(self.root)
        frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Section Title
        ctk.CTkLabel(frame, text="System Response", font=("Roboto", 12, "bold")).pack(anchor="w", padx=10, pady=(5,0))

        # Current Value Display
        self.lbl_voltage = ctk.CTkLabel(frame, text="Current Voltage: -- V", font=("Roboto", 20, "bold"))
        self.lbl_voltage.pack(anchor="center", pady=5)

        # Canvas for Graphing
        # Note: CustomTkinter does not have a Canvas widget, but works perfectly with the standard tk.Canvas
        # We set highlightthickness=0 to remove the ugly white border default in tkinter
        self.canvas = tk.Canvas(frame, bg="black", height=300, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.root.update()

    def refresh_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        # CTkComboBox uses .configure(values=...) instead of dict assignment
        self.port_combo.configure(values=ports)
        if ports:
            self.port_combo.set(ports[0])

    def toggle_connection(self):
        if not self.is_connected:
            try:
                port = self.port_combo.get()
                self.serial_port = serial.Serial(port, 9600, timeout=0.1)
                self.is_connected = True
                self.btn_connect.configure(text="Disconnect", fg_color="red", hover_color="darkred")
                self.status_lbl.configure(text="Status: Connected", text_color="green")
            except Exception as e:
                messagebox.showerror("Connection Error", str(e))
        else:
            if self.serial_port:
                self.serial_port.close()
            self.is_connected = False
            self.btn_connect.configure(text="Connect", fg_color=["#3B8ED0", "#1F6AA5"], hover_color=["#36719F", "#144870"]) # Reset to default blue
            self.status_lbl.configure(text="Status: Disconnected", text_color="red")

    def _read_serial(self):
        if self.is_connected and self.serial_port and self.serial_port.in_waiting:
            try:
                line = self.serial_port.readline().decode('utf-8').strip()
                parts = line.split('|')
                if len(parts) >= 2: 
                    voltage_str = parts[1]
                    try:
                        voltage = float(voltage_str)
                        self.update_graph(voltage)
                        self.lbl_voltage.configure(text=f"Current Voltage: {voltage:.2f} V")
                    except ValueError:
                        pass
            except Exception:
                pass
        
        self.root.after(10, self._read_serial)

    def update_graph(self, new_val):
        self.data_buffer.append(new_val)
        self.canvas.delete("all")
        
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        
        max_v = 3.3
        
        if len(self.data_buffer) > 1:
            points = []
            num_points = len(self.data_buffer)
            dx = w / max(num_points - 1, 1)
            
            for i, val in enumerate(self.data_buffer):
                x = i * dx
                y = h - ((val / max_v) * h)
                points.extend([x, y])
            
            # Using standard tkinter line creation
            self.canvas.create_line(points, fill="#00ff00", width=2)
            
            try:
                sp = int(self.ent_setpoint.get())
                sp_v = (sp * 3.3) / 1024
                y_sp = h - ((sp_v / max_v) * h)
                self.canvas.create_line(0, y_sp, w, y_sp, fill="red", dash=(4, 4))
            except:
                pass

    def send_setpoint(self):
        if self.is_connected:
            try:
                val = int(self.ent_setpoint.get())
                cmd = f"S{val}\n"
                print(f"DEBUG: Sending '{cmd.strip()}'")
                self.serial_port.write(cmd.encode())
            except ValueError:
                messagebox.showerror("Error", "Setpoint must be an integer")

    def send_gains(self):
        if self.is_connected:
            try:
                p = float(self.ent_kp.get())
                i = float(self.ent_ki.get())
                d = float(self.ent_kd.get())
                self.serial_port.write(f"P{p}\n".encode())
                time.sleep(0.05)
                self.serial_port.write(f"I{i}\n".encode())
                time.sleep(0.05)
                self.serial_port.write(f"D{d}\n".encode())
            except ValueError:
                messagebox.showerror("Error", "PID values must be numbers")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = PIDControllerGUI()
    app.run()