from process import InferenceProcessStrategy, FileInput, ProcessedFile
from config import Settings
from shared.logger import logger
import asyncio
from bert_models import ModelStrategy
from tokenizer import TokenizerStrategy
from transformers import pipeline


class Inference:
    def __init__(self):
        self.preprocess = InferenceProcessStrategy.run(Settings.process_inference.preprocess_strategy)
        model_loader = ModelStrategy.run(Settings.model.model_name)
        model_loader.load_checkpoint()
        self.tokenizer = TokenizerStrategy.run(Settings.tokenizer.model_name)
        self.ner_pipe = pipeline(
            task="ner", 
            model=model_loader.model, 
            tokenizer=self.tokenizer.tokenizer, 
            aggregation_strategy="simple"
        )

    def invocations(self, file_input: FileInput) -> list:
        logger.info("Starting inference process.")    
        processed_file: ProcessedFile = asyncio.run(self.preprocess.process(file_input))
        logger.info("Preprocessing completed.")
        text = processed_file.text_as_one_string

        # ---- Get chunks based on token offsets ----
        chunk_spans = self._split_into_offset_chunks(
            text=text,
            stride=Settings.process_inference.chunk_stride,
            max_chunks=Settings.process_inference.max_chunks
        )
        logger.info(f"Created {len(chunk_spans)} text chunks for inference using offsets.")

        all_predictions = []
        for (start, end) in chunk_spans:
            chunk_text = text[start:end]

            logger.debug(f"Running NER on offset chunk [{start}:{end}]")
            chunk_entities = self.ner_pipe(chunk_text)

            # Adjust entities to absolute offsets based on chunk origin
            for ent in chunk_entities:
                ent["absolute_start"] = start + ent["start"]
                ent["absolute_end"] = start + ent["end"]
            # Filter entities based on threshold probability and set score as rounded string
            chunk_entities = [
                {
                    **ent,
                    "score": f"{ent['score']:.3f}"
                }
                for ent in chunk_entities
                if ent["score"] >= Settings.process_inference.threshold_prob
            ]

            all_predictions.extend(chunk_entities)

        logger.info("Inference complete.")
        return all_predictions


    # ----------------------------------------------------------------------
    # Correct chunker: OFFSET-FIRST chunk splitting
    # ----------------------------------------------------------------------
    def _split_into_offset_chunks(
        self,
        text: str,
        stride: int = 400,
        max_chunks: int = 4,
        max_tokens: int = 512
    ):
        """
        Uses tokenizer offsets to split text into sliding windows of max_tokens.
        Returns:
            List[(start_char, end_char)]  where each tuple defines the
            raw text span for the chunk.
        """

        encoding = self.tokenizer.tokenizer.encode_plus(
            text=text,
            is_split_into_words=False,
            padding=False,
            return_offsets_mapping=True,
        )

        offsets = encoding["offset_mapping"]

        # Remove CLS and SEP
        offsets = offsets[1:-1]

        # Sliding window over token offsets
        window_offset_chunks = [
            offsets[i : i + max_tokens]
            for i in range(0, len(offsets), stride)
            if offsets[i : i + max_tokens]
        ]

        # Convert offsets → character spans
        chunk_spans = [
            (chunk[0][0], chunk[-1][1]) for chunk in window_offset_chunks
        ]

        # Keep first max_chunks only
        return chunk_spans[:max_chunks]


if __name__ == "__main__":
    inference_instance = Inference()
    file_input = FileInput(
        filepath="/Users/marioslioutas/ner/artefacts/sample.json"
    )
    results = inference_instance.invocations(file_input)
    for i, res in enumerate(results):
        print(f"{i}: {res}")
