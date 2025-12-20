import os
from typing import TypeVar


T = TypeVar("T")


def require_var_type(variable: object, expected_type: type[T]) -> T:
    """Обеспечивает строгую типизацию"""
    if not isinstance(variable, expected_type):
        raise RuntimeError(
            f"Expected ONLY {expected_type.__name__}, but got {type(variable).__name__}"
        )
    return variable


def require_env_var(name: str) -> str:
    """Безопасно получает переменную окружения, иначе выбрасывает ошибку."""
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(f"Environment variable '{name}' is not set.")
    return value
