from bert_models.products.distilbert import DistilBertModelLoader
from bert_models.products.bert import BertModelLoader
from bert_models.interfaces.model_interface import ModelI


class ModelStrategy:
    _strategies = {
        "distilbert-base-cased": DistilBertModelLoader,
        "bert-base-cased": BertModelLoader
    }

    @staticmethod
    def run(method: str) -> ModelI:
        strategy_class = ModelStrategy._strategies.get(method.lower())
        if not strategy_class:
            raise ValueError(f"Method '{method}' is not supported.")
        return strategy_class()
