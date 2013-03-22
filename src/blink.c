// blink.c
//
// Example program for bcm2835 library
// Blinks a pin on an off every 0.5 secs
//
// After installing bcm2835, you can build this 
// with something like:
// gcc -o blink blink.c -l bcm2835
// sudo ./blink
//
// Or you can test it before installing with:
// gcc -o blink -I ../../src ../../src/bcm2835.c blink.c
// sudo ./blink
//
// Author: Mike McCauley
// Copyright (C) 2011 Mike McCauley
// $Id: RF22.h,v 1.21 2012/05/30 01:51:25 mikem Exp $

#include <bcm2835.h>
#include <time.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>

// Blinks on RPi Plug P1 pin 11 (which is GPIO pin 17)
#define LEFT RPI_GPIO_P1_11
#define RIGHT RPI_GPIO_P1_12

typedef struct stimulus {
	int pin;
	int current;
	double interval;
	struct timespec last;
} Stimulus;

void SIGINTHandler(int signum) {
	bcm2835_gpio_write(LEFT, LOW);
	bcm2835_gpio_write(RIGHT, LOW);
	exit(0);
}


int main(int argc, char **argv)
{
	int i;

	struct timespec ts;

	signal(SIGINT, &SIGINTHandler);

	if (!bcm2835_init())
		return 1;

	Stimulus stimuli[2] = {{.pin = LEFT,
				.current = LOW,
				.interval = 1/(2*10)},
			       {.pin = RIGHT,
				.current = LOW,
				.interval = 1/(2*1)}};

	// Set the pin to be an output
	for (i = 0; i < 2; ++i) {
		bcm2835_gpio_fsel(stimuli[i].pin, BCM2835_GPIO_FSEL_OUTP);
	}

	// Blink
	while (1)
	{
		for (i = 0; i < 2; ++i) {
			clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
			double elapsed = ts.tv_sec - stimuli[i].last.tv_sec;
			elapsed += (ts.tv_nsec - stimuli[i].last.tv_nsec) / 1000000000.0;
			if (elapsed >= stimuli[i].interval) {
				stimuli[i].current = (stimuli[i].current + 1) % 2;
				clock_gettime(CLOCK_MONOTONIC_RAW, &stimuli[i].last);
				bcm2835_gpio_write(stimuli[i].pin, stimuli[i].current);
			}
		}
	}
	bcm2835_close();
	return 0;
}

