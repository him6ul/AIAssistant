# API Endpoints Documentation

## OpenAI API Endpoints Used

### 1. Chat Completions API
- **Endpoint**: `https://api.openai.com/v1/chat/completions`
- **Method**: POST
- **Location**: `app/llm_router.py` (line 77)
- **Model**: `gpt-4-turbo-preview` (configurable via `OPENAI_MODEL` env var)
- **Purpose**: Generate text responses for chat queries
- **Request Format**:
  ```python
  {
    "model": "gpt-4-turbo-preview",
    "messages": [
      {"role": "system", "content": "system prompt"},
      {"role": "user", "content": "user prompt"}
    ],
    "temperature": 0.7,
    "max_tokens": 2000
  }
  ```

### 2. Audio Transcriptions API
- **Endpoint**: `https://api.openai.com/v1/audio/transcriptions`
- **Method**: POST
- **Location**: `app/stt.py` (line 88)
- **Model**: `whisper-1`
- **Purpose**: Convert speech to text for voice commands
- **Request Format**:
  ```python
  {
    "model": "whisper-1",
    "file": audio_file,
    "language": "en"  # optional
  }
  ```

## FastAPI OpenAPI Documentation

Your FastAPI server automatically generates OpenAPI (Swagger) documentation:

### Access Points:
1. **Swagger UI**: http://localhost:8000/docs
   - Interactive API documentation
   - Test endpoints directly from browser
   - See request/response schemas

2. **ReDoc**: http://localhost:8000/redoc
   - Alternative documentation interface
   - Clean, readable format

3. **OpenAPI JSON**: http://localhost:8000/openapi.json
   - Raw OpenAPI specification in JSON format
   - Can be imported into API testing tools

### Available API Endpoints:

#### Chat & Commands
- `POST /chat` - Chat with AI assistant
- `GET /health` - Health check
- `GET /status` - System status

#### Tasks
- `GET /tasks` - Get all tasks
- `GET /tasks/today` - Get today's tasks
- `GET /tasks/overdue` - Get overdue tasks
- `GET /tasks/waiting-on` - Get waiting-on tasks
- `GET /tasks/follow-ups` - Get follow-up tasks
- `POST /tasks` - Create new task
- `PUT /tasks/{task_id}` - Update task
- `DELETE /tasks/{task_id}` - Delete task
- `POST /tasks/extract` - Extract tasks from content

#### Actions
- `POST /actions/execute` - Execute an action (reminder, calendar, email)

#### Ingestion
- `POST /ingestion/email/scan` - Manually scan emails
- `POST /ingestion/onenote/scan` - Manually scan OneNote

#### GitHub (if configured)
- `GET /github/user` - Get GitHub user info
- `GET /github/repos` - Get repositories
- `GET /github/repos/{repo_name}` - Get repository details
- `GET /github/repos/{repo_name}/issues` - Get issues
- `POST /github/repos/{repo_name}/issues` - Create issue
- `GET /github/repos/{repo_name}/pulls` - Get pull requests

## Configuration

### OpenAI API Settings
Set in `.env` file:
```bash
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview  # Optional, defaults to gpt-4-turbo-preview
```

### Base URL
The OpenAI client uses the default base URL: `https://api.openai.com/v1`

## Usage Examples

### Test Chat Endpoint
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather?"}'
```

### View API Documentation
Open in browser: http://localhost:8000/docs

### Get OpenAPI Spec
```bash
curl http://localhost:8000/openapi.json > openapi.json
```

