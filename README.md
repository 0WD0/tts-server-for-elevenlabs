# ElevenLabs TTS 代理服务器

这是一个基于 FastAPI 的代理服务器，用于将 Coqui-TTS 格式的请求转换为 ElevenLabs API 调用。支持 Web 界面和 API 接口。

## 功能特点

- 使用官方 ElevenLabs Python SDK
- 支持 Coqui-TTS 格式的 API 请求
- 提供美观的 Web 界面
- 支持多种声音选择
- 支持多语言
- 实时语音生成和播放
- 支持多 API key 管理和自动切换

## 安装

1. 克隆仓库：
```bash
git clone <repository_url>
cd elevenlabs
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
创建 `.env` 文件并添加你的 ElevenLabs API key。你可以配置单个 key 或多个 key：

```env
# 单个 API key
ELEVENLABS_API_KEY=your_api_key_here

# 或者多个 API key（用逗号分隔）
ELEVENLABS_API_KEYS=key1,key2,key3
```

如果配置了 `ELEVENLABS_API_KEYS`，服务器会自动在多个 key 之间切换，当某个 key 出现错误时会自动切换到下一个可用的 key。每个 key 会维护独立的错误计数，连续两次错误后会暂时禁用该 key。服务器重启会自动清空所有 key 的状态。

## 依赖项

- fastapi==0.109.0
- uvicorn==0.27.0
- requests==2.31.0
- python-dotenv==1.0.0
- pydantic==2.6.0
- jinja2==3.1.3
- python-multipart==0.0.5
- elevenlabs==1.50.7

## 运行服务器

```bash
python app.py
```

服务器将在 `http://localhost:5002` 启动。

## API 使用说明

### 1. 文本转语音 (TTS)

**Endpoint:** `POST /api/tts`

**Content-Type:** `application/x-www-form-urlencoded`

**参数：**
- `text` (必需): 要转换的文本
- `speaker_id` (可选): ElevenLabs 声音 ID，默认为系统选择
- `language_id` (可选): 语言 ID，默认为 "en"

**示例：**
```bash
curl -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data "text=Hello World&speaker_id=21m00Tcm4TlvDq8ikWAM&language_id=en" \
  http://localhost:5002/api/tts \
  --output speech.mp3
```

### 2. 获取可用说话人列表

**Endpoint:** `GET /api/speakers`

**响应示例：**
```json
{
  "success": true,
  "speakers": [
    {
      "id": "21m00Tcm4TlvDq8ikWAM",
      "name": "Rachel",
      "language": ["en"]
    }
  ]
}
```

### 3. 获取支持的语言列表

**Endpoint:** `GET /api/languages`

**响应示例：**
```json
{
  "success": true,
  "languages": [
    {
      "id": "en",
      "name": "English"
    }
  ]
}
```

### 4. 获取 API Key 状态

**Endpoint:** `GET /api/key-status`

**响应示例：**
```json
{
  "success": true,
  "keys": [
    {
      "key": "xxxxx",  // 部分隐藏的 key
      "is_active": true,
      "error_count": 0,
      "last_used": "2024-02-08T10:30:00Z"
    }
  ]
}
```

## 错误处理

系统会自动处理以下情况：

1. API Key 错误或超限：
   - 自动切换到下一个可用的 key
   - 连续两次错误后暂时禁用该 key
   - 所有 key 不可用时返回 503 错误

2. 请求错误：
   - 无效参数: 400 Bad Request
   - 服务器错误: 500 Internal Server Error
   - 服务不可用: 503 Service Unavailable

## Web 界面

访问 `http://localhost:5002` 可以使用 Web 界面：

- 选择不同的声音
- 输入文本进行转换
- 实时播放生成的语音
- 下载生成的音频文件

## 目录结构

```
elevenlabs/
├── app.py              # 主服务器文件
├── requirements.txt    # 项目依赖
├── .env                # 环境变量配置
├── static/             # 静态文件
│   ├── css/            # 样式文件
│   └── js/             # JavaScript 文件
├── templates/          # HTML 模板
└── temp/               # 临时音频文件目录
```

## 注意事项

1. 确保有足够的磁盘空间用于临时音频文件
2. 定期清理 `temp` 目录
3. 注意 ElevenLabs API 的使用限制和配额

## License

MIT
