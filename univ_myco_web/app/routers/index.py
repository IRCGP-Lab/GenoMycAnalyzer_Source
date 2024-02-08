import os
import aiofiles

from datetime import datetime
from fastapi import APIRouter, Request, Depends, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from inspect import currentframe as frame
from models import *
from pathlib import Path
from models import *
from typing import List
from common.consts import *
from common.jfunc import *

# TODO:
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from starlette.requests import Request
from sqlalchemy import or_, and_, func, desc
from common.consts import *
from common.forms import *
from database.conn import db
from database.schema import Users, SampleLog, AnalysisResult
from models import *
from middlewares.token_validator import token_decode



templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix='')

# current path = /
@router.get("/")
async def root(request: Request, session: Session = Depends(db.session)):
    print('/main,Cookie:',request.cookies)
    
    form = MainForm(request)
    
    lv = checkLogin(request.cookies)
    if lv['level'] > 0:
        form.userid = EncToData(request.cookies['DsUsInfoKey'])    # user email
        
    return templates.TemplateResponse("index2.html", form.__dict__)

                
@router.get("/help", response_class=HTMLResponse)
async def help(request: Request):    
    print('get help,Cookie:',request.cookies)
    return templates.TemplateResponse("help4.html", {"request":request,'userid':EncToData(request.cookies['DsUsInfoKey'])})
    

def checkYear(ye):
    try:
        y = int(ye or 0)
        if (y >= 2000) and (y<=3000):
            return datetime(y,1,1,0,0,0), datetime(y,12,31,23,59,59)
        else:
            return datetime(datetime.today().year,1,1,0,0,0), datetime(datetime.today().year,12,31,23,59,59)
    except Exception as e:
        return datetime(datetime.today().year,1,1,0,0,0), datetime(datetime.today().year,12,31,23,59,59)

def dectoK(dec):
    if dec >= 1000:
        return str(round(dec/1000,3)) + 'K'
    else:
        return str(dec)

@router.get("/chart", response_class=HTMLResponse)
async def chart(request: Request, Year:str='', session: Session = Depends(db.session)):  
    print('get chart,Cookie:',request.cookies)
    
    lv = checkLogin(request.cookies)
    if lv['level'] <= 0:
        return RedirectMainpage()


    st,ed = checkYear(Year)

    # Monthly analysis number list
    ml = [0,0,0,0,0,0,0,0,0,0,0,0]
        
    sql = []
    sql.append(and_(SampleLog.created_at>=st,SampleLog.created_at<=ed))
    qry = session.query(func.month(SampleLog.created_at), func.count(func.month(SampleLog.created_at)))\
        .filter(and_(SampleLog.created_at>=st,SampleLog.created_at<=ed))\
        .group_by(func.month(SampleLog.created_at)).all()
    for item in qry:
        ml[item[0]-1] = item[1]
    
    
    # year list
    qry = session.query(func.year(SampleLog.created_at))\
        .group_by(func.year(SampleLog.created_at))\
        .order_by(func.year(SampleLog.created_at))\
        .all()
    ye = []
    for item in qry:
        ye.append(item[0])
    
    # Number of analyses this year
    qry = session.query(func.count(SampleLog.created_at)).filter(and_(SampleLog.created_at>=st,SampleLog.created_at<=ed)).all()
    num = format(qry[0][0],',')
    
    form = AnalysisUserChartForm(request)
    form.Totusers = Users.filter(session=session).count()
    form.TotProcessing = num
    form.Years = ye
    form.YSelect = st.year
    form.Months = ml
    
    return templates.TemplateResponse("used_chart.html", form.__dict__)