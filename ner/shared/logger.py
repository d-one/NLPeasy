import logging
from config import Settings


class ColoredFormatter(logging.Formatter):
    def __init__(
        self,
        colors: dict[str, str],
        reset: str,
        fmt: str | None = None,
        datefmt: str | None = None,
        style="%",
        validate: bool = True,
    ):
        super().__init__(fmt, datefmt, style, validate)
        self.colors = colors
        self.reset = reset

    def format(self, record):
        color = self.colors.get(record.levelname, self.reset)
        message = super().format(record)
        return f"{color}{message}{self.reset}"


cfg = Settings.logging

formatter = ColoredFormatter(
    colors=cfg.colors,
    reset=cfg.reset,
    fmt="%(asctime)s | %(process)d | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
)

console_handler = logging.StreamHandler()
console_handler.setLevel(cfg.level)
console_handler.setFormatter(formatter)

logger = logging.getLogger("Application Logger")
logger.setLevel(cfg.level)
logger.addHandler(console_handler)

if hasattr(cfg, "loggers_to_loguru") and cfg.loggers_to_loguru is not None:
    for logger_name in cfg.loggers_to_loguru:
        specific_logger = logging.getLogger(logger_name)
        specific_logger.handlers = [console_handler]
        specific_logger.setLevel(cfg.level)


def test_logger():
    logger.info("Hello")
    logger.warning("Hello")
    logger.error("Hello")
    logger.debug("Hello")


if __name__ == "__main__":
    test_logger()
