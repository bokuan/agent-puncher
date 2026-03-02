from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
import aiohttp
import json
import os
from database import init_db, insert_log, get_logs, update_log
from config import load_settings, save_settings, Settings

settings: Settings = load_settings()

# Initialize database
init_db()

app = FastAPI()

# Serve static files from the frontend directory
frontend_dir = os.path.join(os.path.dirname(__file__), "web")
app.mount("/web", StaticFiles(directory=frontend_dir, html=True), name="static")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper function to extract prompt from request body
def extract_prompt(request_body):
    if 'messages' in request_body:
        prompt = "\n".join([f"{msg.get('role', '')}: {msg.get('content', '')}" for msg in request_body['messages']])
        return prompt
    return str(request_body)

# Chat completions endpoint
@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    # Get request headers
    request_headers = dict(request.headers)
    
    # Check API key authentication
    auth_header = request_headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        provided_api_key = auth_header[7:]
        if provided_api_key != settings.api_key:
            return {"error": "Unauthorized: Invalid API key"}
    else:
        return {"error": "Unauthorized: No API key provided"}
    
    # Get request body
    request_body = await request.json()
    
    # Extract prompt
    prompt = extract_prompt(request_body)
    
    # Prepare headers for external API
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.external_api_key}"
    }
    
    # Determine if streaming is requested
    streaming = request_body.get('stream', False)
    
    # External API URL
    external_api_url = f"{settings.external_api_base_url}/chat/completions"
    
    if streaming:
        # Handle streaming response
        async def stream_generator():
            full_response = ""
            tokens_used = None
            chunks_json = []
            
            # Create initial log with empty response
            initial_log_response = {
                "stream": True,
                "content": "",
                "chunks": [],
                "usage": None,
            }
            log_id = insert_log(
                prompt=prompt,
                response=json.dumps(initial_log_response, ensure_ascii=False),
                tokens_used=tokens_used,
                external_api_url=external_api_url,
                request_headers=request_headers,
                request_body=request_body,
            )
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        external_api_url,
                        headers=headers,
                        json=request_body,
                        timeout=aiohttp.ClientTimeout(total=300)
                    ) as response:
                        async for chunk in response.content:
                            if chunk:
                                # Forward the chunk to client
                                yield chunk
                                
                                # Process the chunk to build full response
                                chunk_str = chunk.decode('utf-8')
                                lines = chunk_str.split('\n')
                                for line in lines:
                                    if line.startswith('data: '):
                                        data = line[6:]
                                        if data == '[DONE]':
                                            chunks_json.append({"event": "[DONE]"})
                                        else:
                                            try:
                                                json_data = json.loads(data)
                                                chunks_json.append(json_data)
                                                if 'choices' in json_data and json_data['choices']:
                                                    delta = json_data['choices'][0].get('delta', {})
                                                    if 'content' in delta and delta['content'] is not None:
                                                        full_response += delta['content']
                                                # Extract tokens used if available
                                                if 'usage' in json_data and json_data['usage'] is not None:
                                                    tokens_used = json_data['usage'].get('total_tokens')
                                            except json.JSONDecodeError:
                                                pass
                                
                                # Update log every few chunks to enable streaming UI updates
                                if len(chunks_json) % 3 == 0:  # Update every 3 chunks
                                    log_response = {
                                        "stream": True,
                                        "content": full_response,
                                        "chunks": chunks_json,
                                        "usage": {"total_tokens": tokens_used} if tokens_used is not None else None,
                                    }
                                    update_log(
                                        log_id=log_id,
                                        response=json.dumps(log_response, ensure_ascii=False),
                                        tokens_used=tokens_used
                                    )
            except Exception as e:
                yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
                yield "data: [DONE]\n\n"
                # Update log with error
                error_log_response = {
                    "stream": True,
                    "content": f"Error: {str(e)}",
                    "chunks": chunks_json,
                    "usage": {"total_tokens": tokens_used} if tokens_used is not None else None,
                }
                update_log(
                    log_id=log_id,
                    response=json.dumps(error_log_response, ensure_ascii=False),
                    tokens_used=tokens_used
                )
                return
            
            # After streaming ends, log the full response as JSON wrapper
            log_response = {
                "stream": True,
                "content": full_response,
                "chunks": chunks_json,
                "usage": {"total_tokens": tokens_used} if tokens_used is not None else None,
            }
            update_log(
                log_id=log_id,
                response=json.dumps(log_response, ensure_ascii=False),
                tokens_used=tokens_used
            )
        
        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream"
        )
    else:
        # Handle non-streaming response
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    external_api_url,
                    headers=headers,
                    json=request_body,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    response_data = await response.json()
                    
                    # Extract full response
                    full_response = ""
                    if 'choices' in response_data and response_data['choices']:
                        full_response = response_data['choices'][0].get('message', {}).get('content', '')
                    
                    # Extract tokens used
                    tokens_used = response_data.get('usage', {}).get('total_tokens')
                    
                    # Log the full JSON response body
                    insert_log(
                        prompt=prompt,
                        response=json.dumps(response_data, ensure_ascii=False),
                        tokens_used=tokens_used,
                        external_api_url=external_api_url,
                        request_headers=request_headers,
                        request_body=request_body,
                    )
                    
                    return response_data
        except Exception as e:
            # Return error response
            return {"error": str(e)}

@app.get("/api/config")
async def get_config():
    """Return current LLM configuration."""
    return {
        "external_api_base_url": settings.external_api_base_url,
        "external_api_key": settings.external_api_key,
        "web_model": settings.web_model,
        "api_key": settings.api_key,
    }


@app.post("/api/config")
async def update_config(request: Request):
    """Update LLM configuration and persist it to config.json."""
    body = await request.json()
    base_url = body.get("external_api_base_url")
    api_key = body.get("external_api_key")
    web_model = body.get("web_model")

    global settings
    settings = save_settings(base_url=base_url, api_key=api_key, web_model=web_model)

    return {
        "external_api_base_url": settings.external_api_base_url,
        "web_model": settings.web_model,
    }


@app.post("/api/generate-api-key")
async def generate_api_key():
    """Generate a new API key for interface authentication."""
    import secrets
    new_api_key = f"sk-{secrets.token_urlsafe(32)}"
    
    global settings
    settings = save_settings(local_api_key=new_api_key)
    
    return {
        "api_key": new_api_key,
    }

# Chat endpoint for web interface
@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    prompt = data.get('prompt')
    model = data.get('model')
    
    # Prepare request body
    request_body = {
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": True
    }
    if model:
        request_body["model"] = model
    
    # Get request headers
    request_headers = dict(request.headers)
    
    # Extract prompt
    extracted_prompt = extract_prompt(request_body)
    
    # Prepare headers for external API
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.external_api_key}"
    }
    
    # External API URL
    external_api_url = f"{settings.external_api_base_url}/chat/completions"
    
    # Handle streaming response
    async def stream_generator():
        full_response = ""
        tokens_used = None
        chunks_json = []
        
        # Create initial log with empty response
        initial_log_response = {
            "stream": True,
            "content": "",
            "chunks": [],
            "usage": None,
        }
        log_id = insert_log(
            prompt=extracted_prompt,
            response=json.dumps(initial_log_response, ensure_ascii=False),
            tokens_used=tokens_used,
            external_api_url=external_api_url,
            request_headers=request_headers,
            request_body=request_body,
        )
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    external_api_url,
                    headers=headers,
                    json=request_body,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    async for chunk in response.content:
                        if chunk:
                            # Forward the chunk to client
                            yield chunk
                            
                            # Process the chunk to build full response
                            chunk_str = chunk.decode('utf-8')
                            lines = chunk_str.split('\n')
                            for line in lines:
                                if line.startswith('data: '):
                                    data = line[6:]
                                    if data == '[DONE]':
                                        chunks_json.append({"event": "[DONE]"})
                                    else:
                                        try:
                                            json_data = json.loads(data)
                                            chunks_json.append(json_data)
                                            if 'choices' in json_data and json_data['choices']:
                                                delta = json_data['choices'][0].get('delta', {})
                                                if 'content' in delta and delta['content'] is not None:
                                                    full_response += delta['content']
                                                # Extract tokens used if available
                                                if 'usage' in json_data and json_data['usage'] is not None:
                                                    tokens_used = json_data['usage'].get('total_tokens')
                                        except json.JSONDecodeError:
                                            pass
                                
                                # Update log every few chunks to enable streaming UI updates
                                if len(chunks_json) % 3 == 0:  # Update every 3 chunks
                                    log_response = {
                                        "stream": True,
                                        "content": full_response,
                                        "chunks": chunks_json,
                                        "usage": {"total_tokens": tokens_used} if tokens_used is not None else None,
                                    }
                                    update_log(
                                        log_id=log_id,
                                        response=json.dumps(log_response, ensure_ascii=False),
                                        tokens_used=tokens_used
                                    )
        except Exception as e:
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
            yield "data: [DONE]\n\n"
            # Update log with error
            error_log_response = {
                "stream": True,
                "content": f"Error: {str(e)}",
                "chunks": chunks_json,
                "usage": {"total_tokens": tokens_used} if tokens_used is not None else None,
            }
            update_log(
                log_id=log_id,
                response=json.dumps(error_log_response, ensure_ascii=False),
                tokens_used=tokens_used
            )
            return
        
        # After streaming ends, log the full response as JSON wrapper
        log_response = {
            "stream": True,
            "content": full_response,
            "chunks": chunks_json,
            "usage": {"total_tokens": tokens_used} if tokens_used is not None else None,
        }
        update_log(
            log_id=log_id,
            response=json.dumps(log_response, ensure_ascii=False),
            tokens_used=tokens_used
        )
    
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream"
    )


# Logs API endpoint (JSON)
@app.get("/api/logs")
async def get_logs_api():
    logs = get_logs()
    return [dict(log) for log in logs]

if __name__ == "__main__":
    import uvicorn
    import webbrowser
    import time
    
    # Start the server in a separate thread
    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=5685)
    
    import threading
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Wait a moment for the server to start
    time.sleep(2)
    
    # Open the frontend page in the default browser
    webbrowser.open("http://127.0.0.1:5685/web")
    
    # Keep the main thread alive
    server_thread.join()
