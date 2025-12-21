from ai_museum.db.models import Exhibit


def format_exhibit_context(exhibits: list[Exhibit]) -> str:
    """Форматирование информации об экспонатах в контекст"""
    context = "\n\nДоступные экспонаты:\n"
    for exhibit in exhibits:
        context += f"- ID: {exhibit.id}, Название: {exhibit.name}, Описание: {exhibit.description}\n"
    return context


# TODO убрать
# dialog = "dasdsadasdasdasdsadasdasdasdasdasd"

# exps = search_similar_exhibits(dialog) # 3 ближайших по тексту
# contex = format_exhibit_context(exps) # 3 ближайших по тексту в виде текст
# prompt = f"Выбери 1 экспонат, который наиболее пойдет пользователю, экспонаты {contex}, предыдущий диалог {dialog[:2000]}" # -> 1-3 1
# format_exhibit_context(exps[0]) # Информация по наиболее релевантному экспонату
