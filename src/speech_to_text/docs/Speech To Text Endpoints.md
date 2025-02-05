
# Speech to Text API Endpoints Documentation

## Base URL
```
http://localhost:8081
```

## Endpoints Overview

### 1. Chat List

```http
GET /api/connect/chat/list
```

No query parameters required.

Response:

```json
{
    "status": "success",
    "message": "Chat history retrieved successfully",
    "data": {
        "chats": [
            {
                "id": "chat_uuid",
                "modified": 1234567890.123,
                "preview": "First message preview text..."
            },
            {
                "id": "another_chat_uuid",
                "modified": 1234567891.123,
                "preview": "Another message preview..."
            }
        ]
    }
}
```

### 2. Chat Connection

```http
POST /api/connect/chat/start
```

#### Query Parameters:
- `mode` (required): Type of chat interaction
	- `chat`: Regular text chat
	- `voice`: Voice response streamed to speakers
	- `voice-save`: Voice response saved to file
- `optimize` (optional): Enable voice optimization
	- `true`: Apply voice optimizations
	- `false`: No optimization (default)
- `chat_id` (optional): Resume existing chat session
- `doc` (optional): Path to document for analysis

Examples:
```
# Basic chat
POST /api/connect/chat/start?mode=chat

# Optimized voice chat
POST /api/connect/chat/start?mode=voice&optimize=true

# Resume chat with document
POST /api/connect/chat/start?mode=chat&chat_id=abc123&doc=/path/to/doc

# Save voice response
POST /api/connect/chat/start?mode=voice-save&optimize=true
```

Response:
```json
{
    "status": "success",
    "message": "Chat session started",
    "data": {
        "session_id": "uuid-string",
        "chat_id": "chat-uuid-string"
    }
}
```

### 2. Copy to Clipboard
```http
POST /api/connect/copy/start
```

No query parameters required.

Response:
```json
{
    "status": "success",
    "message": "Audio processed and copied to clipboard",
    "data": {
        "transcription": "transcribed text",
        "session_id": "uuid-string"
    }
}
```

### 3. Status Stream (SSE)
```http
GET /api/connect/status/{session_id}
```

Path Parameters:
- `session_id`: Session ID from chat or copy start response

Server-Sent Events Format:
```
event: recording
data: {
    "session_id": "uuid-string",
    "status": "status-type",
    "message": "status message",
    "progress": null|number
}
```

Status Types:
- `calibrating`: Initial microphone calibration
- `recording`: Active recording
- `silence`: Silence detection (includes progress 0-100)
- `processing`: Processing audio
- `streaming`: Playing voice response
- `complete`: Operation complete
- `error`: Error occurred

### 4. Current Status (Polling Alternative)
```http
GET /api/connect/status/current/{session_id}
```

Path Parameters:
- `session_id`: Session ID from chat or copy start response

Response:
```json
{
    "session_id": "uuid-string",
    "status": "status-type",
    "message": "current status message",
    "progress": null|number
}
```

## Feature Flag Combinations

### Chat Mode Combinations
1. Basic Chat:
```http
POST /api/connect/chat/start?mode=chat
```

2. Voice Chat:
```http
POST /api/connect/chat/start?mode=voice
```

1. Optimized Voice Chat:
```http
POST /api/connect/chat/start?mode=voice&optimize=true
```

2. Save Voice Response:
```http
POST /api/connect/chat/start?mode=voice-save&optimize=true
```

3. Resume Chat Session:
```http
POST /api/connect/chat/start?mode=chat&chat_id={existing_chat_id}
```

4. Document Analysis Chat:
```http
POST /api/connect/chat/start?mode=chat&doc={document_path}
```

5. Full Feature Chat:
```http
POST /api/connect/chat/start?mode=voice-save&optimize=true&chat_id={existing_chat_id}&doc={document_path}
```

## Error Responses

All endpoints may return the following error structures:

```json
{
    "status": "error",
    "message": "Error description",
    "error": {
        "type": "error_type",
        "description": "Detailed error description"
    }
}
```

Common Error Types:
- `invalid_parameter`: Invalid request parameters
- `chat_error`: Chat session errors
- `transcription_error`: Audio processing errors
- `server_error`: Internal server errors

## Headers

Required headers for SSE endpoints:
```http
Accept: text/event-stream
Cache-Control: no-cache
```

Required headers for API endpoints:
```http
Content-Type: application/json
```

## Rate Limiting

Currently, no rate limiting is implemented. However, consider:
- One active SSE connection per session
- One active recording session at a time
- Clean up unused sessions
```