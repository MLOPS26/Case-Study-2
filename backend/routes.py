from contextlib import asynccontextmanager
import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.concurrency import run_in_threadpool
from PIL import Image
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from backend.utils.consts import DEVICE, BASE_MODEL
from backend.db.database import Database
from backend.datamodels.datamodels import User as UserModel
from backend.local_model import query_local

model = None
processor = None
device = None
db = Database()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, processor, device

    db.initialize_db()

    model = Qwen2VLForConditionalGeneration.from_pretrained(BASE_MODEL)
    model.to(DEVICE)
    processor = AutoProcessor.from_pretrained(BASE_MODEL)
    device = DEVICE 

    yield

    model = None
    processor = None
    device = None
    db.close()


app = FastAPI(lifespan=lifespan)

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/device")
async def get_device():
    return {"device": device}


@app.post("/users")
async def create_user(email: str = Form(...)):
    new_uuid = str(uuid.uuid4())
    user = UserModel(uuid=new_uuid, email=email)
    if db.add_user(user):
        return {"uuid": user.uuid, "email": user.email}
    else:
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
    file_ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    file_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join("uploads", file_name)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save image: {e}")

    try:
        img = Image.open(file_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {e}")

    try:
        if processor is not None and model is not None:
            response_content = await run_in_threadpool(
                query_local,
                model=model,
                processor=processor,
                device=device,
                image=img,
                question=question,
            )

            try:
                user = db.get_user(user_uuid)
                if not user:
                    #TODO: handle what if no uuid
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
