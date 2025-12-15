# OK lets start writing README

# I want to start with basic

# 1) create local .venv with python 3.12 and install requirements
# a) download your dataset
import pandas as pd
from datasets import DatasetDict, Dataset
from pathlib import Path
from config import Settings
from shared.logger import logger


def load_raw_df_and_save_raw_dataset():
    """Load dataframe, use split column, save as dataset."""
    
    # 1. Load raw data
    raw_path = Path(Settings.dataset.dataset_rw_raw_dataframe_filepath)
    logger.info(f"Loading data from: {raw_path}")
    
    # Load based on file extension
    if raw_path.suffix == '.csv':
        df = pd.read_csv(raw_path)
    elif raw_path.suffix == '.parquet':
        df = pd.read_parquet(raw_path)
    elif raw_path.suffix == '.json':
        df = pd.read_json(raw_path)
    else:
        raise ValueError(f"Unsupported file type: {raw_path.suffix}")
    
    logger.info(f"Loaded {len(df)} rows")
    
    # 2. Check split column exists
    split_col = Settings.dataset.dataset_raw_split_column
    if split_col not in df.columns:
        raise ValueError(f"Split column '{split_col}' not found in data")
    
    # 3. Create splits
    splits = {}
    for split_name in df[split_col].unique():
        split_df = df[df[split_col] == split_name]
        
        # Standardize split names
        if split_name in ['train', 'training']:
            key = 'train'
        elif split_name in ['val', 'validation', 'valid', 'dev']:
            key = 'validation'
        elif split_name in ['test', 'testing']:
            key = 'test'
        else:
            key = split_name
        
        # Create dataset for this split
        splits[key] = Dataset.from_dict({
            Settings.dataset.dataset_tokens_name: split_df[Settings.dataset.dataset_raw_text_column].tolist(),
            Settings.dataset.dataset_ner_tags_name: split_df[Settings.dataset.dataset_raw_label_column].tolist()
        })
        
        logger.info(f"Split '{split_name}' -> '{key}': {len(split_df)} samples")
    
    # 4. Create DatasetDict
    dataset_dict = DatasetDict(splits)
    
    # 5. Save
    save_path = Path(Settings.dataset.dataset_raw_converted_path)
    save_path.mkdir(parents=True, exist_ok=True)
    dataset_dict.save_to_disk(str(save_path))
    
    logger.info(f"Dataset saved to: {save_path}")
    
    return dataset_dict


if __name__ == "__main__":
    dataset = load_raw_df_and_save_raw_dataset()
    print(f"Dataset created: {dataset}")