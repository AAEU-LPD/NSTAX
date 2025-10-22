/*
 * Blink
 * Turns on an LED on for one second,
 * then off for one second, repeatedly.
 */

#include <Arduino.h>

// Define the PWM pin
const int digPin = 8; // Use pin 9 as an example (supports PWM)

const byte numChars = 32;
char receivedChars[numChars];   // an array to store the received data

boolean newData = false;

int dataNumber = 0;             
void(* resetFunc) (void) = 0; //declare reset function @ address 0

void _processString() {
    static byte ndx = 0;
    char endMarker = '\n';
    char rc;
    
    if (Serial.available() > 0) {
        rc = Serial.read();

        if (rc != endMarker) {
            receivedChars[ndx] = rc;
            ndx++;
            if (ndx >= numChars) {
                ndx = numChars - 1;
            }
        }
        else {
            receivedChars[ndx] = '\0'; // terminate the string
            ndx = 0;
            newData = true;
        }
    }
}

void ProcessMagInput() {
    if (newData == true) {
        dataNumber = 0;             // new for this version
        dataNumber = atoi(receivedChars);   // new for this version
        Serial.println(receivedChars);
        switch (dataNumber) {
            case 0:
                digitalWrite(digPin, HIGH); // Turn magnet OFF
                Serial.println("Magnet OFF");
                break;
            case 1:
                Serial.println("Magnet ON");
                digitalWrite(digPin, LOW); // Turn magnet OFF
                unsigned long startTime = millis();
                while (millis() - startTime < 10000);
                digitalWrite(digPin, HIGH); // Turn magnet OFF
                Serial.println("Magnet OFF");
                dataNumber = 1; // Turn on the magnet
                break;
            case -1:
                resetFunc(); // Reset the device
                break;
            default:
                Serial.println("Invalid input.");
                newData = false;
                return; // Exit if the input is invalid
        }
        newData = false;
    }
}

void setup() {
    Serial.begin(9600);
    Serial.println("\nNANOSTATION_M");
    Serial.println("\n<Magnet Station is ready for launch!>");
    Serial.println("\nTrigger magnet on (1) for 10 seconds or type (-1) to reset the device.");
    pinMode(digPin, OUTPUT);
    digitalWrite(digPin, HIGH);
}

void loop() {
    _processString();
    ProcessMagInput();
}

// This code is designed to control a magnet using an Arduino Nano. It listens for serial input to trigger the magnet on for 10 seconds or reset the device.
// The magnet is controlled through a digital pin, and the code includes error handling for invalid input