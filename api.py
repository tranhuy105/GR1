from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import uuid
import os
from dotenv import load_dotenv
from db_setup import setup_database

# Import our enhanced chatbot
from enhanced_chatbot import EnhancedChatBot

# Load environment variables
load_dotenv()

app = FastAPI(title="Handicraft Store Assistant API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Create static directory if it doesn't exist
os.makedirs("static", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Store active sessions
active_sessions = {}

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    customer_id: str = "CUST001"

class SelectionOption(BaseModel):
    text: str
    value: str

class ChatResponse(BaseModel):
    response: str
    session_id: str
    status: str
    selections: Optional[List[SelectionOption]] = None
    waiting_for_approval: bool = False
    tool_call: Optional[Dict[str, Any]] = None

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Create or retrieve session
        session_id = request.session_id or str(uuid.uuid4())
        
        if session_id not in active_sessions:
            active_sessions[session_id] = EnhancedChatBot(customer_id=request.customer_id)
        
        chatbot = active_sessions[session_id]
        
        # Process the message
        result = chatbot.invoke(request.message)
        
        # Ensure we have valid selections
        if not result.get("selections"):
            result["selections"] = []
            
        return ChatResponse(
            response=result.get("response", ""),
            session_id=session_id,
            status=result.get("status", "completed"),
            selections=result.get("selections"),
            waiting_for_approval=result.get("waiting_for_approval", False),
            tool_call=result.get("tool_call")
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

class ApprovalRequest(BaseModel):
    session_id: str
    approved: bool
    message: Optional[str] = None

@app.post("/approve", response_model=ChatResponse)
async def approve_action(request: ApprovalRequest):
    try:
        if request.session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        chatbot = active_sessions[request.session_id]
        
        # Continue with approval or rejection
        result = chatbot.handle_approval(approved=request.approved, message=request.message)
        
        # Ensure we have valid selections
        if not result.get("selections"):
            result["selections"] = []
            
        return ChatResponse(
            response=result.get("response", ""),
            session_id=request.session_id,
            status=result.get("status", "completed"),
            selections=result.get("selections"),
            waiting_for_approval=False,
            tool_call=None
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing approval: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/sessions")
async def list_sessions():
    return {"active_sessions": list(active_sessions.keys())}

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    if session_id in active_sessions:
        del active_sessions[session_id]
        return {"status": "success", "message": f"Session {session_id} deleted"}
    raise HTTPException(status_code=404, detail="Session not found")

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=True) 