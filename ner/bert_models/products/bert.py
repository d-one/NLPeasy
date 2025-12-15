import torch
from pathlib import Path
from typing import Optional, Dict, Any
from transformers import BertForTokenClassification as TokenClassification, BertConfig as Config
from config import Settings
from shared.logger import logger
from bert_models.interfaces.model_interface import ModelI

CUDA_AVAILABLE: bool = torch.cuda.is_available()
DEVICE: str = "cuda" if CUDA_AVAILABLE else "cpu"


class BertModelLoader(ModelI):
    def __init__(self):
        self.device = torch.device(DEVICE)
        self._model = self._build_model()
        logger.info(f"Model initialized on device: {self.device}")
        
    @property
    def model(self) -> TokenClassification:
        return self._model
    
    def _build_model(self) -> TokenClassification:
        """Build the model with correct configuration"""
        try:
            if Settings.tokenizer.load_from_local:
                logger.info(f"Loading model from local path: {Settings.model.local_model_path}")
                model = self._load_local_model()
            else:
                logger.info(f"Loading model from HuggingFace: {Settings.model.model_name}")
                model = self._load_from_huggingface()
            
            # Move to device
            model.to(self.device)
            logger.info(f"Model loaded successfully on {self.device}")

            return model
            
        except Exception as e:
            logger.error(f"Failed to build model: {e}")
            raise
    
    def _load_local_model(self) -> TokenClassification:
        """Load model from local checkpoint with proper configuration"""
        # First try loading with custom config
        config_path = Path(Settings.model.local_model_path) / "config.json"
        if config_path.exists():
            config = Config.from_pretrained(Settings.model.local_model_path)
            logger.info(f"Loaded config from {config_path}")
        else:
            # Create new config with correct num_labels
            config = Config.from_pretrained(
                Settings.model.model_name,
                num_labels=Settings.model.num_labels,
                id2label={str(i): label for i, label in enumerate(Settings.model.labels_mapping.keys())},
                label2id=Settings.model.labels_mapping
            )
            logger.warning(f"No config.json found at {Settings.model.local_model_path}, using default with {Settings.model.num_labels} labels")
        
        # Load model with config
        model = TokenClassification.from_pretrained(
            Settings.model.local_model_path,
            config=config,
            ignore_mismatched_sizes=True  # Important for classifier size mismatch
        )
        return model
    
    def _load_from_huggingface(self) -> TokenClassification:
        """Load model from HuggingFace with correct number of labels"""
        # Create mapping dictionaries
        id2label = {str(i): label for i, label in enumerate(Settings.model.labels_mapping.keys())}
        label2id = {label: i for i, label in enumerate(Settings.model.labels_mapping.keys())}
        
        logger.info(f"Creating model with {Settings.model.num_labels} labels")
        logger.info(f"Label mapping: {id2label}")
        
        # Load model with correct configuration
        model = TokenClassification.from_pretrained(
            Settings.model.model_name,
            num_labels=Settings.model.num_labels,
            id2label=id2label,
            label2id=label2id,
            ignore_mismatched_sizes=True
        )
        return model
    
    def load_checkpoint(self, checkpoint_path: Optional[Path] = None) -> None:
        """Load checkpoint and update model weights"""
        try:
            if checkpoint_path is None:
                checkpoint_path = self._find_latest_checkpoint()
            
            logger.info(f"Loading checkpoint from: {checkpoint_path}")
            
            # Load checkpoint
            checkpoint = torch.load(str(checkpoint_path), map_location=self.device, weights_only=False)
            
            # Extract state dict
            if 'state_dict' in checkpoint:
                state_dict = checkpoint['state_dict']
                # Remove 'model.' prefix if present (from Lightning)
                state_dict = {k.replace('model.', ''): v for k, v in state_dict.items()}
            else:
                state_dict = checkpoint
            
            # Update model config
            self._update_model_config_from_checkpoint(checkpoint)
            
            # Load weights
            missing_keys, unexpected_keys = self._model.load_state_dict(state_dict, strict=False)
            
            if missing_keys:
                logger.warning(f"Missing keys in checkpoint: {missing_keys}")
            if unexpected_keys:
                logger.warning(f"Unexpected keys in checkpoint: {unexpected_keys}")
            
            self._model.to(self.device)
            self._model.eval()
            
            logger.info(f"Checkpoint loaded successfully from {checkpoint_path}")
            
            
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            raise
    
    def _find_latest_checkpoint(self) -> Path:
        """Find the latest checkpoint in the finetuned directory"""
        ckpt_folder = Path(Settings.model.local_model_path_finetuned)
        
        if not ckpt_folder.exists():
            raise FileNotFoundError(f"Checkpoint directory not found: {ckpt_folder}")
        
        # Look for .ckpt files
        checkpoint_files = list(ckpt_folder.glob("*.ckpt"))
        
        if not checkpoint_files:
            # Also check for pytorch_model.bin
            pytorch_files = list(ckpt_folder.glob("pytorch_model.bin"))
            if pytorch_files:
                checkpoint_files = pytorch_files
            else:
                raise FileNotFoundError(f"No checkpoint files found in {ckpt_folder}")
        
        # Sort by modification time (newest first)
        checkpoint_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        latest_checkpoint = checkpoint_files[0]
        logger.info(f"Found {len(checkpoint_files)} checkpoint(s). Using latest: {latest_checkpoint}")
        
        return latest_checkpoint
    
    def _update_model_config_from_checkpoint(self, checkpoint: Dict[str, Any]) -> None:
        """Update model configuration from checkpoint if available"""
        # Update num_labels
        if 'hyper_parameters' in checkpoint:
            hyperparams = checkpoint['hyper_parameters']
            if 'num_labels' in hyperparams:
                self._model.config.num_labels = hyperparams['num_labels']
        
        # Ensure label mappings are correct
        self._model.config.id2label = {str(i): label for i, label in enumerate(Settings.model.labels_mapping.keys())}
        self._model.config.label2id = Settings.model.labels_mapping
        
        logger.info(f"Model config updated: num_labels={self._model.config.num_labels}")
