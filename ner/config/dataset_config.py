from pydantic import BaseModel, Field


class DatasetConfig(BaseModel):
    dataset_huggingface_name: str = Field(
        default="conll2003",
        description="The name of the dataset from Hugging Face Datasets library.",
    )
    dataset_raw_dataframe_filepath: str = Field(
        default="data/raw/dataset.csv",
        description="Filepath to the raw dataset dataframe.",
    )
    dataset_raw_label_column: str = Field(
        default="ner_tags",
        description="The column name for NER tags in the raw dataset.",
    )
    dataset_raw_text_column: str = Field(
        default="tokens",
        description="The column name for text tokens in the raw dataset.",
    )
    dataset_raw_split_column: str = Field(
        default="split",
        description="The column name for dataset splits in the raw dataset.",
    )
    dataset_raw_converted_path: str = Field(
        default="data/raw/converted_dataset",
        description="Path to save the converted raw dataset.",
    )
    dataset_processed_input_ids_name: str = Field(
        default="input_ids",
        description="The name for input IDs in the processed dataset.",
    )
    dataset_processed_attention_mask_name: str = Field(
        default="attention_mask",
        description="The name for attention masks in the processed dataset.",
    )
    dataset_processed_labels_name: str = Field(
        default="labels",
        description="The name for labels in the processed dataset.",
    )
    dataset_processed_subword_tokens_name: str = Field(
        default="subword_tokens",
        description="The name for subword tokens in the processed dataset.",
    )
    dataset_processed_path: str = Field(
        default="data/processed/dataset",
        description="Path to save the processed dataset.",
    )