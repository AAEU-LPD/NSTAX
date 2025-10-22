/*
 * Blink
 * Turns on an LED on for one second,
 * then off for one second, repeatedly.
 */

#include <Arduino.h>

// Define the PWM pin
const int pwmPin = 9; // Use pin 9 as PWM output

const byte numChars = 32;
char receivedChars[numChars];   // an array to store the received data

boolean newData = false;

int dataNumber = 0;             
int prevNumber = 0;             
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

void ProcessSpeedInput() {
    if (newData == true) {
        dataNumber = atoi(receivedChars);  
        Serial.println(receivedChars);
        switch (dataNumber) {
            case 0:
                dataNumber = 0; // Off
                break;
            case 1:
                dataNumber = 150; // Low speed
                break;
            case 2:
                dataNumber = 160; // Medium speed
                break;
            case 3:
                dataNumber = 210; // High speed
                break;
            case 4:
                dataNumber = 220; // Full speed
                break;
            case -1:
                resetFunc(); // Reset the device
                break;
            default:
                Serial.println("Invalid input. Please enter a number between 0 and 4.");
                newData = false;
                return; // Exit if the input is invalid
        }
        if (dataNumber == prevNumber) {
            Serial.println("No change in speed. Keeping the previous setting.");
            newData = false;
            return;
        }
        else
        {
            Serial.print("Changing speed ... ");
            analogWrite(pwmPin, 0); // Turn off the motor
            unsigned long startTime = millis();
            while (millis() - startTime < 1000);
        }
        Serial.print("Setting motor speed to ... ");
        Serial.println((float)dataNumber/255.0*100); 
        analogWrite(pwmPin, dataNumber); // Ensure PWM is off initially
        prevNumber = dataNumber; // Store the last valid number
        newData = false;
    }
}

void setup() {
    Serial.begin(9600);
    Serial.println("\nNANOSTATION_V");
    Serial.println("\n<Vibration Station is ready for launch!>");
    Serial.println("\nSet vibration motor speed (0-4) or type -1 to reset the device.");
    pinMode(pwmPin, OUTPUT);
    analogWrite(pwmPin, 0); // Ensure PWM is off initially
}

void loop() {
    _processString();
    ProcessSpeedInput();
}
// This code is for a simple Arduino sketch that reads input from the serial port
// to control a vibration motor. It allows the user to set the motor speed