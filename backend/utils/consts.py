import torch

BASE_MODEL = "Qwen/Qwen2-VL-2B-Instruct"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DB_PATH = "db/app.duckdb"
