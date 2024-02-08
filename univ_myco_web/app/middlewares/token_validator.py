import base64
import hmac
import time
import typing
import re

import jwt
import sqlalchemy.exc


from starlette.requests import Request
from starlette.responses import JSONResponse

from common.consts import EXCEPT_PATH_LIST, EXCEPT_PATH_REGEX
from database.conn import db
from database.schema import Users, ApiKeys
from errors import exceptions as ex
from common import config, consts
from errors.exceptions import APIException, SqlFailureEx, APIQueryStringEx
from jwt.exceptions import ExpiredSignatureError, DecodeError
from models import UserToken

from utils.date_utils import D
from utils.logger import api_logger
from utils.query_utils import to_dict


async def access_control(request: Request, call_next):
    request.state.req_time = D.datetime()
    request.state.start = time.time()
    request.state.inspect = None
    request.state.user = None
    request.state.service = None

    ip = request.headers["x-forwarded-for"] if "x-forwarded-for" in request.headers.keys() else request.client.host
    request.state.ip = ip.split(",")[0] if "," in ip else ip
    headers = request.headers
    cookies = request.cookies

    url = request.url.path
    if await url_pattern_check(url, EXCEPT_PATH_REGEX) or url in EXCEPT_PATH_LIST:
        response = await call_next(request)
        if url != "/":
            await api_logger(request=request, response=response)
        return response

    try:
        if url.startswith("/api"):
            if "authorization" in headers.keys():
                token_info = await token_decode(access_token=headers.get("Authorization"))
                request.state.user = UserToken(**token_info)
                # no token
            else:
                if "Authorization" not in headers.keys():
                    raise ex.NotAuthorized()
        else:
            cookies["Authorization"] = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6MTQsImVtYWlsIjoia29hbGFAZGluZ3JyLmNvbSIsIm5hbWUiOm51bGwsInBob25lX251bWJlciI6bnVsbCwicHJvZmlsZV9pbWciOm51bGwsInNuc190eXBlIjpudWxsfQ.4vgrFvxgH8odoXMvV70BBqyqXOFa2NDQtzYkGywhV48"

            if "Authorization" not in cookies.keys():
                raise ex.NotAuthorized()

            token_info = await token_decode(access_token=cookies.get("Authorization"))
            request.state.user = UserToken(**token_info)
        response = await call_next(request)
        await api_logger(request=request, response=response)
    except Exception as e:

        error = await exception_handler(e)
        error_dict = dict(status=error.status_code, msg=error.msg, detail=error.detail, code=error.code)
        response = JSONResponse(status_code=error.status_code, content=error_dict)
        await api_logger(request=request, error=error)

    return response


async def url_pattern_check(path, pattern):
    result = re.match(pattern, path)
    if result:
        return True
    return False


async def token_decode(access_token):
    """
    :param access_token:
    :return:
    """
    try:
        access_token = access_token.replace("Bearer ", "")
        payload = jwt.decode(access_token, key=consts.JWT_SECRET, algorithms=[consts.JWT_ALGORITHM])
    except ExpiredSignatureError:
        raise ex.TokenExpiredEx()
    except DecodeError:
        raise ex.TokenDecodeEx()
    return payload


async def exception_handler(error: Exception):
    print(error)
    if isinstance(error, sqlalchemy.exc.OperationalError):
        error = SqlFailureEx(ex=error)
    if not isinstance(error, APIException):
        error = APIException(ex=error, detail=str(error))
    return error
