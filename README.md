# Logistics AI Insights / Chatbot guide

This guide explains how to run the Logistics AI Bot with the React frontend.

## Architecture

```
React Frontend (fe-react/)
    ↓ HTTP POST /ask
FastAPI Backend (backend/api.py)
    ↓
Gateway (classifies & produces to Kafka)
    ↓
Kafka Topic: events.workflow.commands
    ↓
Responder (consumes, invokes tools, produces response)
    ↓
Kafka Topic: events.output.message
    ↓
Gateway (consumes response)
    ↓
FastAPI returns response to Frontend
```

<img src="architecture.png" alt="Architecture" width="600">

## Prerequisites

1. **Kafka** must be running
2. **Python 3.12+** with dependencies installed
3. **Node.js** / npm for the React frontend

## Setup

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install dependencies (if using uv):
```bash
uv sync
```

Or with pip:
```bash
pip install -r requirements.txt  # if you have one, or install from pyproject.toml
```

3. Make sure Kafka topics exist:
   - `events.workflow.commands`
   - `events.output.message`
   - `events.insights.message`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd fe-react
```

2. Install dependencies:
```bash
npm install
```

## Running the Application

### Step 1: Start the Backend API Server

In the `backend/` directory:

```bash
python api.py
```

Or using uvicorn directly:
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
✅ All services started! API server ready.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Start the React Frontend

In a **new terminal**, navigate to `fe-react/` directory:

```bash
cd fe-react
npm run dev
```

The frontend will start on `http://localhost:5173` (Vite default port).

### Step 3: Open the Chat Interface

Open your browser and navigate to:
```
http://localhost:5173
```

## API Endpoints

### POST /ask
Send a chat message to the AI assistant.

**Request:**
```json
{
  "question": "What are the details of order with id 12?"
}
```

**Response:**
```json
{
  "answer": "Order ID: 12\nStatus: Processing\n..."
}
```

### GET /health
Check if the API and services are running.

**Response:**
```json
{
  "status": "healthy",
  "gateway": true,
  "responder": true
}
```

## Troubleshooting

### CORS Errors
If you see CORS errors, make sure:
- The frontend URL is in the `allow_origins` list in `api.py`
- Both services are running on the expected ports

### No Response from API
1. Check if Kafka is running
2. Check if the Responder consumer is connected (check backend logs)
3. Verify Kafka topics exist
4. Check the `/health` endpoint

### Frontend Can't Connect
1. Verify the backend is running on `http://localhost:8000`
2. Check browser console for errors
3. Verify the API endpoint URL in `App.tsx` matches your backend URL

## Development

### Backend Development
- The API server auto-reloads with `--reload` flag
- Check logs for Kafka consumer/producer status
- Use `/health` endpoint to verify services

### Frontend Development
- Vite hot-reloads on file changes
- Check browser console for errors
- Network tab shows API requests/responses

## Notes

- The Gateway and Responder services start automatically when the API server starts
- Both consumers run in background threads
- Default tool messages (greetings, etc.) are handled directly without Kafka

