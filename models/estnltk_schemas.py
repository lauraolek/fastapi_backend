from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

# Utility function for Pydantic's alias_generator
def to_camel(string: str) -> str:
    """Converts a string from snake_case to camelCase."""
    if "_" not in string:
        return string
    
    parts = string.split('_')
    # Join parts after capitalizing all but the first one
    return parts[0] + "".join(part.capitalize() for part in parts[1:])

# Global configuration settings for all models
# Ensures input can be snake_case or camelCase, but output is always camelCase
CAMEL_CASE_CONFIG = {
    "alias_generator": to_camel,
    "populate_by_name": True,
}


class ImageWordBase(BaseModel):
    """Base schema for an Image Word, containing core data."""
    id: Optional[int] = Field(None, description="Database ID of the word.")
    word: str = Field(..., description="The base word (e.g., 'table', 'run').")
    
    image_url: Optional[str] = Field(
        None, 
        description="The URL pointing to the image representation of the word."
    )

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

class ImageWordCreate(ImageWordBase):
    """Schema for creating a new Image Word entry."""
    pass

class ImageWord(ImageWordBase):
    """Full schema for an Image Word, including system-generated fields."""    
    # Pydantic will convert this field's name to 'conjugatedWord' in the output JSON
    conjugated_word: Optional[str] = Field(None, description="The morphologically conjugated form of the word (e.g., 'running').")
    
    model_config = {
        **CAMEL_CASE_CONFIG,
        "from_attributes": True, 
        "json_schema_extra": {
            "examples": [
                {
                    "id": 42,
                    "word": "sööma",
                    "imageUrl": "https://example.com/eat.png",
                    "conjugatedWord": "süüa"
                }
            ]
        }
    }

class SentenceRequest(BaseModel):
    """
    Defines the expected structure for the POST request body. 
    It is a list of ImageWordBase objects containing the base word and image URL.
    """
    sentence: List[ImageWordBase]
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    model_config["json_schema_extra"] = {
        "examples": [
            {
                "sentenceList": [
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
        alias_generator=to_camel,
        populate_by_name=True,
    )