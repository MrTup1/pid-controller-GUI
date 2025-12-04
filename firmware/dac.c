#include <avr/io.h>
#include <util/delay.h>
#include <stdlib.h>
#include "debug.h"
#include "freq.h"

// 
#define uart_available() (UCSR0A & _BV(RXC0))

void clear_stdin();

const char EOT = 4;

int main(void) {
    DDRB |= _BV(PINB7);
    PORTB &= ~_BV(PINB7); // Start with LED off

    DDRD &= ~_BV(PIND0);
    DDRD |= _BV(PIND1);

    init_debug_uart0();
    initialise_tone();
    ICR1 = 4095;
    OCR1A = 1024;

    uint16_t cycle = 50;

    while (1) {
        printf("Enter your duty cycle: \n");

        if (scanf(" %u", &cycle) == 1) {
            printf("\nDuty cycle set to %u\n", cycle);
            set_duty_cycle(cycle);
            continue;
        }

        printf("Invalid input, try again.\n");
        clear_stdin();   // flush garbage
    }
}

void clear_stdin() {
    int c;
    // Read characters until a newline or carriage return is found, prevents invalid input infinite printing
    do {
        c = getchar();
    } while (c != '\n' && c != '\r' && c != EOF);
}