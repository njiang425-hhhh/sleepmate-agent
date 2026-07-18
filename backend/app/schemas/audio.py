from pydantic import BaseModel, Field


class TTSRequest(BaseModel):
    script_text: str = Field(min_length=1, max_length=4096)


class TTSResponse(BaseModel):
    audio_path: str
    cached: bool
