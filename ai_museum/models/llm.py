from typing import Literal

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_gigachat import GigaChat, GigaChatEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import SecretStr

from ai_museum.utils import require_env_var


class LLMFactory:
    """Фабрика для создания экземпляров LLM (OpenAI, GigaChat)."""

    @classmethod
    def get_llm(cls, name: Literal["gigachat", "openai"]) -> BaseChatModel:
        """Возвращает экземпляр LLM по имени."""

        if name == "openai":
            return ChatOpenAI(
                base_url=require_env_var("OPENAI_BASE_URL"),
                api_key=SecretStr(require_env_var("OPENAI_KEY")),
            )

        if name == "gigachat":
            return GigaChat(
                credentials=require_env_var("GIGACHAT_KEY"),
                scope=require_env_var("GIGACHAT_SCOPE"),
                model=require_env_var("GIGACHAT_MODEL"),
                verify_ssl_certs=False,
            )

        raise ValueError(f"Unknown LLM name: {name!r}")

    @classmethod
    def get_embeddings(cls, name: Literal["gigachat", "openai"]) -> Embeddings:
        """Возвращает экземпляр Embeddings по имени."""

        if name == "openai":
            return OpenAIEmbeddings(
                base_url=require_env_var("OPENAI_BASE_URL"),
                api_key=SecretStr(require_env_var("OPENAI_KEY")),
                model="text-embedding-3-small",
            )

        if name == "gigachat":
            return GigaChatEmbeddings(
                credentials=require_env_var("GIGACHAT_KEY"),
                model=require_env_var("GIGACHAT_EMBEDDER_MODEL"),
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
            return require_env_var("GIGACHAT_MODEL")

        raise ValueError(f"Unknown Embeddings name: {name!r}")
