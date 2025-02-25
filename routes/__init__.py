from fastapi import APIRouter
from .auth import router as auth_router
from .songs import router as songs_router

router = APIRouter(
    prefix="/api/v1",
    responses={
        404: {
                "description":"Not found"
            },
        500: {
                "description":"Internal Server Error"
            },
        400: {
                "description":"Bad Request"
            },
        },
)

router.include_router(auth_router)
router.include_router(songs_router)
