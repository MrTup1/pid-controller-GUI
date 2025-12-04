#include <avr/io.h>
#include <util/delay.h>
#include <avr/interrupt.h>
#include <stdlib.h>
#include "debug.h"

// --- Visualization Constants ---
const double SCALE = 50.0; 
const uint32_t PRINT_INTERVAL_MS = 100; // Increased to 100ms to prevent UART lag affecting PID

// --- PID Configuration ---
const int16_t SETPOINT = 300; 
const uint16_t MAX_COUNT = 511; 
const uint16_t MIN_COUNT = 0;

const uint32_t PID_INTERVAL_MS = 10; 

// PID Gains
float Kp = 0.6; 
float Ki = 0.05;
float Kd = 0.02; // Small Kd helps dampen rapid changes

// --- Globals ---
volatile uint32_t timer_ms = 0;
float integral_error = 0;
int16_t last_error = 0;
uint32_t last_pid_time = 0;

// --- Interrupts ---
ISR(TIMER0_COMPA_vect){ 
    timer_ms++; 
}

// --- Hardware Init ---
void init_timer0() {
    TCCR0A = (1 << WGM01); 
    TCCR0B = (1 << CS01) | (1 << CS00); 
    OCR0A = 187; 
    TIMSK0 = (1 << OCIE0A); 
}

void init_pwm_timer1() {
    DDRD |= _BV(PD5);
    TCCR1A |= _BV(COM1A1); 
    TCCR1B |= _BV(CS10) | _BV(WGM13); 
    ICR1 = MAX_COUNT; 
}

uint32_t get_time_ms(){
    uint32_t current;
    cli();
    current = timer_ms;
    sei();
    return current;
}

uint16_t adc_read(){
    ADCSRA |= (1 << ADSC); 
    while (ADCSRA & (1 << ADSC)); 
    return (ADC);
}

// --- Printing ---
void print_status(uint32_t time, uint16_t sample, float output) {
    double volts = ((double)sample * 3.3) / 1024.0;
    char volt_string[8];
    dtostrf(volts, 6, 4, volt_string);
    
    // Print Voltage and PWM output to diagnose "stuck" issues
    printf("%06lu | V:%s | PWM:%3d | ", time, volt_string, (int)output);
    
    int length = (int)(volts * 50); 
    for(int i = 0; i < length; i++) printf("-");
    printf("*\n");
}

int main(void) {
    DDRB |= _BV(PINB7); 
    init_debug_uart0();
    init_timer0();
    init_pwm_timer1();

    DIDR0 |= _BV(ADC1D);
    ADMUX |= _BV(REFS0) | _BV(MUX0); 
    ADCSRA = (1 << ADEN) | (1 << ADPS2) | (1 << ADPS1);
    
    sei();

    printf("\nPID Anti-Windup Test\n");

    int16_t current_adc = 0;
    int16_t error = 0;
    int16_t derivative = 0;
    float control_output = 0;
    
    // P, I, D terms
    float P_term, I_term, D_term;

    uint32_t last_print_time = 0;

    while (1) {
        uint32_t current_time = get_time_ms();

        if (current_time - last_pid_time >= PID_INTERVAL_MS) {
            last_pid_time = current_time;

            current_adc = adc_read();
            error = SETPOINT - current_adc;

            if (abs(error) < 2) { //Stops integral term oscillation
                error = 0;
            }

            P_term = Kp * error;
            
            derivative = error - last_error;
            D_term = Kd * derivative;
            last_error = error;

            //Basic PD output
            float tentative_output = P_term + (Ki * integral_error) + D_term;

            // A. We are NOT saturated (Output is within 0-511)
            // OR
            // B. We ARE saturated, but the Error is opposite sign (Unwinding)
            if (tentative_output >= MAX_COUNT) {
                if (error < 0) { 
                    integral_error += error; 
                }
            } 
            else if (tentative_output <= MIN_COUNT) {
                if (error > 0) {
                    integral_error += error; 
                }
            } 
            else {
                integral_error += error;
            }

            // Hard Clamp Integral range just in case
            // 511 / 0.05 (Ki) = ~10200. No need to go higher than that.
            if (integral_error > 10200) integral_error = 10200;
            if (integral_error < -10200) integral_error = -10200;

            //Final Output
            I_term = Ki * integral_error;
            control_output = P_term + I_term + D_term;


            if (control_output > MAX_COUNT) control_output = MAX_COUNT;
            if (control_output < MIN_COUNT) control_output = MIN_COUNT;

            OCR1A = (uint16_t)control_output;
        }

        // Separate Visualization Loop
        // Moved outside the PID block to ensure timing independence
        if(get_time_ms() - last_print_time >= PRINT_INTERVAL_MS){
            last_print_time = get_time_ms();
            print_status(last_print_time, current_adc, control_output);
            PORTB ^= _BV(PINB7);
        }
    }
}