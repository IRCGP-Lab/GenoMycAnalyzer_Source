from datetime import datetime
from enum import Enum
from typing import List

from pydantic import Field
from pydantic.main import BaseModel
from pydantic.networks import EmailStr, IPvAnyAddress
from fastapi import Request

# =========  token =========

class Token(BaseModel):
    userid:str = None
    logintime:datetime =0
    Authorization: str = None

# =========  USER =========


class UserRegister(BaseModel):
    userid: str = None
    name: str = None
    pw: str = None
    level: str = None
    logintime : datetime = 0
    registtime : datetime = 0


class UserLogin(BaseModel):
    email: str = None
    pw: str = None


class UserInfo(BaseModel):
    userid: str = None
    name: str = None
    level: str = None
    class Config:
        orm_mode = True

    
class UsersList(BaseModel):
    totcount : int
    totpage : int
    nowpage : int
    users : List = []
    class Config:
        orm_mode = True


class UserEdit(BaseModel):
    userid : str = None
    pw: str = None
    level: str = None

    class Config:
        orm_mode = True

# =========  ANALYSIS =========


class AnalysisDatalist(BaseModel):
    totcount : int
    totpage : int
    nowpage : int
    files : List = []

    class Config:
        orm_mode = True

class AnalysisSetSample(BaseModel):
    Analysis_R1_Data_Id: int
    Analysis_R2_Data_Id: int
    Sample_DataID: str = None
    Sample_PatientID: str = None
    Sample_PatientName: str = None
    Sample_Source: str = None
    Sample_CultureType: str = None
    Sample_RecvDate: datetime
    Sample_LibPrepDate: datetime
    Sample_SeqDate: datetime
    Sample_ReportDate: datetime
    Sample_LabTechnician: str = None
    Sample_Contact: str = None
    Report_AdditionalComment: str = None
    Report_DoctorName: str = None
    Report_ReportLab: str = None
    Report_LabAddress: str = None

    class Config:
        orm_mode = True

class AnalysisBatchSetSample(BaseModel):
    Analysis_R1_Data_Id: int
    Analysis_R2_Data_Id: int
    Sample_DataID: str = None
    Sample_PatientID: str = None
    Sample_PatientName: str = None
    Sample_Source: str = None
    Sample_CultureType: str = None
    Sample_RecvDate: datetime
    Sample_LibPrepDate: datetime
    Sample_SeqDate: datetime
    Sample_ReportDate: datetime
    Sample_LabTechnician: str = None
    Sample_Contact: str = None
    Analysis_Step1Time : datetime
    Analysis_Step2Time : datetime
    Analysis_Step3Time : datetime
    Analysis_Step4Time : datetime

    class Config:
        orm_mode = True
        
class AnalysisSetSampleFull(BaseModel):     # SAMPLE GROUP
    Analysis_R1_Data_Id: int
    Analysis_R2_Data_Id: int
    Analysis_StepNo: int
    Analysis_Step1Time: datetime
    Analysis_Step2Time: datetime
    Analysis_Step3Time: datetime
    Analysis_Step4Time: datetime
    Analysis_RawFastQRead: int
    Analysis_RawFastQBase: int
    Analysis_RawFastQ30: float
    Analysis_TrimFastQRead: int
    Analysis_TrimFastQBase: int
    Analysis_TrimFastQ30: float
    Analysis_SpikeMapRead1: int
    Analysis_SpikeMapRead2: int
    Analysis_SpikeMapRead3: int
    Analysis_SpeciesPredName: str = None
    Analysis_SpeciesPredMapTot: int
    Analysis_SpeciesPredMapRead: int
    Analysis_SpeciesPredMapRate: float
    Analysis_AlignHostGenomeRead: int
    Analysis_AlignDupRead: int
    Analysis_AlignDupRate: float
    Analysis_AlignMapReadTot: int
    Analysis_AlignMapRateTot: float
    Analysis_AlignReadLen: int
    Analysis_AlignInsert: float
    Analysis_AlignBaseQuality: float
    Analysis_AlignMapQuality: float
    Analysis_AlignMapReadTarget: int
    Analysis_AlignMapRateTarget: float
    Analysis_AlignCoverage: float
    Analysis_Align1xCoverage: float
    Analysis_Align50xCoverage: float
    Analysis_Align100xCoverage: float
    Analysis_QcTotReadFastQ: int
    Analysis_QcQ30ReadFastQ: int
    Analysis_QcAvgMapRead: int
    Analysis_QcMapReadSpecies: int
    Analysis_QcMapRateSpecies: int
    Analysis_QcCoverageDeep: int
    Sample_DataID: str = None
    Sample_PatientID: str = None
    Sample_PatientName: str = None
    Sample_Source: str = None
    Sample_CultureType: str = None
    Sample_RecvDate: datetime
    Sample_LibPrepDate: datetime
    Sample_SeqDate: datetime
    Sample_ReportDate: datetime
    Sample_LabTechnician: str = None
    Sample_Contact: str = None
    Report_Sequencer: str = None
    Report_Method: str = None
    Report_Pipeline: str = None
    Report_Reference: str = None
    Report_QualityControl: str = None
    Report_Species: str = None
    Report_Lineage: str = None
    Report_Spligotype: str = None
    Report_FinalResult: str = None
    Report_AdditionalComment: str = None
    Report_DoctorName: str = None
    Report_ReportLab: str = None
    Report_LabAddress: str = None

    class Config:
        orm_mode = True


class AnalysisGetSamplesList(BaseModel):
    totcount : int
    totpage : int
    nowpage : int
    samples : List = []

    class Config:
        orm_mode = True


class AnalysisGetSampleSummary(BaseModel):      # Summary
    id: int
    Sample_DataID: str = None
    PatientID: str = None
    R1_file: str = None
    R1_sz: str = None
    R2_file: str = None
    R2_sz: str = None
    StepNo: int
    Step1Time: datetime
    Step2Time: datetime
    Step3Time: datetime
    Step4Time: datetime
    Qc: str = None
    Mycobacterium: str = None
    Tuberculosis: str = None
    SNP: str = None
    Spoligotype: str = None
    AMK: int
    BDQ: int
    CAP: int
    CFZ: int
    DLM: int
    EMB: int
    ETO: int
    INH: int
    KAN: int
    LFX: int
    LZD: int
    MFX: int
    PZA: int
    RIF: int
    STM: int

    class Config:
        orm_mode = True


class AnalysisGetSampleStatistics(BaseModel):     # Statistics & QC
    id: int
    Analysis_RawFastQRead: int
    Analysis_RawFastQBase: int
    Analysis_RawFastQ30: float
    Analysis_TrimFastQRead: int
    Analysis_TrimFastQBase: int
    Analysis_TrimFastQ30: float
    Analysis_SpikeMapRead1: int
    Analysis_SpikeMapRead2: int
    Analysis_SpikeMapRead3: int
    Analysis_SpeciesPredName: str = None
    Analysis_SpeciesPredMapTot: int
    Analysis_SpeciesPredMapRead: int
    Analysis_SpeciesPredMapRate: float
    Analysis_AlignHostGenomeRead: int
    Analysis_AlignDupRead: int
    Analysis_AlignDupRate: float
    Analysis_AlignMapReadTot: int
    Analysis_AlignMapRateTot: float
    Analysis_AlignReadLen: int
    Analysis_AlignInsert: float
    Analysis_AlignBaseQuality: float
    Analysis_AlignMapQuality: float
    Analysis_AlignMapReadTarget: int
    Analysis_AlignMapRateTarget: float
    Analysis_AlignCoverage: float
    Analysis_Align1xCoverage: float
    Analysis_Align50xCoverage: float
    Analysis_Align100xCoverage: float
    Analysis_QcTotReadFastQ: int
    Analysis_QcQ30ReadFastQ: int
    Analysis_QcAvgMapRead: int
    Analysis_QcMapReadSpecies: int
    Analysis_QcMapRateSpecies: int
    Analysis_QcCoverageDeep: int
    Report_Lineage: str = None
    Species: List = []
    SubSpecies: List = []

    class Config:
        orm_mode = True




class AnalysisGetSampleVariants(BaseModel):     # Variants
    id: int
    Sample_Id: int
    Position: int
    Ref: str = None
    Alt: str = None
    Depth: int
    VarAlleleFreq: float
    VarType: str = None
    Gene: str = None
    GeneID: str = None
    Necleotide: str = None
    AminoAcid: str = None

    class Config:
        orm_mode = True


class AnalysisGetSampleStatistics2(BaseModel):     # Statistics & QC
    id: int
    a: int
    b: str = None
    c: List = {}
    d: List = {}

class AnalysisGetSampleRAV(BaseModel):     # RAV
    id: int
    Sample_Id: int
    Position: int
    Ref: str = None
    Alt: str = None
    Depth: int
    VarAlleleFreq: float
    VarType: str = None
    Gene: str = None
    GeneID: str = None
    Necleotide: str = None
    AminoAcid: str = None
    AMK :int
    BDQ :int
    CAP :int
    CFZ :int
    DLM :int
    EMB :int
    ETO :int
    INH :int
    KAN :int
    LFX :int
    LZD :int
    MFX :int
    PZA :int
    RIF :int
    STM :int
    OverlapLv:int
    
    class Config:
        orm_mode = True



class AnalysisGetSampleReport(BaseModel):     # Report
    id: int
    Sample_DataID: str = None
    Sample_PatientID: str = None
    Sample_PatientName: str = None
    Sample_Source: str = None
    Sample_CultureType: str = None
    Sample_RecvDate: datetime
    Sample_LibPrepDate: datetime
    Sample_SeqDate: datetime
    Sample_ReportDate: datetime
    Sample_LabTechnician: str = None
    Sample_Contact: str = None
    Report_Sequencer: str = None
    Report_Method: str = None
    Report_Pipeline: str = None
    Report_Reference: str = None
    Report_QualityControl: str = None
    Report_Species: str = None
    Report_Lineage: str = None
    Report_Spligotype: str = None
    Report_FinalResult: str = None
    Report_AdditionalComment: str = None
    Report_DoctorName: str = None
    Report_ReportLab: str = None
    Report_LabAddress: str = None
    DrugList: List = []

    class Config:
        orm_mode = True



# =========  ETC =========


class EmailRecipients(BaseModel):
    name: str
    email: str


class SendEmail(BaseModel):
    email_to: List[EmailRecipients] = None


class KakaoMsgBody(BaseModel):
    msg: str = None


class MessageOk(BaseModel):
    message: str = Field(default="OK")


class UserToken(BaseModel):
    id: int
    userid: str = None
    name: str = None

    class Config:
        orm_mode = True


class UserMe(BaseModel):
    id: int
    userid: str = None
    name: str = None

    class Config:
        orm_mode = True


class AddApiKey(BaseModel):
    user_memo: str = None

    class Config:
        orm_mode = True


class GetApiKeyList(AddApiKey):
    id: int = None
    access_key: str = None
    created_at: datetime = None


class GetApiKeys(GetApiKeyList):
    secret_key: str = None


class CreateAPIWhiteLists(BaseModel):
    ip_addr: str = None


class GetAPIWhiteLists(CreateAPIWhiteLists):
    id: int

    class Config:
        orm_mode = True
