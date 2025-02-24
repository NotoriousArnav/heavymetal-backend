from fastapi import APIRouter

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
