from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import List, Optional
import requests
from dotenv import load_dotenv
import os
import io

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
	title="TTS Proxy Server",
	description="A proxy server that converts Coqui-TTS style requests to ElevenLabs API calls",
	version="1.0.0"
)

# ElevenLabs API configuration
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
if not ELEVENLABS_API_KEY:
	raise ValueError("ELEVENLABS_API_KEY not found in environment variables")

ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1"
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Adam voice ID

# Voice mapping from Coqui-TTS to ElevenLabs
VOICE_MAPPING = {
	"default": DEFAULT_VOICE_ID,
}

# Pydantic models for request/response validation
class TTSRequest(BaseModel):
	text: str = Field(..., description="Text to be converted to speech")
	speaker_id: Optional[str] = Field(default="default", description="Speaker ID for voice selection")
	language_id: Optional[str] = Field(default="en", description="Language ID for the text")

class Speaker(BaseModel):
	id: str
	name: str
	language: List[str]

class SpeakersResponse(BaseModel):
	success: bool
	speakers: List[Speaker]

class Language(BaseModel):
	id: str
	name: str

class LanguagesResponse(BaseModel):
	success: bool
	languages: List[Language]

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.post("/api/tts")
async def text_to_speech(request: TTSRequest):
	"""
	将文本转换为语音
	- 接受 Coqui-TTS 格式的请求
	- 使用 ElevenLabs API 生成语音
	"""
	try:
		# 将 Coqui-TTS 的 speaker_id 映射到 ElevenLabs 的 voice
		voice_id = VOICE_MAPPING.get(request.speaker_id, DEFAULT_VOICE_ID)
		
		# 准备请求
		url = f"{ELEVENLABS_API_URL}/text-to-speech/{voice_id}"
		headers = {
			"Accept": "audio/mpeg",
			"xi-api-key": ELEVENLABS_API_KEY,
			"Content-Type": "application/json"
		}
		data = {
			"text": request.text,
			"model_id": "eleven_multilingual_v2",
			"voice_settings": {
				"stability": 0.5,
				"similarity_boost": 0.75
			}
		}
		
		# 发送请求到 ElevenLabs API
		response = requests.post(url, json=data, headers=headers)
		
		if response.status_code != 200:
			raise HTTPException(
				status_code=response.status_code,
				detail=f"ElevenLabs API error: {response.text}"
			)
		
		# 创建内存缓冲区
		audio_buffer = io.BytesIO(response.content)
		audio_buffer.seek(0)
		
		return StreamingResponse(
			audio_buffer,
			media_type="audio/mpeg",
			headers={
				"Content-Disposition": "attachment; filename=speech.mp3"
			}
		)
		
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/speakers", response_model=SpeakersResponse)
async def list_speakers():
	"""
	获取所有可用的说话人列表
	返回格式与 Coqui-TTS 兼容
	"""
	try:
		# 调用 ElevenLabs API 获取可用的声音列表
		url = f"{ELEVENLABS_API_URL}/voices"
		headers = {"xi-api-key": ELEVENLABS_API_KEY}
		
		response = requests.get(url, headers=headers)
		if response.status_code != 200:
			raise HTTPException(
				status_code=response.status_code,
				detail=f"ElevenLabs API error: {response.text}"
			)
		
		voices_data = response.json()
		speakers = []
		
		for voice in voices_data["voices"]:
			speakers.append(Speaker(
				id=voice["voice_id"],
				name=voice["name"],
				language=["en"]  # ElevenLabs 支持多语言，这里简化处理
			))
		
		return SpeakersResponse(success=True, speakers=speakers)
		
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/languages", response_model=LanguagesResponse)
async def list_languages():
	"""
	获取支持的语言列表
	返回格式与 Coqui-TTS 兼容
	"""
	languages = [
		Language(id="en", name="English"),
		Language(id="zh", name="Chinese"),
		Language(id="es", name="Spanish"),
		Language(id="fr", name="French"),
		Language(id="de", name="German"),
		Language(id="it", name="Italian"),
		Language(id="pt", name="Portuguese"),
		Language(id="pl", name="Polish"),
		Language(id="tr", name="Turkish"),
		Language(id="ru", name="Russian"),
		Language(id="nl", name="Dutch"),
		Language(id="cs", name="Czech"),
		Language(id="ar", name="Arabic"),
		Language(id="hi", name="Hindi")
	]
	
	return LanguagesResponse(success=True, languages=languages)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
	"""
	渲染主页
	"""
	return templates.TemplateResponse(
		"index.html",
		{"request": request}
	)

if __name__ == "__main__":
	import uvicorn
	uvicorn.run(app, host="0.0.0.0", port=5002)
