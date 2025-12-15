from abc import ABC, abstractmethod
from process.inference.entities import FileInput, ProcessedFile


class InferenceProcessorI(ABC):
    @abstractmethod
    async def process(self, file_input: FileInput) -> ProcessedFile:
        pass
