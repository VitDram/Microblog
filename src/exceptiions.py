from fastapi import Request
from fastapi.responses import JSONResponse


class UnicornException(Exception):
    def __init__(self, result: bool, error_type: str, error_message: str):
        self.result: bool = result
        self.error_type: str = error_type
        self.error_message: str = error_message
        super().__init__(self.error_message)


async def unicorn_exception_handler(
        request: Request, exc: UnicornException
) -> JSONResponse:
    """Вывод информации об ошибке"""
    return JSONResponse(
        status_code=418,
        content={
            "result": exc.result,
            "error_type": exc.error_type,
            "error_message": exc.error_message,
        },
    )
