from dataclasses import dataclass
from os import path, environ
from typing import List

base_dir = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))


@dataclass
class Config:
    """
    default configuration
    """
    BASE_DIR: str = base_dir
    DB_POOL_RECYCLE: int = 900
    DB_ECHO: bool = False
    DEBUG: bool = False
    TEST_MODE: bool = False
    ALLOW_SITE = ["*"]
    DB_URL: str = environ.get("DB_URL", "mysql+pymysql://user:password@localhost/db?charset=utf8mb4")


@dataclass
class LocalConfig(Config):
    TRUSTED_HOSTS = ["*"]
    ALLOW_SITE = ["*"]
    DEBUG: bool = True
    


@dataclass
class ProdConfig(Config):
    TRUSTED_HOSTS = ["*"]
    ALLOW_SITE = ["*"]


@dataclass
class TestConfig(Config):
    DB_URL: str = "mysql+pymysql://user:password@localhost/db?charset=utf8mb4"
    TRUSTED_HOSTS = ["*"]
    ALLOW_SITE = ["*"]
    TEST_MODE: bool = True


def conf():
    """
    :return:
    """
    config = dict(prod=ProdConfig, local=LocalConfig, test=TestConfig)
    return config[environ.get("API_ENV", "local")]()
