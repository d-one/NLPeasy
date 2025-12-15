from abc import ABC, abstractmethod


class TokenizerI(ABC):

    @abstractmethod
    def __init__(self):
        pass

    @property
    @abstractmethod
    def tokenizer(self):
        pass

    @abstractmethod
    def _build_tokenizer(self):
        pass
