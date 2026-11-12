#include <ESP32Servo.h>

Servo myServo;

void setup() {
  Serial.begin(115200);

  // 1. Allocate all 4 hardware PWM timers for ESP32Servo
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

  // 2. Set frequency and attach
  myServo.setPeriodHertz(50); // Standard 50Hz servo
  myServo.attach(26, 500, 2400);

  Serial.println("Servo test started");
}

void loop() {
  Serial.println("Moving to 0 degrees");
  myServo.write(0);
  delay(2000);

  Serial.println("Moving to 90 degrees");
  myServo.write(90);
  delay(2000);

  Serial.println("Moving to 180 degrees");
  myServo.write(180);
  delay(2000);
}