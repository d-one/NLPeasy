import os
from typing import Dict, Optional
import pytorch_lightning as pl
import torch
from pytorch_lightning import seed_everything
from torch import Tensor
from torch.optim import AdamW
from torchmetrics import Accuracy, ConfusionMatrix
from transformers import BertPreTrainedModel
from transformers.modeling_outputs import TokenClassifierOutput
from shared.logger import logger
from config import Settings

os.environ["TOKENIZERS_PARALLELISM"] = "true"
torch.manual_seed(Settings.model.seed)
seed = seed_everything(Settings.model.seed, workers=True)


class LitModel(pl.LightningModule):
    def __init__(self, model: BertPreTrainedModel):
        super().__init__()
        self.save_hyperparameters()
        self.model = model
        self.accuracy = Accuracy(task=Settings.model.task, num_classes=Settings.model.num_labels)
        self.confusion_matrix = ConfusionMatrix(num_classes=Settings.model.num_labels, task=Settings.model.task)
        if Settings.model.class_counts:
            class_counts = torch.tensor(Settings.model.class_counts, dtype=torch.float32)
            class_weights = 1.0 / class_counts
            logger.info(f"Using provided class weights: {class_weights}")
            class_weights = class_weights / class_weights.sum()
            self.loss_fn = torch.nn.CrossEntropyLoss(
                weight=class_weights,
                ignore_index=-100
            )
        else:
            logger.info("No class weights provided, using default CrossEntropyLoss.")
            self.loss_fn = torch.nn.CrossEntropyLoss(ignore_index=-100)

    def forward(
        self, input_ids: Tensor, attention_mask: Tensor, labels: Optional[Tensor] = None
    ) -> TokenClassifierOutput | tuple[Tensor]:
        return self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels,
        )

    def training_step(self, batch: Dict[str, Tensor], batch_idx: int) -> Tensor:
        return self._shared_eval_step(batch, "train")

    def validation_step(self, batch: Dict[str, Tensor], batch_idx: int) -> Tensor:
        return self._shared_eval_step(batch, "val")

    def test_step(self, batch: Dict[str, Tensor], batch_idx: int) -> Tensor:
        return self._shared_eval_step(batch, "test")

    def on_validation_epoch_end(self):
        """
        Better formatted confusion matrix
        """
        cm = self.confusion_matrix.compute().cpu().numpy()
        n_classes = cm.shape[0]
        
        print(f"\n{'='*80}")
        print(f"Epoch {self.current_epoch} - Confusion Matrix")
        print('='*80)
        
        # Calculate column widths based on max value
        max_val = cm.max()
        col_width = max(6, len(str(max_val)))
        
        # Print column headers
        header = "True \\ Pred".ljust(10)
        for j in range(n_classes):
            header += f" {j:>{col_width}}"
        print(header)
        print("-" * (10 + n_classes * (col_width + 1)))
        
        # Print each row with row totals
        for i in range(n_classes):
            row_total = cm[i].sum()
            row = f"{i:<9} |"
            
            for j in range(n_classes):
                value = cm[i, j]
                # Highlight diagonal (correct predictions)
                if i == j:
                    row += f" \033[92m{value:>{col_width}}\033[0m"  # Green
                elif value > 0:
                    row += f" {value:>{col_width}}"
                else:
                    row += f" {'-':>{col_width}}"
            
            # Add row total and accuracy
            accuracy = cm[i, i] / row_total * 100 if row_total > 0 else 0
            row += f" | Total: {row_total:>6} ({accuracy:5.1f}%)"
            print(row)
        
        # Print column totals
        print("-" * (10 + n_classes * (col_width + 1)))
        col_totals = "Total     |"
        for j in range(n_classes):
            col_total = cm[:, j].sum()
            col_totals += f" {col_total:>{col_width}}"
        print(col_totals)
        
        # Overall accuracy
        total_correct = cm.diagonal().sum()
        total_samples = cm.sum()
        overall_acc = total_correct / total_samples * 100 if total_samples > 0 else 0
        
        print(f"\nOverall: {total_correct}/{total_samples} = {overall_acc:.2f}%")
        print('='*80)
        
        # Reset confusion matrix
        self.confusion_matrix.reset()

    def _shared_eval_step(self, batch: Dict[str, Tensor], stage: str) -> Tensor:
        outputs = self.forward(
            input_ids=batch[Settings.dataset.dataset_processed_input_ids_name],
            attention_mask=batch[Settings.dataset.dataset_processed_attention_mask_name],
            labels=None
        )
        logits = outputs.logits
        labels = batch['labels']
        
        loss = self.loss_fn(
            logits.view(-1, self.model.num_labels),
            labels.view(-1)
        )
        preds = torch.argmax(logits, dim=-1)
        mask = batch[Settings.dataset.dataset_processed_attention_mask_name].bool()

        active_preds = preds[mask]
        active_labels = labels[mask]

        # Filter out -100 values from the masked results
        valid_labels_mask = active_labels != -100
        active_preds = active_preds[valid_labels_mask]
        active_labels = active_labels[valid_labels_mask]

        # Update metrics
        acc = self.accuracy(active_preds, active_labels)
        self.confusion_matrix.update(active_preds, active_labels)

        # Log scalars
        self.log(f"{stage}_loss", loss, prog_bar=True, logger=True)
        self.log(f"{stage}_acc", acc, prog_bar=True, logger=True)

        return loss
    
    def configure_optimizers(self):
        optimizer = AdamW(
            self.parameters(),
            lr=Settings.model.learning_rate,  # Lower learning rate
            weight_decay=Settings.model.weight_decay,
            eps=Settings.model.adam_epsilon,
        )
        
        # Simple scheduler without needing steps_per_epoch
        scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(
            optimizer,
            T_0=Settings.model.scheduler_T0,  # First restart after 10 epochs
            T_mult=Settings.model.scheduler_T_mult,  # Double the interval each time
            eta_min=Settings.model.scheduler_eta_min,  # Minimum learning rate
        )
        
        return {
            "optimizer": optimizer,
            "lr_scheduler": {
                "scheduler": scheduler,
                "interval": "epoch",  # Update per epoch, not step
            }
        }