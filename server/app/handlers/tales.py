from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.tale import TaleCreate, TaleResponse, TaleMessageRequest, TalePartResponse
from app.services.tale_service import TaleService
from app.services.user_service import UserService
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/tales", tags=["tales"])
tale_service = TaleService()


def _assert_own(current_user: User, user_id: int) -> None:
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещён")


@router.post("/{user_id}/create", response_model=TaleResponse)
async def create_tale(
    user_id: int,
    tale_data: TaleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _assert_own(current_user, user_id)

    # ── Блокируем генерацию, если профиль не заполнен ─────────────────────────
    is_complete, missing = UserService.is_profile_complete(current_user)
    if not is_complete:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Заполните профиль перед созданием сказки.",
                "missing_fields": missing,
            },
        )
    # ──────────────────────────────────────────────────────────────────────────

    tale = await tale_service.create_tale(db, user_id, tale_data, current_user)
    return TaleResponse(
        id=tale.id,
        name=tale.name,
        genre=tale.genre,
        moral=tale.moral,
        hero=tale.hero,
        size=tale.size,
        content=tale.content,
        current_stage=len(tale.content),
        is_completed=False,
    )


@router.get("/{user_id}/current", response_model=TaleResponse)
async def get_current_tale(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _assert_own(current_user, user_id)
    tale = await tale_service.get_user_tale(db, user_id)
    if not tale:
        raise HTTPException(status_code=404, detail="Нет активной сказки")

    return TaleResponse(
        id=tale.id,
        name=tale.name,
        genre=tale.genre,
        moral=tale.moral,
        hero=tale.hero,
        size=tale.size,
        content=tale.content,
        current_stage=len(tale.content),
        is_completed=len(tale.content) >= tale.size,
    )


@router.post("/{user_id}/add", response_model=TalePartResponse)
async def add_message(
    user_id: int,
    request: TaleMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _assert_own(current_user, user_id)
    tale = await tale_service.get_user_tale(db, user_id)
    if not tale:
        raise HTTPException(status_code=404, detail="Нет активной сказки")
    if len(tale.content) >= tale.size:
        raise HTTPException(status_code=400, detail="Сказка уже закончена")

    result = await tale_service.add_message(db, tale, request.message, current_user)

    # FIX: сервис возвращает assistant_response/part_number,
    #      схема ожидает response/stage — маппим явно.
    return TalePartResponse(
        response=result["assistant_response"],
        stage=result["part_number"],
        is_completed=result["is_completed"],
    )


@router.get("/{user_id}/last")
async def get_last_part(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _assert_own(current_user, user_id)
    tale = await tale_service.get_user_tale(db, user_id)
    if not tale:
        raise HTTPException(status_code=404, detail="Нет активной сказки")

    last_response = await tale_service.get_last_response(tale)
    return {"response": last_response, "stage": len(tale.content)}


@router.post("/{user_id}/complete", response_class=PlainTextResponse)
async def complete_tale(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _assert_own(current_user, user_id)
    tale = await tale_service.get_user_tale(db, user_id)
    if not tale:
        raise HTTPException(status_code=404, detail="Нет активной сказки")

    full_text = await tale_service.complete_tale(db, tale)
    return PlainTextResponse(content=full_text, media_type="text/plain")
