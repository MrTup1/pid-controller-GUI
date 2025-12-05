import customtkinter as ctk

def slider_event(value):
    # Update the label text with the current slider value
    # value is a float, so we convert it to an int or format it as needed
    value_label.configure(text=str(int(value)))

app = ctk.CTk()
app.geometry("400x300")
app.title("Slider with Number Label")

# 1. Create the Label (starts with default text)
value_label = ctk.CTkLabel(app, text="0", font=("Arial", 20))
value_label.pack(pady=20)

# 2. Create the Slider
# 'command' calls the function whenever the slider moves
slider = ctk.CTkSlider(app, from_=0, to=100, command=slider_event)
slider.pack(pady=10)

app.mainloop()