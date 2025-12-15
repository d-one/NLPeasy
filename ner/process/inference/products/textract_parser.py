import json
from config import Settings
from shared.logger import logger
from process.inference.interfaces.inference_process_interface import InferenceProcessorI
from process.inference.entities import FileInput, ProcessedFile


class TextractParser(InferenceProcessorI):

    async def process(self, file_input: FileInput) -> ProcessedFile:
        """Process the Textract OCR output dictionary to extract text.
        Args:
            file_input: FileInput entity containing the filepath to the Textract OCR output dictionary.
        Returns:
            ProcessedFile entity containing the extracted text as one string and as a list of texts per page.
        """
        try:
            with open(file_input.filepath, 'r') as f:
                input_dict = json.load(f)

            # Initialize a dictionary to hold text lines for each page
            pages = {}
            list_of_textracted_words = []
            for block in input_dict["Blocks"]:
                if block["BlockType"] == "LINE":
                    # Get the page number for this line
                    page_number = block["Page"]

                    # Initialize the page in the dictionary if it's not already there
                    if page_number not in pages:
                        pages[page_number] = []
                    try:
                        # Append the line to the list of lines for this page
                        pages[page_number].append(block["Text"])
                    except:
                        continue

            # Now, convert the dictionary of pages into a list of texts
            list_of_texts = []
            for page_number in sorted(pages.keys()):
                page_text = "\n".join(pages[page_number])
                list_of_texts.append(page_text)

            # Generate one string from the list of strings
            text_as_one_string = " ".join(list_of_texts)

        except:
            list_of_texts, text_as_one_string = ["-1"], "-1"
            logger.debug("Output replaced with -1 because loading failed.")

        return ProcessedFile(
            text_as_one_string=text_as_one_string,
            list_of_texts=list_of_texts
        )