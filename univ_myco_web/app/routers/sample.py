import openpyxl
import subprocess
from datetime import datetime

from fastapi import APIRouter, Depends, File, UploadFile, Form, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import json
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
import datetime


# TODO:
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse, FileResponse
from starlette.requests import Request
from sqlalchemy import or_, and_
from common.consts import *
from common.forms import *
from database.conn import db
from database.schema import *
from models import *
from middlewares.token_validator import token_decode
from routers.analysis import convert_size

from starlette.responses import RedirectResponse


templates = Jinja2Templates(directory="templates")

# current path = /samples
router = APIRouter(prefix='')


@router.get("/", status_code=201, response_class=HTMLResponse)
async def get_samplelist(request: Request, pageno: int = 1, sortid: str = '-id', search_name: str = '', error_msg: str = '', Session: Session = Depends(db.session)):
    """
    `Sample files list `\n
    :param request:
    :return:
    """
    print('/Get:datalist,Cookie:', request.cookies)

    lv = checkLogin(request.cookies)
    if lv['level'] <= 0:
        return RedirectMainpage()

    usid = Datafile.user_id.__eq__(lv['userid'])
        
    flist = []
    alllist = {}
    ser = Datafile.customfilter(session=Session,filter=[usid]).order_by('filename').all()
    for m in ser:
        alllist[str(m.id)] = m.filename
        flist.append(m.filename)


    ser = SampleGroup.Sample_DataID.like('%'+search_name+'%')
    usid = SampleGroup.user_id.__eq__(lv['userid'])

    form = SamplelistForm(request)
    form.userid = EncToData(request.cookies['DsUsInfoKey'])

    if search_name == '':   # check sample name
        form.totpage = SampleGroup.customfilter(session=Session, filter=[usid]).pagecount()
        form.totcount = SampleGroup.customfilter(session=Session, filter=[usid]).count()
        lt = SampleGroup.customfilter(session=Session, filter=[usid]).order_by(sortid).page(MAX_PAGE_ROW_COUNT, pageno).all()
    else:
        form.totpage = SampleGroup.customfilter(session=Session, filter=[ser,usid]).pagecount()
        form.totcount = SampleGroup.customfilter(session=Session, filter=[ser,usid]).count()
        lt = SampleGroup.customfilter(session=Session, filter=[ser,usid]).order_by(sortid).page(MAX_PAGE_ROW_COUNT, pageno).all()

    form.nowpage = pageno
    form.error_msg = error_msg
    form.order_id = '?pageno={0}&sortid={1}&search_name={2}'.format(pageno, sortInvert(sortid, 'id'), search_name)
    form.order_sampleid = '?pageno={0}&sortid={1}&search_name={2}'.format(pageno, sortInvert(sortid, 'Sample_DataID'), search_name)
    form.order_date = '?pageno={0}&sortid={1}&search_name={2}'.format(pageno, sortInvert(sortid, 'created_at'), search_name)
    form.order_status = '?pageno={0}&sortid={1}&search_name={2}'.format(pageno, sortInvert(sortid, 'Analysis_StepNo'), search_name)
    form.search_link = '?pageno={0}&sortid={1}&search_name={2}'.format(pageno, sortid, search_name)
    form.search_name = search_name
    form.page = makePageNo(pageno, MAX_PAGE_NUMBER_COUNT, form.totpage)
    form.page['page_previous_link'] = '?pageno={0}&sortid={1}&search_name={2}'.format(form.page['page_previous'], sortid, search_name) if form.page['page_previous'] != '' else ''
    form.page['page_next_link'] = '?pageno={0}&sortid={1}&search_name={2}'.format(form.page['page_next'],     sortid, search_name) if form.page['page_next'] != '' else ''
    form.page['page_list_link'] = []
    form.filelist = flist
    for pgno in form.page['page_list']:  # page link
        form.page['page_list_link'].append('?pageno={0}&sortid={1}&search_name={2}'.format(pgno, sortid, search_name) if pgno != pageno else '')

    # get list
    fidx = []
    for item in lt:

        # find file name
        if str(item.Analysis_R1_Data_Id) in alllist.keys():
            r1 = alllist[str(item.Analysis_R1_Data_Id)]
        else:
            r1 = ''
        if str(item.Analysis_R2_Data_Id) in alllist.keys():
            r2 = alllist[str(item.Analysis_R2_Data_Id)]
        else:
            r2 = ''

        fidx.append(item.id)
        try:
            s = item.created_at.strftime("%m/%d/%Y %H:%M")
        except Exception as e:
            # Null check 
            s = '01/01/2000 00:00'

        if item.Analysis_SpeciesPredName.lower() == 'mycobacterium tuberculosis':
            if(item.Analysis_QcTotReadFastQ > 0)and (item.Analysis_QcQ30ReadFastQ > 0) and (item.Analysis_QcMapReadSpecies > 0) and (item.Analysis_QcMapRateSpecies > 0)and (item.Analysis_QcCoverageDeep > 0):
                qc = 'Pass'
            else:
                qc = 'Failed'
            
            lnag = item.Report_Lineage
            sptp = item.Report_Spligotype
        else:
            if(item.Analysis_QcTotReadFastQ > 0)and (item.Analysis_QcQ30ReadFastQ > 0) and (item.Analysis_QcMapReadSpecies > 0) and (item.Analysis_QcMapRateSpecies > 0):
                qc = 'Pass'
            elif(item.Analysis_StepNo != 99):
                qc = 'Not started'
            else:
                qc = 'Failed'            
            lnag = 'N/A'
            sptp = 'N/A'
            
        form.samples.append({'id': item.id,
                             'sample_id': item.Sample_DataID,
                             'r1_name': r1,
                             'r2_name': r2,
                             'quality': qc,
                             'species': item.Report_Species,
                             'lineage': lnag,
                             'spoligotype': sptp,
                             'created_at': s,
                             'step_no': item.Analysis_StepNo,
                             'step_no_name': stepnoToStr(item.Analysis_StepNo),
                             'PatientID': item.Sample_PatientID,
                             'PatientName': item.Sample_PatientName,
                             'SampleRecvDate': item.Sample_RecvDate.strftime('%m/%d/%Y'),
                             'SeqDate': item.Sample_SeqDate.strftime('%m/%d/%Y'),
                             'LabPrepDate': item.Sample_LibPrepDate.strftime('%m/%d/%Y'),
                             'LabTechnician': item.Sample_LabTechnician,
                             'Contact': item.Sample_Contact
                             })

    return templates.TemplateResponse("sample_list.html", form.__dict__)



# file upload
@router.post("/upload")
async def create_batchfile_upload(request: Request, files: List[UploadFile] = File(...), Session: Session = Depends(db.session)):
    """
    `Sample batch files upload`\n
    :param request:
    :param files:
    :return:
    """
    lv = checkLogin(request.cookies)
    if lv['level'] <= 0:
        return RedirectMainpage()

    for file in files:  # Check extension
        if os.path.splitext(file.filename)[1] != '.xlsx':
            error_msg = 'Error : Only ".xlsx" file format can be registered. [{0}]'.format(file.filename)
            return RedirectResponse(url="/samples?error_msg=" + error_msg, status_code=302)

    for file in files:
        contents = await file.read()

        if os.path.isfile(TEMP_PATH+'batch.xlsx'):
            os.remove(TEMP_PATH+'batch.xlsx')    # delete old data
        with open(TEMP_PATH+'batch.xlsx', "wb") as fp:
            fp.write(contents)

        samplelt = excelDataLoad(TEMP_PATH+'batch.xlsx')
        if len(samplelt) == 0:
            error_msg = 'Error : This is not a valid format.'
            return RedirectResponse(url="/samples?error_msg=" + error_msg, status_code=302)
        else:
            for sample in samplelt:
                # find file id
                df = Datafile.filter(session=Session, filename=sample['Analysis_R1_Data_Id'].strip(), user_id=lv['userid']).first()
                if df:
                    sample['Analysis_R1_Data_Id'] = df.id
                else:
                    sample['Analysis_R1_Data_Id'] = 0

                df = Datafile.filter(session=Session, filename=sample['Analysis_R2_Data_Id'].strip(), user_id=lv['userid']).first()
                if df:
                    sample['Analysis_R2_Data_Id'] = df.id
                else:
                    sample['Analysis_R2_Data_Id'] = 0
                sample['user_id'] = lv['userid']
                
                SampleGroup.create(session=Session, auto_commit=True, **sample)  # write db

    return RedirectResponse(url="/samples", status_code=302)


@router.post("/addsample", response_class=HTMLResponse)
async def add_sample(request: Request, sample: Form_SampleAddSet = Depends(Form_SampleAddSet), pageno: int = 1, sortid: str = '-id', search_name: str = '', error_msg: str = '', Session: Session = Depends(db.session)):
    """
    `Sample data add`\n
    :param request:
    :return:
    """

    content_type = request.headers.get('Content-Type')
    print('/addsample:post:Cookie:', request.cookies)

    lv = checkLogin(request.cookies)
    if lv['level'] <= 0:
        return RedirectMainpage()

    # find R1 fild id 
    ser = Datafile.filter(session=Session,  filename=sample.Analysis_R1name, user_id=lv['userid'])
    if ser and ser.first():
        r1 = ser.first().id
    else:
        r1 = 0

    # find R2 file id
    ser = Datafile.filter(session=Session,  filename=sample.Analysis_R2name, user_id=lv['userid'])
    if ser and ser.first():
        r2 = ser.first().id
    else:
        r2 = 0

    if (sample.AnalysisID.strip() == ''):    # id check 
        add = {}
        add['Sample_DataID'] = sample.SampleDataID
        add['Sample_PatientID'] = sample.PatientID
        add['Sample_PatientName'] = sample.PatientName
        add['Sample_RecvDate'] = strToDate(sample.RecvDate)
        add['Sample_LibPrepDate'] = strToDate(sample.LibPrepDate)
        add['Sample_SeqDate'] = strToDate(sample.SeqDate)
        add['Sample_LabTechnician'] = ''
        add['Sample_Source'] = ''
        add['Sample_CultureType'] = ''
        add['Sample_ReportDate'] = datetime.strptime('20000101', '%Y%m%d')
        add['Sample_Contact'] = ''
        add['Analysis_Step1Time'] = datetime.strptime('20000101', '%Y%m%d')
        add['Analysis_Step2Time'] = datetime.strptime('20000101', '%Y%m%d')
        add['Analysis_Step3Time'] = datetime.strptime('20000101', '%Y%m%d')
        add['Analysis_Step4Time'] = datetime.strptime('20000101', '%Y%m%d')
        add['Analysis_Step5Time'] = datetime.strptime('20000101', '%Y%m%d')
        add['Analysis_R1_Data_Id'] = r1
        add['Analysis_R2_Data_Id'] = r2
        add['user_id'] = lv['userid']
        add['Report_Sequencer'] = 'Illumina MiSeqDx'
        add['Report_Method'] = 'whole genome sequencing'
        add['Report_Pipeline'] = 'MycoAnalyzer version 1.0.0'
        SampleGroup.create(session=Session, auto_commit=True, **add)
    else:
        sp = SampleGroup.filter(session=Session, id=int(sample.AnalysisID))
        if sp and sp.first():
            sp.update(auto_commit=True, **{
                'Sample_DataID': sample.SampleDataID,
                'Sample_PatientID': sample.PatientID,
                'Sample_PatientName': sample.PatientName,
                'Sample_RecvDate': strToDate(sample.RecvDate),
                'Sample_LibPrepDate': strToDate(sample.LibPrepDate),
                'Sample_SeqDate': strToDate(sample.SeqDate),
                'Analysis_R1_Data_Id': r1,
                'Analysis_R2_Data_Id': r2,
                'user_id': lv['userid']
            })

    return RedirectResponse(url="/samples?pageno={0}&sortid={1}&search_name={2}".format(pageno, sortid, search_name), status_code=302)

# Sample edit
@router.post("/editsample", response_class=HTMLResponse)
async def edit_sample(request: Request, sample: Form_SampleEditSet = Depends(Form_SampleEditSet), Session: Session = Depends(db.session)):
    """
    `Sample data edit`\n
    :param request:
    :return:/
    """

    content_type = request.headers.get('Content-Type')
    print('/editsample:post:Cookie:', request.cookies)

    lv = checkLogin(request.cookies)
    if lv['level'] <= 0:
        return RedirectMainpage()

    # find R1 file id
    ser = Datafile.filter(session=Session, user_id=lv['userid'],  filename=sample.Analysis_R1name)
    if ser and ser.first():
        r1 = ser.first().id
    else:
        r1 = 0

    # find R2 file id
    ser = Datafile.filter(session=Session, user_id=lv['userid'],  filename=sample.Analysis_R2name)
    if ser and ser.first():
        r2 = ser.first().id
    else:
        r2 = 0

    if (sample.AnalysisID.strip() != ''):    # check id
        sp = SampleGroup.filter(session=Session, id=int(sample.AnalysisID), user_id=lv['userid'])
        if sp and sp.first():
            sp.update(auto_commit=True, **{
                'Sample_DataID': sample.SampleDataID,
                'Sample_PatientID': sample.PatientID,
                'Sample_PatientName': sample.PatientName,
                'Sample_RecvDate': strToDate(sample.RecvDate),
                'Sample_LibPrepDate': strToDate(sample.LibPrepDate),
                'Sample_SeqDate': strToDate(sample.SeqDate),
                'Sample_ReportDate': strToDate(sample.ReportDate),
                'Sample_Source': sample.SampleSource,
                'Sample_CultureType': sample.CultureType,
                'Report_Sequencer' : sample.Sequencer,
                'Report_Method' : sample.Method,
                'Report_Pipeline' : sample.Pipeline,
                'Report_DoctorName': sample.DrName,
                'Report_ReportLab': sample.ReportLab,
                'Report_LabAddress': sample.Address,
                'Analysis_R1_Data_Id': r1,
                'Analysis_R2_Data_Id': r2,
                'user_id': lv['userid']
            })

    return RedirectResponse(url="/samples/summary/{0}".format(sample.AnalysisID), status_code=302)


# Sample delete
@router.post("/deltesample", response_class=HTMLResponse)
async def delete_sample(request: Request, sample: Form_SampleId = Depends(Form_SampleId), Session: Session = Depends(db.session), pageno: int = 1, sortid: str = '-id', search_name: str = ''):
    """
    `Sample delete`\n
    :param request:
    :return:
    """
    print('/Post:datalist,Cookie:', request.cookies, sample.sampleid)
    lv = checkLogin(request.cookies)
    if lv['level'] <= 0:
        return RedirectMainpage()

    # sample data delete
    for siid in sample.sampleid:
        SampleGroup.filter(session=Session, id=siid, user_id=lv['userid']).delete(auto_commit=True)
        AnalysisResult.filter(session=Session, Sample_Id=siid, user_id=lv['userid']).delete(auto_commit=True)
        Species.filter(session=Session, Sample_Id=siid, user_id=lv['userid']).delete(auto_commit=True)

    return RedirectResponse(url="/samples?pageno={0}&sortid={1}&search_name={2}".format(pageno, sortid, search_name), status_code=302)


# Sample edit
@router.post("/editcomment", response_class=HTMLResponse)
async def edit_sample(request: Request, AnalysisID:str=Form(...), AddtionalComment :str=Form(...),  Session: Session = Depends(db.session)):
    """
    `Sample data edit`\n
    :param request:
    :return:
    """

    print('/editcomment:post,Cookie:', request.cookies, AnalysisID)

    lv = checkLogin(request.cookies)
    if lv['level'] <= 0:
        return RedirectMainpage()
    
    if (AnalysisID.strip() != ''):    # check id
        sp = SampleGroup.filter(session=Session, id=int(AnalysisID), user_id=lv['userid'])
        if sp and sp.first():
            #s = .replace("\r\n","<br>")
            sp.update(auto_commit=True, **{
                'Report_AdditionalComment': AddtionalComment
            })
    
    return RedirectResponse(url="/samples/report/{0}".format(AnalysisID), status_code=302)


@router.get("/config", response_class=HTMLResponse)
async def get_config(request: Request, accept_msg:str = '', error_msg: str = '', Session: Session = Depends(db.session)):
    """
    `Sample circos image`\n
    :param request:
    :param sampleidx:
    :return:
    """
    print('/Get:circos, Cookie:', request.cookies)
    lv = checkLogin(request.cookies)
    if lv['level'] <= 0:
        return RedirectMainpage()

    form = {'ReadMapping_IntralControlOP': 'True',
            'refDB':'WHO_DB_20220821',
            'Kraken2_minbaseQulity': '1',
            'Kraken2_minhitGroups': '3',
            'Braken_OptionR': '100',
            'Braken_OptionL': 'S',
            'BcfToolsQualitySymbol': '<=',
            'BcfToolsQualityValue': '100',
            'BcfToolsDpSymbol': '<',
            'BcfToolsDpValue': '50',
            'SnpEff_ud': '1000',
            'VAF_dp':'3'    # VAF Value : 3 = 3% = 0.03
            }
    form['request'] = request
    form['userid'] = EncToData(request.cookies['DsUsInfoKey'])
    form['error_msg'] = error_msg
    form['accept_msg'] = accept_msg

    sql = []
    sql.append((or_(WhoResult.user_id==0, WhoResult.user_id==lv['userid'])))
    dbname = WhoResult.colunm_customfilter(session=Session,cols=WhoResult.db_name, filter=sql).group_by2('db_name').all()
    ds = []
    for dn in dbname:
        ds.append(dn[0].strip())
    form['ReferenceDB'] = ds
    
    df = AnalysisConfig.filter(user_id=lv['userid'])
    if df and df.count() > 0: 
        for cfg in df.all():
            if (cfg.param != 'request') and (cfg.param) != 'userid':
                form[cfg.param] = cfg.val

    return templates.TemplateResponse("sample_config.html", form)

@router.post("/config", response_class=HTMLResponse)
async def post_config(request: Request, ckReadmap: bool = Form(False), cfg: Form_Config = Depends(), Session: Session = Depends(db.session)):
    """
    `config post`\n
    :param request:
    :return:
    """
    print('/post login,Cookie:', request.cookies, ckReadmap, cfg)

    lv = checkLogin(request.cookies)
    if lv['level'] <= 0:
        return RedirectMainpage()


    AnalysisConfig.filter(session=Session,  user_id=lv['userid']).delete(auto_commit=True)
    AnalysisConfig.create(session=Session,  user_id=lv['userid'], param='ReadMapping_IntralControlOP', val=str(ckReadmap))
    AnalysisConfig.create(session=Session,  user_id=lv['userid'], param='refDB', val=str(cfg.refDB))
    AnalysisConfig.create(session=Session,  user_id=lv['userid'], param='Kraken2_minbaseQulity', val=cfg.edKrakenQuality)
    AnalysisConfig.create(session=Session,  user_id=lv['userid'], param='Kraken2_minhitGroups', val=cfg.edKrakengroups)
    AnalysisConfig.create(session=Session,  user_id=lv['userid'], param='Braken_OptionR', val=cfg.edBraken_r)
    AnalysisConfig.create(session=Session,  user_id=lv['userid'], param='BcfToolsQualitySymbol', val=cfg.cbBcftoolsQc)
    AnalysisConfig.create(session=Session,  user_id=lv['userid'], param='BcfToolsQualityValue', val=cfg.cbBcftoolsQcval)
    AnalysisConfig.create(session=Session,  user_id=lv['userid'], param='BcfToolsDpSymbol', val=cfg.cbBcftoolsDp)
    AnalysisConfig.create(session=Session,  user_id=lv['userid'], param='BcfToolsDpValue', val=cfg.cbBcftoolsDpval)
    AnalysisConfig.create(session=Session,  user_id=lv['userid'], param='SnpEff_ud', val=cfg.edSnpeff)
    AnalysisConfig.create(session=Session,  user_id=lv['userid'], param='VAF_dp', val=cfg.edVaf_dp)

    Session.commit()
    return RedirectResponse(url="/samples/config", status_code=301)


@router.get("/summary/{sampleid}/circos", response_class=HTMLResponse)
async def getSampleCircos(request: Request, sampleid: int, Session: Session = Depends(db.session)):
    """
    `Sample circos image`\n
    :param request:
    :param sampleidx:
    :return:
    """
    print('/Get:circos, Cookie:',request.cookies)
    lv = checkLogin(request.cookies)
    if lv['level'] <= 0:
        return RedirectMainpage()

    df = SampleGroup.filter(session=Session, id=sampleid, user_id=lv['userid'])
    if df and df.first():

        form = CircosImgForm(request)
        form.userid = EncToData(request.cookies['DsUsInfoKey'])
        form.CircosFile = "/static/circos/{0}.png".format(sampleid)

        return templates.TemplateResponse("circosimage.html", form.__dict__)
    else:
        return JSONResponse(status_code=202, content=dict(msg="SAMPLE_NOT_FOUND"))


def dragSummaryCheck(drugType, deleteGene, use, result):
    if use==True:
        result = 1
        
    if (('katG' in deleteGene)and(drugType == 'INH')):
        result = 1
    elif(('PncA' in deleteGene)and(drugType == 'PZA')):
        result = 1
    elif(('gid' in deleteGene)and(drugType == 'STM')):
        result = 1
    elif(('ethA' in deleteGene)and(drugType == 'ETO')):
        result = 1
        
    return result
    
    
@router.get("/summary/{sampleid}", response_class=HTMLResponse)
async def get_samplesummary(request: Request, sampleid : int, Session: Session = Depends(db.session)):
    """
    `Sample detail`\n
    :param request:
    :return:
    """
    print('/Get:sample1, Cookie:',request.cookies)
    lv = checkLogin(request.cookies)
    if lv['level'] <= 0:
        return RedirectMainpage()

    #--------- check id
    smp = SampleGroup.filter(id=sampleid, user_id=lv['userid']).first()

    if not smp:
        return RedirectResponse(url="/samples", status_code=302)


    #---------file info
    usid = Datafile.user_id.__eq__(lv['userid'])
    rfile = {}
    alllist = {}
    allsize = {}
    ser = Datafile.customfilter(session=Session, filter=[usid]).order_by('filename').all()

    flist = []
    for m in ser:
        alllist[str(m.id)] = m.filename
        allsize[str(m.id)] = m.filesize
        flist.append(m.filename)


    form = SampleSummaryForm(request)
    form.userid = EncToData(request.cookies['DsUsInfoKey'])
    form.SampleID     = smp.id
    form.sampledataID = smp.Sample_DataID
    form.patientID     = smp.Sample_PatientID
    form.patientName =  smp.Sample_PatientName
    if str(smp.Analysis_R1_Data_Id) in alllist.keys():
        form.r1name = alllist[str(smp.Analysis_R1_Data_Id)]
        form.r1size = convert_size(allsize[str(smp.Analysis_R1_Data_Id)])
    else:
        form.r1name = 'NONE'
        form.r1size = ''
        
    if str(smp.Analysis_R2_Data_Id) in alllist.keys():
        form.r2name = alllist[str(smp.Analysis_R2_Data_Id)]
        form.r2size = convert_size(allsize[str(smp.Analysis_R2_Data_Id)])
    else:
        form.r2name = 'NONE'
        form.r2size = ''

    form.labTechnician = smp.Sample_LabTechnician
    form.sampleSource = smp.Sample_Source
    form.cultureType = smp.Sample_CultureType
    form.sequencer = smp.Report_Sequencer
    form.method = smp.Report_Method
    form.pipeline = smp.Report_Pipeline
    form.recvDate = smp.Sample_RecvDate.strftime('%m/%d/%Y')
    form.seqDate = smp.Sample_SeqDate.strftime('%m/%d/%Y')
    form.labprepDate = smp.Sample_LibPrepDate.strftime('%m/%d/%Y')
    form.reportDate = smp.Sample_ReportDate.strftime('%m/%d/%Y')
    form.drName = smp.Report_DoctorName
    form.reportLab = smp.Report_ReportLab
    form.address = smp.Report_LabAddress
    form.stepno = smp.Analysis_StepNo
    form.stepstr = stepnoToStr(smp.Analysis_StepNo)
    form.stime1 = smp.Analysis_Step1Time.strftime('%m/%d/%Y %H:%M') if smp.Analysis_Step5Time else datetime.now().strftime('%m/%d/%Y %H:%M')
    form.stime2 = smp.Analysis_Step2Time.strftime('%m/%d/%Y %H:%M') if smp.Analysis_Step5Time else datetime.now().strftime('%m/%d/%Y %H:%M')
    form.stime3 = smp.Analysis_Step3Time.strftime('%m/%d/%Y %H:%M') if smp.Analysis_Step5Time else datetime.now().strftime('%m/%d/%Y %H:%M')
    form.stime4 = smp.Analysis_Step4Time.strftime('%m/%d/%Y %H:%M') if smp.Analysis_Step5Time else datetime.now().strftime('%m/%d/%Y %H:%M')
    form.stime5 = smp.Analysis_Step5Time.strftime('%m/%d/%Y %H:%M') if smp.Analysis_Step5Time else datetime.now().strftime('%m/%d/%Y %H:%M')

    if smp.Analysis_SpeciesPredName.lower() == 'mycobacterium tuberculosis':
        if(smp.Analysis_QcTotReadFastQ > 0)and (smp.Analysis_QcQ30ReadFastQ > 0) and (smp.Analysis_QcMapReadSpecies > 0) and (smp.Analysis_QcMapRateSpecies > 0)and (smp.Analysis_QcCoverageDeep > 0):
            form.Qcontrol = 'Pass'
        else:
            form.Qcontrol = 'Failed'
    else:
        if(smp.Analysis_QcTotReadFastQ > 0)and (smp.Analysis_QcQ30ReadFastQ > 0) and (smp.Analysis_QcMapReadSpecies > 0) and (smp.Analysis_QcMapRateSpecies > 0):
            form.Qcontrol = 'Pass'
        elif(smp.Analysis_StepNo != 99):
            form.Qcontrol = 'Not started'
        else:
            form.Qcontrol = 'Failed'
                                                         
                             
    form.Mycobac = smp.Analysis_SpeciesPredName

    if smp.Analysis_SpeciesPredName.lower() == 'mycobacterium tuberculosis':
        form.Lineage = smp.Report_Lineage
        form.Spoligotype = smp.Report_Spligotype
    else:
        form.Lineage = 'N/A'
        form.Spoligotype = 'N/A'

    form.filelist = flist
    form.timenow =  datetime.now().strftime("%m%d%Y%H%M%S")
    
    sql = []
    sql.append((and_(AnalysisTargetGeneDeletion.Sample_Id==sampleid, AnalysisTargetGeneDeletion.user_id==lv['userid'])))
    delGen = AnalysisTargetGeneDeletion.colunm_customfilter(session=Session,cols=AnalysisTargetGeneDeletion.gene, filter=sql).group_by2('gene').all()
    gd = []
    if delGen:
        for d in delGen:
            gd.append(d[0])


    if form.Mycobac.lower() == 'mycobacterium tuberculosis':    # only Mycobacterium tuberculosis
        tb = AnalysisResult
        sql = []
        sql.append((tb.Sample_Id==smp.id))
        sql.append((or_(tb.AMK.in_([1,2]), tb.BDQ.in_([1,2]), tb.CAP.in_([1,2]), tb.CFZ.in_([1,2]), tb.DLM.in_([1,2]), tb.EMB.in_([1,2]), tb.ETO.in_([1,2]), tb.INH.in_([1,2]),
                        tb.KAN.in_([1,2]), tb.LFX.in_([1,2]), tb.MFX.in_([1,2]), tb.PZA.in_([1,2]), tb.RIF.in_([1,2]), tb.STM.in_([1,2]))))
        drg_alllist = AnalysisResult.customfilter(session=Session, filter=sql).order_by('-VarAlleleFreq').all()
        form.dr_amk = 0
        form.dr_bdq = 0
        form.dr_cap = 0
        form.dr_cfz = 0
        form.dr_dlm = 0
        form.dr_emb = 0
        form.dr_eto = 0
        form.dr_inh = 0
        form.dr_kan = 0
        form.dr_lfx = 0
        form.dr_lzd = 0
        form.dr_mfx = 0
        form.dr_pza = 0
        form.dr_rif = 0
        form.dr_stm = 0

        if drg_alllist:
            for im in drg_alllist:
                form.dr_amk = dragSummaryCheck('   ',gd, in_range(im.AMK,1,2), form.dr_amk)
                form.dr_bdq = dragSummaryCheck('   ',gd, in_range(im.BDQ,1,2), form.dr_bdq)
                form.dr_cap = dragSummaryCheck('CAP',gd, in_range(im.CAP,1,2), form.dr_cap)
                form.dr_cfz = dragSummaryCheck('   ',gd, in_range(im.CFZ,1,2), form.dr_cfz)
                form.dr_dlm = dragSummaryCheck('   ',gd, in_range(im.DLM,1,2), form.dr_dlm)
                form.dr_emb = dragSummaryCheck('   ',gd, in_range(im.EMB,1,2), form.dr_emb)
                form.dr_eto = dragSummaryCheck('ETO',gd, in_range(im.ETO,1,2), form.dr_eto)
                form.dr_inh = dragSummaryCheck('INH',gd, in_range(im.INH,1,2), form.dr_inh)
                form.dr_kan = dragSummaryCheck('   ',gd, in_range(im.KAN,1,2), form.dr_kan)
                form.dr_lfx = dragSummaryCheck('   ',gd, in_range(im.LFX,1,2), form.dr_lfx)
                form.dr_lzd = dragSummaryCheck('   ',gd, in_range(im.LZD,1,2), form.dr_lzd)
                form.dr_mfx = dragSummaryCheck('   ',gd, in_range(im.MFX,1,2), form.dr_mfx)
                form.dr_pza = dragSummaryCheck('PZA',gd, in_range(im.PZA,1,2), form.dr_pza)
                form.dr_rif = dragSummaryCheck('   ',gd, in_range(im.RIF,1,2), form.dr_rif)
                form.dr_stm = dragSummaryCheck('STM',gd, in_range(im.STM,1,2), form.dr_stm)
        else:
            form.dr_amk = dragSummaryCheck('   ',gd, False, 0)
            form.dr_bdq = dragSummaryCheck('   ',gd, False, 0)
            form.dr_cap = dragSummaryCheck('CAP',gd, False, 0)
            form.dr_cfz = dragSummaryCheck('   ',gd, False, 0)
            form.dr_dlm = dragSummaryCheck('   ',gd, False, 0)
            form.dr_emb = dragSummaryCheck('   ',gd, False, 0)
            form.dr_eto = dragSummaryCheck('ETO',gd, False, 0)
            form.dr_inh = dragSummaryCheck('INH',gd, False, 0)
            form.dr_kan = dragSummaryCheck('   ',gd, False, 0)
            form.dr_lfx = dragSummaryCheck('   ',gd, False, 0)
            form.dr_lzd = dragSummaryCheck('   ',gd, False, 0)
            form.dr_mfx = dragSummaryCheck('   ',gd, False, 0)
            form.dr_pza = dragSummaryCheck('PZA',gd, False, 0)
            form.dr_rif = dragSummaryCheck('   ',gd, False, 0)
            form.dr_stm = dragSummaryCheck('STM',gd, False, 0)
    else:
        form.dr_amk = 2
        form.dr_bdq = 2
        form.dr_cap = 2
        form.dr_cfz = 2
        form.dr_dlm = 2
        form.dr_emb = 2
        form.dr_eto = 2
        form.dr_inh = 2
        form.dr_kan = 2
        form.dr_lfx = 2
        form.dr_lzd = 2
        form.dr_mfx = 2
        form.dr_pza = 2
        form.dr_rif = 2
        form.dr_stm = 2

    return templates.TemplateResponse("sample_summary.html", form.__dict__)




@router.get("/statistics/{sampleid}", response_class=HTMLResponse)
async def get_samplestatistics(request: Request, sampleid : int, Session: Session = Depends(db.session)):
    """
    `Sample detail`\n
    :param request:
    :return:
    """
    print('/Get:static, Cookie:',request.cookies)
    lv = checkLogin(request.cookies)
    if lv['level'] <= 0:
        return RedirectMainpage()

    #--------- check id
    smp = SampleGroup.filter(id=sampleid, user_id=lv['userid']).first()

    if not smp:
        return RedirectResponse(url="/samples", status_code=302)
    
    # Reads mapping to host genome (human) Internal control on
    df = AnalysisConfig.filter(user_id=lv['userid'])
    ReadIntCtlOp = 'True'
    if df and df.count() > 0: 
        for cfg in df.all():
            if(cfg.param == 'ReadMapping_IntralControlOP'):
                ReadIntCtlOp = cfg.val

    form = SampleStatisticsForm(request)
    form.userid = EncToData(request.cookies['DsUsInfoKey'])
    form.SampleID     = smp.id
    form.ReadIntCtlOp = ReadIntCtlOp
    form.RawFastQRead = format(smp.Analysis_RawFastQRead, ',')
    form.RawFastQBase = format(smp.Analysis_RawFastQBase, ',')
    form.RawFastQ30 = '{:.2f}%'.format(smp.Analysis_RawFastQ30 * 100)
    form.TrimFastQRead = format(smp.Analysis_TrimFastQRead, ',')
    form.TrimFastQBase = format(smp.Analysis_TrimFastQBase, ',')
    form.TrimFastQ30 = '{:.2f}%'.format(smp.Analysis_TrimFastQ30 * 100)
    form.SpikeMapRead1 = str(smp.Analysis_SpikeMapRead1)
    form.SpikeMapRead2 = str(smp.Analysis_SpikeMapRead2)
    form.SpikeMapRead3 = str(smp.Analysis_SpikeMapRead3)
    form.SpeciesPredName = smp.Analysis_SpeciesPredName
    form.SpeciesPredMapTot = format(smp.Analysis_SpeciesPredMapTot, ',')
    form.SpeciesPredMapRead = format(smp.Analysis_SpeciesPredMapRead, ',')
    form.SpeciesPredMapRate = '{:.2f}%'.format(smp.Analysis_SpeciesPredMapRate * 100)
    form.AlignHostGenomeRead = format( smp.Analysis_AlignHostGenomeRead, ',') if smp.Analysis_SpeciesPredName.lower() == 'mycobacterium tuberculosis' else 'N/A'
    form.AlignDupRead = format(smp.Analysis_AlignDupRead, ',') if smp.Analysis_SpeciesPredName.lower() == 'mycobacterium tuberculosis' else 'N/A'
    form.AlignDupRate = '{:.2f}%'.format(smp.Analysis_AlignDupRate*100) if smp.Analysis_SpeciesPredName.lower() == 'mycobacterium tuberculosis' else 'N/A'
    form.AlignMapReadTot = format(smp.Analysis_AlignMapReadTot, ',') if smp.Analysis_SpeciesPredName.lower() == 'mycobacterium tuberculosis' else 'N/A'
    form.AlignMapRateTot = '{:.2f}%'.format(smp.Analysis_AlignMapRateTot*100) if smp.Analysis_SpeciesPredName.lower() == 'mycobacterium tuberculosis' else 'N/A'
    form.AlignReadLen = format(smp.Analysis_AlignReadLen, ',') if smp.Analysis_SpeciesPredName.lower() == 'mycobacterium tuberculosis' else 'N/A'
    form.AlignInsert = '{:.2f}'.format(smp.Analysis_AlignInsert) if smp.Analysis_SpeciesPredName.lower() == 'mycobacterium tuberculosis' else 'N/A'
    form.AlignBaseQuality = '{:.2f}'.format(smp.Analysis_AlignBaseQuality) if smp.Analysis_SpeciesPredName.lower() == 'mycobacterium tuberculosis' else 'N/A'
    form.AlignMapQuality = '{:.2f}'.format(smp.Analysis_AlignMapQuality) if smp.Analysis_SpeciesPredName.lower() == 'mycobacterium tuberculosis' else 'N/A'
    form.AlignMapReadTarget = format(smp.Analysis_AlignMapReadTarget, ',') 
    form.AlignMapRateTarget = '{:.2f}%'.format(smp.Analysis_AlignMapRateTarget*100)
    form.AlignCoverage = format(smp.Analysis_AlignCoverage, ',') if smp.Analysis_SpeciesPredName.lower() == 'mycobacterium tuberculosis' else 'N/A'
    form.Align1xCoverage = '{:.2f}%'.format(smp.Analysis_Align1xCoverage) if smp.Analysis_SpeciesPredName.lower() == 'mycobacterium tuberculosis' else 'N/A'
    form.Align50xCoverage = '{:.2f}%'.format(smp.Analysis_Align50xCoverage) if smp.Analysis_SpeciesPredName.lower() == 'mycobacterium tuberculosis' else 'N/A'
    form.Align100xCoverage = '{:.2f}%'.format(smp.Analysis_Align100xCoverage) if smp.Analysis_SpeciesPredName.lower() == 'mycobacterium tuberculosis' else 'N/A'
    
    if smp.Analysis_StepNo != 99:
        form.QcTotReadFastQ = 'Not started'
        form.QcQ30ReadFastQ = 'Not started'
        form.QcAvgMapRead = 'Not started'
        form.QcMapReadSpecies = 'Not started'
        form.QcMapRateSpecies = 'Not started'
        form.QcCoverageDeep = 'Not started'
    else:
        form.QcTotReadFastQ = 'Pass' if smp.Analysis_QcTotReadFastQ == 1 else 'Failed'
        form.QcQ30ReadFastQ = 'Pass' if smp.Analysis_QcQ30ReadFastQ == 1 else 'Failed'
        form.QcAvgMapRead = 'Pass' if smp.Analysis_QcAvgMapRead == 1 else 'Failed'
        form.QcMapReadSpecies = 'Pass' if smp.Analysis_QcMapReadSpecies == 1 else 'Failed'
        form.QcMapRateSpecies = 'Pass' if smp.Analysis_QcMapRateSpecies == 1 else 'Failed'
        if smp.Analysis_SpeciesPredName.lower() == 'mycobacterium tuberculosis':
            form.QcCoverageDeep = 'Pass' if smp.Analysis_QcCoverageDeep == 1 else 'Failed'
        else:
            form.QcCoverageDeep = 'N/A'
        
    form.species = []
    form.speciessub = []
    form.Lineage  = smp.Report_Lineage if smp.Analysis_SpeciesPredName.lower() == 'mycobacterium tuberculosis' else 'N/A'   # only Mycobacterium tuberculosis 만 분석
    form.Spoligotype = smp.Report_Spligotype if smp.Analysis_SpeciesPredName.lower() == 'mycobacterium tuberculosis' else 'N/A'   # only Mycobacterium tuberculosis 만 분석

    ls = Species.filter(Sample_Id=smp.id,Stype=1,user_id=lv['userid'],map_rate__gte=0.1).order_by('-map_read').all()    # map rate가 10% 이상인것만 표시
    if ls:
        for item in ls:
            form.species.append({'name':item.Sname,'read':item.map_read,'rate':'{:.2f}%'.format(item.map_rate*100)})     # map rate가 10% 이상인것만 표시
    ls = Species.filter(Sample_Id=smp.id,Stype=2,user_id=lv['userid'],map_rate__gte=0.1).order_by('-map_read').all()
    if ls:
        for item in ls:
            form.speciessub.append({'name':item.Sname,'read':item.map_read,'rate':'{:.2f}%'.format(item.map_rate*100)})

    return templates.TemplateResponse("sample_statistics.html", form.__dict__)



@router.get("/variants/{sampleid}", response_class=HTMLResponse)
async def get_samplevariants(request: Request, sampleid : int, pageno: int=1, Session: Session = Depends(db.session)):
    """
    `Sample detail`\n
    :param request:
    :return:
    """
    print('/Get:variant, Cookie:',request.cookies)
    lv = checkLogin(request.cookies)
    if lv['level'] <= 0:
        return RedirectMainpage()

    #--------- check id
    smp = SampleGroup.filter(id=sampleid, user_id=lv['userid']).first()

    if not smp:
        return RedirectResponse(url="/samples", status_code=302)


    form = SampleVariantsRavForm(request)
    form.userid = EncToData(request.cookies['DsUsInfoKey'])
    form.SampleID = sampleid
    form.SampledataID = smp.Sample_DataID
    form.totpage = AnalysisResult.filter(session=Session,Sample_Id=sampleid, user_id=lv['userid']).pagecount()
    form.totcount = AnalysisResult.filter(session=Session,Sample_Id=sampleid, user_id=lv['userid']).count()
    form.nowpage = pageno
    form.page = makePageNo(pageno, MAX_PAGE_NUMBER_COUNT,form.totpage)
    form.page['page_previous_link'] = '?pageno={0}'.format(form.page['page_previous']) if form.page['page_previous'] != '' else ''
    form.page['page_next_link'] =     '?pageno={0}'.format(form.page['page_next'],) if form.page['page_next'] != '' else ''
    form.page['page_list_link'] = []
    form.reseultlt  = []
    for pgno in form.page['page_list']: # page link
        form.page['page_list_link'].append('?pageno={0}'.format(pgno) if pgno != pageno else '')

    lt = AnalysisResult.filter(session=Session,Sample_Id=sampleid, user_id=lv['userid']).order_by('-VarAlleleFreq','Position').page(MAX_PAGE_ROW_COUNT, pageno).all()
    if len(lt):
        for item in lt:
            form.reseultlt.append({'Sample_Id':item.Sample_Id,'Position':str(item.Position),'Ref':item.Ref,
                                    'Alt':item.Alt,
                                    'Depth':str(item.Depth),
                                    'VarAlleleFreq':'{:.2f}'.format(item.VarAlleleFreq),
                                    'VarType':item.VarType,
                                    'Gene':item.Gene,
                                    'GeneID':item.GeneID,
                                    'Necleotide':item.Necleotide,
                                    'AminoAcid':item.AminoAcid
                                    })

    return templates.TemplateResponse("sample_variants.html", form.__dict__)

@router.get("/genedeletion/{sampleid}", response_class=HTMLResponse)
async def get_samplegenedeletion(request: Request, sampleid : int, pageno: int=1, Session: Session = Depends(db.session)):
    """
    `Sample detail`\n
    :param request:
    :return:
    """
    print('/Get:variant, Cookie:',request.cookies)
    lv = checkLogin(request.cookies)
    if lv['level'] <= 0:
        return RedirectMainpage()

    #--------- check id
    cnt = SampleGroup.filter(id=sampleid, user_id=lv['userid']).count()

    if cnt <= 0:
        return RedirectResponse(url="/samples", status_code=302)
        
    form = SampleTargetGeneDeletionFormForm(request)
    form.userid = EncToData(request.cookies['DsUsInfoKey'])
    form.SampleID = sampleid
    form.Coveragedepth = 0
    form.reseultlt  = []

    #--------- check coveragedepth 
    smp = SampleGroup.filter(id=sampleid, user_id=lv['userid']).first()
    if smp:
        form.Coveragedepth = smp.Analysis_AlignCoverage

    tb = AnalysisTargetGeneDeletion
    sql = []
    sql.append((tb.Sample_Id==sampleid))
    sql.append((tb.user_id==lv['userid']))
    
    rtlt = AnalysisTargetGeneDeletion.customfilter(session=Session, filter=sql).page(MAX_PAGE_ROW_COUNT, pageno)
    form.totcount = AnalysisTargetGeneDeletion.customfilter(session=Session, filter=sql).count()
    form.totpage = AnalysisTargetGeneDeletion.customfilter(session=Session, filter=sql).pagecount()
    form.nowpage = pageno
    if rtlt :
        lt = rtlt.all()
        for item in lt:
            form.reseultlt.append({'position':"{0} - {1}".format(item.posmin,item.posmax), 'posmin':item.posmin, 'posmax':item.posmax, 'gene':item.gene})


    form.page = makePageNo(pageno, MAX_PAGE_NUMBER_COUNT,form.totpage)
    form.page['page_previous_link'] = '?pageno={0}'.format(form.page['page_previous']) if form.page['page_previous'] != '' else ''
    form.page['page_next_link'] =     '?pageno={0}'.format(form.page['page_next']) if form.page['page_next'] != '' else ''
    form.page['page_list_link'] = []
    for pgno in form.page['page_list']: # page link
        form.page['page_list_link'].append('?pageno={0}'.format(pgno) if pgno != pageno else '')

    return templates.TemplateResponse("sample_genedeletion.html", form.__dict__)

        

@router.get("/rav/{sampleid}", response_class=HTMLResponse)
async def get_samplerav(request: Request, sampleid : int, pageno: int=1, ravfilter:str='', Session: Session = Depends(db.session)):
    """
    `Sample detail`\n
    :param request:
    :return:
    """
    print('/Get:variant, Cookie:',request.cookies)
    lv = checkLogin(request.cookies)
    if lv['level'] <= 0:
        return RedirectMainpage()


    #--------- check id
    smp = SampleGroup.filter(id=sampleid, user_id=lv['userid']).first()

    if not smp:
        return RedirectResponse(url="/samples", status_code=302)

    form = SampleVariantsRavForm(request)
    form.userid = EncToData(request.cookies['DsUsInfoKey'])
    form.SampleID = smp.id
    form.SampledataID = smp.Sample_DataID
    form.reseultlt  = []
    form.ravfilter = list(ravfilter)
    print('------------------------------------------>',ravfilter)
    tb = AnalysisResult
    sql = []
    sql.append((tb.Sample_Id==sampleid))
    sql.append((tb.user_id==lv['userid']))
    
    if(len(form.ravfilter) == 0):
        sql.append((or_(tb.AMK>0, tb.BDQ>0, tb.CAP>0, tb.CFZ>0, tb.DLM>0,tb.EMB>0, tb.ETO>0,tb.INH>0, tb.KAN>0, tb.LFX>0, tb.LZD>0, tb.MFX>0, tb.PZA>0, tb.RIF>0, tb.STM>0)))
    else:
        sql.append((or_(tb.AMK.in_(form.ravfilter), tb.BDQ.in_(form.ravfilter), tb.CAP.in_(form.ravfilter), tb.CFZ.in_(form.ravfilter), tb.DLM.in_(form.ravfilter),
                    tb.EMB.in_(form.ravfilter), tb.ETO.in_(form.ravfilter), tb.INH.in_(form.ravfilter), tb.KAN.in_(form.ravfilter), tb.LFX.in_(form.ravfilter), 
                    tb.LZD.in_(form.ravfilter), tb.MFX.in_(form.ravfilter), tb.PZA.in_(form.ravfilter), tb.RIF.in_(form.ravfilter), tb.STM.in_(form.ravfilter))))

    form.totcount = AnalysisResult.customfilter(session=Session, filter=sql).count()
    form.totpage = AnalysisResult.customfilter(session=Session, filter=sql).pagecount()
    form.nowpage = ensure_range(pageno,1,max(form.totpage,1))
    
    rtlt = AnalysisResult.customfilter(session=Session, filter=sql).order_by('-VarAlleleFreq','Position').page(MAX_PAGE_ROW_COUNT, form.nowpage)
    if rtlt :
        lt = rtlt.all()
        for item in lt:
            if item.OverlapLv == 1: ovl = 'Nucleotide'
            elif item.OverlapLv == 2: ovl = 'Amino acid'
            elif item.OverlapLv == 3: ovl = 'Both'
            else: ovl = ''
            form.reseultlt.append({'Sample_Id':item.Sample_Id,'Position':str(item.Position),'Ref':item.Ref,
                                    'Alt':item.Alt,
                                    'Depth':str(item.Depth),
                                    'VarAlleleFreq':'{:.2f}'.format(item.VarAlleleFreq),
                                    'VarType':item.VarType,
                                    'Gene':item.Gene,
                                    'GeneID':item.GeneID,
                                    'Necleotide':item.Necleotide,
                                    'AminoAcid':item.AminoAcid,
                                    'AMK':item.AMK if item.AMK>0 else '',
                                    'BDQ':item.BDQ if item.BDQ>0 else '',
                                    'CAP':item.CAP if item.CAP>0 else '',
                                    'CFZ':item.CFZ if item.CFZ>0 else '',
                                    'DLM':item.DLM if item.DLM>0 else '',
                                    'EMB':item.EMB if item.EMB>0 else '',
                                    'ETO':item.ETO if item.ETO>0 else '',
                                    'INH':item.INH if item.INH>0 else '',
                                    'KAN':item.KAN if item.KAN>0 else '',
                                    'LFX':item.LFX if item.LFX>0 else '',
                                    'LZD':item.LZD if item.LZD>0 else '',
                                    'MFX':item.MFX if item.MFX>0 else '',
                                    'PZA':item.PZA if item.PZA>0 else '',
                                    'RIF':item.RIF if item.RIF>0 else '',
                                    'STM':item.STM if item.STM>0 else '',
                                    'OverlapLv':ovl
                                    })


    form.page = makePageNo(pageno, MAX_PAGE_NUMBER_COUNT,form.totpage)
    form.page['page_previous_link'] = '?pageno={0}'.format(form.page['page_previous']) if form.page['page_previous'] != '' else ''
    form.page['page_next_link'] =     '?pageno={0}'.format(form.page['page_next']) if form.page['page_next'] != '' else ''
    form.page['page_list_link'] = []
    for pgno in form.page['page_list']: # page link
        if(ravfilter == ''):
            pglk = '?pageno={0}'.format(pgno) if pgno != form.nowpage else ''
        else:
            pglk = '?ravfilter={0}&pageno={1}'.format(ravfilter, pgno) if pgno != form.nowpage else ''
        form.page['page_list_link'].append(pglk)
            
    return templates.TemplateResponse("sample_rav.html", form.__dict__)

@router.get("/report_20230910/{sampleid}", response_class=HTMLResponse)
async def get_samplereport(request: Request, sampleid : int, Session: Session = Depends(db.session)):
    """
    `Sample detail`\n
    :param request:
    :return:
    """
    print('/Get:variant, Cookie:',request.cookies)
    lv = checkLogin(request.cookies)
    if lv['level'] <= 0:
        return RedirectMainpage()

    #--------- check id
    smp = SampleGroup.filter(id=sampleid, user_id=lv['userid']).first()
    
    if not smp:
        os.remove('/home/jj/univ_myco/pdf/{0}.pdf'.format(sampleid))
        return RedirectResponse(url="/samples", status_code=302)

    form = SampleReportForm(request)
    form.userid = EncToData(request.cookies['DsUsInfoKey'])
    form.SampleID = sampleid
    form.DataID = smp.Sample_DataID
    form.PatientID = smp.Sample_PatientID
    form.PatientName = smp.Sample_PatientName
    form.Source = smp.Sample_Source
    form.CultureType = smp.Sample_CultureType
    form.RecvDate = smp.Sample_RecvDate.strftime('%m/%d/%Y')
    form.LibPrepDate = smp.Sample_LibPrepDate.strftime('%m/%d/%Y')
    form.SeqDate  = smp.Sample_SeqDate.strftime('%m/%d/%Y')
    form.ReportDate  = smp.Sample_ReportDate.strftime('%m/%d/%Y')
    form.LabTechnician  = smp.Sample_LabTechnician
    form.Contact = smp.Sample_Contact
    form.Species = smp.Report_Species
    form.FinalResult = smp.Report_FinalResult
    form.AdditionalComment = smp.Report_AdditionalComment
    form.DoctorName = smp.Report_DoctorName
    form.ReportLab = smp.Report_ReportLab
    form.LabAddress = smp.Report_LabAddress
    form.AMK = []
    form.BDQ = []
    form.CAP = []
    form.CFZ = []
    form.DLM = []
    form.EMB = []
    form.ETO = []
    form.INH = []
    form.KAN = []
    form.LFX = []
    form.LZD = []
    form.MFX = []
    form.PZA = []
    form.RIF = []
    form.STM = []

    if(smp.Analysis_QcTotReadFastQ > 0)and (smp.Analysis_QcQ30ReadFastQ > 0) and (smp.Analysis_QcAvgMapRead > 0) and (smp.Analysis_QcMapReadSpecies > 0) and (smp.Analysis_QcMapRateSpecies > 0)and (smp.Analysis_QcCoverageDeep > 0):
        form.QualityControl = 'Pass'
    else:
        form.QualityControl = 'Fail'
        
    if smp.Analysis_SpeciesPredName.lower() == 'mycobacterium tuberculosis':    # only Mycobacterium tuberculosis 
        form.Spoligotype = smp.Report_Spligotype
        form.Lineage = smp.Report_Lineage
        
        tb = AnalysisResult
        sql = []
        sql.append((tb.Sample_Id==smp.id)) 
        sql.append((tb.user_id==lv['userid']))
        sql.append((or_(tb.AMK.in_([1,2]), tb.BDQ.in_([1,2]), tb.CAP.in_([1,2]), tb.CFZ.in_([1,2]), tb.DLM.in_([1,2]), tb.EMB.in_([1,2]), tb.ETO.in_([1,2]), tb.INH.in_([1,2]), 
                        tb.KAN.in_([1,2]), tb.LFX.in_([1,2]), tb.MFX.in_([1,2]), tb.PZA.in_([1,2]), tb.RIF.in_([1,2]), tb.STM.in_([1,2]))))
        drg_alllist = AnalysisResult.customfilter(session=Session, filter=sql).order_by('-VarAlleleFreq').all()
        
        
        if drg_alllist: 
            for im in drg_alllist:
                if(im.AMK>0): form.AMK.append({'Gene':'{0}({1}, {2:.1f}%, {3})'.format(im.Gene,im.AminoAcid if(im.AminoAcid!='.') else im.Necleotide,im.VarAlleleFreq,im.Tier), 'Result':'{0}'.format('R' if(im.AMK>0) else ''),'Coment':''})
                if(im.BDQ>0): form.BDQ.append({'Gene':'{0}({1}, {2:.1f}%, {3})'.format(im.Gene,im.AminoAcid if(im.AminoAcid!='.') else im.Necleotide,im.VarAlleleFreq,im.Tier), 'Result':'{0}'.format('R' if(im.BDQ>0) else ''),'Coment':''})
                if(im.CAP>0): form.CAP.append({'Gene':'{0}({1}, {2:.1f}%, {3})'.format(im.Gene,im.AminoAcid if(im.AminoAcid!='.') else im.Necleotide,im.VarAlleleFreq,im.Tier), 'Result':'{0}'.format('R' if(im.CAP>0) else ''),'Coment':''})
                if(im.CFZ>0): form.CFZ.append({'Gene':'{0}({1}, {2:.1f}%, {3})'.format(im.Gene,im.AminoAcid if(im.AminoAcid!='.') else im.Necleotide,im.VarAlleleFreq,im.Tier), 'Result':'{0}'.format('R' if(im.CFZ>0) else ''),'Coment':''})
                if(im.DLM>0): form.DLM.append({'Gene':'{0}({1}, {2:.1f}%, {3})'.format(im.Gene,im.AminoAcid if(im.AminoAcid!='.') else im.Necleotide,im.VarAlleleFreq,im.Tier), 'Result':'{0}'.format('R' if(im.DLM>0) else ''),'Coment':''})
                if(im.EMB>0): form.EMB.append({'Gene':'{0}({1}, {2:.1f}%, {3})'.format(im.Gene,im.AminoAcid if(im.AminoAcid!='.') else im.Necleotide,im.VarAlleleFreq,im.Tier), 'Result':'{0}'.format('R' if(im.EMB>0) else ''),'Coment':''})
                if(im.ETO>0): form.ETO.append({'Gene':'{0}({1}, {2:.1f}%, {3})'.format(im.Gene,im.AminoAcid if(im.AminoAcid!='.') else im.Necleotide,im.VarAlleleFreq,im.Tier), 'Result':'{0}'.format('R' if(im.ETO>0) else ''),'Coment':''})
                if(im.INH>0): form.INH.append({'Gene':'{0}({1}, {2:.1f}%, {3})'.format(im.Gene,im.AminoAcid if(im.AminoAcid!='.') else im.Necleotide,im.VarAlleleFreq,im.Tier), 'Result':'{0}'.format('R' if(im.INH>0) else ''),'Coment':''})
                if(im.KAN>0): form.KAN.append({'Gene':'{0}({1}, {2:.1f}%, {3})'.format(im.Gene,im.AminoAcid if(im.AminoAcid!='.') else im.Necleotide,im.VarAlleleFreq,im.Tier), 'Result':'{0}'.format('R' if(im.KAN>0) else ''),'Coment':''})
                if(im.LFX>0): form.LFX.append({'Gene':'{0}({1}, {2:.1f}%, {3})'.format(im.Gene,im.AminoAcid if(im.AminoAcid!='.') else im.Necleotide,im.VarAlleleFreq,im.Tier), 'Result':'{0}'.format('R' if(im.LFX>0) else ''),'Coment':''})
                if(im.LZD>0): form.LZD.append({'Gene':'{0}({1}, {2:.1f}%, {3})'.format(im.Gene,im.AminoAcid if(im.AminoAcid!='.') else im.Necleotide,im.VarAlleleFreq,im.Tier), 'Result':'{0}'.format('R' if(im.LZD>0) else ''),'Coment':''})
                if(im.MFX>0): form.MFX.append({'Gene':'{0}({1}, {2:.1f}%, {3})'.format(im.Gene,im.AminoAcid if(im.AminoAcid!='.') else im.Necleotide,im.VarAlleleFreq,im.Tier), 'Result':'{0}'.format('R' if(im.MFX>0) else ''),'Coment':''})
                if(im.PZA>0): form.PZA.append({'Gene':'{0}({1}, {2:.1f}%, {3})'.format(im.Gene,im.AminoAcid if(im.AminoAcid!='.') else im.Necleotide,im.VarAlleleFreq,im.Tier), 'Result':'{0}'.format('R' if(im.PZA>0) else ''),'Coment':''})
                if(im.RIF>0): form.RIF.append({'Gene':'{0}({1}, {2:.1f}%, {3})'.format(im.Gene,im.AminoAcid if(im.AminoAcid!='.') else im.Necleotide,im.VarAlleleFreq,im.Tier), 'Result':'{0}'.format('R' if(im.RIF>0) else ''),'Coment':''})
                if(im.STM>0): form.STM.append({'Gene':'{0}({1}, {2:.1f}%, {3})'.format(im.Gene,im.AminoAcid if(im.AminoAcid!='.') else im.Necleotide,im.VarAlleleFreq,im.Tier), 'Result':'{0}'.format('R' if(im.STM>0) else ''),'Coment':''})
    else:
        form.Spoligotype = 'N/A'
        form.Lineage = 'N/A'

    reportToPdf(sampleid,form)

    return templates.TemplateResponse("MycoReportForm.html", form.__dict__)
    
def dragGene2(drugType, deleteGene, dbCheck, resultDB, reportGene, reportResult, reportComment):
    if dbCheck:
        if resultDB.AminoAcid != '.':
            reportGene.append('{0}({1}, {2:.1f}%, {3})'.format(resultDB.Gene, resultDB.AminoAcid, resultDB.VarAlleleFreq, resultDB.Tier))
        else:
            reportGene.append('{0}({1}, {2:.1f}%, {3})'.format(resultDB.Gene, resultDB.Necleotide, resultDB.VarAlleleFreq, resultDB.Tier))
        reportResult = 'R'
    else:
        reportResult = 'S' if reportResult=='' else reportResult
    
    
    if (('katG' in deleteGene)and(drugType == 'INH')):
        reportComment = 'katG large deletion'
        reportResult = 'R'
    elif(('PncA' in deleteGene)and(drugType == 'PZA')):
        reportComment = 'PncA large deletion'
        reportResult = 'R'
    elif(('gid' in deleteGene)and(drugType == 'STM')):
        reportComment = 'gid large deletion'
        reportResult = 'R'
    elif(('ethA' in deleteGene)and(drugType == 'ETO')):
        reportComment = 'ethA large deletion'
        reportResult = 'R'   
            
    return reportGene,reportResult,reportComment

def finalResultCheck(db, form, species):
    rt = []
    drg = []
    if db.Analysis_SpeciesPredName.lower() == 'mycobacterium tuberculosis':
        if form.INHResult=='R': drg.append('INH')
        if form.RIFResult=='R': drg.append('RIF')
        if form.EMBResult=='R': drg.append('EMB')
        if form.PZAResult=='R': drg.append('PZA')
        if form.LFXResult=='R': drg.append('LFX')
        if form.MFXResult=='R': drg.append('MFX')
        if form.LZDResult=='R': drg.append('LZD')
        if form.BDQResult=='R': drg.append('BDQ')
        if form.CFZResult=='R': drg.append('CFZ')
        if form.DLMResult=='R': drg.append('DLM')
        if form.AMKResult=='R': drg.append('AMK')
        if form.CAPResult=='R': drg.append('CAP')
        if form.KANResult=='R': drg.append('KAN')
        if form.STMResult=='R': drg.append('STM')
        if form.ETOResult=='R': drg.append('ETO')
        
        rt.append('This isolate is positive for ')
        rt.append('___I___')
        rt.append('M. tuberculosis.')
        rt.append('___II___')
        rt.append('___N___')
        if len(drg)>0:
            rt.append('This isolate is resistant to ' + ','.join(drg) +'.')
        else:
            rt.append('Resistance-associated variant was not detected in this isolate.')
    else:
        if(len(species) == 1):
            #rt = 'This isolate is positive for {0}.' .format(species[0].replace('Mycobacterium ','M '))
            rt.append('This isolate is positive for ')
            rt.append('___I___')
            rt.append('{0}.'.format(species[0].replace('Mycobacterium ','M ')))
            rt.append('___II___')
        elif(len(species) >= 2):
            #rt = 'This isolate is a mixed sample of non-tuberculosis Mycobacteria ({0}).' .format(','.join(species).replace('Mycobacterium ','M '))
            rt.append('This isolate is a mixed sample of non-tuberculosis Mycobacteria ')
            rt.append('___I___')
            rt.append('{0}.'.format(species[0].replace('Mycobacterium ','M ')))
            rt.append('___II___')
        else:
            #rt = 'This isolate is negative for Mycobacterium.'
            rt.append('This isolate is negative for Mycobacterium.')

    return rt   

@router.get("/report/{sampleid}", response_class=HTMLResponse)
async def get_samplereport(request: Request, sampleid : int, Session: Session = Depends(db.session)):
    """
    `Sample detail`\n
    :param request:
    :return:
    """
    print('/Get:variant, Cookie:',request.cookies)
    lv = checkLogin(request.cookies)
    if lv['level'] <= 0:
        return RedirectMainpage()

    #--------- check id
    smp = SampleGroup.filter(id=sampleid, user_id=lv['userid']).first()
    
    if not smp:
        os.remove('/home/jj/univ_myco/pdf/{0}.pdf'.format(sampleid))
        return RedirectResponse(url="/samples", status_code=302)


    form = SampleReportDataForm(request)
    form.userid = EncToData(request.cookies['DsUsInfoKey'])
    form.SampleID = sampleid
    form.DataID = smp.Sample_DataID
    form.PatientID = smp.Sample_PatientID
    form.PatientName = smp.Sample_PatientName
    form.Source = smp.Sample_Source
    form.CultureType = smp.Sample_CultureType
    form.RecvDate = smp.Sample_RecvDate.strftime('%m/%d/%Y')
    form.LibPrepDate = smp.Sample_LibPrepDate.strftime('%m/%d/%Y')
    form.SeqDate  = smp.Sample_SeqDate.strftime('%m/%d/%Y')
    form.ReportDate  = smp.Sample_ReportDate.strftime('%m/%d/%Y')
    form.Species = smp.Report_Species
    form.Sequencer = smp.Report_Sequencer
    form.Method = smp.Report_Method
    form.Pipeline = smp.Report_Pipeline
    form.FinalResult = smp.Report_FinalResult
    form.AdditionalComment = smp.Report_AdditionalComment
    form.DoctorName = smp.Report_DoctorName
    form.ReportLab = smp.Report_ReportLab
    form.LabAddress = smp.Report_LabAddress

    if smp.Analysis_SpeciesPredName.lower() == 'mycobacterium tuberculosis':
        if(smp.Analysis_QcTotReadFastQ > 0)and (smp.Analysis_QcQ30ReadFastQ > 0) and (smp.Analysis_QcMapReadSpecies > 0) and (smp.Analysis_QcMapRateSpecies > 0)and (smp.Analysis_QcCoverageDeep > 0):
            form.QualityControl = 'Pass'
        else:
            form.QualityControl = 'Failed'
    else:
        if(smp.Analysis_QcTotReadFastQ > 0)and (smp.Analysis_QcQ30ReadFastQ > 0) and (smp.Analysis_QcMapReadSpecies > 0) and (smp.Analysis_QcMapRateSpecies > 0):
            form.QualityControl = 'Pass'
        elif(smp.Analysis_StepNo != 99):
            form.QualityControl = 'Not started'
        else:
            form.QualityControl = 'Failed'
            
    sql = []
    sql.append((and_(AnalysisTargetGeneDeletion.Sample_Id==sampleid, AnalysisTargetGeneDeletion.user_id==lv['userid'])))
    delGen = AnalysisTargetGeneDeletion.colunm_customfilter(session=Session,cols=AnalysisTargetGeneDeletion.gene, filter=sql).group_by2('gene').all()
    gd = []
    if delGen:
        for d in delGen:
            gd.append(d[0])
        
    if smp.Analysis_SpeciesPredName.lower() == 'mycobacterium tuberculosis':    # only Mycobacterium tuberculosis
        form.Spoligotype = smp.Report_Spligotype
        form.Lineage = smp.Report_Lineage
        
        tb = AnalysisResult
        sql = []
        sql.append((tb.Sample_Id==smp.id)) 
        sql.append((tb.user_id==lv['userid']))
        sql.append((or_(tb.INH.in_([1,2]), tb.RIF.in_([1,2]), tb.EMB.in_([1,2]), tb.PZA.in_([1,2]), tb.LFX.in_([1,2]), 
                        tb.MFX.in_([1,2]), tb.LZD.in_([1,2]), tb.BDQ.in_([1,2]), tb.CFZ.in_([1,2]), tb.DLM.in_([1,2]), 
                        tb.AMK.in_([1,2]), tb.CAP.in_([1,2]), tb.KAN.in_([1,2]), tb.STM.in_([1,2]),tb.ETO.in_([1,2]))))
        drg_alllist = AnalysisResult.customfilter(session=Session, filter=sql).order_by('-VarAlleleFreq').all()

        if drg_alllist: 
            for im in drg_alllist:
                form.AMKGene, form.AMKResult, form.AMKComment = dragGene2('   ',gd,in_range(im.AMK,1,2), im, form.AMKGene, form.AMKResult, form.AMKComment)
                form.BDQGene, form.BDQResult, form.BDQComment = dragGene2('   ',gd,in_range(im.BDQ,1,2), im, form.BDQGene, form.BDQResult, form.BDQComment)
                form.CAPGene, form.CAPResult, form.CAPComment = dragGene2('CAP',gd,in_range(im.CAP,1,2), im, form.CAPGene, form.CAPResult, form.CAPComment)
                form.CFZGene, form.CFZResult, form.CFZComment = dragGene2('   ',gd,in_range(im.CFZ,1,2), im, form.CFZGene, form.CFZResult, form.CFZComment)
                form.DLMGene, form.DLMResult, form.DLMComment = dragGene2('   ',gd,in_range(im.DLM,1,2), im, form.DLMGene, form.DLMResult, form.DLMComment)
                form.EMBGene, form.EMBResult, form.EMBComment = dragGene2('   ',gd,in_range(im.EMB,1,2), im, form.EMBGene, form.EMBResult, form.EMBComment)
                form.ETOGene, form.ETOResult, form.ETOComment = dragGene2('ETO',gd,in_range(im.ETO,1,2), im, form.ETOGene, form.ETOResult, form.ETOComment)
                form.INHGene, form.INHResult, form.INHComment = dragGene2('INH',gd,in_range(im.INH,1,2), im, form.INHGene, form.INHResult, form.INHComment)
                form.KANGene, form.KANResult, form.KANComment = dragGene2('   ',gd,in_range(im.KAN,1,2), im, form.KANGene, form.KANResult, form.KANComment)
                form.LFXGene, form.LFXResult, form.LFXComment = dragGene2('   ',gd,in_range(im.LFX,1,2), im, form.LFXGene, form.LFXResult, form.LFXComment)
                form.LZDGene, form.LZDResult, form.LZDComment = dragGene2('   ',gd,in_range(im.LZD,1,2), im, form.LZDGene, form.LZDResult, form.LZDComment)
                form.MFXGene, form.MFXResult, form.MFXComment = dragGene2('   ',gd,in_range(im.MFX,1,2), im, form.MFXGene, form.MFXResult, form.MFXComment)
                form.PZAGene, form.PZAResult, form.PZAComment = dragGene2('PZA',gd,in_range(im.PZA,1,2), im, form.PZAGene, form.PZAResult, form.PZAComment)
                form.RIFGene, form.RIFResult, form.RIFComment = dragGene2('   ',gd,in_range(im.RIF,1,2), im, form.RIFGene, form.RIFResult, form.RIFComment)
                form.STMGene, form.STMResult, form.STMComment = dragGene2('STM',gd,in_range(im.STM,1,2), im, form.STMGene, form.STMResult, form.STMComment)
        else:
            form.AMKGene, form.AMKResult, form.AMKComment = dragGene2('   ',gd,False, None, form.AMKGene, form.AMKResult, form.AMKComment)
            form.BDQGene, form.BDQResult, form.BDQComment = dragGene2('   ',gd,False, None, form.BDQGene, form.BDQResult, form.BDQComment)
            form.CAPGene, form.CAPResult, form.CAPComment = dragGene2('CAP',gd,False, None, form.CAPGene, form.CAPResult, form.CAPComment)
            form.CFZGene, form.CFZResult, form.CFZComment = dragGene2('   ',gd,False, None, form.CFZGene, form.CFZResult, form.CFZComment)
            form.DLMGene, form.DLMResult, form.DLMComment = dragGene2('   ',gd,False, None, form.DLMGene, form.DLMResult, form.DLMComment)
            form.EMBGene, form.EMBResult, form.EMBComment = dragGene2('   ',gd,False, None, form.EMBGene, form.EMBResult, form.EMBComment)
            form.ETOGene, form.ETOResult, form.ETOComment = dragGene2('ETO',gd,False, None, form.ETOGene, form.ETOResult, form.ETOComment)
            form.INHGene, form.INHResult, form.INHComment = dragGene2('INH',gd,False, None, form.INHGene, form.INHResult, form.INHComment)
            form.KANGene, form.KANResult, form.KANComment = dragGene2('   ',gd,False, None, form.KANGene, form.KANResult, form.KANComment)
            form.LFXGene, form.LFXResult, form.LFXComment = dragGene2('   ',gd,False, None, form.LFXGene, form.LFXResult, form.LFXComment)
            form.LZDGene, form.LZDResult, form.LZDComment = dragGene2('   ',gd,False, None, form.LZDGene, form.LZDResult, form.LZDComment)
            form.MFXGene, form.MFXResult, form.MFXComment = dragGene2('   ',gd,False, None, form.MFXGene, form.MFXResult, form.MFXComment)
            form.PZAGene, form.PZAResult, form.PZAComment = dragGene2('PZA',gd,False, None, form.PZAGene, form.PZAResult, form.PZAComment)
            form.RIFGene, form.RIFResult, form.RIFComment = dragGene2('   ',gd,False, None, form.RIFGene, form.RIFResult, form.RIFComment)
            form.STMGene, form.STMResult, form.STMComment = dragGene2('STM',gd,False, None, form.STMGene, form.STMResult, form.STMComment)

    else:
        form.Spoligotype = 'N/A'
        form.Lineage = 'N/A'


    sp = []
    ls = Species.filter(Sample_Id=smp.id,Stype=1,user_id=lv['userid'],map_rate__gte=0.1).order_by('-map_read').all()    # Only if map rate is more than 10%
    for item in ls:
        sp.append(item.Sname) 
            
    form.FinalResult = finalResultCheck(smp, form, sp)
   
    reportToPdf(sampleid,form)
    
    return templates.TemplateResponse("MycoReportForm.html", form.__dict__)
    
# start/stop
@router.post("/startstoplist", response_class=HTMLResponse)
async def datastartstoplist(request: Request, sample: Form_SampleId= Depends(Form_SampleId), Session: Session = Depends(db.session), pageno: int=1, sortid: str = '-id', search_name:str=''):
    """
    `Data start/stop`\n
    :param request:
    :return:
    """
    print('/Post:datalist,Cookie:',request.cookies, sample.sampleid)
    lv = checkLogin(request.cookies)
    if lv['level'] <= 0:
        return RedirectMainpage()
    
    for sid in sample.sampleid:
        s = SampleGroup.filter(session=Session, id=sid, user_id=lv['userid'])
        if s and s.first().id == int(sid):
            if s.first().Analysis_StepNo in [0]:    # fisrt -> start
                s.update(auto_commit=True, **{'Analysis_StepNo': 1})   
            elif s.first().Analysis_StepNo in [99,5]:   # finish,stop -> Restart
                s.update(auto_commit=True, **{'Analysis_StepNo': 2})   
            else:     # STOP
                s.update(auto_commit=True, **{'Analysis_StepNo': 5})   
        
    return RedirectResponse(url="/samples?pageno={0}&sortid={1}&search_name={2}".format(pageno, sortid, search_name), status_code=302)

# start/stop
@router.post("/startstop", response_class=HTMLResponse)
async def datastartstop(request: Request, sample: Form_SampleId= Depends(Form_SampleId), Session: Session = Depends(db.session)):
    """
    `Data start/stop`\n
    :param request:
    :return:
    """
    lv = checkLogin(request.cookies)
    if lv['level'] <= 0:
        return RedirectMainpage()
    
    if len(sample.sampleid) == 1:
        print('/Post:datalist,Cookie:',request.cookies, sample.sampleid)
        sid = sample.sampleid[0]

        s = SampleGroup.filter(session=Session, id=sid, user_id=lv['userid'])
        if s and s.first().id == int(sid):
            if s.first().Analysis_StepNo in [0]:    # fisrt -> start
                s.update(auto_commit=True, **{'Analysis_StepNo': 1})
                
                add = {}
                add['sample_id'] = sid
                add['user_id'] = lv['userid']
                add['message'] = 'Analysis start'
                SampleLog.create(session=Session, auto_commit=True, **add)
                    
            elif s.first().Analysis_StepNo in [99,5]:   # finish,stop -> Restart
                s.update(auto_commit=True, **{'Analysis_StepNo': 2})   
                add = {}
                add['sample_id'] = sid
                add['user_id'] = lv['userid']
                add['message'] = 'Analysis restart'
                SampleLog.create(session=Session, auto_commit=True, **add)
                
            else:     # STOP
                s.update(auto_commit=True, **{'Analysis_StepNo': 5})   
            
        return RedirectResponse(url="/samples/summary/{0}".format(sid), status_code=302)
    else:
        return RedirectResponse(url="/samples", status_code=302)


def bamTrim(sampleid, pos):
    psSt = ensure_range(pos-100000,1,4411532)    
    psEd = ensure_range(pos+100000,1,4411532)
    ss = TOOLS_PATH+'samtools-1.16.1/samtools view -bh {0}{1}_dup_removed.bam NC_000962.3:{2}-{3} > {0}{1}_dup_removed_pos.bam'.format(DATA_PATH,sampleid,psSt,psEd)
    try:        
        os.system(ss)
    except Exception as e:
        print('ERROR MSG : ',e)
        return False
    
    ss = TOOLS_PATH+'samtools-1.16.1/samtools index {0}{1}_dup_removed_pos.bam'.format(DATA_PATH,sampleid)
    try:        
        os.system(ss)
    except Exception as e:
        print('ERROR MSG : ',e)
        return False
    return True
        


@router.head("/igvview/{sampleid}", response_class=HTMLResponse)
@router.get("/igvview/{sampleid}", response_class=HTMLResponse)
async def get_igv(request: Request, sampleid : int, locus:int, locusmax:int=0, Session: Session = Depends(db.session)):
    """
    `IGV View`\n
    """
    lv = checkLogin(request.cookies)
    if lv['level'] <= 0:
        return RedirectMainpage()
    
    #--------- check id
    smp = SampleGroup.filter(id=sampleid, user_id=lv['userid']).first()
    
    if not smp:
        return JSONResponse(status_code=202, content=dict(msg="No data found."))
    if smp.Analysis_StepNo != 99:
        return JSONResponse(status_code=202, content=dict(msg="No data found."))
    

    bamTrim(sampleid, locus)
    
    if(locusmax==0):
        mn = locus-500
        mx = locus+500
    else:
        mn = locus-50
        mx = locusmax+50
    
    form = IgvViewForm(request)
    form.userid = EncToData(request.cookies['DsUsInfoKey'])
    form.sampleid = sampleid
    form.fastaurl = "/datafiles/ref/NC_000962.3.fasta"
    form.fastaindexurl = "/datafiles/ref/NC_000962.3.fasta.fai"
    form.cytobandurl = "/datafiles/ref/cytoBand.txt"
    form.refurl = "/datafiles/ref/MTB_H37Rv_Gene_Anno_NC_000962.3.bed"
    form.dataurl = "/datafiles/ref/{0}_dup_removed_pos.bam".format(sampleid)            
    form.dataurlindex = "/datafiles/ref/{0}_dup_removed_pos.bam.bai".format(sampleid)   
    form.datalocus = 'NC_000962.3:{0}-{1}'.format(format(ensure_range(mn, 1, 4411532),','), format(ensure_range(mx, 1, 4411532),','))

    return templates.TemplateResponse("igvview.html", form.__dict__)
 
 
def exportVariant(userid, sampleid, session):
    lt = [['Position','REF','ALT','Depth','Variant allele frequency', 'Variant type', 'Gene', 'Gene ID', 'Nucleotide change','Amino Acid change']]
    items = AnalysisResult.filter(session=session,Sample_Id=sampleid, user_id=userid).order_by('-VarAlleleFreq','Position').all()
    if len(items):
        for item in items:
            lt.append([str(item.Position),
                       item.Ref,
                       item.Alt,
                       str(item.Depth),
                       '{:.2f}'.format(item.VarAlleleFreq),
                       item.VarType,
                       item.Gene,
                       item.GeneID,
                       item.Necleotide,
                       item.AminoAcid])
    
    return lt


def exportRAV(userid, sampleid, session):
    lt = [['Position','REF','ALT','Depth','Variant allele frequency', 'Variant type', 'Gene', 'Gene ID', 'Nucleotide change','Amino Acid change','AMK','BDQ','CAP','CFZ','DLM','EMB','ETO','INH','KAN','LFX','LZD','MFX','PZA','RIF','STM','Overlap Level']]

    tb = AnalysisResult
    sql = []
    sql.append((tb.Sample_Id==sampleid))
    sql.append((tb.user_id==userid))
    sql.append((or_(tb.AMK>0, tb.BDQ>0, tb.CAP>0, tb.CFZ>0, tb.DLM>0,tb.EMB>0, tb.ETO>0,
               tb.INH>0, tb.KAN>0, tb.LFX>0, tb.LZD>0, tb.MFX>0, tb.PZA>0, tb.RIF>0, tb.STM>0)))
        
    items = AnalysisResult.customfilter(session=session,filter=sql).order_by('-VarAlleleFreq','Position').all()
    if len(items):
        for item in items:
            if item.OverlapLv == 1: ovl = 'Nucleotide'
            elif item.OverlapLv == 2: ovl = 'Amino acid'
            elif item.OverlapLv == 3: ovl = 'Both'
            else: ovl = ''
            lt.append([str(item.Position),
                        item.Ref,
                        item.Alt,
                        str(item.Depth),
                        '{:.2f}'.format(item.VarAlleleFreq),
                        item.VarType,
                        item.Gene,
                        item.GeneID,
                        item.Necleotide,
                        item.AminoAcid,
                        item.AMK if item.AMK>0 else '',
                        item.BDQ if item.BDQ>0 else '',
                        item.CAP if item.CAP>0 else '',
                        item.CFZ if item.CFZ>0 else '',
                        item.DLM if item.DLM>0 else '',
                        item.EMB if item.EMB>0 else '',
                        item.ETO if item.ETO>0 else '',
                        item.INH if item.INH>0 else '',
                        item.KAN if item.KAN>0 else '',
                        item.LFX if item.LFX>0 else '',
                        item.LZD if item.LZD>0 else '',
                        item.MFX if item.MFX>0 else '',
                        item.PZA if item.PZA>0 else '',
                        item.RIF if item.RIF>0 else '',
                        item.STM if item.STM>0 else '',
                        ovl
                       ])
    return lt

def exportSampleList(userid, searchname, session):
    ser = SampleGroup.Sample_DataID.like('%'+searchname+'%')
    usid = SampleGroup.user_id.__eq__(userid)
    
    rfile = {}
    rflt = Datafile.filter(session=session,user_id=userid).all()
    for m in rflt:
        rfile[str(m.id)] = m.filename

    if searchname == '':   # check sample name
        items = SampleGroup.customfilter(session=session, filter=[usid]).all()
    else:
        items = SampleGroup.customfilter(session=session, filter=[usid,ser]).all()

    # header list
    lt = [['Analysis ID','Sample ID','R1 file','R2 file','Quality','Species','Lineage','Spoligotype','Created time','Status']]
   
    for item in items:
        # find file name
        if str(item.Analysis_R1_Data_Id) in rfile.keys():
            r1 = rfile[str(item.Analysis_R1_Data_Id)]
        else:
            r1 = ''
        if str(item.Analysis_R2_Data_Id) in rfile.keys():
            r2 = rfile[str(item.Analysis_R2_Data_Id)]
        else:
            r2 = ''
                    
        try:
            s = item.created_at.strftime("%m/%d/%Y %H:%M")
        except Exception as e:
            # null check
            s = '01/01/2000 00:00'
            
        if item.Analysis_SpeciesPredName.lower() == 'mycobacterium tuberculosis':
            if(item.Analysis_QcTotReadFastQ > 0)and (item.Analysis_QcQ30ReadFastQ > 0) and (item.Analysis_QcMapReadSpecies > 0) and (item.Analysis_QcMapRateSpecies > 0)and (item.Analysis_QcCoverageDeep > 0):
                qc = 'Pass'
            else:
                qc = 'Failed'
        else:
            if(item.Analysis_QcTotReadFastQ > 0)and (item.Analysis_QcQ30ReadFastQ > 0) and (item.Analysis_QcMapReadSpecies > 0) and (item.Analysis_QcMapRateSpecies > 0):
                qc = 'Pass'
            elif(item.Analysis_StepNo != 99):
                qc = 'Not started'
            else:
                qc = 'Failed'            
            
        lt.append([item.id,item.Sample_DataID,r1,r2,qc,item.Report_Species,item.Report_Lineage,item.Report_Spligotype,s,stepnoToStr(item.Analysis_StepNo)])
        
    return lt


@router.post("/sampleExport", status_code=201, response_class=HTMLResponse)
async def post_sampleExprt(request: Request, exportdata: str= Form(''), sampleid: str= Form(''), sampledataid: str=Form(''), Session: Session = Depends(db.session)):
    """
    `Sample list Export Download`\n
    :param request:
    :param sampleid:
    :return:
    """
    
    print('/Get:Export sample Cookie:', request.cookies)
    lv = checkLogin(request.cookies)
    if lv['level'] <= 0:
        return RedirectMainpage()

    if(exportdata == '<VariantsExport>'):
        lt = exportVariant(lv['userid'], sampleid, Session)
        fn = 'VariantExport_{0}_{1}.xlsx'.format(sampleid,sampledataid)

    elif(exportdata == '<RAVExport>'):
        lt = exportRAV(lv['userid'], sampleid, Session)
        fn = 'RAVExport_{0}_{1}.xlsx'.format(sampleid,sampledataid)
    else:
        lt = exportSampleList(lv['userid'], exportdata, Session)
        fn = 'SampleExport.xlsx'
    
    if saveExcelFile(TEMP_PATH+fn, lt):
        return FileResponse(path=TEMP_PATH+fn, filename=fn)
   
