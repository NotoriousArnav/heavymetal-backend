from fastapi import APIRouter
from auth import router as auth_router

router = APIRouter(
    prefix="/api/v1",
    tags=["General Purpose APIs", "Auth", "Users", "Public"],
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
