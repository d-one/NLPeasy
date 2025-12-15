from pydantic import BaseModel, Field


class LoggingConfig(BaseModel):
    """Logging configuration settings.

    Attributes:
        level (int): The logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL).
        format (str): The logging format string.
        loggers_to_loguru (list[str]): A list of logger names to be redirected to Loguru.
    """

    level: int = Field(
        default=10,
        description="The logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )
    format: str = Field(
        default="%(asctime)s | %(process)d | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        description="The logging format string.",
    )
    loggers_to_loguru: list[str] = Field(
        default=["uvicorn", "uvicorn.access", "uvicorn.error"],
        description="A list of logger names to be redirected to the main logger.",
    )
    colors: dict[str, str] = Field(
        default={
            "DEBUG": "\033[94m",
            "INFO": "\033[92m",
            "WARNING": "\033[93m",
            "ERROR": "\033[91m",
            "CRITICAL": "\033[91m",
        }
    )
    reset: str = Field(default="\033[0m")

    class Config:
        extra = "allow"
