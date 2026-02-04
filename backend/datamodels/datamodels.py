from typing import Optional
from pydantic import BaseModel


class ImageInput(BaseModel):
    question: str
    image_url: Optional[str] = None
    image_b64: Optional[str] = None


class ImageResponse(BaseModel):
    response: str


class TextInput(BaseModel):
    input_string: str

class User(BaseModel):
    uuid: str
    email: str


