import os
import uuid
from typing import Literal

import dotenv
import requests
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import OpenAIEmbeddings
from langchain_gigachat import GigaChat, GigaChatEmbeddings
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.embeddings import Embeddings
from pydantic import SecretStr

if not dotenv.load_dotenv():
    print("Не удалось подгрузить переменные из .env")


# пока нигде не используется но вдруг понадобится
def get_gigachat_access_token(token: str, scope: str) -> SecretStr:
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),  # любой UUID запроса
        "Authorization": f"Basic {token}",
    }
    data = {"scope": scope}
    response = requests.post(url, headers=headers, data=data, verify=False)

    if not response.ok:
        raise RuntimeError(
            f"Ошибка при получении токена (HTTP {response.status_code}):\n{response.text}"
        )

    data = response.json()

    if "access_token" not in data:
        raise KeyError(f"Нет access_token в ответе: {data}")

    return SecretStr(data["access_token"])


class LLMFactory:
    """Фабрика для создания экземпляров LLM (OpenAI, GigaChat)."""

    @staticmethod
    def _get_env_var(name: str) -> str:
        """Безопасно получает переменную окружения, иначе выбрасывает ошибку."""
        value = os.getenv(name)
        if not value:
            raise EnvironmentError(f"Environment variable '{name}' is not set.")
        return value

    @classmethod
    def get_llm(cls, name: Literal["gigachat", "openai"]) -> BaseChatModel:
        """Возвращает экземпляр LLM по имени."""

        if name == "openai":
            return ChatOpenAI(
                base_url=cls._get_env_var("OPENAI_BASE_URL"),
                api_key=SecretStr(cls._get_env_var("OPENAI_KEY")),
            )

        if name == "gigachat":
            return GigaChat(
                credentials=cls._get_env_var("GIGACHAT_KEY"),
                model=cls._get_env_var("GIGACHAT_MODEL"),
                verify_ssl_certs=False,
            )

        raise ValueError(f"Unknown LLM name: {name!r}")
        
    @classmethod
    def get_embeddings(cls, name: Literal["gigachat", "openai"]) -> Embeddings:
        """Возвращает экземпляр Embeddings по имени."""

        if name == "openai":
            return OpenAIEmbeddings(
                base_url=cls._get_env_var("OPENAI_BASE_URL"),
                api_key=cls._get_env_var("OPENAI_KEY"),
                model="text-embedding-3-small"
            )

        if name == "gigachat":
            return GigaChatEmbeddings(
                credentials=cls._get_env_var("GIGACHAT_KEY"),
                model=cls._get_env_var("GIGACHAT_EMBEDDER_MODEL"),
                verify_ssl_certs=False,
                scope="GIGACHAT_API_CORP",
            )

        raise ValueError(f"Unknown Embeddings name: {name!r}")

    @classmethod
    def get_embedding_model(cls, name: Literal["gigachat", "openai"]) -> str:
        """Возвращает название модели для эмбеддингов."""
        
        if name == "openai":
            return "text-embedding-3-small"
            
        if name == "gigachat":
            return cls._get_env_var("GIGACHAT_MODEL")
            
        raise ValueError(f"Unknown Embeddings name: {name!r}")
