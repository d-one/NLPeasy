from datasets import load_dataset, load_from_disk
from config import Settings


class DatasetLoader:
    def load_from_huggingface(self):
        dataset = load_dataset(path=Settings.dataset.dataset_huggingface_name)
        return dataset
    
    def load_raw_dataset_from_disk(self):
        dataset = load_from_disk(Settings.dataset.dataset_raw_converted_path)
        return dataset
    
    def load_processed_processed_from_disk(self):
        dataset = load_from_disk(Settings.dataset.dataset_processed_path)
        return dataset
