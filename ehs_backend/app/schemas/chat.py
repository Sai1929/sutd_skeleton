from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    image_b64: str | None = None
    image_mime: str = "image/jpeg"


class ChatResponseOut(BaseModel):
    reply: str
    model: str
