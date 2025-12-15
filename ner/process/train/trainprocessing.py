from shared.logger import logger
from config import Settings
from transformers import PreTrainedTokenizerBase


class TrainProcessor:
    def __init__(self, tokenizer: PreTrainedTokenizerBase):
        logger.info("Processor initialized with settings: %s", Settings.model_dump_json())
        self.tokenizer = tokenizer

    def process_batch(self, batch: dict) -> dict:
        tokens = batch[Settings.dataset.dataset_raw_text_column]
        ner_tags = batch[Settings.dataset.dataset_raw_label_column]

        # 1. Tokenize whole batch at once
        encoding = self.tokenizer.batch_encode_plus(
            tokens,
            is_split_into_words=True,
            truncation=Settings.tokenizer.truncation,
            padding=Settings.tokenizer.padding,
            return_offsets_mapping=Settings.tokenizer.return_offsets_mapping,
        )

        

        all_input_ids = []
        all_attention_mask = []
        all_labels = []
        all_subword_tokens = []

        # 2. Align labels for each example
        for i, labels in enumerate(ner_tags):
            word_ids = encoding.word_ids(batch_index=i)
            subword_tokens = encoding.tokens(batch_index=i)

            if Settings.tokenizer.padding == "do_not_pad":
                pad_start_index = None
            else:
                pad_start_index = subword_tokens.index(self.tokenizer.pad_token)

            aligned_labels = self.align_labels_with_tokens(
                labels=labels,
                word_ids=word_ids,
                pad_start_index=pad_start_index,
            )


            all_labels.append(aligned_labels)
            all_input_ids.append(encoding[Settings.dataset.dataset_processed_input_ids_name][i])
            all_attention_mask.append(encoding[Settings.dataset.dataset_processed_attention_mask_name][i])
            all_subword_tokens.append(subword_tokens)

        return {
            Settings.dataset.dataset_processed_input_ids_name: all_input_ids,
            Settings.dataset.dataset_processed_attention_mask_name: all_attention_mask,
            Settings.dataset.dataset_processed_labels_name: all_labels,
            Settings.dataset.dataset_processed_subword_tokens_name: all_subword_tokens
        }

    @staticmethod
    def align_labels_with_tokens(labels, word_ids, pad_start_index):
        new_labels = []
        previous_word_id = None

        for idx, word_id in enumerate(word_ids):

            # 1️⃣ PAD → ignore
            if pad_start_index is not None and (idx >= pad_start_index):
                new_labels.append(-100)
                continue

            # 2️⃣ CLS / SEP → label 0
            if word_id is None:
                new_labels.append(0)
                continue

            # 3️⃣ First subword
            if word_id != previous_word_id:
                new_labels.append(labels[word_id])
            else:
                # 4️⃣ Subword → B-* → I-*
                label = labels[word_id]
                if label % 2 == 1:
                    label += 1
                new_labels.append(label)

            previous_word_id = word_id

        return new_labels

