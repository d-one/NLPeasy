from tokenizer.products.distilbert import DistilBertTokenizer
from tokenizer.products.bert import BertTokenizer
from tokenizer.interfaces.tokenizer_interface import TokenizerI


class TokenizerStrategy:
    _strategies = {
        "distilbert-base-cased": DistilBertTokenizer,
        "bert-base-cased": BertTokenizer
    }

    @staticmethod
    def run(method: str) -> TokenizerI:
        strategy_class = TokenizerStrategy._strategies.get(method.lower())
        if not strategy_class:
            raise ValueError(f"Method '{method}' is not supported.")
        return strategy_class()
