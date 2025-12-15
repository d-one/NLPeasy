import os
import json
from pathlib import Path
import pytorch_lightning as pl
from pl_models.data_loader import MixedDataset, NERDataModule
from pl_models.model import LitModel
from bert_models import ModelStrategy
from tokenizer import TokenizerStrategy
from shared.logger import logger
from config import Settings
from dataset.load import DatasetLoader
from datasets import Dataset
from pytorch_lightning.callbacks import EarlyStopping, ModelCheckpoint

os.environ["TOKENIZERS_PARALLELISM"] = "true"


def lightning_training(
    dataset: Dataset
) -> object:
    """
    Training call. First create dataset and corresponding dataloder.
    Then initialize the model.
    Then train, vaidate and test the model.
    Args:
        input_uri: pandas DataFrame
        model_dir: path for the model output
        hyperparameters:hyperparameter dictionary
        num_labels: num labels
    Returns:
        model
    """


    bert_model_loader = ModelStrategy.run(Settings.model.model_name)
    tokenizer_loader = TokenizerStrategy.run(Settings.tokenizer.model_name)

    data_module = NERDataModule(
        train_dataset=MixedDataset(dataset["train"]),
        val_dataset=MixedDataset(dataset["validation"]),
        test_dataset=MixedDataset(dataset["test"]),
        tokenizer=tokenizer_loader.tokenizer,
    )
    model = LitModel(
        model=bert_model_loader.model
    )
    early_stop = EarlyStopping(
        monitor="val_loss", patience=Settings.model.patience, mode="min"
    )
    checkpoint = ModelCheckpoint(
        save_top_k=Settings.model.max_epochs,
        every_n_epochs=1,
        monitor="val_loss",
        mode="min",
        dirpath=Settings.model.local_model_path_finetuned,
        filename="model-{epoch:02d}-{val_loss:.2f}-{val_acc:.2f}",
        save_last=True,
    )
    trainer = pl.Trainer(
        max_epochs=Settings.model.max_epochs,
        accelerator=Settings.model.accelerator,
        devices=Settings.model.devices,
        deterministic=Settings.model.deterministic,
        default_root_dir=Settings.model.local_model_path_finetuned,
        precision=Settings.model.precision,
        callbacks=[early_stop, checkpoint],
        gradient_clip_val=Settings.model.gradient_clip_val,  # Add gradient clipping
        accumulate_grad_batches=Settings.model.accumulate_grad_batches,  # Ensure no accumulation
        enable_progress_bar=True,
        log_every_n_steps=Settings.model.log_every_n_steps,
    )

    trainer.fit(model=model, datamodule=data_module)
    trainer.test(model=model, datamodule=data_module)
    # save settings as json in same model dir with model dump json
    save_path = Path(Settings.model.local_model_path_finetuned) / "settings.json"
    with open(save_path, 'w') as f:
        json.dump(Settings.model_dump(), f, indent=2, default=str)
    return trainer


if __name__ == "__main__":
    ner_dataset = DatasetLoader()
    dataset = ner_dataset.load_processed_processed_from_disk()
    trainer = lightning_training(dataset=dataset)
