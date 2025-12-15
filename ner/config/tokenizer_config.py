from pydantic import BaseModel, Field


class TokenizerConfig(BaseModel):
    model_name: str = Field(
        default="bert-base-cased",
        description="The name of the pre-trained tokenizer model to be used.",
    )
    padding: str = Field(
        default="max_length",
        description="Padding strategy to use ('longest', 'max_length', 'do_not_pad').",
    )
    max_length: int = Field(
        default=512,
        description="Maximum length of the sequences after tokenization.",
    )
    add_special_tokens: bool = Field(
        default=True,
        description="Whether to add special tokens (e.g., [CLS], [SEP]) to the sequences.",
    )
    return_offsets_mapping: bool = Field(
        default=True,
        description="Whether to return the offsets mapping of tokens to original text.",
    )
    load_from_local: bool = Field(
        default=False,
        description="Whether to load the tokenizer from a local path.",
    )
    local_tokenizer_path: str = Field(
        default="",
        description="The local path to load the tokenizer from, if load_from_local is True.",
    )
    truncation: bool = Field(
        default=True,
        description="Whether to truncate sequences longer than max_length.",
    )
