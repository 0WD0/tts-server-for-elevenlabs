# ElevenLabs TTS Server

A simple Flask server that provides an API interface to ElevenLabs text-to-speech service.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file and add your ElevenLabs API key:
```
ELEVENLABS_API_KEY=your_api_key_here
```

## Running the Server

```bash
python app.py
```

The server will start on `http://localhost:5000`

## API Endpoints

### 1. Text to Speech
- **Endpoint**: `/tts`
- **Method**: POST
- **Body**:
```json
{
    "text": "Text to convert to speech",
    "voice": "Adam"  // Optional, defaults to "Adam"
}
```
- **Response**: Audio file (MP3)

### 2. List Available Voices
- **Endpoint**: `/voices`
- **Method**: GET
- **Response**: List of available voices and their IDs

## Example Usage

Using curl:
```bash
# Convert text to speech
curl -X POST http://localhost:5000/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello, world!", "voice":"Adam"}' \
  --output speech.mp3

# List available voices
curl http://localhost:5000/voices
```
