from pydantic import BaseModel, Field

# --- Request DTO ---
# Defines the expected input structure for the TTS generation endpoint.
class TtsRequest(BaseModel):
    """
    Model for the incoming request body to generate TTS audio.
    """
    sentence: str = Field(..., description="The text string to be converted to speech.")
    speaker: str = Field("mari", description="The voice model to use (e.g., 'mari', 'madis').")
    speed: float = Field(1.0, description="The speed of speech (1.0 is normal).")

# --- Response DTO ---
# Defines the structured output for the TTS generation endpoint.
class TtsResponse(BaseModel):
    """
    Model for the outgoing JSON response containing the generated audio.
    """
    audioBase64: str = Field(..., description="The generated audio content, Base64 encoded (WAV format).")