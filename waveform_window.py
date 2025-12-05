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

    def draw(self, event): # Captures mouse movement 
        if self.is_playing: return # Don't edit while playing
        
        x = event.x
        y = event.y
        
        # Check if cursor out of bounds
        if x < 0: x = 0
        if x >= self.canvas_width: x = self.canvas_width - 1
        if y < 0: y = 0
        if y > self.canvas_height: y = self.canvas_height
        
        # Map X pixel to index (0-99)
        index = int((x / self.canvas_width) * 100)
        if index >= 100: index = 99
        
        # Map Y pixel to ADC value (0-1023)
        # Y is inverted (0 is top), so flip it
        normalized_y = 1 - (y / self.canvas_height) 
        adc_val = int(normalized_y * 1023)
        
        self.waveform_data[index] = adc_val
        
        # Draw white circle at cursor location
        r = 2
        self.canvas.create_oval(x-r, y-r, x+r, y+r, fill="white", outline="") #x-r, top left, y+r bottom right
        
        # Smoothing the wave, If user drags fast, might skip indexes which creates gaps, set neighbouring points equal to ccurrent value
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
        pass

    def toggle_play(self): # UI of button to play
        if not self.is_playing:
            self.is_playing = True
            self.btn_play.configure(text="Stop Loop", fg_color="orange")
            threading.Thread(target=self.send_loop, daemon=True).start()
        else:
            self.is_playing = False
            self.btn_play.configure(text="▶ Play Loop", fg_color="green")

    def send_loop(self):
        # Loop runs in the background and streams commands 
        i = 0
        while self.is_playing:
            if not self.serial_port or not self.serial_port.is_open:
                self.is_playing = False
                break
                
            val = self.waveform_data[i]
            
            # Send the setpoint command in S0.5\n format
            try:
                cmd = f"S{val}\n"
                self.serial_port.write(cmd.encode())
            except:
                self.is_playing = False
                break
            
            # Move to next point
            i += 1
            if i >= 100: i = 0
            
            # Speed control
            time.sleep(0.05) #5 seconds to complete each wave, each points takes 0.05 seconds
            
        # Reset button when loop finishes
        self.btn_play.configure(text="▶ Play Loop", fg_color="green")