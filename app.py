from flask import Flask, request, jsonify, send_file
from elevenlabs import generate, set_api_key, voices as elevenlabs_voices
from dotenv import load_dotenv
import os
import io

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Set up ElevenLabs API key
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
if ELEVENLABS_API_KEY:
    set_api_key(ELEVENLABS_API_KEY)

# Voice mapping from Coqui-TTS to ElevenLabs
VOICE_MAPPING = {
    "default": "Adam",  # 默认使用 Adam 声音
}

@app.route('/api/tts', methods=['POST'])
def coqui_style_tts():
    """
    处理 Coqui-TTS 格式的请求并转换为 ElevenLabs 格式
    Coqui-TTS 格式:
    {
        "text": "text to speak",
        "speaker_id": "speaker_name",
        "language_id": "en"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400
        
        text = data.get('text')
        speaker_id = data.get('speaker_id', 'default')
        
        # 将 Coqui-TTS 的 speaker_id 映射到 ElevenLabs 的 voice
        voice = VOICE_MAPPING.get(speaker_id, 'Adam')
        
        # 生成音频
        audio = generate(
            text=text,
            voice=voice,
            model="eleven_multilingual_v2"
        )
        
        # 创建内存缓冲区
        audio_buffer = io.BytesIO(audio)
        audio_buffer.seek(0)
        
        return send_file(
            audio_buffer,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name='speech.mp3'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/speakers', methods=['GET'])
def list_speakers():
    """
    返回可用的说话人列表，格式与 Coqui-TTS 兼容
    """
    try:
        available_voices = elevenlabs_voices()
        speakers = []
        
        for voice in available_voices:
            speakers.append({
                "id": voice.voice_id,
                "name": voice.name,
                "language": ["en"]  # ElevenLabs 支持多语言，这里简化处理
            })
        
        return jsonify({
            "success": True,
            "speakers": speakers
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/languages', methods=['GET'])
def list_languages():
    """
    返回支持的语言列表，格式与 Coqui-TTS 兼容
    """
    # ElevenLabs 支持多语言，这里返回主要支持的语言
    languages = [
        {"id": "en", "name": "English"},
        {"id": "zh", "name": "Chinese"},
        {"id": "es", "name": "Spanish"},
        {"id": "fr", "name": "French"},
        {"id": "de", "name": "German"},
        {"id": "it", "name": "Italian"},
        {"id": "pt", "name": "Portuguese"},
        {"id": "pl", "name": "Polish"},
        {"id": "tr", "name": "Turkish"},
        {"id": "ru", "name": "Russian"},
        {"id": "nl", "name": "Dutch"},
        {"id": "cs", "name": "Czech"},
        {"id": "ar", "name": "Arabic"},
        {"id": "hi", "name": "Hindi"}
    ]
    
    return jsonify({
        "success": True,
        "languages": languages
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
