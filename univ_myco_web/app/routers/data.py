from datetime import datetime

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from inspect import currentframe as frame
from models import *
from pathlib import Path
from common.consts import *
from common.forms import *
from common.jfunc import *
from models import *
import aiofiles
from typing import List
import os


# TODO:
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse, FileResponse
from starlette.requests import Request
from sqlalchemy import or_, and_
from common.consts import *
from common.forms import *
from database.conn import db
from database.schema import Users, Datafile, SampleGroup, AnalysisResult, Species, WhoResult
from models import *
from middlewares.token_validator import token_decode
from routers.analysis import convert_size

from starlette.responses import RedirectResponse


templates = Jinja2Templates(directory="templates")

# current path = /datafiles
router = APIRouter(prefix='')


@router.get("/", status_code=201,  response_class=HTMLResponse)
async def get_filelist(request: Request, pageno: int = 1, sortid: str = '-id', search_name: str = '', error_msg: str = '', Session: Session = Depends(db.session)):
    """
    `Data files list`\n
    :param request:
    :return:
    """
    print('/Get:datalist,Cookie:', request.cookies)
    lv = checkLogin(request.cookies)
    if lv['level'] <= 0:
        return RedirectMainpage()

    ser = Datafile.filename.like('%'+search_name+'%')
    usid = Datafile.user_id.__eq__(lv['userid'])

    form = DatafilelistForm(request)
    form.userid = EncToData(request.cookies['DsUsInfoKey'])
    if search_name == '':   # check file name
        form.totpage = Datafile.customfilter(session=Session, filter=[usid]).pagecount(16)
        form.totcount = Datafile.customfilter(session=Session, filter=[usid]).count()
        lt = Datafile.customfilter(session=Session, filter=[usid]).order_by(sortid).page(16, pageno).all()
    else:
        form.totpage = Datafile.customfilter(session=Session, filter=[ser,usid]).pagecount(16)
        form.totcount = Datafile.customfilter(session=Session, filter=[ser,usid]).count()
        lt = Datafile.customfilter(session=Session, filter=[ser,usid]).order_by(sortid).page(16, pageno).all()

    form.nowpage = pageno
    form.error_msg = error_msg
    form.files = []
    form.order_id = '?pageno={0}&sortid={1}&search_name={2}'.format(pageno, sortInvert(sortid, 'id'), search_name)
    form.order_name = '?pageno={0}&sortid={1}&search_name={2}'.format(pageno, sortInvert(sortid, 'filename'), search_name)
    form.order_size = '?pageno={0}&sortid={1}&search_name={2}'.format(pageno, sortInvert(sortid, 'filesize'), search_name)
    form.order_date = '?pageno={0}&sortid={1}&search_name={2}'.format(pageno, sortInvert(sortid, 'created_at'), search_name)
    form.search_name = '?pageno={0}&sortid={1}&search_name={2}'.format(pageno, sortid, search_name)
    form.page = makePageNo(pageno, 16, form.totpage)
    form.page['page_previous_link'] = '?pageno={0}&sortid={1}&search_name={2}'.format(form.page['page_previous'], sortid, search_name) if form.page['page_previous'] != '' else ''
    form.page['page_next_link'] = '?pageno={0}&sortid={1}&search_name={2}'.format(form.page['page_next'],     sortid, search_name) if form.page['page_next'] != '' else ''
    form.page['page_list_link'] = []
    for pgno in form.page['page_list']:  # page link
        form.page['page_list_link'].append('?pageno={0}&sortid={1}&search_name={2}'.format(pgno, sortid, search_name) if pgno != pageno else '')

    # get file list
    fidx = []
    for item in lt:
        fidx.append(item.id)
        s = item.created_at.strftime("%m/%d/%Y %H:%M")
        form.files.append({'id': item.id, 'filename': item.filename, 'filesize': convert_size(item.filesize), 'created_at': s})

    return templates.TemplateResponse("data_list.html", form.__dict__)

# file upload
@router.post("/upload", response_class=HTMLResponse)
async def create_upload_files(request: Request, files: List[UploadFile] = File(...), session: Session = Depends(db.session)):
    """
    `Sample data files upload`\n
    :param request:
    :param files:
    :return:
    """
    lv = checkLogin(request.cookies)
    if lv['level'] <= 0:
        return RedirectMainpage()
    
    for file in files:  # check extension
        fname = '__{0}__{1}'.format(lv['userid'],file.filename) 
        
        if os.path.isfile(DATA_PATH+fname):
            error_msg = 'Error : There is already a file with same name [{0}]'.format(file.filename)
            return RedirectResponse(url="/datafiles/?error_msg=" + error_msg, status_code=302)
        if file.filename[-9:].lower() != '.fastq.gz':
            error_msg = 'Error : Only ".fastq.gz" file format can be registered. [{0}]'.format(file.filename)
            return RedirectResponse(url="/datafiles/?error_msg=" + error_msg, status_code=302)

    for file in files:
        fname = '__{0}__{1}'.format(lv['userid'],file.filename) 
        
        await file.seek(0)
        contents = await file.read()
        fz = len(contents)
        async with aiofiles.open(os.path.join(DATA_DIR, fname), "wb") as fp:
            await fp.write(contents)

        # check datafile 
        df = Datafile.filter(session=session, filename=file.filename, user_id=lv['userid'])
        if df and df.first():
            df.update(auto_commit=True, **{'filename': file.filename, 'filesize': fz, 'user_id':lv['userid']})
        else:
            Datafile.create(session=session, auto_commit=True, filename=file.filename, filesize=fz, user_id=lv['userid'])  # write db

        print('file upload:',file.filename, fz)

    return RedirectResponse(url="/datafiles", status_code=302)


# db file upload
@router.post("/dbsource")
async def create_dbsource_files(request: Request, files: List[UploadFile] = File(...), session: Session = Depends(db.session)):
    """
    `DB data files upload`\n
    :param request:
    :param files:
    :return:
    """
    lv = checkLogin(request.cookies)
    if lv['level'] <= 0:
        return RedirectMainpage()
    
    if len(files) != 1: 
        error_msg = 'No file selected.'
        return RedirectResponse(url="/samples/config?error_msg=" + error_msg, status_code=302)
    fn = files[0]
    dbname = os.path.splitext(fn.filename)[0]
    
    print('fdbsource upload:',fn.filename)
    
        
    if os.path.splitext(fn.filename)[1].lower() != '.xlsx':
        error_msg = 'Only ".xlsx" file format can be registered. [{0}]'.format(fn.filename)
        return RedirectResponse(url="/samples/config?error_msg=" + error_msg, status_code=302)

    sql = []
    sql.append((or_(WhoResult.user_id==0, WhoResult.user_id==lv['userid'])))
    dbs = WhoResult.colunm_customfilter(session=session,cols=WhoResult.db_name, filter=sql).group_by2('db_name').all()
    for dn in dbs:
        if dn[0].strip() == dbname:
            error_msg = 'The file name already exists. [{0}]'.format(fn.filename)
            return RedirectResponse(url="/samples/config?error_msg=" + error_msg, status_code=302)
    

    # delete old data
    if os.path.isfile(TEMP_PATH+'who_db.xlsx'):
        os.remove(TEMP_PATH+'who_db.xlsx')

    contents = await fn.read()
    fz = len(contents)
    with open(os.path.join(TEMP_DIR, 'who_db.xlsx'), "wb") as fp:
        fp.write(contents)

    if addDbFileLoad(TEMP_PATH+'who_db.xlsx', dbname, lv['userid'], session=session):
        accept_msg = 'Updates complete.'
        return RedirectResponse(url="/samples/config?accept_msg=" + accept_msg, status_code=302)
    else:
        error_msg = 'DB File format error!'
        return RedirectResponse(url="/samples/config?error_msg=" + error_msg, status_code=302)



# delete db file
@router.post("/dbdelete")
async def post_db_delete(request: Request, dbname: str = Form(...), session: Session = Depends(db.session)):
    """
    `DB data files upload`\n
    :param request:
    :param files:
    :return:
    """
    lv = checkLogin(request.cookies)
    if lv['level'] <= 0:
        return RedirectMainpage()
    
    print('dbdelete:', dbname)

    lt = WhoResult.filter(session=session,db_name=dbname,user_id=lv['userid']).first()
    if lt:
        # config file delete
        WhoResult.filter(session=session,db_name=dbname,user_id=lv['userid']).delete(auto_commit=True)
        return RedirectResponse(url="/samples/config", status_code=302)
    else:
        error_msg = 'This is not a delete user db. : ' + dbname
        return RedirectResponse(url="/samples/config?error_msg=" + error_msg, status_code=302)


# remove file
@router.post("/deletefile", response_class=HTMLResponse)
async def post_datafile(request: Request, datafile: Form_SampleId = Depends(Form_SampleId), Session: Session = Depends(db.session), pageno: int = 1, sortid: str = '-id', search_name: str = ''):
    """
    `Data delete`\n
    :param request:
    :return:
    """
    print('/Post:delfile,Cookie:', request.cookies, datafile.sampleid)
    lv = checkLogin(request.cookies)
    if lv['level'] <= 0:
        return RedirectMainpage()

    # sample data delete
    for fid in datafile.sampleid:
        sf = Datafile.filter(session=Session, id=int(fid),user_id=lv['userid'])
        if sf and sf.first().id == int(fid):
            # make output directory
            s = sf.first().filename
            sf.delete(auto_commit=True)
            if os.path.isfile(DATA_PATH + s):    
                os.remove(DATA_PATH + s)

    return RedirectResponse(url="/datafiles?pageno={0}&sortid={1}&search_name={2}".format(pageno, sortid, search_name), status_code=302)


@router.head("/ref/{filename}")
@router.get("/ref/{filename}")
async def download_file(request: Request, filename: str):
    """
    `Report PDF file Download`\n
    :param request:
    :param sampleid:
    :return:
    """
    lv = checkLogin(request.cookies)
    if lv['level'] <= 0:
        return RedirectMainpage()

    if filename in ["NC_000962.3.fasta", "NC_000962.3.fasta.fai", "cytoBand.txt", "MTB_H37Rv_Gene_Anno_NC_000962.3.bed"]:
        file_path = REF_PATH+str(filename)
    else:
        file_path = DATA_PATH+str(filename)
    if os.path.isfile(file_path):
        return FileResponse(path=file_path, filename=filename)
    else:
        return JSONResponse(status_code=201, content=dict(msg="File not found"))


@router.get("/pdf/{sampleid}", response_class=HTMLResponse)
async def get_pdfreport(request: Request, sampleid: int):
    """
    `Report PDF file Download`\n
    :param request:
    :param sampleid:
    :return:
    """

    print('/Get:PDF Cookie:', request.cookies)
    lv = checkLogin(request.cookies)
    if lv['level'] <= 0:
        return RedirectMainpage()

    ser = SampleGroup.user_id.__eq__(lv['userid'])
    cnt = SampleGroup.customfilter(session=Session,filter=ser).pagecount()
        
    file_path = "/homepath/univ_myco_web/pdf/{0}.pdf".format(sampleid)
    fex = os.path.isfile(file_path)
    
    if(fex==False) or (cnt==0):
        return JSONResponse(status_code=201, content=dict(msg="File not found"))
    else:
        return FileResponse(path=file_path, filename=file_path)

