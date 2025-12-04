flash:
	avr-gcc -mmcu=atmega644p -DF_CPU=12000000 -Wall -Wl,-u,vfprintf -lprintf_flt -lm -Os $(name).c -o $(name).elf
	avr-objcopy -O ihex $(name).elf $(name).hex
	avrdude -c usbasp -p m644p -U flash:w:$(name).hex

cmder:
	avr-gcc -mmcu=atmega644p -DF_CPU=12000000 -Wall -Os cmder.c uart.c -o $cmder.elf
	avr-objcopy -O ihex cmder.elf cmder.hex
	avrdude -c usbasp -p m644p -U flash:w:cmder.hex