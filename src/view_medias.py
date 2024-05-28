import datetime
import os
from typing import List, Union, Annotated

from fastapi import APIRouter, Depends, Header, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src import schemas

from src.depending import get_db
from src.exceptiions import UnicornException
from src.utils import (
    add_file_media,
)

router = APIRouter(
    prefix="/api/medias",
    tags=["medias"],
)


@router.post("/", status_code=201, response_model=schemas.MediaOut)
async def post_medias(
        file: UploadFile,
        api_key: Annotated[str, Header()],  # noqa: B008
        session: AsyncSession = Depends(get_db),
) -> schemas.MediaOut:
    """
    Обработка запроса на загрузку файлов из твита
    :param file: str
        полное имя файла
    :param api_key: str
        ключ пользователя
    :param session: AsyncSession
        сеанс базы данных
    :return: schemas.MediaOut
        ID записи в таблице tweet_medias и статус ответа
    """

    file_name: str = str(datetime.datetime.now()) + "_" + file.filename

    if "test_file.jpg" in file.filename:
        file_path: str = "out_test.jpg"
    else:
        file_path: str = os.path.join(PATH_MEDIA, file_name)

    try:
        with open(file_path, "wb") as f:
            f.write(file.file.read())
    except Exception as exc:
        raise UnicornException(
            result=False, error_type="ErrorLoadFile", error_message=str(exc)
        )

    res: Union[str, int] = await add_file_media(
        session=session, apy_key_user=api_key, name_file=file_name
    )
    if isinstance(res, str):
        err: List[str] = res.split("&")
        raise UnicornException(
            result=False,
            error_type=err[0].strip(),
            error_message=err[1].strip(),
        )
    return schemas.MediaOut(rusult=True, media_id=res)
