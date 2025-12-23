import re

from langchain_core.messages import AnyMessage
import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool


@tool
def web_search(query: str, k: int = 3) -> str:
    """Быстрый веб-поиск через DuckDuckGo HTML; возвращает краткие записи.

    Формат: номер. заголовок\nсниппет\nссылка
    """
    print(f"Был вызван поиск: {query}")
    headers = {"User-Agent": "ai_museum/1.0 (+https://example.org)"}
    try:
        resp = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
    except Exception as e:
        return f"Ошибка поиска: {e}"

    soup = BeautifulSoup(resp.text, "html.parser")
    results: list[tuple[str, str, str]] = []

    for item in soup.select("div.result"):
        a = item.select_one("a.result__a") or item.select_one("a")
        if not a:
            continue
        href = a.get("href") or ""
        title = a.get_text(strip=True) or "(no title)"
        sn_el = item.select_one(".result__snippet")
        snippet = sn_el.get_text(strip=True) if sn_el else ""
        results.append((title, snippet, href))
        if len(results) >= k:
            break

    if not results:
        return "Ничего не найдено"

    out_lines: list[str] = []
    for idx, (title, snippet, href) in enumerate(results, start=1):
        out_lines.append(f"{idx}. {title}\n{snippet}\n{href}")

    return "\n\n".join(out_lines)


def clean_message(message: AnyMessage):
    text = message.text

    clean_text = re.sub(r" ?\[?sources=(:?\[(:?.*)\]|собственные знания)\]?", "", text)
    clean_text = re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', clean_text)
    message.content = clean_text

    return message
