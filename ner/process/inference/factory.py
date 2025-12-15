from process.inference.interfaces.inference_process_interface import InferenceProcessorI
from process.inference.products.dump_json_parser import DumpJsonParser
from process.inference.products.textract_parser import TextractParser


class InferenceProcessStrategy:
    _strategies = {
        "dump_json": DumpJsonParser,
        "textract_parser": TextractParser
    }

    @staticmethod
    def run(method: str) -> InferenceProcessorI:
        strategy_class = InferenceProcessStrategy._strategies.get(method.lower())
        if not strategy_class:
            raise ValueError(f"Method '{method}' is not supported.")
        return strategy_class()
