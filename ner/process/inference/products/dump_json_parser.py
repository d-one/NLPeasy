import json
from config import Settings
from shared.logger import logger
from process.inference.interfaces.inference_process_interface import InferenceProcessorI
from process.inference.entities import FileInput, ProcessedFile


class DumpJsonParser(InferenceProcessorI):

    async def process(self, file_input: FileInput) -> ProcessedFile:
        """Process the file and searchs for text in the file.
        Args:
            file_input: FileInput entity containing the filepath to the Textract OCR output dictionary.
        Returns:
            ProcessedFile entity containing the extracted text as one string and as a list of texts per page.
        """
        try:
            with open(file_input.filepath, 'r') as f:
                input_dict = json.load(f)

            # just read the text fields from json
            list_of_texts = []
            for item in input_dict:
                try:
                    text = item["text"]
                    list_of_texts.append(text)
                except:
                    continue
            text_as_one_string = " ".join(list_of_texts)

        except:
            list_of_texts, text_as_one_string = ["-1"], "-1"
            logger.debug("Output replaced with -1 because loading failed.")

        return ProcessedFile(
            text_as_one_string=text_as_one_string,
            list_of_texts=list_of_texts
        )
