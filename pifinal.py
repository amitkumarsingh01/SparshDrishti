from flask import Flask, request
import cv2
import os
import time
import requests
from pydub import AudioSegment
import simpleaudio as sa
import speech_recognition as sr

app = Flask(__name__)

# Set the URL of the laptop where the image will be sent
laptop_url = 'http://192.168.55.200:5000/upload'  # Change to your laptop's IP and port
laptop_url2 = 'http://192.168.55.200:5000/text_chain'

# Directory to save audio files locally on the Raspberry Pi
save_directory = r'/home/sujith/Desktop/dsu/audio_files'
if not os.path.exists(save_directory):
    os.makedirs(save_directory)

def play_audio(audio_path):
    try:
        print("Playing audio...")
        audio = AudioSegment.from_file(audio_path, format="mp3")
        play_obj = sa.play_buffer(audio.raw_data, num_channels=audio.channels, 
                                  bytes_per_sample=audio.sample_width, 
                                  sample_rate=audio.frame_rate)
        play_obj.wait_done()
    except Exception as e:
        print(f"Error playing audio: {e}")

@app.route('/audio_chain', methods=['POST'])
def record_audio():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening... Speak now.")

        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
        except sr.WaitTimeoutError:
            print("No speech detected within the timeout period.")
            return "No speech detected within the timeout period.", 400
    try:
        # Convert speech to text
        text = recognizer.recognize_google(audio)
        print(f"Recognized Text: {text}")
        response = requests.post(laptop_url2, json={"text": text})
        if response.status_code == 200:
            response_data = response.json()
            audio_file_url = response_data["audio_file"]

            # Download the audio file from the URL and save it on the Pi
            audio_path = os.path.join(save_directory, "output.mp3")
            audio_content = requests.get(audio_file_url)

            if audio_content.status_code == 200:
                with open(audio_path, 'wb') as f:
                    f.write(audio_content.content)
                print(f"Audio file saved to: {audio_path}")

                # Play the downloaded audio file
                play_audio(audio_path)
            else:
                print("Error downloading audio file from the laptop.")

            return "Audio processed and played successfully.", 200

    except sr.UnknownValueError:
        print("Could not understand audio.")
        return "Could not understand audio.", 400
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
        return "Could not request results.", 400

@app.route('/capture', methods=['POST'])
def capture_image():
    # Initialize the webcam (use 0 for the default camera)
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        return "Error: Could not open webcam.", 500

    # Capture a new frame immediately when requested
    ret, frame = camera.read()
    if ret:
        # Save the captured image temporarily
        temp_image_path = 'temp_image.jpg'
        cv2.imwrite(temp_image_path, frame)
        print(f"Current image captured, sending to laptop...")

        # Open the image file and send it to the laptop
        with open(temp_image_path, 'rb') as img_file:
            response = requests.post(laptop_url, files={'image': img_file})

        if response.status_code == 200:
            print("Image successfully sent to laptop, waiting for response...")

            # Wait for the response from the laptop, which should include the audio file URL
            response_data = response.json()
            audio_file_url = response_data["audio_file"]

            # Download the audio file from the URL and save it on the Pi
            audio_path = os.path.join(save_directory, "output.mp3")
            audio_content = requests.get(audio_file_url)

            if audio_content.status_code == 200:
                with open(audio_path, 'wb') as f:
                    f.write(audio_content.content)
                print(f"Audio file saved to: {audio_path}")

                # Play the downloaded audio file
                play_audio(audio_path)
            else:
                print("Error downloading audio file from the laptop.")

            # Release the camera resource after capturing and sending the image
            camera.release()

            return "Image processed, audio saved, and played successfully.", 200
        else:
            camera.release()
            return "Error: Could not send image to laptop.", 500
    else:
        camera.release()
        return "Error: Could not capture image.", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Run the Flask server on port 5000
