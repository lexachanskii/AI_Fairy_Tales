from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from app.models.tale import Tale
from app.models.user import User, Sex
from app.schemas.tale import TaleCreate, TaleSizeEnum, HeroModeEnum
from app.services.ai_service import AIService


class TaleService:
    def __init__(self):
        self.size_map = {
            TaleSizeEnum.TINY:   3,
            TaleSizeEnum.SMALL:  8,
            TaleSizeEnum.MEDIUM: 16,
            TaleSizeEnum.LARGE:  32,
        }
        self._ai_service = AIService()

    def _resolve_hero(self, user: User, tale_data: TaleCreate) -> str:
        if tale_data.hero_mode == HeroModeEnum.PROFILE_CHILD:
            sex_label = "мальчик" if user.sex == Sex.MALE else "девочка"
            parts = [user.name or "ребёнок"]
            if user.age:
                parts.append(f"{user.age} лет")
            parts.append(sex_label)
            if user.hobby:
                parts.append(f"увлечения: {user.hobby}")
            return ", ".join(parts)

        if tale_data.hero_mode == HeroModeEnum.RANDOM:
            return "Случайный герой"

        return (tale_data.hero_description or "").strip()

    def _resolve_name(self, tale_data: TaleCreate) -> str:
        name = (tale_data.name or "").strip()
        if name:
            return name
        genre = tale_data.genre if tale_data.genre != "Случайный жанр" else "сказка"
        return f"Новая {genre.lower()}"[:100]

    async def create_tale(self, db: AsyncSession, user_id: int, tale_data: TaleCreate, user: User) -> Tale:
        result = await db.execute(select(Tale).where(Tale.user_id == user_id))
        old_tale = result.scalar_one_or_none()
        if old_tale:
            old_tale.user_id = None
            await db.flush()

        tale = Tale(
            name=self._resolve_name(tale_data),
            genre=tale_data.genre,
            hero=self._resolve_hero(user, tale_data),
            moral=(tale_data.moral or "Случайная мораль").strip(),
            size=self.size_map[tale_data.size],
            content=[],
            user_id=user_id,
        )
        db.add(tale)
        await db.commit()
        await db.refresh(tale)
        return tale

    async def get_user_tale(self, db: AsyncSession, user_id: int) -> Tale | None:
        result = await db.execute(select(Tale).where(Tale.user_id == user_id))
        return result.scalar_one_or_none()

    async def add_message(
        self,
        db: AsyncSession,
        tale: Tale,
        user_message: str,
        user: User,
    ) -> dict:
        """
        Генерирует ответ модели на сообщение пользователя и сохраняет в историю сказки.

        Параметр user необходим для формирования контекста (пол, возраст, хобби),
        аналогично тому, как в старом боте get_prompt() читал поля пользователя из БД.
        """
        await db.refresh(tale)

        current_stage = len(tale.content)

        if current_stage >= tale.size:
            raise ValueError("Сказка уже закончена")

        bot_response = await self._ai_service.generate_response(user, tale, user_message)

        new_part = {
            "part_number":        current_stage + 1,
            "user_message":       user_message,
            "assistant_response": bot_response,
        }

        tale.content = list(tale.content) + [new_part]
        flag_modified(tale, "content")
        await db.commit()

        return {
            "part_number":        current_stage + 1,
            "user_message":       user_message,
            "assistant_response": bot_response,
            "is_completed":       (current_stage + 1) >= tale.size,
        }

    async def complete_tale(self, db: AsyncSession, tale: Tale) -> str:
        if not tale.content:
            raise ValueError("Сказка пуста")

        full_text = (
            f"Название: {tale.name}\n"
            f"Главный герой: {tale.hero or 'не указан'}\n"
            f"Жанр: {tale.genre}\n"
            f"Мораль: {tale.moral or 'не указана'}\n\n"
        )
        for part in tale.content:
            full_text += f"Часть {part['part_number']}:\n{part['assistant_response']}\n\n"

        tale.user_id = None
        await db.commit()
        return full_text

    async def get_last_response(self, tale: Tale) -> str | None:
        if not tale.content:
            return None
        return tale.content[-1].get("assistant_response")
