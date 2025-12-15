from pydantic import Field
import os
from pydantic_settings import (
    BaseSettings,
    JsonConfigSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from pathlib import Path
from config.dataset_config import DatasetConfig
from config.tokenizer_config import TokenizerConfig
from config.model_config import ModelConfig
from config.decorators import singleton
from config.logging_config import LoggingConfig
from config.process_inference_config import ProcessInferenceConfig

@singleton
class Settings(BaseSettings):
    """AppSettings is a configuration class that inherits from BaseSettings and is used to manage application settings.

    Attributes:
        fastapi (FastAPIConfig): Configuration settings for FastAPI.
        cors (CorsConfig): Configuration settings for Cross-Origin Resource Sharing (CORS).
        logging (LoggingConfig): Configuration settings for logging.
        server (ServerConfig): Configuration settings for the server.
        endpoints (EndpointsConfig): Configuration settings for API endpoints.
        model_config (SettingsConfigDict): Configuration for the settings model, specifying the JSON file path.

    Methods:
        settings_customise_sources(cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings):
            Customizes the sources from which settings are loaded, prioritizing JSON configuration files.
    """

    dataset: DatasetConfig = Field(default_factory=DatasetConfig)
    tokenizer: TokenizerConfig = Field(default_factory=TokenizerConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    process_inference: ProcessInferenceConfig = Field(default_factory=ProcessInferenceConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    model_config = SettingsConfigDict(
        json_file=os.getenv("SETTTINGS_FILE"),
        json_file_encoding="utf-8",
        validate_default=False,
        validate_assignment=False,
        env_file=str(Path(__file__).parents[1] / ".env"),
    )
    PYTHONPATH: str = Field(default="./ner", description="Path to the ner module.")
    SETTTINGS_FILE: str = Field(
        default=str(Path(__file__).parents[1] / "settingsygbu.json"),
        description="Path to the settings JSON file.",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Customizes the sources from which settings are loaded, prioritizing JSON configuration files."""
        return (JsonConfigSettingsSource(settings_cls), env_settings, dotenv_settings)


if __name__ == "__main__":
    print(Settings.model_dump())
