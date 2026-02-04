from contextlib import asynccontextmanager
import os
import shutil
import uuid
import sys

# Add current directory to sys.path to ensure local imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.concurrency import run_in_threadpool
from PIL import Image
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from utils.consts import DEVICE, BASE_MODEL
from db.database import Database
from datamodels.datamodels import User as UserModel
from local_model import query_local

# Global variables
model = None
processor = None
device = None
db = Database()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, processor, device

    # Initialize DB
    db.initialize_db()

    # Initialize Model
    model = Qwen2VLForConditionalGeneration.from_pretrained(BASE_MODEL)
    model.to(DEVICE)
    processor = AutoProcessor.from_pretrained(BASE_MODEL)
    device = DEVICE  # explicitly set global device

    yield

    model = None
    processor = None
    device = None
    db.close()


app = FastAPI(lifespan=lifespan)

# Mount uploads directory for serving images
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/device")
async def get_device():
    return {"device": device}


@app.post("/users")
async def create_user(email: str = Form(...)):
    # Generate a UUID if one isn't provided (or could accept one)
    # Using email as unique constraint
    new_uuid = str(uuid.uuid4())
    user = UserModel(uuid=new_uuid, email=email)
    if db.add_user(user):
        return {"uuid": user.uuid, "email": user.email}
    else:
        # Return existing user or error - for now just return uuid
        existing_user = db.con.execute(
            "SELECT uuid, email FROM users WHERE email = ?", (email,)
        ).fetchone()
        if existing_user:
            return {"uuid": existing_user[0], "email": existing_user[1]}
        return {"error": "User with this email may already exist", "uuid": new_uuid}


@app.get("/history/{user_uuid}")
async def get_history(user_uuid: str):
    return db.get_user_history(user_uuid)


@app.post("/inference")
async def inference(
    question: str = Form(...), user_uuid: str = Form(...), file: UploadFile = File(...)
):
    # 1. Save the file locally
    file_ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    file_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join("uploads", file_name)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save image: {e}")

    # 2. Open image for inference
    try:
        img = Image.open(file_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {e}")

    try:
        if processor is not None and model is not None:
            # Use the refactored local_model.query_local function
            # Note: query_local is synchronous but runs in threadpool to avoid blocking
            response_content = await run_in_threadpool(
                query_local,
                model=model,
                processor=processor,
                device=device,
                image=img,
                question=question,
            )

            # 3. Save to History
            try:
                # Ensure user exists (auto-create for demo/prototype smoothness if needed, or error)
                user = db.get_user(user_uuid)
                if not user:
                    # For now just pass, assuming valid UUID from frontend or previous /users call
                    pass

                db.add_history_entry(user_uuid, question, response_content, file_path)
            except Exception as db_e:
                print(f"Failed to save history: {db_e}")

            return {"response": response_content}
        else:
            raise HTTPException(status_code=500, detail="Model not initialized")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {e}")
