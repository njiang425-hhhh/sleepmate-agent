import logging

from fastapi import APIRouter, HTTPException, Request

from app.schemas.audio import TTSRequest, TTSResponse
from app.services.tts_service import TTSConfigurationError, TTSStorageError, TTSUnavailableError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/audio/tts")
async def tts(request: TTSRequest, req: Request) -> TTSResponse:
    tts_service = req.app.state.tts_service
    if tts_service is None:
        raise HTTPException(status_code=503, detail="语音服务未启用")

    try:
        audio_path, cached = await tts_service.generate(request.script_text)
        return TTSResponse(audio_path=audio_path, cached=cached)
    except TTSUnavailableError:
        raise HTTPException(status_code=503, detail="语音服务暂时不可用，请稍后重试")
    except TTSStorageError:
        raise HTTPException(status_code=500, detail="服务器内部错误")
    except TTSConfigurationError:
        raise HTTPException(status_code=503, detail="语音服务配置异常")
    except Exception:
        logger.exception("Unexpected TTS error")
        raise HTTPException(status_code=500, detail="服务器内部错误")
