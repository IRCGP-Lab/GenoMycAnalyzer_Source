from datetime import datetime, timedelta

import bcrypt
import jwt
import hashlib
from common.jfunc import *
from fastapi import APIRouter, Depends, Form
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.param_functions import Cookie
from fastapi.params import Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from sqlalchemy.orm import Session
from starlette.responses import JSONResponse, PlainTextResponse, RedirectResponse, Response
from starlette.requests import Request
from database.conn import db
from database.schema import Users
from models import *
from common.forms import *
from routers.auth import is_id_exist, create_access_token

from typing import Optional

from common.consts import EXCEPT_PATH_LIST, EXCEPT_PATH_REGEX, DATA_DIR, TEMP_DIR, API_KEY_HEADER

templates = Jinja2Templates(directory="templates")
# current path = /user
router = APIRouter(prefix="")


@router.get("/", response_class=HTMLResponse)
async def get_users(request: Request):
    """
    `Sample files list 조회`\n
    :param request:
    :return:
    """
    print('/Get:datalist,Cookie:', request.cookies)

    return "A"


@router.get("/activate", response_class=HTMLResponse)
async def get_repassword(request: Request, key: str = '', Session: Session = Depends(db.session)):
    """
    `Activate`\n
    :param request:
    :return:
    """
    print('get repassword,Cookie:', request.cookies)

    if key:
        em, otm = KeyToRepasswordEmail(key)
        if (em) and (otm != datetime.strptime('20000101000000', '%Y%m%d%H%M%S')):
            odif = datetime.now()-otm
            if ((odif.days == 0) and (odif.seconds >= 0) and (odif.seconds <= 6000000)):
                ser = Users.filter(session=Session,  email=em)
                if ser and ser.first():
                    ser.update(auto_commit=True, **{'status': 'active'})  # status active
                    return templates.TemplateResponse("user_login.html", {'request': request})

    return RedirectResponse(url="/", status_code=301)


@router.get("/login", response_class=HTMLResponse)
async def get_login(request: Request):
    """
    `User Login`\n
    :param request:
    :return:
    """
    print('/get login,Cookie:', request.cookies)
    return templates.TemplateResponse("user_login.html", {'request': request})


@router.post("/login", response_class=HTMLResponse)
async def post_loginpost(request: Request, login: Form_Login = Depends(Form_Login), Session: Session = Depends(db.session)):
    """
    `User Login`\n
    :param request:
    :return:
    """
    print('/post login,Cookie:', request.cookies, login)

    upw = md5make(login.EmailPW)

    # User ID(email) 
    ser = Users.filter(session=Session,  email=login.Email, pw=upw, status='active')
    if ser and ser.first():
        response = RedirectResponse(url="/", status_code=301)
        response.set_cookie("DsUsInfoKey", DataToEnc(login.Email))
        response.set_cookie("DsTmInfoKey", DataToEnc(datetime.now().strftime('%Y%m%d%H%M%S')))    # login time
        return response
    else:
        form = LoginForm(request)
        form.useremail = login.Email
        form.ErrorMsg = 'Invalid login email or password.'
        return templates.TemplateResponse("user_login.html", form.__dict__)



@router.get("/logout", response_class=HTMLResponse)
async def get_logout(request: Request):
    """
    `User Logout`\n
    :param request:
    :return:
    """
    print('/post login,Cookie:', request.cookies)
    return RedirectMainpage()


@router.get("/repassword", response_class=HTMLResponse)
async def get_repassword(request: Request, Repwkey: str = '', Session: Session = Depends(db.session)):
    """
    `Repassword Login`\n
    :param request:
    :return:
    """
    print('get repassword,Cookie:', request.cookies)

    if Repwkey:
        em, otm = KeyToRepasswordEmail(Repwkey)
        if (em) and (otm != datetime.strptime('20000101000000', '%Y%m%d%H%M%S')):
            odif = datetime.now()-otm
            if ((odif.days == 0) and (odif.seconds >= 0) and (odif.seconds <= 6000000)):
                form = RepasswordForm(request)
                form.Repwkey = Repwkey
                return templates.TemplateResponse("user_repassword.html", form.__dict__)
            else:
                return RedirectResponse(url="/", status_code=301)
        else:
            return RedirectResponse(url="/", status_code=301)
    else:
        id = EncToData(request.cookies.get('DsUsInfoKey'))

        if (id == ''):
            response = RedirectResponse(url="/", status_code=301)
            response.set_cookie("DsUsInfoKey", None)
            response.set_cookie("DsTmInfoKey", None)
            return response
        else:
            form = RepasswordForm(request)
            form.Repwkey = RepasswordEmailToKey(id)
            form.userid = id
            return templates.TemplateResponse("user_repassword.html", form.__dict__)


@router.post("/repassword", response_class=HTMLResponse)
async def post_repassword(request: Request, pwinfo: Form_Login = Depends(Form_Repassword), Session: Session = Depends(db.session)):
    """
    `Repassword Login`\n
    :param request:
    :return:
    """
    print('post repassword,Cookie:', request.cookies, pwinfo)

    if pwinfo.Repwkey != '#':
        em, otm = KeyToRepasswordEmail(pwinfo.Repwkey)
        if (em) and (otm != datetime.strptime('20000101000000', '%Y%m%d%H%M%S')):
            odif = datetime.now()-otm
            if ((odif.days == 0) and (odif.seconds >= 0) and (odif.seconds <= 60000)):  # check timeout
                if (pwinfo.EmailPW != pwinfo.confirm_EmailPW) or (verifyPw(pwinfo.EmailPW) == False):
                    form = RepasswordForm(request)
                    form.Repwkey = pwinfo.Repwkey
                    form.ErrorMsg = 'Invalid your password.'
                    return templates.TemplateResponse("user_repassword.html", form.__dict__)
                else:
                    ser = Users.filter(session=Session,  email=em)
                    if ser and ser.first():
                        pw = md5make(pwinfo.EmailPW)
                        ser.update(auto_commit=True, **{'pw': pw})  # repassword

                    response = RedirectResponse(url="/", status_code=301)
                    response.set_cookie("DsUsInfoKey", None)
                    response.set_cookie("DsTmInfoKey", None)
                    return response

    return RedirectResponse(url="/", status_code=301)


@router.get("/resendpassword", response_class=HTMLResponse)
async def get_resendpassword(request: Request):
    """
    `Resendpassword Login`\n
    :param request:
    :return:
    """
    print('get resendpassword,Cookie:', request.cookies)
    return templates.TemplateResponse("user_resendpassword.html", {'request': request})


@router.post("/resendpassword", response_class=HTMLResponse)
async def post_resendpassword(request: Request, Email: str = Form(...)):
    """
    `Resendpassword`\n
    :param request:
    :return:
    """
    print('post resendpassword,Cookie:', request.cookies)

    if verifyEmail(Email):
        ser = Users.filter(email=Email)
        if ser:
            if ser.first():
                sendRepaswordEmail(Email)

            response = RedirectResponse(url="/", status_code=301)   # Logout
            response.set_cookie("DsUsInfoKey", None)
            response.set_cookie("DsTmInfoKey", None)
            return response
        else:
            form = LoginForm(request)
            form.ErrorMsg = 'Invalid email address.'
            return templates.TemplateResponse("user_resendpassword.html", form.__dict__)
    else:
        form = LoginForm(request)
        form.ErrorMsg = 'Invalid email address.'
        return templates.TemplateResponse("user_resendpassword.html", form.__dict__)


@router.get("/register")
async def get_register(request: Request):
    """
    `User register`\n
    :param request:
    :return:
    """
    print('/register,Cookie:', request.cookies)

    return templates.TemplateResponse("user_register.html", {'request': request})


@router.post("/register", response_class=HTMLResponse)
async def post_register(request: Request, reginfo: Form_Register = Depends(Form_Register), Session: Session = Depends(db.session)):
    """
    `User register`\n
    :param request:
    :return:
    """
    print('post register,Cookie:', request.cookies)

    form = RegisterForm(request)
    form.useremail = reginfo.Email 

    if verifyEmail(reginfo.Email):
        if verifyPw(reginfo.EmailPW):
            if (reginfo.EmailPW == reginfo.confirm_EmailPW):
                ser = Users.filter(email=reginfo.Email)
                if ser:
                    if ser.first():
                        form.ErrorMsg = "An account already exists with the same email address"
                    else:
                        add = {}
                        add['status'] = 'blocked'
                        add['userid'] = ''
                        add['pw'] = md5make(reginfo.EmailPW)
                        add['email'] = reginfo.Email
                        add['level'] = 'user'
                        Users.create(session=Session, auto_commit=True, **add)

                        sendActivateEmail(reginfo.Email)
                        form.ErrorMsg = 'Please click the activation link we sent to your email'
                else:
                    form.ErrorMsg = 'Please click the activation link we sent to your email'
            else:
                form.ErrorMsg = 'Invalid your confirm password.'
        else:
            form.ErrorMsg = 'Invalid your password.'
    else:
        form.ErrorMsg = 'Invalid your email address.'
    
    return templates.TemplateResponse("user_register.html", form.__dict__)


@router.get("/policy")
async def policy(request: Request):
    """
    `User policy`\n
    :param request:
    :return:
    """
    print('/register,Cookie:', request.cookies)
    return templates.TemplateResponse("user_policy_service.html", {'request': request})


class RequiresLoginException(Exception):
    pass
