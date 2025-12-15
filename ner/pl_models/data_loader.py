from typing import Any, Dict
import os
import torch
from torch.utils.data import DataLoader, Dataset
from datasets import Dataset
import pytorch_lightning as pl
from pytorch_lightning import seed_everything
from transformers import DataCollatorForTokenClassification, PreTrainedTokenizerFast
from config import Settings

os.environ["TOKENIZERS_PARALLELISM"] = "true"
torch.manual_seed(Settings.model.seed)
seed_everything(Settings.model.seed, workers=True)


class MixedDataset(Dataset):
    def __init__(self, custom_dataset: Dataset):
        self.custom_dataset = custom_dataset

    def __len__(self) -> int:
        return self.custom_dataset.num_rows

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        return self.custom_dataset[idx]

class NERDataModule(pl.LightningDataModule):
    def __init__(
        self,
        train_dataset,
        val_dataset,
        test_dataset,
        tokenizer: PreTrainedTokenizerFast
    ):
        super().__init__()
        self.train_dataset = train_dataset
        self.val_dataset = val_dataset
        self.test_dataset = test_dataset
        self.batch_size = Settings.model.batch_size
        self.num_workers = Settings.model.num_workers
        self.pin_memory = Settings.model.pin_memory
        self.data_collator = DataCollatorForTokenClassification(
            tokenizer=tokenizer,
            padding='longest',  # Pad to longest in batch
            max_length=512,
            label_pad_token_id=-100,
            return_tensors='pt'
        )

    def collate_fn(self, batch):
        """
        Filter out extra keys before passing to data collator
        """
        filtered_batch = []
        
        for item in batch:
            filtered_batch.append({
                Settings.dataset.dataset_processed_input_ids_name: item[Settings.dataset.dataset_processed_input_ids_name],
                Settings.dataset.dataset_processed_attention_mask_name: item[Settings.dataset.dataset_processed_attention_mask_name],   
                Settings.dataset.dataset_processed_labels_name: item[Settings.dataset.dataset_processed_labels_name],
            })
        
        return self.data_collator(filtered_batch)

    def train_dataloader(self):
        return DataLoader(
            self.train_dataset,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=self.num_workers,
            pin_memory=self.pin_memory,
            collate_fn=self.collate_fn,
        )

    def val_dataloader(self):
        return DataLoader(
            self.val_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            pin_memory=self.pin_memory,
            collate_fn=self.collate_fn,
        )

    def test_dataloader(self):
        return DataLoader(
            self.test_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            pin_memory=self.pin_memory,
            collate_fn=self.collate_fn,
        )
