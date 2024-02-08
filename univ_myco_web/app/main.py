from dataclasses import asdict
from typing import Optional

import uvicorn
import os
from fastapi import FastAPI, Depends

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from common.consts import EXCEPT_PATH_LIST, EXCEPT_PATH_REGEX, DATA_DIR, TEMP_DIR, API_KEY_HEADER
from database.conn import db, Base
from common.config import conf
from middlewares.token_validator import access_control
from middlewares.trusted_hosts import TrustedHostMiddleware
from routers import index, sample, data, users
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.gzip import GZipMiddleware
from starlette.requests import Request
from starlette.responses import Response


def create_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)


def create_app():
    """
    :return:
    """
    create_dir()
    
    c = conf()
    app = FastAPI()
    app.mount("/static", StaticFiles(directory="static"), name="static")

    conf_dict = asdict(c)
    db.init_app(app, **conf_dict)

    Base.metadata.create_all(db.engine)

    app.add_middleware(CORSMiddleware,
                       allow_origins=["*"],
                       allow_credentials=True,
                       allow_methods=["*"],
                       allow_headers=["*"],
                       )

    app.include_router(index.router)
    app.include_router(users.router, tags=["Users"], prefix="/user")

    if conf().DEBUG:
        app.include_router(data.router, tags=["Datafile"], prefix="/datafiles")
        app.include_router(sample.router, tags=["Samples"], prefix="/samples")
    else:
        app.include_router(data.router, tags=["Datafile"], prefix="/datafiles", dependencies=[Depends(API_KEY_HEADER)])
        app.include_router(sample.router, tags=["Samples"], prefix="/samples", dependencies=[Depends(API_KEY_HEADER)])
    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, reload_delay=8)

