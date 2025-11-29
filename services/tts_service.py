import asyncio
import random
import logging
from typing import Dict, Any

import httpx
from fastapi import HTTPException, status

API_URL = "https://api.tartunlp.ai/text-to-speech/v2"
MAX_RETRIES = 5
BASE_DELAY_MS = 500

logger = logging.getLogger(__name__)

class TtsService:
    """
    Service class responsible for communicating with the TartuNLP Text-to-Speech API,
    handling asynchronous requests and exponential backoff for resilience.
    """

    def __init__(self, http_client: httpx.AsyncClient):
        """Initializes the service with an external httpx client."""
        self.http_client = http_client
        logger.info("TtsService initialized.")

    async def _make_request(self, payload: Dict[str, Any], attempt: int) -> bytes:
        """Helper to execute the asynchronous API call with retry logic."""
        
        # Calculate delay with jitter: BASE_DELAY * 2^attempt + random(0 to BASE_DELAY)
        delay_s = (BASE_DELAY_MS / 1000.0) * (2 ** attempt) + random.uniform(0, BASE_DELAY_MS / 1000.0)

        try:
            # Execute the request
            response = await self.http_client.post(
                API_URL,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "audio/wav"
                }
            )
            
            # Handle success (2xx)
            if 200 <= response.status_code < 300:
                return response.content
            
            status_code = response.status_code
            
            # Handle retryable errors (429, 5xx)
            if status_code == 429 or status_code >= 500:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(
                        f"Retryable error (Status {status_code}) on attempt {attempt + 1}. "
                        f"Waiting {delay_s:.2f}s..."
                    )
                    await asyncio.sleep(delay_s)
                    # Use a generic exception to trigger the retry loop in the calling method
                    raise httpx.RequestError(f"Status {status_code}", request=response.request) 
                else:
                    logger.error(f"Server failed after {MAX_RETRIES} attempts. Last Status: {status_code}")
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="External TTS service failed after maximum retries."
                    )
            
            # Handle non-retryable client errors (4xx other than 429)
            error_detail = response.text
            logger.error(f"Non-retryable API Client Error: Status {status_code}. Body: {error_detail[:100]}...")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"External TTS API error (Status {status_code}): {error_detail[:50]}"
            )

        except (httpx.RequestError, asyncio.TimeoutError) as e:
            # Handle network/timeout errors
            if attempt < MAX_RETRIES - 1:
                logger.error(f"Network error on attempt {attempt + 1}: {e.__class__.__name__}. Waiting {delay_s:.2f}s...")
                await asyncio.sleep(delay_s)
                raise # Re-raise to trigger the retry loop
            else:
                logger.error(f"Network failed after {MAX_RETRIES} attempts. Last error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Failed to connect to the external TTS service."
                )

    async def text_to_speech(self, text: str, speaker: str, speed: float) -> bytes:
        """
        Main method to send the request and handle retries.
        """
        payload = {
            "text": text,
            "speaker": speaker,
            "speed": speed
        }
        
        log_text = text[:30] + "..." if len(text) > 30 else text
        logger.info(f"Requesting TTS for text: '{log_text}' with speaker: {speaker}")

        for attempt in range(MAX_RETRIES):
            try:
                audio_bytes = await self._make_request(payload, attempt)
                return audio_bytes
            except (httpx.RequestError, asyncio.TimeoutError):
                continue
        
        # Fallback error if the loop finishes without success
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unknown failure during TTS generation after maximum retries."
        )