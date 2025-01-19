from fastapi import FastAPI
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId  
import google.generativeai as genai
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from dotenv import dotenv_values
from bson import ObjectId
from fastapi import HTTPException


app = FastAPI()

config = dotenv_values(".env")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[config["SERVER_ORIGIN"]],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_password = config["DB_CLUSTER_KEY"]

MONGO_URI = f"mongodb+srv://ashokwick123:{db_password}@cluster0.v9wbi.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = config["DB_NAME"]

@app.on_event("startup")
def startup_db_client():
    """Connect to MongoDB on app startup."""
    app.state.mongodb_client = MongoClient(MONGO_URI)
    app.state.database = app.state.mongodb_client[DB_NAME]
    app.state.chat_collection = app.state.database["chats"]
    print("Connected to MongoDB!")

@app.on_event("shutdown")
def shutdown_db_client():
    """Close MongoDB connection on app shutdown."""
    app.state.mongodb_client.close()

class Message(BaseModel):
    id: str
    user_message: str
    bot_reply: str

class ChatRequest(BaseModel):
    user_message: str  

class AIRequest(BaseModel):
    prompt: str  


ai_key = config["GEN_AI_KEY"]
genai.configure(api_key=ai_key)
model = genai.GenerativeModel("gemini-1.5-flash")


@app.get("/")
def read_root():
    return {"message": "Welcome to backend"}

@app.post("/genai")
def generate_ai_response(request: AIRequest):
    """Generate AI response using Google Gemini API."""
    try:
        response = model.generate_content(request.prompt)
        if hasattr(response, "text"):
            return {"user_prompt": request.prompt, "ai_response": response.text}
        else:
            return {"error": "AI response is empty"}
    except Exception as e:
        return {"error": str(e)}

@app.post('/chat', response_model=Message)
def reply_user_req(chat_request: ChatRequest):
    """Handles user chat requests and stores responses in MongoDB."""
    user_message = chat_request.user_message  
    instructions = "Answer in 1 or 2 lines, and be concise. "
    full_prompt = instructions + user_message

    try:
        response = model.generate_content(full_prompt)
        bot_reply = response.text if hasattr(response, "text") else "AI response is empty"
    except Exception as e:
        bot_reply = f"Error: {str(e)}"
    
    chat_collection = app.state.chat_collection
    existing_conversation = chat_collection.find_one({"user_message": user_message})

    if existing_conversation:
        chat_collection.update_one(
            {"_id": existing_conversation["_id"]},
            {"$push": {"messages": {"user_message": user_message, "bot_reply": bot_reply, "timestamp": datetime.utcnow()}}}
        )
        inserted_id = existing_conversation["_id"]
    else:
        chat_data = {
            "user_message": user_message,
            "messages": [{"user_message": user_message, "bot_reply": bot_reply, "timestamp": datetime.utcnow()}],
            "timestamp": datetime.utcnow()
        }
        inserted = chat_collection.insert_one(chat_data)
        inserted_id = inserted.inserted_id

    return {"id": str(inserted_id), "user_message": user_message, "bot_reply": bot_reply}

@app.get("/chats", response_model=list[Message])
def get_chat_history():
    """Fetches the last 20 conversations from MongoDB."""
    chat_collection = app.state.chat_collection
    chats = chat_collection.find().sort("timestamp", -1).limit(20)

    response = []
    for chat in chats:
        for message in chat["messages"]:
            response.append({
                "id": str(chat["_id"]), 
                "user_message": message["user_message"],
                "bot_reply": message["bot_reply"]
            })
    
    return response


@app.get("/chat/{message_id}", response_model=Message)
def get_message_by_id(message_id: str):
    """Fetch a specific chat message by its ID from MongoDB."""
    try:
        if not ObjectId.is_valid(message_id):
            raise HTTPException(status_code=400, detail="Invalid ObjectId format")

        chat = app.state.chat_collection.find_one({"_id": ObjectId(message_id)})

        if not chat:
            raise HTTPException(status_code=404, detail="Message not found")

        latest_message = chat["messages"][-1] 

        return {
            "id": str(chat["_id"]),
            "user_message": latest_message["user_message"],
            "bot_reply": latest_message["bot_reply"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


    
