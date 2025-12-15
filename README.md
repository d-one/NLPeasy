# NER Fine-tuning with DistilBERT

## 🛠️ Setup

### 1. Create Virtual Environment
```bash
python -m venv .venv --python=python3.12
source .venv/bin/activate
pip install -r requirements.txt
```


### 2. Set Python Path
```bash
export PYTHONPATH="$PYTHONPATH:$(pwd)/ner"
```


### 3. Download model and tokenizer (below python example):

```python
from transformers import DistilBertTokenizerFast, DistilBertForTokenClassification

# Save to your configured paths
tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-cased")
tokenizer.save_pretrained("/path/to/downloaded/tokenizer")

model = DistilBertForTokenClassification.from_pretrained("distilbert-base-cased")
model.save_pretrained("/path/to/downloaded/model")
```

### 4. Configure Settings

Below some importantsettings from ner/settings.json:

```json
{
  "tokenizer": {
    "local_tokenizer_path": "/path/to/downloaded/tokenizer",
    "model_name": "distilbert-base-cased"
  },
  "model": {
    "local_model_path": "/path/to/downloaded/model",
    "local_model_path_finetuned": "/path/to/save/checkpoints"
  },
  "dataset": {
    "dataset_raw_dataframe_filepath": "/path/to/your/data.parquet",
    "dataset_raw_text_column": "tokens",
    "dataset_raw_label_column": "ner_tags",
    "dataset_raw_split_column": "split"
  }
}
```

## 📊 Pipelines - Executables
Run these scripts in order:

### 1. Preprocess Raw Data
Converts raw data to dataset format
```bash
python ner/pipelines/preprocess_raw_data_for_training.py
```

### 2. Tokenize Training Data
Tokenizes and aligns labels for training
```bash
python ner/pipelines/preprocess_train_data.py
```

### 3. Train Model
*Fine-tunes BERT pre-trained model*

```bash
python ner/pipelines/train.py
```

### 4. Run Inference
Use the trained model on new text
```bash
python ner/inference/inference.py
```

```text
ner/                          # Main project directory
├── bert_models/              # Pre-trained BERT models or configurations
├── config/                   # Configuration files
├── dataset/                  # Dataset storage or processing
├── inference/                # Inference/prediction scripts
├── pipelines/                # Training pipeline scripts
│   ├── preprocess_raw_data_for_training.py
│   ├── preprocess_train_data.py
│   └── train.py
├── pl_models/                # PyTorch Lightning models (likely)
├── data_loader.py            # Data loading utilities
├── model.py                  # Model architecture definition
├── process/                  # Data processing utilities
├── inference/                # (Duplicate - might be a mistake)
├── train/                    # Training utilities
├── shared/                   # Shared utilities/modules
├── tokenizer/                # Tokenizer configuration
├── .env/                     # Environment configurations
└── settings.json             # Project settings file
```