from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv
import os
from api_key_manager import ApiKeyManager
from elevenlabs import VoiceSettings

# Load environment variables
load_dotenv()

# Constants
TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

# Initialize API key manager
api_keys = os.getenv('ELEVENLABS_API_KEYS', '').split(',')
if not api_keys or not api_keys[0]:
	api_keys = [os.getenv('ELEVENLABS_API_KEY', '')]

key_manager = ApiKeyManager(
	keys=[k.strip() for k in api_keys if k.strip()],
	consecutive_errors_limit=2  # 连续错误2次后永久禁用
)

# Initialize FastAPI app
app = FastAPI(
	title="TTS Proxy Server",
	description="A proxy server that converts Coqui-TTS style requests to ElevenLabs API calls",
	version="1.0.0"
)

# ElevenLabs API configuration
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1"
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Adam voice ID

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

@app.get("/api/key-status")
async def get_key_status():
	"""获取所有 API key 的状态"""
	return JSONResponse(content=key_manager.get_status())

@app.post("/api/tts")
async def text_to_speech(
	text: str = Form(...),
	speaker_id: str = Form(default="default"),
	language_id: str = Form(default="en")
):
	"""
	将文本转换为语音
	- 接受 form-urlencoded 格式的请求
	- 使用 ElevenLabs API 生成语音
	"""
	try:
		# 获取可用的客户端
		key = key_manager.get_key()
		client = key_manager.get_client()
		if not key or not client:
			raise HTTPException(
				status_code=503,
				detail="No API keys available. Please try again later."
			)

		try:
			# 使用 SDK 生成语音
			response = client.text_to_speech.convert(
				voice_id=speaker_id if speaker_id != "default" else DEFAULT_VOICE_ID,
				text=text,
				model_id="eleven_multilingual_v2",
				voice_settings=VoiceSettings(
					stability=0.5,
					similarity_boost=0.75,
					use_speaker_boost=True
				)
			)
			
			# 保存到临时文件
			temp_file = os.path.join(TEMP_DIR, "speech.mp3")
			with open(temp_file, "wb") as f:
				for chunk in response:
					if chunk:
						f.write(chunk)
			
			# 报告成功
			key_manager.report_success(key)
			
			return FileResponse(
				temp_file,
				media_type="audio/mpeg",
				filename="speech.mp3"
			)
			
		except Exception as e:
			# 报告错误
			key_manager.report_error(key, str(e))
			raise HTTPException(
				status_code=500,
				detail=str(e)
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
		key = key_manager.get_key()
		client = key_manager.get_client()
		if not key or not client:
			raise HTTPException(
				status_code=503,
				detail="No API keys available"
			)
			
		try:
			response = client.voices.get_all()
			speakers = []
			
			for voice in response.voices:
				speakers.append(Speaker(
					id=voice.voice_id,
					name=voice.name,
					language=["en"]  # ElevenLabs 支持多语言，这里简化处理
				))
			
			key_manager.report_success(key)
			return SpeakersResponse(success=True, speakers=speakers)
			
		except Exception as e:
			key_manager.report_error(key, str(e))
			raise HTTPException(status_code=500, detail=str(e))
			
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
