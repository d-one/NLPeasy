from abc import ABC, abstractmethod
from transformers import BertPreTrainedModel
from pathlib import Path
from typing import Optional, Dict, Any


class ModelI(ABC):

    @abstractmethod
    def __init__(self):
        pass

    @property
    @abstractmethod
    def model(self) -> BertPreTrainedModel:
        pass

    @abstractmethod
    def _build_model(self) -> BertPreTrainedModel:
        pass

    @abstractmethod
    def _load_local_model(self) -> BertPreTrainedModel:
        pass

    @abstractmethod
    def _load_from_huggingface(self) -> BertPreTrainedModel:
        pass

    @abstractmethod
    def load_checkpoint(self, checkpoint_path: Optional[Path] = None) -> None:
        pass

    @abstractmethod
    def _find_latest_checkpoint(self) -> Path:
        pass

    @abstractmethod
    def _update_model_config_from_checkpoint(self, checkpoint: Dict[str, Any]) -> None:
        pass
