import os
import json
from dotenv import load_dotenv
import websockets

# Load the API key from the .env file
load_dotenv()
ELEVENLABS_API_KEY = os.getenv("sk_f94c4ca02c61136a0d8b6ecc22616c5ace829db45341a02c")

voice_id = 'JBFqnCBsd6RMkjVDRZzb'
# model_id = 'eleven_flash_v2_5'
model_id = 'eleven_multilingual_v2'

async def text_to_speech_ws_streaming(voice_id, model_id):
    uri = f"wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input?model_id={model_id}"
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({
            "text": " ",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.8, "use_speaker_boost": False},
            "generation_config": {
                "chunk_length_schedule": [120, 160, 250, 290]
            },
            "xi_api_key": ELEVENLABS_API_KEY,
        }))

        text = "The twilight sun cast its warm golden hues upon the vast rolling fields, saturating the landscape with an ethereal glow. Silently, the meandering brook continued its ceaseless journey, whispering secrets only the trees seemed privy to."
        await websocket.send(json.dumps({"text": text}))

        # Send empty string to indicate the end of the text sequence which will close the websocket connection
        await websocket.send(json.dumps({"text": ""}))

        ...

