import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import time
import collections

class PIDControllerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PID Controller Interface")
        self.root.geometry("800x600")

        # Serial Connection
        self.serial_port = None
        self.is_connected = False
        self.data_buffer = collections.deque(maxlen=200) # Store last 200 points for graph

        # GUI Layout
        self._setup_connection_frame()
        self._setup_control_frame()
        self._setup_visualization_frame()

        # Start Serial Polling Loop
        self.root.after(10, self._read_serial)

    def _setup_connection_frame(self):
        frame = ttk.LabelFrame(self.root, text="Connection Settings", padding=10)
        frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame, text="Port:").pack(side="left")
        self.port_combo = ttk.Combobox(frame, width=15)
        self.port_combo.pack(side="left", padx=5)
        self.refresh_ports()

        self.btn_refresh = ttk.Button(frame, text="↻", width=3, command=self.refresh_ports)
        self.btn_refresh.pack(side="left", padx=2)

        self.btn_connect = ttk.Button(frame, text="Connect", command=self.toggle_connection)
        self.btn_connect.pack(side="left", padx=10)

        self.status_lbl = ttk.Label(frame, text="Status: Disconnected", foreground="red")
        self.status_lbl.pack(side="left", padx=10)

    def _setup_control_frame(self):
        frame = ttk.LabelFrame(self.root, text="PID Controls", padding=10)
        frame.pack(fill="x", padx=10, pady=5)

        # Setpoint Control
        ttk.Label(frame, text="Target (0-1023):").grid(row=0, column=0, padx=5, pady=5)
        self.ent_setpoint = ttk.Entry(frame, width=10)
        self.ent_setpoint.insert(0, "300")
        self.ent_setpoint.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Set Target", command=self.send_setpoint).grid(row=0, column=2, padx=5, pady=5)
        
        # PID Constants
        ttk.Label(frame, text="Kp:").grid(row=0, column=3, padx=5)
        self.ent_kp = ttk.Entry(frame, width=6)
        self.ent_kp.insert(0, "0.6")
        self.ent_kp.grid(row=0, column=4, padx=5)

        ttk.Label(frame, text="Ki:").grid(row=0, column=5, padx=5)
        self.ent_ki = ttk.Entry(frame, width=6)
        self.ent_ki.insert(0, "0.05")
        self.ent_ki.grid(row=0, column=6, padx=5)

        ttk.Label(frame, text="Kd:").grid(row=0, column=7, padx=5)
        self.ent_kd = ttk.Entry(frame, width=6)
        self.ent_kd.insert(0, "0.02")
        self.ent_kd.grid(row=0, column=8, padx=5)

        ttk.Button(frame, text="Update Gains", command=self.send_gains).grid(row=0, column=9, padx=10)

    def _setup_visualization_frame(self):
        frame = ttk.LabelFrame(self.root, text="System Response", padding=10)
        frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Current Value Display
        self.lbl_voltage = ttk.Label(frame, text="Current Voltage: -- V", font=("Arial", 16, "bold"))
        self.lbl_voltage.pack(anchor="center")

        # Canvas for Graphing
        self.canvas = tk.Canvas(frame, bg="black", height=300)
        self.canvas.pack(fill="both", expand=True, pady=10)
        
        # Draw initial grid
        self.root.update()
        self.width = self.canvas.winfo_width()
        self.height = self.canvas.winfo_height()

    def refresh_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.current(0)

    def toggle_connection(self):
        if not self.is_connected:
            try:
                port = self.port_combo.get()
                self.serial_port = serial.Serial(port, 9600, timeout=0.1)
                self.is_connected = True
                self.btn_connect.config(text="Disconnect")
                self.status_lbl.config(text="Status: Connected", foreground="green")
            except Exception as e:
                messagebox.showerror("Connection Error", str(e))
        else:
            if self.serial_port:
                self.serial_port.close()
            self.is_connected = False
            self.btn_connect.config(text="Connect")
            self.status_lbl.config(text="Status: Disconnected", foreground="red")

    def _read_serial(self):
        if self.is_connected and self.serial_port and self.serial_port.in_waiting:
            try:
                line = self.serial_port.readline().decode('utf-8').strip()
                # New format: "123400|1.2500|200"
                
                parts = line.split('|')
                if len(parts) >= 2: # Ensure we have at least time and voltage
                    voltage_str = parts[1] # 2nd item is voltage
                    try:
                        voltage = float(voltage_str)
                        self.update_graph(voltage)
                        self.lbl_voltage.config(text=f"Current Voltage: {voltage:.2f} V")
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
        
        # Scaling
        max_v = 3.3
        
        if len(self.data_buffer) > 1:
            points = []
            num_points = len(self.data_buffer)
            dx = w / max(num_points - 1, 1)
            
            for i, val in enumerate(self.data_buffer):
                x = i * dx
                # Invert y (0 is top in tkinter)
                y = h - ((val / max_v) * h)
                points.extend([x, y])
            
            self.canvas.create_line(points, fill="#00ff00", width=2)
            
            # Draw threshold line for Setpoint (approximate visualization)
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
                # Protocol: "S<value>\n"
                cmd = f"S{val}\n"
                print(f"DEBUG: Sending '{cmd.strip()}'")  # <--- Add this
                self.serial_port.write(cmd.encode())
            except ValueError:
                messagebox.showerror("Error", "Setpoint must be an integer")

    def send_gains(self):
        if self.is_connected:
            try:
                p = float(self.ent_kp.get())
                i = float(self.ent_ki.get())
                d = float(self.ent_kd.get())
                # Protocol: P<val>, I<val>, D<val>
                self.serial_port.write(f"P{p}\n".encode())
                time.sleep(0.05)
                self.serial_port.write(f"I{i}\n".encode())
                time.sleep(0.05)
                self.serial_port.write(f"D{d}\n".encode())
            except ValueError:
                messagebox.showerror("Error", "PID values must be numbers")

if __name__ == "__main__":
    root = tk.Tk()
    app = PIDControllerGUI(root)
    root.mainloop()