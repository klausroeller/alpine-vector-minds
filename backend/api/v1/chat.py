from fastapi import APIRouter, Depends, HTTPException, status
from openai import AsyncOpenAI, OpenAIError
from pydantic import BaseModel

from api.v1.auth import get_current_user
from vector_db.embeddings import settings as embedding_settings
from vector_db.models.user import User

router = APIRouter()


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    response: str


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    client = AsyncOpenAI(api_key=embedding_settings.OPENAI_API_KEY)
    try:
        completion = await client.chat.completions.create(
            model=embedding_settings.OPENAI_CHAT_MODEL,
            messages=[{"role": "user", "content": request.prompt}],
        )
    except OpenAIError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenAI API error: {e}",
        ) from e

    content = completion.choices[0].message.content
    return ChatResponse(response=content or "")
