from typing import TypeVar

from pydantic_settings import BaseSettings

T = TypeVar("T", bound=BaseSettings)


def singleton(cls: type[T]) -> T:
    """A decorator to implement the singleton pattern for a class.

    This ensures that only one instance of the class exists throughout the application.

    Args:
        cls (type[T]): The class to be decorated as a singleton.

    Returns:
        T: The single instance of the class.
    """
    instances = {}

    if cls not in instances:
        instances[cls] = cls()

    return instances[cls]
