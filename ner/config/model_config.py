from pydantic import BaseModel, Field

class ModelConfig(BaseModel):
    model_name: str = Field(
        default="bert-base-cased",
        description="The name of the pre-trained model to be used.",
    )
    num_labels: int = Field(
        default=9,
        description="The number of unique labels for the NER task.",
    )
    batch_size: int = Field(
        default=16,
        description="The batch size for training and evaluation.",
    )
    num_workers: int = Field(
        default=4,
        description="The number of worker threads for data loading.",
    )
    shuffle: bool = Field(
        default=True,
        description="Whether to shuffle the dataset during training.",
    )
    pin_memory: bool = Field(
        default=True,
        description="Whether to pin memory during data loading.",
    )
    drop_last: bool = Field(
        default=False,
        description="Whether to drop the last incomplete batch.",
    )
    learning_rate: float = Field(
        default=3e-5,
        description="The learning rate for the optimizer.",
    )
    weight_decay: float = Field(
        default=0.05,
        description="The weight decay for the optimizer.",
    )
    adam_epsilon: float = Field(
        default=1e-8,
        description="The epsilon value for the Adam optimizer.",
    )
    warmup_steps: int = Field(
        default=0,
        description="The number of warmup steps for learning rate scheduling.",
    )
    max_epochs: int = Field(
        default=25,
        description="The maximum number of training epochs.",
    )
    seed: int = Field(
        default=42,
        description="The random seed for reproducibility.",
    )

    patience: int = Field(
        default=3,
        description="The number of epochs with no improvement after which training will be stopped.",
    )
    task: str = Field(
        default="multiclass",
        description="The type of classification task.",
    )
    labels_mapping: dict = Field(
        default={
            0: "O",
            1: "B-PER",
            2: "I-PER",
            3: "B-ORG",
            4: "I-ORG",
            5: "B-LOC",
            6: "I-LOC"
        },
        description="Mapping from label IDs to label names.",
    )
    class_counts: list = Field(
        default=[],
        description="Class counts for handling class imbalance.",
    )
    load_from_local: bool = Field(
        default=False,
        description="Whether to load the tokenizer from a local path.",
    )
    local_model_path: str = Field(
        default="",
        description="The local path to load the model from, if load_from_local is True.",
    )
    local_model_path_finetuned: str = Field(
        default="",
        description="The local path to load the fine-tuned model from, if applicable.",
    )
    scheduler_T0: int = Field(
        default=3,
        description="The number of epochs for the first restart in the CosineAnnealingWarmRestarts scheduler.",
    )
    scheduler_T_mult: int = Field(
        default=2,
        description="The factor by which the number of epochs between restarts increases in the CosineAnnealingWarmRestarts scheduler.",
    )
    scheduler_eta_min: float = Field(
        default=1e-6,
        description="The minimum learning rate in the CosineAnnealingWarmRestarts scheduler.",
    )
    accelerator: str = Field(
        default="mps",
        description="The type of accelerator to use for training (e.g., 'cpu', 'cuda', 'mps').",
    )
    devices: int = Field(
        default=1,
        description="The number of devices to use for training.",
    )
    deterministic: bool = Field(
        default=False,
        description="Whether to use deterministic algorithms for reproducibility.",
    )
    precision: str = Field(
        default="32",
        description="The precision to use for training (e.g., '16', '32').",
    )
    gradient_clip_val: float = Field(
        default=1.0,
        description="The value to clip gradients during training.",
    )
    accumulate_grad_batches: int = Field(
        default=1,
        description="The number of batches to accumulate gradients over.",
    )
    log_every_n_steps: int = Field(
        default=50,
        description="How often to log training metrics.",
    )
