from typing import List
from pydantic import BaseModel, ConfigDict, Field

from models.schemas import ImageWord

class SentenceRequest(BaseModel):
    """
    Defines the expected structure for the POST request body. 
    It is a list of ImageWordBase objects containing the base word and image URL.
    """
    sentence: List[ImageWord]
    
    model_config = ConfigDict(
        populate_by_name=True,
    )
    
    model_config["json_schema_extra"] = {
        "examples": [
            {
                "sentence": [
                    {"word": "Ma tahan", "imageUrl": None}, 
                    {"word": "sööma", "imageUrl": "https://example.com/eat.png"}
                ]
            }
        ]
    }


class SentenceResponse(BaseModel):
    """
    Defines the structure for the API response, returning a list of 
    ImageWord objects containing the original and conjugated forms.
    """
    sentence: List[ImageWord] = Field(..., description="The list of words, each including its original word, image URL, and conjugated form.")
    model_config = ConfigDict(
        populate_by_name=True,
    )