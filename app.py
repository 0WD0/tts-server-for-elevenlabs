from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import List, Optional
import requests
from dotenv import load_dotenv
import os
import io
from api_key_manager import ApiKeyManager

# Load environment variables
load_dotenv()

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
		# 获取可用的 API key
		api_key = key_manager.get_key()
		if not api_key:
			raise HTTPException(
				status_code=503,
				detail="No API keys available. Please try again later."
			)

		# 将 Coqui-TTS 的 speaker_id 映射到 ElevenLabs 的 voice
		voice_id = VOICE_MAPPING.get(speaker_id, DEFAULT_VOICE_ID)
		
		# 准备请求
		url = f"{ELEVENLABS_API_URL}/text-to-speech/{voice_id}"
		headers = {
			"Accept": "audio/mpeg",
			"xi-api-key": api_key,
			"Content-Type": "application/json"
		}
		data = {
			"text": text,
			"model_id": "eleven_multilingual_v2",
			"voice_settings": {
				"stability": 0.5,
				"similarity_boost": 0.75
			}
		}
		
		# 发送请求到 ElevenLabs API
		response = requests.post(url, json=data, headers=headers)
		
		if response.status_code == 200:
			key_manager.report_success(api_key)
		else:
			error_msg = f"ElevenLabs API error: {response.text}"
			key_manager.report_error(api_key, error_msg)
			raise HTTPException(
				status_code=response.status_code,
				detail=error_msg
			)
		
		# 创建临时文件
		temp_dir = os.path.join(os.path.dirname(__file__), "temp")
		os.makedirs(temp_dir, exist_ok=True)
		temp_file = os.path.join(temp_dir, "speech.mp3")
		
		# 保存音频到临时文件
		with open(temp_file, "wb") as f:
			f.write(response.content)
		
		return FileResponse(
			temp_file,
			media_type="audio/mpeg",
			filename="speech.mp3"
		)
		
	except requests.exceptions.RequestException as e:
		if api_key:
			key_manager.report_error(api_key, str(e))
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
		headers = {"xi-api-key": key_manager.get_key()}
		
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
