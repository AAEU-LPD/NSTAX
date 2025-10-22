/*
 * Blink
 * Turns on an LED on for one second,
 * then off for one second, repeatedly.
 */

#include <Arduino.h>

// Define the pins

const int relayB = 2; 
const int relayA = 3; 
const int enablePinA = 5; 
const int pwmPinA = 6; 
const int gndPinA = 7; 
const int enablePinB = 9; 
const int pwmPinB = 10; 
const int gndPinB = 11; 

// Define case constants
const int CASE_MOTOR_A_SPEED_OFF = 0;
const int CASE_MOTOR_A_SPEED_LOW = 1;
const int CASE_MOTOR_A_SPEED_MEDIUM = 2;
const int CASE_MOTOR_A_SPEED_HIGH = 3;
const int CASE_MOTOR_B_SPEED_OFF = 10;
const int CASE_MOTOR_B_SPEED_LOW = 11;
const int CASE_MOTOR_B_SPEED_MEDIUM = 12;
const int CASE_MOTOR_B_SPEED_HIGH = 13;
const int CASE_MAGNET_A_ON = 30; // Magnet A ON
const int CASE_MAGNET_A_OFF = 31; // Magnet A OFF
const int CASE_MAGNET_B_ON = 20; // Magnet B ON
const int CASE_MAGNET_B_OFF = 21; // Magnet B OFF

// Define speed constants
const int SPEED_OFF = 0; // Off
const int SPEED_LOW = 80; // Low speed
const int SPEED_MEDIUM = 90; // Medium speed
const int SPEED_HIGH = 100; // High speed
// Define magnet timeout
const unsigned long MAGNET_TIMEOUT = 10000; // 10 seconds

// Define the number of characters to read
const byte numChars = 32;
char receivedChars[numChars];   // an array to store the received data

// Temporary variabless
unsigned long startTime = 0; 
boolean newData = false;
int pwmPin = 0;
int prevPin = 0; 
int rcvdNumber = 0;             
int dataNumber = 0;             
int prevNumber = 0;        

// Function pointer for reset
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
// 100-180 MIN/MAX VOLT LIMIT (4V-8V)
// 80-100 CALIBRATION LIMIT (3.2V-4V)
void ProcessSpeedInput() {
    if (newData == true) {
        rcvdNumber = atoi(receivedChars);  
        Serial.println(receivedChars);
        // Check Input
        switch (rcvdNumber) {
            case CASE_MOTOR_A_SPEED_OFF:
                dataNumber = SPEED_OFF; // Off
                pwmPin = pwmPinA; 
                break;
            case CASE_MOTOR_A_SPEED_LOW:
                dataNumber = SPEED_LOW; // Low speed
                pwmPin = pwmPinA; 
                break;
            case CASE_MOTOR_A_SPEED_MEDIUM:
                dataNumber = SPEED_MEDIUM; // Medium speed
                pwmPin = pwmPinA; 
                break;
            case CASE_MOTOR_A_SPEED_HIGH:
                dataNumber = SPEED_HIGH; // High speed
                pwmPin = pwmPinA; 
                break;
            case CASE_MOTOR_B_SPEED_OFF:
                dataNumber = SPEED_OFF; // Off
                pwmPin = pwmPinB; 
                break;
            case CASE_MOTOR_B_SPEED_LOW:
                dataNumber = SPEED_LOW; // Low speed
                pwmPin = pwmPinB; 
                break;
            case CASE_MOTOR_B_SPEED_MEDIUM:
                dataNumber = SPEED_MEDIUM; // Medium speed
                pwmPin = pwmPinB; 
                break;
            case CASE_MOTOR_B_SPEED_HIGH:
                dataNumber = SPEED_HIGH; // High speed
                pwmPin = pwmPinB; 
                break;
            case CASE_MAGNET_A_OFF:
                digitalWrite(relayA, LOW);
                Serial.println("Magnet A - OFF");
                newData = false;
                return;
            case CASE_MAGNET_A_ON:
                Serial.println("Magnet A - ON");
                digitalWrite(relayA, HIGH); // Turn magnet ON
                startTime = millis();
                while (millis() - startTime < MAGNET_TIMEOUT);
                digitalWrite(relayA, LOW); // Turn magnet OFF
                Serial.println("Magnet A - OFF");
                newData = false;
                return;
            case CASE_MAGNET_B_OFF:
                digitalWrite(relayB, LOW);
                Serial.println("Magnet B - OFF");
                newData = false;
                return;
            case CASE_MAGNET_B_ON:
                Serial.println("Magnet B - ON");
                digitalWrite(relayB, HIGH); // Turn magnet ON
                startTime = millis();
                while (millis() - startTime < MAGNET_TIMEOUT);
                digitalWrite(relayB, LOW); // Turn magnet OFF
                Serial.println("Magnet B - OFF");
                newData = false;
                return;
            case -1:
                resetFunc(); // Reset the device
                break;
            default:
                Serial.println("Invalid input. Please enter a number between 0 and 4.");
                newData = false;
                return; // Exit if the input is invalid
        }
        // Motor Operation Logic
        if (dataNumber == prevNumber && pwmPin == prevPin) {
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
        prevPin = pwmPin; // Store the last valid number
        newData = false;
    }
}

void setup() {
    Serial.begin(9600);
    Serial.println("\nNANOSTATION_MV");
    Serial.println("\n<Vibration/Magnet Station is ready for launch!>");
    Serial.println("\nSet vibration motor speed Motor A:(0-3), Motor B:(10-13)\nSet Magnet A:(20-21) Magnet B:(30-31)\nType (-1) to reset the device.");
    // Initialize Relay
    pinMode(relayA, OUTPUT);
    pinMode(relayB, OUTPUT);
    // Initialize Motor Driver
    pinMode(enablePinA, OUTPUT);
    pinMode(enablePinB, OUTPUT);
    pinMode(pwmPinA, OUTPUT);
    pinMode(pwmPinB, OUTPUT);
    pinMode(gndPinA, OUTPUT);
    pinMode(gndPinB, OUTPUT);
    // Set the initial state of relay
    digitalWrite(relayA, LOW); // Relay A OFF
    digitalWrite(relayB, LOW); // Relay B OFF
    // Set the initial state of motor
    digitalWrite(enablePinA, LOW); // Disnable the motor
    digitalWrite(enablePinB, LOW); // Disable the motor
    analogWrite(pwmPinA, 0); // Ensure PWM is off initially
    analogWrite(pwmPinB, 0); // Ensure PWM is off initially
    digitalWrite(gndPinA, LOW); // Ensure PWM is off initially
    digitalWrite(gndPinB, LOW); // Ensure PWM is off initially
    digitalWrite(enablePinA, HIGH); // Enable the motor
    digitalWrite(enablePinB, HIGH); // Enable the motor
}

void loop() {
    _processString();
    ProcessSpeedInput();
}
// This code is for a simple Arduino sketch that reads input from the serial port
// to control a vibration motor. It allows the user to set the motor speed