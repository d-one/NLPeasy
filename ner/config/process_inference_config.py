from pydantic import BaseModel, Field


class ProcessInferenceConfig(BaseModel):
    preprocess_strategy: str = Field(
        default="dump_json",
        description="The preprocessing strategy to be used (e.g., 'dump_json', 'textract_parser').",
    )
    max_chunks: int = Field(
        default=4,
        description="The maximum number of chunks to split the input text into during preprocessing.",
    )
    chunk_stride: int = Field(
        default=400,
        description="The stride size for overlapping chunks during text splitting.",
    )
    threshold_prob: float = Field(
        default=0.8,
        description="The probability threshold for filtering NER predictions.",
    )
