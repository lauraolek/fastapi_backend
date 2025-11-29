import base64
from typing import Optional
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from contextlib import asynccontextmanager

from models.tts_schemas import TtsRequest, TtsResponse
from services.tts_service import TtsService

router = APIRouter()

# Global dependency: This httpx client will be closed automatically in main.py's lifespan
_http_client: Optional[httpx.AsyncClient] = None

def get_tts_service() -> TtsService:
    """Dependency function to get the initialized TTS Service."""
    if _http_client is None:
        # Should not happen if the client is initialized in main.py lifespan, 
        # but provides a fallback
        raise RuntimeError("HTTP Client not initialized in application lifespan.")
    return TtsService(http_client=_http_client)


@router.post(
    "/audio", 
    response_model=TtsResponse,
    summary="Generate Base64-encoded WAV audio from text.",
    status_code=status.HTTP_200_OK
)
async def generate_audio(
    request_data: TtsRequest,
    tts_service: TtsService = Depends(get_tts_service)
):
    """
    Generates audio from the input text parameters and returns the WAV audio 
    Base64-encoded, along with the original text and format metadata.
    """
    try:
        # 1. Call the asynchronous service layer to get the binary audio bytes
        audio_bytes = await tts_service.text_to_speech(
            text=request_data.sentence,
            speaker=request_data.speaker,
            speed=request_data.speed
        )

        # 2. Encode the audio bytes to a Base64 string
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

        # 3. Construct the structured response DTO and return
        return TtsResponse(
            audioBase64=audio_base64
        )

    except HTTPException:
        # Re-raise exceptions intended for the client (e.g., 400, 503)
        raise
    except Exception as e:
        # Catch any unexpected server-side errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected server error occurred: {type(e).__name__}"
        )

# --- Lifespan integration ---
# Define the client management functions to be called by main.py
@asynccontextmanager
async def tts_lifespan_manager(app):
    global _http_client
    print("TTS Service Startup: Initializing httpx.AsyncClient.")
    _http_client = httpx.AsyncClient(timeout=15.0)
    yield
    print("TTS Service Shutdown: Closing httpx.AsyncClient.")
    await _http_client.aclose()