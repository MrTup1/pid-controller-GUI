import tkinter as tk
import customtkinter as ctk
import time
import threading

class WaveformWindow(ctk.CTkToplevel):
    def __init__(self, parent, serial_port):
        super().__init__(parent)
        self.title("Arbitrary Waveform Generator")
        self.geometry("600x500")
        self.serial_port = serial_port
        
        # Data storage
        self.waveform_data = [0] * 100 # 100 points for one cycle
        self.is_playing = False
        
        # Layout
        self.lbl_info = ctk.CTkLabel(self, text="Draw your waveform below (One Cycle)", font=("Roboto", 14))
        self.lbl_info.pack(pady=10)
        
        # Drawing Canvas
        # We use standard tk.Canvas because it handles mouse drawing events better
        self.canvas_height = 300
        self.canvas_width = 500
        self.canvas = tk.Canvas(self, bg="black", width=self.canvas_width, height=self.canvas_height, cursor="crosshair")
        self.canvas.pack(pady=10)
        
        # Draw reference lines
        self.canvas.create_line(0, self.canvas_height/2, self.canvas_width, self.canvas_height/2, fill="gray", dash=(2,2))
        self.canvas.create_text(10, 10, text="3.3V (1023)", fill="white", anchor="nw")
        self.canvas.create_text(10, self.canvas_height-10, text="0V (0)", fill="white", anchor="sw")

        # Bind Mouse Events
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<Button-1>", self.draw)
        
        # Controls
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=10, fill="x", padx=20)
        
        self.btn_play = ctk.CTkButton(btn_frame, text="▶ Play Loop", command=self.toggle_play, fg_color="green")
        self.btn_play.pack(side="left", padx=10, expand=True)
        
        self.btn_clear = ctk.CTkButton(btn_frame, text="Clear", command=self.clear_canvas, fg_color="red")
        self.btn_clear.pack(side="left", padx=10, expand=True)

        # Initial flat line
        self.draw_plot()

    def draw(self, event):
        """ Capture mouse movement and update waveform data """
        if self.is_playing: return # Don't edit while playing
        
        x = event.x
        y = event.y
        
        # Bounds checking
        if x < 0: x = 0
        if x >= self.canvas_width: x = self.canvas_width - 1
        if y < 0: y = 0
        if y > self.canvas_height: y = self.canvas_height
        
        # Map X pixel to index (0-99)
        index = int((x / self.canvas_width) * 100)
        if index >= 100: index = 99
        
        # Map Y pixel to ADC value (0-1023)
        # Y is inverted (0 is top), so we flip it
        normalized_y = 1 - (y / self.canvas_height) 
        adc_val = int(normalized_y * 1023)
        
        self.waveform_data[index] = adc_val
        
        # Visual feedback: Draw a small circle where we are drawing
        r = 2
        self.canvas.create_oval(x-r, y-r, x+r, y+r, fill="white", outline="")
        
        # Smoothing: If you drag fast, you might skip indices.
        # Ideally, we would interpolate here, but for simple drawing, updating the 
        # neighboring points usually feels smooth enough.
        if index > 0: self.waveform_data[index-1] = adc_val
        if index < 99: self.waveform_data[index+1] = adc_val

    def clear_canvas(self):
        self.waveform_data = [0] * 100
        self.canvas.delete("all")
        # Redraw grid
        self.canvas.create_line(0, self.canvas_height/2, self.canvas_width, self.canvas_height/2, fill="gray", dash=(2,2))
        self.canvas.create_text(10, 10, text="3.3V (1023)", fill="white", anchor="nw")
        self.canvas.create_text(10, self.canvas_height-10, text="0V (0)", fill="white", anchor="sw")

    def draw_plot(self):
        """ Redraw the entire green line based on data """
        # We don't redraw constantly to save resources, only when needed or finished drawing
        # But for this simple version, leaving the white dots is fine.
        pass

    def toggle_play(self):
        if not self.is_playing:
            self.is_playing = True
            self.btn_play.configure(text="⏹ Stop Loop", fg_color="orange")
            # Start the sender thread
            threading.Thread(target=self.send_loop, daemon=True).start()
        else:
            self.is_playing = False
            self.btn_play.configure(text="▶ Play Loop", fg_color="green")

    def send_loop(self):
        """ This loop runs in the background and streams commands """
        i = 0
        while self.is_playing:
            if not self.serial_port or not self.serial_port.is_open:
                self.is_playing = False
                break
                
            val = self.waveform_data[i]
            
            # Send the setpoint command
            try:
                cmd = f"S{val}\n"
                self.serial_port.write(cmd.encode())
            except:
                self.is_playing = False
                break
            
            # Move to next point
            i += 1
            if i >= 100: i = 0
            
            # Speed control: 100 points * 0.05s = 5 seconds per cycle (0.2 Hz)
            # Make it faster for oscilloscope viewing: 0.01s (10ms) -> 1 second cycle (1 Hz)
            time.sleep(0.05) 
            
        # Reset button when loop finishes
        self.btn_play.configure(text="▶ Play Loop", fg_color="green")