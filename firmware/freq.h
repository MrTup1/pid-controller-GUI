#include <avr/io.h>
#include <util/delay.h>

const uint16_t MAX = 4095; //12 Bit timer, using the 16 bit timer 1

unsigned long toneClock;   

// Initialize frequency oscillator (using timers)
void initialise_tone(void);
void tone(uint16_t frequency);

void initialise_tone(void)
{
    DDRD = _BV(PD5);
    TCCR1A |= _BV(COM1A1);
	TCCR1B |= _BV(CS10) | _BV(WGM13);
    toneClock = 12000000 / (8 * 2 * 2);
    ICR1 = MAX;
}

void set_duty_cycle(uint16_t percent) { //Uses phase frequency match
    OCR1A = (((float)percent / 100.0) * MAX);
}

void tone(uint16_t frequency)
{
    uint16_t top = toneClock / frequency;
	OCR1A = top;

}