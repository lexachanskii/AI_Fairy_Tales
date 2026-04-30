from openai import AsyncOpenAI

from app.config import settings
from app.models.user import User, Sex
from app.models.tale import Tale

_client = AsyncOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
)


def _build_stage_instruction(tale: Tale, stage: int) -> str:
    is_final_stage = stage >= tale.size

    base = (
        f"Сказка состоит ровно из {tale.size} частей. "
        f"Сейчас нужно написать часть {stage} из {tale.size}."
    )

    if is_final_stage:
        return (
            base + "\n"
            "Это последняя часть сказки. Заверши сюжет мягко, цельно и по-доброму. "
            "Не задавай вопрос для продолжения, не предлагай варианты выбора, "
            "не используй формат вроде `а)` / `б)`. "
            "В конце должно быть ощущение завершённой сказки."
        )

    return (
        base + "\n"
        "Это не последняя часть. Продолжи сюжет и в конце задай один короткий вопрос, "
        "чтобы ребёнок мог выбрать, что произойдёт дальше. Можно предложить 2 понятных варианта."
    )


def _build_first_user_prompt(user: User, tale: Tale, user_message: str, stage: int = 1) -> str:
    sex_label = "Мужской" if user.sex == Sex.MALE else "Женский"
    name = user.name or "не указано"
    age = str(user.age) if user.age else "не указано"
    hobby = user.hobby or "не указано"

    return (
        "Ты — дедушка Дрёма, добрый и мудрый сказочник. "
        "Ты рассказываешь интерактивную сказку, в которой пользователь сам влияет на сюжет. "
        "Сохраняй тёплый, детский и понятный тон.\n\n"
        f"Информация о ребёнке:\n"
        f"- Имя: {name}\n"
        f"- Пол: {sex_label}\n"
        f"- Возраст: {age}\n"
        f"- Увлечения: {hobby}\n\n"
        f"Параметры сказки:\n"
        f"- Тема/название: {tale.name}\n"
        f"- Главный герой истории: {tale.hero or 'Случайный герой'}\n"
        f"- Жанр: {tale.genre}\n"
        f"- Мораль: {tale.moral or 'Случайная мораль'}\n"
        f"- Всего частей: {tale.size}\n\n"
        f"{_build_stage_instruction(tale, stage)}\n\n"
        f"Пользователь написал: {user_message}"
    )


def _build_continuation_prompt(tale: Tale, user_message: str, stage: int) -> str:
    return (
        f"{_build_stage_instruction(tale, stage)}\n\n"
        f"Пользователь написал: {user_message}"
    )


def _build_messages(user: User, tale: Tale, user_message: str) -> list[dict]:
    messages: list[dict] = []
    history: list[dict] = tale.content or []

    for i, part in enumerate(history):
        past_stage = i + 1
        past_user_msg = part.get("user_message", "")
        past_bot_reply = part.get("assistant_response", "")

        if i == 0:
            messages.append({
                "role": "user",
                "content": _build_first_user_prompt(user, tale, past_user_msg, past_stage),
            })
        else:
            messages.append({
                "role": "user",
                "content": _build_continuation_prompt(tale, past_user_msg, past_stage),
            })

        messages.append({"role": "assistant", "content": past_bot_reply})

    next_stage = len(history) + 1

    if not history:
        messages.append({
            "role": "user",
            "content": _build_first_user_prompt(user, tale, user_message, next_stage),
        })
    else:
        messages.append({
            "role": "user",
            "content": _build_continuation_prompt(tale, user_message, next_stage),
        })

    return messages


class AIService:
    async def generate_response(self, user: User, tale: Tale, user_message: str) -> str:
        messages = _build_messages(user, tale, user_message)

        response = await _client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=False,
            temperature=settings.AI_TEMPERATURE,
        )

        return response.choices[0].message.content
