
import inspect
from typing import List, Type, Optional, Dict
from fastapi import Request, Form
from datetime import datetime, date
from pydantic import BaseModel
from pydantic.fields import ModelField


def form_body(cls):
    cls.__signature__ = cls.__signature__.replace(
        parameters=[
            arg.replace(default=Form(...))
            for arg in cls.__signature__.parameters.values()
        ]
    )
    return cls


class MainForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.userid: Optional[str]


class DatafilelistForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.userid:  str
        self.error_msg: Optional[str] = None
        self.totcount: Optional[int]
        self.totpage: Optional[int]
        self.nowpage: Optional[int]
        self.order_id: Optional[str] = None
        self.order_name: Optional[str] = None
        self.order_size: Optional[str] = None
        self.order_date: Optional[str] = None
        self.search_name: Optional[str] = None
        self.files: List = []
        self.page: Dict = {}

    async def load_data(self):
        form = await self.request.form()
        self.nowpage = form.get("pageno")


class SamplelistForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.userid:  str
        self.error_msg: Optional[str] = None
        self.totcount: Optional[int]
        self.totpage: Optional[int]
        self.nowpage: Optional[int]
        self.order_id: Optional[str] = None
        self.order_sampleid: Optional[str] = None
        self.order_r1name: Optional[str] = None
        self.order_r2name: Optional[str] = None
        self.order_date: Optional[str] = None
        self.order_status: Optional[str] = None
        self.search_name: Optional[str] = None
        self.export_name: Optional[str] = None
        self.samples: List = []
        self.page: Dict = {}
        self.filelist: List = []

    async def load_data(self):
        form = await self.request.form()
        self.nowpage = form.get("pageno")


class SampleSummaryForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.userid:  str
        self.SampleID: Optional[int] = None
        self.sampledataID: Optional[str] = None
        self.patientID: Optional[str] = None
        self.patientName: Optional[str] = None
        self.r1name: Optional[str] = None
        self.r2name: Optional[str] = None
        self.r1size: Optional[str] = None
        self.r2size: Optional[str] = None
        self.sampleSource: Optional[str] = None
        self.cultureType: Optional[str] = None
        self.recvDate: Optional[str] = None
        self.sequencer: Optional[str] = None
        self.method: Optional[str] = None
        self.pipeline: Optional[str] = None
        self.seqDate: Optional[str] = None
        self.labprepDate: Optional[str] = None
        self.reportDate: Optional[str] = None
        self.drName: Optional[str] = None
        self.reportLab: Optional[str] = None
        self.address: Optional[str] = None
        self.stepno: Optional[int] = None
        self.stepstr: Optional[str] = None
        self.stime1: Optional[str] = None
        self.stime2: Optional[str] = None
        self.stime3: Optional[str] = None
        self.stime4: Optional[str] = None
        self.stime5: Optional[str] = None
        self.Qcontrol: Optional[str] = None
        self.Mycobac: Optional[str] = None
        self.Lineage: Optional[str] = None
        self.Spoligotype:  Optional[str] = None
        self.dr_amk: int
        self.dr_bdq:  int
        self.dr_cap:  int
        self.dr_cfz:  int
        self.dr_dlm:  int
        self.dr_emb:  int
        self.dr_eto:  int
        self.dr_inh:  int
        self.dr_kan:  int
        self.dr_lfx:  int
        self.dr_lzd:  int
        self.dr_mfx:  int
        self.dr_pza:  int
        self.dr_rif:  int
        self.dr_stm:  int
        self.filelist: List = []
        self.timenow: Optional[str] = None


class SampleStatisticsForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.userid:  str
        self.SampleID: int
        self.ReadIntCtlOp: str
        self.Lineage: str
        self.Spoligotype: str
        self.RawFastQRead : str
        self.RawFastQBase : str
        self.RawFastQ30 : str
        self.TrimFastQRead : str
        self.TrimFastQBase : str
        self.TrimFastQ30 : str
        self.SpikeMapRead1 : str
        self.SpikeMapRead2 : str
        self.SpikeMapRead3 : str
        self.SpeciesPredName : str
        self.SpeciesPredMapTot : str
        self.SpeciesPredMapRead : str
        self.SpeciesPredMapRate : str
        self.AlignHostGenomeRead : str
        self.AlignDupRead : str
        self.AlignDupRate : str
        self.AlignMapReadTot : str
        self.AlignMapRateTot : str
        self.AlignReadLen : str
        self.AlignInsert : str
        self.AlignBaseQuality : str
        self.AlignMapQuality : str
        self.AlignMapReadTarget : str
        self.AlignMapRateTarget : str
        self.AlignCoverage : str
        self.Align1xCoverage : str
        self.Align50xCoverage : str
        self.Align100xCoverage : str
        self.QcTotReadFastQ : str
        self.QcQ30ReadFastQ : str
        self.QcAvgMapRead : str
        self.QcMapReadSpecies : str
        self.QcMapRateSpecies : str
        self.QcCoverageDeep : str
        self.species : List = []
        self.speciessub : List = []


class SampleTargetGeneDeletionFormForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.userid:  str
        self.SampleID: int
        self.Coveragedepth: int
        self.totcount: Optional[int]
        self.totpage: Optional[int]
        self.nowpage: Optional[int]
        self.page: Dict = {}
        self.reseultlt = List = []

class SampleVariantsRavForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.userid:  str
        self.SampleID: int
        self.SampledataID: str
        self.totcount: Optional[int]
        self.totpage: Optional[int]
        self.nowpage: Optional[int]
        self.ravfilter:  List = []
        self.page: Dict = {}
        self.reseultlt = List = []


class SampleReportForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.userid:  str
        self.SampleID: int
        self.DataID: str
        self.PatientID: str
        self.PatientName: str
        self.Source: str
        self.CultureType: str
        self.RecvDate: str
        self.LibPrepDate: str
        self.SeqDate: str
        self.ReportDate: str
        self.LabTechnician: str
        self.Contact: str
        self.QualityControl: str
        self.Species: str
        self.Lineage: str
        self.Spoligotype: str
        self.FinalResult: str
        self.AdditionalComment: str
        self.DoctorName: str
        self.ReportLab: str
        self.LabAddress: str
        self.AMK: list = []
        self.BDQ: list = []
        self.CAP: list = []
        self.CFZ: list = []
        self.DLM: list = []
        self.EMB: list = []
        self.ETO: list = []
        self.INH: list = []
        self.KAN: list = []
        self.LFX: list = []
        self.LZD: list = []
        self.MFX: list = []
        self.PZA: list = []
        self.RIF: list = []
        self.STM: list = []


class SampleReportDataForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.userid:  str = ''
        self.SampleID: int = 0
        self.DataID: str = ''
        self.PatientID: str = ''
        self.PatientName: str = ''
        self.Source: str = ''
        self.CultureType: str = ''
        self.RecvDate: str = ''
        self.LibPrepDate: str = ''
        self.SeqDate: str = ''
        self.ReportDate: str = ''
        self.Sequencer: str = ''
        self.Method: str = ''
        self.Pipeline: str = ''
        self.QualityControl: str = ''
        self.Species: str = ''
        self.Lineage: str = ''
        self.Spoligotype: str = ''
        self.FinalResult: str = ''
        self.AdditionalComment: str = ''
        self.DoctorName: str = ''
        self.ReportLab: str = ''
        self.LabAddress: str = ''
        '''
        self.AMKGene: str = ''
        self.BDQGene: str = ''
        self.CAPGene: str = ''
        self.CFZGene: str = ''
        self.DLMGene: str = ''
        self.EMBGene: str = ''
        self.ETOGene: str = ''
        self.INHGene: str = ''
        self.KANGene: str = ''
        self.LFXGene: str = ''
        self.LZDGene: str = ''
        self.MFXGene: str = ''
        self.PZAGene: str = ''
        self.RIFGene: str = ''
        self.STMGene: str = ''
        '''
        self.AMKGene: list = []
        self.BDQGene: list = []
        self.CAPGene: list = []
        self.CFZGene: list = []
        self.DLMGene: list = []
        self.EMBGene: list = []
        self.ETOGene: list = []
        self.INHGene: list = []
        self.KANGene: list = []
        self.LFXGene: list = []
        self.LZDGene: list = []
        self.MFXGene: list = []
        self.PZAGene: list = []
        self.RIFGene: list = []
        self.STMGene: list = []
        self.AMKResult: str = ''
        self.BDQResult: str = ''
        self.CAPResult: str = ''
        self.CFZResult: str = ''
        self.DLMResult: str = ''
        self.EMBResult: str = ''
        self.ETOResult: str = ''
        self.INHResult: str = ''
        self.KANResult: str = ''
        self.LFXResult: str = ''
        self.LZDResult: str = ''
        self.MFXResult: str = ''
        self.PZAResult: str = ''
        self.RIFResult: str = ''
        self.STMResult: str = ''
        self.AMKComment: str = ''
        self.BDQComment: str = ''
        self.CAPComment: str = ''
        self.CFZComment: str = ''
        self.DLMComment: str = ''
        self.EMBComment: str = ''
        self.ETOComment: str = ''
        self.INHComment: str = ''
        self.KANComment: str = ''
        self.LFXComment: str = ''
        self.LZDComment: str = ''
        self.MFXComment: str = ''
        self.PZAComment: str = ''
        self.RIFComment: str = ''
        self.STMComment: str = ''


class aaaform:
    def __init__(self, request: Request):
        self.request: Request = request
        self.PATIENTID:  str


class IgvViewForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.userid:  str
        self.sampleid: str
        self.fastaurl: str
        self.fastaindexurl: str
        self.cytobandurl: str
        self.refurl: str
        self.dataurl: str
        self.dataurlindex: str
        self.datalocus: str


class CircosImgForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.userid:  str
        self.CircosFile: str


class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.useremail: str = ''
        self.ErrorMsg: str = ''


class RepasswordForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.userid: str = ''
        self.Repwkey: str
        self.ErrorMsg: str


class RegisterForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.useremail: str = ''
        self.ErrorMsg: str = ''


class AnalysisConfigForm:
    def __init__(self, request: Request):
        self.configdict: dict = {}
        
class AnalysisUserChartForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.Totusers: str
        self.TotProcessing: str
        self.Years: list = []
        self.YSelect: int
        self.Months: list = []


@form_body
class Form_SampleId(BaseModel):
    sampleid:  List = []


@form_body
class Form_SampleAddSet(BaseModel):
    AnalysisID: Optional[str] = None
    RecvDate: Optional[str] = None
    SeqDate: Optional[str] = None
    LibPrepDate: Optional[str] = None
    Analysis_R1name: Optional[str] = None
    Analysis_R2name: Optional[str] = None
    SampleDataID: str
    PatientID: str
    PatientName: Optional[str] = None


@form_body
class Form_SampleEditSet(BaseModel):
    AnalysisID: Optional[str] = None
    SampleDataID: Optional[str] = None
    PatientID: Optional[str] = None
    PatientName: Optional[str] = None
    SampleSource: Optional[str] = None
    CultureType: Optional[str] = None
    Sequencer: Optional[str] = None
    Method: Optional[str] = None
    Pipeline: Optional[str] = None
    RecvDate: Optional[str] = None
    LibPrepDate: Optional[str] = None
    SeqDate: Optional[str] = None
    ReportDate: Optional[str] = None
    Analysis_R1name: Optional[str] = None
    Analysis_R2name: Optional[str] = None
    DrName: Optional[str] = None
    ReportLab: Optional[str] = None
    Address: Optional[str] = None

@form_body
class Form_CommentEditSet(BaseModel):
    AnalysisID: Optional[str] = None
    AddtionalComment: Optional[str] = None


@form_body
class Form_Login(BaseModel):
    Email: str
    EmailPW: str


@form_body
class Form_Repassword(BaseModel):
    Repwkey: str
    EmailPW: str
    confirm_EmailPW: str


@form_body
class Form_Register(BaseModel):
    Email: str = ''
    EmailPW: str = ''
    confirm_EmailPW: str = ''

@form_body
class Form_ExportData(BaseModel):
    exportdata: Optional[str] = None

@form_body
class Form_Config(BaseModel):
    refDB: str = ''
    edKrakenQuality:  str = ''
    edKrakengroups: str = ''
    edBraken_r: str = ''
    #cbBraken_l: str = ''
    cbBcftoolsQc: str = ''
    cbBcftoolsQcval: str = ''
    cbBcftoolsDp: str = ''
    cbBcftoolsDpval: str = ''
    edSnpeff: str = ''
    edVaf_dp: str = ''
