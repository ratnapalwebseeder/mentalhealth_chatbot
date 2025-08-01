import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mentalhealth-mistral:latest"

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # This will store the conversation for the current session
    history = ""

    try:
        while True:
            user_input = await websocket.receive_text()

            # Append the new user message to the history
            history += f"User: {user_input}\n"

            # Create the full prompt with history + new message
            prompt = f"{history}Assistant:"

            payload = {
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            }

            timeout = httpx.Timeout(60.0, connect=10.0)

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(OLLAMA_URL, json=payload)
                response.raise_for_status()
                data = response.json()

            bot_response = data.get("response", "").strip()

            # Append the assistant's response to the history
            history += f"Assistant: {bot_response}\n"

            await websocket.send_text(bot_response)

    except WebSocketDisconnect:
        print("WebSocket connection closed")

    except Exception as e:
        await websocket.send_text(f"Error: {str(e)}")
        print(f"Unhandled error: {e}")
