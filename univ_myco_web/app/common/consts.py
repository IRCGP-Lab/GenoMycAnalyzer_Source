JWT_SECRET = "JWT_KEY"
JWT_ALGORITHM = "HS256"
EXCEPT_PATH_LIST = ["/", "/openapi.json"]
EXCEPT_PATH_REGEX = "^(/docs|/redoc|/api/login|/api/analysis/afiles|/static/images|/samples/addsample__)"
MAX_API_KEY = 3
MAX_API_WHITELIST = 10
MAX_PAGE_ROW_COUNT = 15
MAX_PAGE_NUMBER_COUNT = 10

DATA_DIR = "/homepath/univ_myco/Data"
DATA_PATH = DATA_DIR+"/"
REF_DIR = "/homepath/univ_myco/Reference"
REF_PATH = REF_DIR+"/"
TOOLS_DIR ="/homepath/tools"
TOOLS_PATH = TOOLS_DIR+"/"
TEMP_DIR = DATA_DIR+"/Temp"
TEMP_PATH = TEMP_DIR+"/"

from fastapi.security import APIKeyHeader
API_KEY_HEADER = APIKeyHeader(name="Authorization", auto_error=False)

SMTP_SERVER_ADDR = 'smtp.gmail.com'
SMTP_SERVER_FROM = 'email@gmail.com'
SMTP_SERVER_PW = 'password'
SMTP_SERVER_PORT = 1234
