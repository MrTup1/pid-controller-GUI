#include <avr/io.h>
#include <util/delay.h>
#include <avr/interrupt.h>
#include <stdlib.h>
#include "debug.h"

#define IS_UART_DATA_AVAILABLE() (UCSR0A & _BV(RXC0))

void flush_serial_buffer(void);
void print_voltage(uint32_t time, uint16_t ADC_output);
void print_graph();
uint16_t adc_read();
void initialise_timer();


const char EOT = 4;
const uint16_t MAX_COUNT = 511;
volatile uint32_t timer_ms = 0;
const double SCALE = 50.0; 
const uint32_t PRINT_INTERVAL_MS = 50;

void set_duty_cycle(uint16_t percent) {
    OCR1A = (((float)percent / 100.0) * MAX_COUNT);
}

void initialise_timer() {
    TCCR0A = (1 << WGM01); // CTC Mode
    TCCR0B = (1 << CS01) | (1 << CS00); // Prescaler set to 64
    
    // Set TOP value (OCR0A) for 1ms interrupt
    // (12,000,000 Hz) / (64 * 1000 Hz) - 1 = 186.5 -> use 187
    OCR0A = 187;

    TIMSK0 = (1 << OCIE0A); // enable Timer0 interrupts
}

ISR(TIMER0_COMPA_vect){ timer_ms++; }

uint32_t get_time_ms(){
    uint32_t current;
    
    cli(); // Clear interrupts, pauses timer interrupts, timer_ms takes 4 clock cycles to make
    current = timer_ms;
    sei(); // Set interrupts
    
    return current;
}

void flush_serial_buffer(void) {
    while (IS_UART_DATA_AVAILABLE()) {
        getchar();   // discard
    }
}

uint16_t adc_read(){
    ADCSRA |= (1 << ADSC); // Start conversion, stays high 

    while (ADCSRA & (1 << ADSC)); // Wait for conversion to finish

    return (ADC);
}


void print_voltage(uint32_t time, uint16_t sample) {
    int i;
    double volts = ((double)sample * 3.3) / 1024.0;
    char volt_string[8];
    dtostrf(volts, 6, 4, volt_string);
    int length = SCALE * volts; 
    printf("%06lu", time);
    printf("   %s", volt_string);
    for(i = 0; i < length; i++) {
        printf(" ");
    }
    printf("*\n");
}

void print_graph() {
    uint32_t last_time = 0;
    printf("\nTime (ms) | Voltage (V) | Plot\n");
    printf("----------|-------------|----------------------------------------------------------------------------------------------------\n");
    for(;;){
        uint32_t current = get_time_ms();
        if(current - last_time >= PRINT_INTERVAL_MS){
            uint16_t adc_val = adc_read();
            print_voltage(current, adc_val);
            last_time = current;
        }
    }
}

int main(void) {
    DDRB |= _BV(PINB7);
    PORTB &= ~_BV(PINB7); // Start with Il Matto LED off

    DDRD &= ~_BV(PIND0);
    DDRD |= _BV(PIND1);

    DDRD = _BV(PD5);
    TCCR1A |= _BV(COM1A1);
    TCCR1B |= _BV(CS10) | _BV(WGM13); 
    ICR1 = MAX_COUNT;

    DIDR0 |= _BV(ADC1D);
    ADMUX |=  _BV(REFS0) | _BV(MUX0); 
    ADCSRA = (1 << ADEN) | (1 << ADPS2) | (1 << ADPS1); // 64 Prescalar
    sei();

    init_debug_uart0();
    init_timer();

    uint16_t cycle = 50;
    set_duty_cycle(cycle);
    

    while (1) {
        printf("Enter duty cycle: ");

        if (scanf(" %u", &cycle) == 1) {
            printf("\nDuty cycle set to %u \n", cycle);
            set_duty_cycle(cycle);
            print_graph();
            continue;
        }

        printf("Invalid input, try again.\n");
        clear_stdin();   // flush garbage
    }
}

