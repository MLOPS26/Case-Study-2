from contextlib import asynccontextmanager
import os
import shutil
import uuid
import time
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.concurrency import run_in_threadpool
from PIL import Image
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from backend.utils.consts import DEVICE, BASE_MODEL
from backend.db.database import Database
from backend.datamodels.datamodels import User as UserModel
from backend.local_model import query_local
from backend.remote_model import query_remote
from huggingface_hub import InferenceClient
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram

# Prometheus Metrics Definitions

# Metric to track inference requests by mode and status
INFERENCE_COUNTER = Counter(
    "app_inference_requests_total",
    "Total number of inference requests",
    ["mode", "status"]
)

# Inference Latency
INFERENCE_DURATION = Histogram(
    "app_inference_duration_seconds",
    "Time taken for the AI model to generate a response",
    ["mode"] # Track local vs remote speed
)

# Image Upload Size
UPLOAD_SIZE = Histogram(
    "app_image_upload_bytes",
    "Size of uploaded images in bytes",
    # Buckets from 10KB up to 10MB to categorize sizes
    buckets=(10240, 51200, 102400, 1048576, 5242880, 10485760) 
)

# User Activity
USER_ACTIVITY = Counter(
    "app_user_actions_total",
    "Tracks distinct user actions",
    ["action"]
)

# Internal Database Errors
DB_ERRORS = Counter(
    "app_db_errors_total",
    "Tracks silent database failures",
    ["operation"]
)

# Local model setup
model = None
processor = None
device = None

# Remote model setup
remote_model="zai-org/GLM-4.5V"
client = InferenceClient(model=remote_model, token=os.environ.get("HF_TOKEN"))

# DB setup
db = Database()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, processor, device
    try:
        db.initialize_db()
    except Exception:
        DB_ERRORS.labels(operation="initialize").inc()

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
Instrumentator().instrument(app).expose(app)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/device")
async def get_device():
    return {"device": device}


@app.post("/users")
async def create_user(email: str = Form(...)):
    USER_ACTIVITY.labels(action="signup_attempt").inc()
    new_uuid = str(uuid.uuid4())
    user = UserModel(uuid=new_uuid, email=email)
    
    try:
        success = db.add_user(user)
    except Exception:
        DB_ERRORS.labels(operation="add_user").inc()
        success = False

    if success:
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
    USER_ACTIVITY.labels(action="view_history").inc()
    try:
        return db.get_user_history(user_uuid)
    except Exception:
        DB_ERRORS.labels(operation="get_history").inc()
        return []


@app.post("/inference")
async def inference(
    question: str = Form(...), user_uuid: str = Form(...), file: UploadFile = File(...), mode: str = Form(...)
):
    # Track Upload Size
    file_content = await file.read()
    UPLOAD_SIZE.observe(len(file_content))
    await file.seek(0) # Reset pointer so we can save it below

    file_ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    file_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join("uploads", file_name)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        INFERENCE_COUNTER.labels(mode=mode, status="error").inc()
        raise HTTPException(status_code=500, detail=f"Failed to save image: {e}")

    try:
        img = Image.open(file_path)
    except Exception as e:
        INFERENCE_COUNTER.labels(mode=mode, status="error").inc()
        raise HTTPException(status_code=400, detail=f"Invalid image file: {e}")

    try:
        # Start timing the inference
        start_time = time.perf_counter()
        
        if mode == "local":
            if processor is not None and model is not None:
                response_content = await run_in_threadpool(
                    query_local,
                    model=model,
                    processor=processor,
                    device=device,
                    image=img,
                    question=question,
                )
            else:
                raise Exception("Local model not initialized")
        elif mode == "remote":
            response_content = await run_in_threadpool(
                query_remote,
                image=img,
                question=question,
                client=client
            )
        else: 
            INFERENCE_COUNTER.labels(mode="unknown", status="error").inc()
            raise HTTPException(status_code=400, detail="Invalid mode.")

        # Record Latency and Success
        duration = time.perf_counter() - start_time
        INFERENCE_DURATION.labels(mode=mode).observe(duration)
        INFERENCE_COUNTER.labels(mode=mode, status="success").inc()

        try:
            db.add_history_entry(user_uuid, question, response_content, file_path)
        except Exception as db_e:
            DB_ERRORS.labels(operation="save_history").inc()
            print(f"Failed to save history: {db_e}")

        return {"response": response_content}
    
    except Exception as e:
        INFERENCE_COUNTER.labels(mode=mode, status="error").inc()
        raise HTTPException(status_code=500, detail=f"Inference error: {e}")