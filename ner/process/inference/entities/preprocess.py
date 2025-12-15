from pydantic import BaseModel


class FileInput(BaseModel):
    """Represents the entity for file input."""

    filepath: str


class ProcessedFile(BaseModel):
    """Represents the entity for a processed file."""
    text_as_one_string: str
    list_of_texts: list[str]
