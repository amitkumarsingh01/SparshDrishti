#include <WiFi.h>
#include <HTTPClient.h>

// Wi-Fi credentials
const char* ssid = "Project";
const char* password = "12345678";

// Server URLs
const char* captureServer = "http://192.168.54.58:5000/capture";   // Raspberry Pi's server for image capture
const char* stateServer = "http://192.168.54.200:5000/update";       // Server for sending switch state updates
const char* audioServer = "http://192.168.54.58:5000/audio_chain";

// Pin configuration
#define SWITCH_PIN 13        // Pin for the switch
#define BUTTON_PIN 27         // Pin for image capture button
#define AUDIO_PIN 14
const int trigPin = 5;       // Trigger pin of the ultrasonic sensor
const int echoPin = 18;      // Echo pin of the ultrasonic sensor
const int buzzerPin = 15;    // Pin connected to the buzzer

// Timing variables
unsigned long currentTime, previousTime, delayTime;

// Ultrasonic sensor variables
long duration;
int distance;

// Button state variables
int lastSwitchState = HIGH;  // Last state of the switch
bool currentState = false;   // Current toggle state

void setup() {
  // Serial communication setup
  Serial.begin(115200);
  
  // Pin mode setup
  pinMode(SWITCH_PIN, INPUT_PULLUP);   // Set switch pin as input with pull-up
  pinMode(BUTTON_PIN, INPUT_PULLUP);   // Set button pin as input with pull-up
  pinMode(AUDIO_PIN, INPUT_PULLUP);
  pinMode(trigPin, OUTPUT);            // Set ultrasonic trigger pin as output
  pinMode(echoPin, INPUT);             // Set ultrasonic echo pin as input
  pinMode(buzzerPin, OUTPUT);          // Set buzzer pin as output
  digitalWrite(buzzerPin, LOW);        // Initialize buzzer to LOW

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" Connected!");
}

void loop() {
  // Handle switch toggle and send state to server
  int switchState = digitalRead(SWITCH_PIN);
  if (switchState == LOW && lastSwitchState == HIGH) {
    currentState = !currentState;
    String stateString = currentState ? "True" : "False";
    Serial.println("Switch Toggled: " + stateString);
    
    // Send switch state to the server
    sendSwitchState(stateString);

    // Wait for the button release to avoid multiple toggles
    while (digitalRead(SWITCH_PIN) == LOW) {
      delay(10);
    }
  }
  lastSwitchState = switchState;  // Update last switch state
  
  // Handle image capture button press
  if (digitalRead(BUTTON_PIN) == LOW) {
    Serial.println("Button pressed, sending capture request...");
    sendImageCaptureRequest();
    
    delay(1000);  // Debounce delay to prevent multiple triggers
  }

  if (digitalRead(AUDIO_PIN) == LOW) {
    Serial.println("Button pressed, sending audio request...");
    sendAudioCaptureRequest();
    
    delay(1000);  // Debounce delay to prevent multiple triggers
  }

  // Handle ultrasonic sensor and buzzer
  handleUltrasonicSensor();
  
  delay(50);  // Small delay for debouncing and sensor reading stabilization
}

// Function to handle ultrasonic sensor readings and buzzer sound
void handleUltrasonicSensor() {
  currentTime = millis(); // Get the current time

  // Clear the trigger pin
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  // Set the trigger pin high for 10 microseconds
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  // Read the echo pin and calculate distance
  duration = pulseIn(echoPin, HIGH);
  distance = duration * 0.034 / 2;

  // Print distance on the serial monitor
  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.println(" cm");

  // If distance is within 100cm, buzz the buzzer
  if (distance < 100 && distance >= 2) {
    delayTime = map(distance, 2, 100, 200, 400); // Map distance to delay time between 200 and 400 ms
    digitalWrite(buzzerPin, LOW); // Turn the buzzer on

    // Control the buzzer's on-off timing
    if (currentTime - previousTime >= delayTime) {
      digitalWrite(buzzerPin, HIGH); // Turn the buzzer off
      previousTime = currentTime;   // Reset the timer
    }
  } else {
    digitalWrite(buzzerPin, HIGH);  // Turn off the buzzer if distance exceeds 100 cm
  }
}

// Function to send switch state to the server
void sendSwitchState(String state) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(stateServer);  // Specify the server URL
    http.addHeader("Content-Type", "application/json");  // Specify content type

    // Create JSON payload
    String payload = "{\"state\":\"" + state + "\"}";
    
    int httpResponseCode = http.POST(payload);  // Send HTTP POST request
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("Response: " + response);
    } else {
      Serial.println("Error in sending request");
    }

    http.end();  // Close connection
  }
}

// Function to send an image capture request to the Raspberry Pi
void sendImageCaptureRequest() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(captureServer);  // Specify the server URL

    int httpResponseCode = http.POST("");  // Send HTTP POST request
    if (httpResponseCode == 200) {
      Serial.println("Image capture request sent successfully");
    } else {
      Serial.print("Error: ");
      Serial.println(httpResponseCode);
    }

    http.end();  // Close connection
  } else {
    Serial.println("Error in WiFi connection");
  }
}

// Function to send an audio capture request to the Raspberry Pi
void sendAudioCaptureRequest() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(audioServer);  // Specify the server URL

    int httpResponseCode = http.POST("");  // Send HTTP POST request
    if (httpResponseCode == 200) {
      Serial.println("Audio capture request sent successfully");
    } else {
      Serial.print("Error: ");
      Serial.println(httpResponseCode);
    }

    http.end();  // Close connection
  } else {
    Serial.println("Error in WiFi connection");
  }
}