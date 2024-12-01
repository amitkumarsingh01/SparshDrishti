from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import pygame
import requests
from dotenv import load_dotenv
import google.generativeai as gai
from PIL import Image
from gtts import gTTS
import random
import base64
import mimetypes

app = Flask(__name__)

save_directory = 'C://Users//aksml//Development//Hardware//Avishkar//DSU_Final//public'
# save_directory = r'C:\Users\aksml\Development\Hardware\Avishkar\DSU_Final\Hardware ESP32\ffinal\public\audio.wav'
laptop_host = '192.168.54.200'

id_file_path = os.path.join(save_directory, 'last_id.txt')

if not os.path.exists(save_directory):
    os.makedirs(save_directory)

load_dotenv()

gai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = gai.GenerativeModel("gemini-1.5-flash-latest")
chat = model.start_chat(history=[])

switch_state = False
pygame.init()

def get_next_id():
    starting_id = 101

    if not os.path.exists(id_file_path):
        with open(id_file_path, 'w') as f:
            f.write(str(starting_id - 1)) 

    with open(id_file_path, 'r') as f:
        last_id = int(f.read().strip())

    next_id = last_id + 1
    while os.path.exists(os.path.join(save_directory, f"{next_id}.jpg")):
        next_id += 1

    with open(id_file_path, 'w') as f:
        f.write(str(next_id))

    return next_id

# Function to play audio when the state is toggled to True
def play_audio():
    audio_path = os.path.join(os.path.dirname(__file__), 'public', 'audio.wav')
    if os.path.exists(audio_path):
        pygame.mixer.init()
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()
    else:
        print("Audio file not found!")

# Function to process the image using the Gemini model
def gemini_img_bot(image_path):
    # Open the image
    image = Image.open(image_path)

    input_message = "Describe the image for blind people short and clear within 75-80 words."
    
    response = chat.send_message([input_message, image]) 
    
    return response.text

# Function to process the text using the Gemini model
def gemini_text_bot(text):
    prompt_text = f"""
        Based on the old responses, generate a new follow up response to the following text (with in 75-80 words):

        {text}
    """

    response = chat.send_message(prompt_text) 
    return response.text

# Function to send data to the specified server
def send_data_to_server(data):
    url = "https://api.golain.io/e24db58e-f36d-43d4-babd-a72ca77b4184/wke/Send_data/"
    headers = {
        "Authorization": f"APIKEY {os.getenv('GOLAIN_1_API_KEY')}",
        "Content-Type": "application/json",
        "ORG-ID": "5f7a2aee-a7f3-4f01-80fa-962af495049b"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending data to server: {e}")
        return {"status": "failed", "message": str(e)}
    
def encode_image_to_base64(image_path):
    try:
        # Detect MIME type (e.g., image/png or image/jpeg)
        mime_type, _ = mimetypes.guess_type(image_path)

        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

        # Add the MIME prefix to the Base64 string
        return f"data:{mime_type};base64,{encoded_string}"
    except FileNotFoundError:
        print(f"File not found: {image_path}")
        return None

@app.route('/upload', methods=['POST'])
def upload_image():
    new_id = get_next_id()
    if 'image' not in request.files:
        return "No image file found in the request.", 400

    image_file = request.files['image']
    if image_file.filename == '':
        return "No selected file.", 400

    image_path = os.path.join(save_directory, f"{new_id}.jpg")
    image_file.save(image_path)
    # print(f"Image received and saved to {image_path}")

    response_text = gemini_img_bot(image_path)

    # Save the description to a text file
    output_text_path = os.path.join(save_directory, f"{new_id}.txt")
    with open(output_text_path, "w") as f:
        f.write(response_text)

    # Convert the text to speech and save as an audio file
    output_audio_path = os.path.join(save_directory, f"{new_id}.mp3")
    tts = gTTS(text=response_text, lang='en')
    tts.save(output_audio_path)

    audio_url = f'http://{laptop_host}:5000/audio/{new_id}.mp3'
    text_url = f'http://{laptop_host}:5000/text/{new_id}.txt'

    # Prepare data to send to the external server
    data_to_send = {
        "id": new_id,
        "text": response_text,
        "image": encode_image_to_base64(image_path),
    }

    # Send data to the external server
    # server_response = send_data_to_server(data_to_send)
    # print(f"Response from server: {server_response}")

    return jsonify({
        "message": "Image successfully processed.",
        "description": response_text,
        "text_file": text_url,
        "audio_file": audio_url,
        # "server_response": server_response,
        "id": new_id
    }), 200

@app.route('/text_chain', methods=['POST'])
def audio_chain():
    new_id = get_next_id()
    data = request.get_json()
    print(data)
    if 'text' not in data:
        return "No text found in the request.", 400

    response_text = gemini_text_bot(data['text'])

    print(response_text)

    # Save the description to a text file
    output_text_path = os.path.join(save_directory, f"{new_id}.txt")
    with open(output_text_path, "w") as f:
        f.write(response_text)

    # Convert the text to speech and save as an audio file
    output_audio_path = os.path.join(save_directory, f"{new_id}.mp3")
    tts2 = gTTS(text=response_text, lang='en')
    tts2.save(output_audio_path)

    audio_url = f'http://{laptop_host}:5000/audio/{new_id}.mp3'
    text_url = f'http://{laptop_host}:5000/text/{new_id}.txt'

    return jsonify({
        "message": "Text successfully processed.",
        "description": response_text,
        "text_file": text_url,
        "audio_file": audio_url,
        "id": new_id
    }), 200

# Route to serve the audio file
@app.route('/audio/<filename>', methods=['GET'])
def serve_audio(filename):
    return send_from_directory(save_directory, filename)

# Route to serve the text file
@app.route('/text/<filename>', methods=['GET'])
def serve_text(filename):
    return send_from_directory(save_directory, filename)

# Route to update the switch state and play audio when necessary
@app.route('/update', methods=['POST'])
def update():
    global switch_state
    data = request.get_json()
    if 'state' in data:
        new_state = data['state'].lower() == "true"
        if new_state and not switch_state:  
            print("Switch State Updated to True - Playing Audio")
            play_audio()
        switch_state = new_state  
        return jsonify({'status': 'success', 'message': f'State updated to {switch_state}'}), 200
    return jsonify({'status': 'failed', 'message': 'Invalid data'}), 400

@app.route('/state')
def state():
    global switch_state
    return jsonify({'switch_state': switch_state})

# Route to serve images
@app.route('/images/<filename>', methods=['GET'])
def serve_image(filename):
    return send_from_directory(save_directory, filename)

@app.route('/')
def index():
    return render_template('index.html')

# Run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)