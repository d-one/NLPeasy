import pandas as pd
from pathlib import Path
from shared.logger import logger
from config import Settings
from tokenizer import TokenizerStrategy
from process import TrainProcessor
from dataset.load import DatasetLoader


def main():
    tokenizer_instance = TokenizerStrategy.run(Settings.tokenizer.model_name)
    processor = TrainProcessor(tokenizer=tokenizer_instance.tokenizer)
    ner_dataset = DatasetLoader()
    dataset = ner_dataset.load_raw_dataset_from_disk()
    processed = dataset.map(
        processor.process_batch,
        batched=True,
        load_from_cache_file=False,
    )
    processed.save_to_disk(Settings.dataset.dataset_processed_path)


if __name__ == "__main__":
    main()
