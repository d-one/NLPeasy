from transformers import DistilBertTokenizerFast
from config import Settings
from shared.logger import logger
from tokenizer.interfaces.tokenizer_interface import TokenizerI


class DistilBertTokenizer(TokenizerI):
    def __init__(self):
        self._tokenizer = self._build_tokenizer()

    @property
    def tokenizer(self):
        return self._tokenizer

    def _build_tokenizer(self):
        if Settings.tokenizer.load_from_local:
            tokenizer = DistilBertTokenizerFast.from_pretrained(Settings.tokenizer.local_tokenizer_path)
        else:
            tokenizer = DistilBertTokenizerFast.from_pretrained(Settings.tokenizer.model_name)
        return tokenizer
