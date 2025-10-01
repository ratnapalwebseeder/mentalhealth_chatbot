import os
import json
import logging
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Basic logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration from environment
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("MODEL_NAME", "mental-mistral:latest")
API_TIMEOUT = float(os.getenv("API_TIMEOUT", "60.0"))
MAX_HISTORY_LENGTH = int(os.getenv("MAX_HISTORY_LENGTH", "4096"))

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # need to add frontend url here
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("New websocket connection")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info("Websocket disconnected")

manager = ConnectionManager()

def truncate_history(history: str) -> str:
    """Keep conversation history manageable"""
    if len(history) > MAX_HISTORY_LENGTH:
        return history[-MAX_HISTORY_LENGTH:]
    return history

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await manager.connect(websocket)
    history = ""
    
    try:
        while True:
            user_input = await websocket.receive_text()
            logger.info("Received user message")
            
            # Update history
            history = truncate_history(f"{history}User: {user_input}\n")
            prompt = f"{history}Assistant:"
            
            # Call Ollama API
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    OLLAMA_URL,
                    json={
                        "model": MODEL_NAME,
                        "prompt": prompt,
                        "stream": True
                    }
                ) as response:
                    bot_response = ""
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        data = json.loads(line)
                        if "response" in data:
                            chunk = data["response"]
                            bot_response += chunk
                            await websocket.send_text(chunk)
                        # if data.get("done", False):
                        #     # Optional: signal frontend end of stream
                        #     await websocket.send_text("[[END]]")
                
                # Update history with bot response
                history = truncate_history(f"{history}Assistant: {bot_response}\n")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        await websocket.send_text(f"Error: {str(e)}")
        manager.disconnect(websocket)

@app.get("/health")
async def health_check():
    return {"status": "ok"}