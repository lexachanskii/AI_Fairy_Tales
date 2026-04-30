from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
from enum import Enum


class TaleSizeEnum(str, Enum):
    TINY = "tiny"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class HeroModeEnum(str, Enum):
    PROFILE_CHILD = "profile_child"
    RANDOM = "random"
    CUSTOM = "custom"


class TaleCreate(BaseModel):
    name: Optional[str] = Field(default="", max_length=100)
    genre: str = Field(default="Случайный жанр", min_length=1, max_length=100)
    moral: Optional[str] = Field(default="Случайная мораль", max_length=500)
    hero_mode: HeroModeEnum = HeroModeEnum.PROFILE_CHILD
    hero_description: Optional[str] = Field(default="", max_length=500)
    size: TaleSizeEnum = TaleSizeEnum.SMALL

    @model_validator(mode="after")
    def validate_custom_hero(self):
        if self.hero_mode == HeroModeEnum.CUSTOM and not (self.hero_description or "").strip():
            raise ValueError("Опишите главного героя или выберите ребёнка из профиля / случайного героя")
        return self


class TaleMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)


class TalePartResponse(BaseModel):
    response: str
    stage: int
    is_completed: bool


class TaleResponse(BaseModel):
    id: int
    name: str
    genre: str
    moral: Optional[str] = None
    hero: Optional[str] = None
    size: int
    content: List[dict]
    current_stage: int
    is_completed: bool

    class Config:
        from_attributes = True
