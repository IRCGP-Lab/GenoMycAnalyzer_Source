
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    func,
    Enum,
    Boolean,
    Float,
    ForeignKey,
)
from sqlalchemy.orm import Session, relationship, joinedload
from sqlalchemy import or_
from database.conn import Base, db
from datetime import datetime
from math import ceil
from common.consts import MAX_PAGE_ROW_COUNT
import pytz


class BaseMixin:
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now())
    updated_at = Column(DateTime, nullable=False,
                        default=datetime.now(), onupdate=datetime.now())

    def __init__(self):
        self._q = None
        self._session = None
        self.served = None

    def all_columns(self):
        return [c for c in self.__table__.columns if c.primary_key is False and c.name != "created_at"]

    def all_columns2(self):
        return [c for c in self.__table__.columns if c.primary_key is False]

    def __hash__(self):
        return hash(self.id)

    @classmethod
    def create(cls, session: Session, auto_commit=False, **kwargs):
        """
        테이블 데이터 적재 전용 함수
        :param session:
        :param auto_commit: 자동 커밋 여부
        :param kwargs: 적재 할 데이터
        :return:
        """
        obj = cls()
        for col in obj.all_columns2():
            col_name = col.name
            if col_name in kwargs:
                setattr(obj, col_name, kwargs.get(col_name))

        setattr(obj, 'created_at', datetime.now())
        setattr(obj, 'updated_at', datetime.now())
        session.add(obj)
        session.flush()
        if auto_commit:
            session.commit()
        return obj

    @classmethod
    def get(cls, session: Session = None, **kwargs):
        """
        Simply get a Row
        :param session:
        :param kwargs:
        :return:
        """
        sess = next(db.session()) if not session else session
        query = sess.query(cls)
        for key, val in kwargs.items():
            col = getattr(cls, key)
            query = query.filter(col == val)

        if query.count() > 1:
            raise Exception(
                "Only one row is supposed to be returned, but got more than one.")
        result = query.first()
        if not session:
            sess.close()
        return result

    @classmethod
    def filter(cls, session: Session = None, **kwargs):
        """
        Simply get a Row
        :param session:
        :param kwargs:
        :return:
        """
        cond = []
        for key, val in kwargs.items():
            key = key.split("__")
            if len(key) > 2:
                raise Exception("No 2 more dunders")
            col = getattr(cls, key[0])
            if len(key) == 1: cond.append((col == val))
            elif len(key) == 2 and key[1] == 'gt': cond.append((col > val))
            elif len(key) == 2 and key[1] == 'gte':cond.append((col >= val))
            elif len(key) == 2 and key[1] == 'lt': cond.append((col < val))
            elif len(key) == 2 and key[1] == 'lte':cond.append((col <= val))
            elif len(key) == 2 and key[1] == 'in': cond.append((col.in_(val)))

        obj = cls()
        if session:
            obj._session = session
            obj.served = True
        else:
            obj._session = next(db.session())
            obj.served = False
        query = obj._session.query(cls)
        query = query.filter(*cond)
        obj._q = query
        return obj

    @classmethod
    def customfilter(cls, session: Session = None, filter=[]):
        """
        Simply get a Row
        :param session:
        :param filter list:
        :return:
        """

        obj = cls()
        if session:
            obj._session = session
            obj.served = True
        else:
            obj._session = next(db.session())
            obj.served = False
        query = obj._session.query(cls)
        query = query.filter(*filter)
        obj._q = query
        return obj

    @classmethod
    def cls_attr(cls, col_name=None):
        if col_name:
            col = getattr(cls, col_name)
            return col
        else:
            return cls

    @classmethod
    def colunm_customfilter(cls, session: Session = None, cols=None, filter=[]):
        obj = cls()
        if session:
            obj._session = session
            obj.served = True
        else:
            obj._session = next(db.session())
            obj.served = False
        query = obj._session.query(cols)
        query = query.filter(*filter)
        obj._q = query
        return obj

    
    def customSql1(cls, session: Session = None, sql=''):   # join 1
        obj = cls()
        if session:
            obj._session = session
            obj.served = True
        else:
            obj._session = next(db.session())
            obj.served = False

        query = obj._session.query(cls).options(joinedload(SampleGroup.Analysis_R1_Data_Id))
        query = query.filter(*filter)
        query = query.join(Datafile.id)
        obj._q = query
        return obj

    def group_by2(self, *args: str):
        for col_name in args:
            col = self.cls_attr(col_name)
            self._q = self._q.group_by(col)
                    
            #results = self._q( WhoResult.db_name ).filter(WhoResult.user_id == 0).group_by( WhoResult.db_name)    
        return self
          


            
    
    def order_by(self, *args: str):
        for a in args:
            if a.startswith("-"):
                col_name = a[1:]
                is_asc = False
            else:
                col_name = a
                is_asc = True
            col = self.cls_attr(col_name)
            self._q = self._q.order_by(col.asc()) if is_asc else self._q.order_by(col.desc())
        return self

    def limit(self, *args: str):
        if len(args) == 1:
            self._q = self._q.limit(args[0])            # 상위 제한수
        elif len(args) == 2:
            self._q = self._q.slice(args[0], args[1])    # 범위 제한수[시작,종료]

        return self

    def pagecount(self, page_div_number: int = MAX_PAGE_ROW_COUNT):        # page 나눌 수
        result = ceil(self._q.count() / page_div_number)
        self.close()
        return result

    # 나눌수, page수 ( 가져올 page 범위 limit )
    def page(self, page_div_number: int = MAX_PAGE_ROW_COUNT, page_no: int = 0):
        st = (page_div_number * (page_no-1))
        ed = (page_div_number * page_no)
        self._q = self._q.slice(st, ed)    # 범위 제한수[시작,종료]

        return self

    def update(self, auto_commit: bool = False, **kwargs):
        qs = self._q.update(kwargs)
        get_id = self.id
        ret = None

        self._session.flush()
        if qs > 0:
            ret = self._q.first()
        if auto_commit:
            self._session.commit()
        return ret

    def first(self):
        result = self._q.first()
        self.close()
        return result

    def delete(self, auto_commit: bool = False):
        self._q.delete()
        if auto_commit:
            self._session.commit()

    def all(self):
        # print(self.served)
        result = self._q.all()
        self.close()
        return result

    def count(self):
        result = self._q.count()
        self.close()
        return result

    def close(self):
        if not self.served:
            self._session.close()
        else:
            self._session.flush()


class Users(Base, BaseMixin):       # USER
    __tablename__ = "users_tb"
    status = Column(Enum("active", "deleted", "blocked"), default="active")
    userid = Column(String(length=255), nullable=True, default="")
    pw = Column(String(length=255), nullable=True, default="")
    name = Column(String(length=255), nullable=True, default="")
    email = Column(String(length=255), nullable=True, default="")
    level = Column(Enum("manager", "user"), default="user")
    #keys = relationship("ApiKeys", back_populates="users")


class ApiKeys(Base, BaseMixin):     # KEY
    __tablename__ = "api_key_tb"
    access_key = Column(String(length=64), nullable=False,
                        index=True, default="")
    secret_key = Column(String(length=64), nullable=False, default="")
    user_memo = Column(String(length=40), nullable=True, default="")
    status = Column(Enum("active", "stopped", "deleted"), default="active")
    user_id = Column(Integer, ForeignKey("users_tb.id"),
                     nullable=False, default=0)
    #users = relationship("Users", back_populates="keys")


class Datafile(Base, BaseMixin):        # DATA FILE
    __tablename__ = "data_tb"
    filename = Column(String(length=255), nullable=True, default="")
    filesize = Column(Integer, nullable=True, default=0)
    user_id = Column(Integer, nullable=True, default=-1)
 

class SampleGroup(Base, BaseMixin):     # SAMPLE GROUP
    __tablename__ = "sample_tb"
    Analysis_R1_Data_Id = Column(Integer, nullable=False, default=0)
    Analysis_R2_Data_Id = Column(Integer, nullable=True, default=0)
    Analysis_StepNo = Column(Integer, nullable=True, default=0)
    Analysis_Step1Time = Column(DateTime, nullable=True)
    Analysis_Step2Time = Column(DateTime, nullable=True)
    Analysis_Step3Time = Column(DateTime, nullable=True)
    Analysis_Step4Time = Column(DateTime, nullable=True)
    Analysis_Step5Time = Column(DateTime, nullable=True)
    Analysis_RawFastQRead = Column(Integer, nullable=True, default=0)
    Analysis_RawFastQBase = Column(Integer, nullable=True, default=0)
    Analysis_RawFastQ30 = Column(Float, nullable=True, default=0)
    Analysis_TrimFastQRead = Column(Integer, nullable=True, default=0)
    Analysis_TrimFastQBase = Column(Integer, nullable=True, default=0)
    Analysis_TrimFastQ30 = Column(Float, nullable=True, default=0)
    Analysis_SpikeMapRead1 = Column(Integer, nullable=True, default=0)
    Analysis_SpikeMapRead2 = Column(Integer, nullable=True, default=0)
    Analysis_SpikeMapRead3 = Column(Integer, nullable=True, default=0)
    Analysis_SpeciesPredName = Column(
        String(length=200), nullable=True, default="")
    Analysis_SpeciesPredMapTot = Column(Integer, nullable=True, default=0)
    Analysis_SpeciesPredMapRead = Column(Integer, nullable=True, default=0)
    Analysis_SpeciesPredMapRate = Column(Float, nullable=True, default=0)
    Analysis_AlignHostGenomeRead = Column(Integer, nullable=True, default=0)
    Analysis_AlignDupRead = Column(Integer, nullable=True, default=0)
    Analysis_AlignDupRate = Column(Float, nullable=True, default=0)
    Analysis_AlignMapReadTot = Column(Integer, nullable=True, default=0)
    Analysis_AlignMapRateTot = Column(Float, nullable=True, default=0)
    Analysis_AlignReadLen = Column(Integer, nullable=True, default=0)
    Analysis_AlignInsert = Column(Float, nullable=True, default=0)
    Analysis_AlignBaseQuality = Column(Float, nullable=True, default=0)
    Analysis_AlignMapQuality = Column(Float, nullable=True, default=0)
    Analysis_AlignMapReadTarget = Column(Integer, nullable=True, default=0)
    Analysis_AlignMapRateTarget = Column(Float, nullable=True, default=0)
    Analysis_AlignCoverage = Column(Float, nullable=True, default=0)
    Analysis_Align1xCoverage = Column(Float, nullable=True, default=0)
    Analysis_Align50xCoverage = Column(Float, nullable=True, default=0)
    Analysis_Align100xCoverage = Column(Float, nullable=True, default=0)
    Analysis_QcTotReadFastQ = Column(Integer, nullable=True, default=0)
    Analysis_QcQ30ReadFastQ = Column(Integer, nullable=True, default=0)
    Analysis_QcAvgMapRead = Column(Integer, nullable=True, default=0)
    Analysis_QcMapReadSpecies = Column(Integer, nullable=True, default=0)
    Analysis_QcMapRateSpecies = Column(Integer, nullable=True, default=0)
    Analysis_QcCoverageDeep = Column(Integer, nullable=True, default=0)
    Sample_DataID = Column(String(length=200), nullable=True)
    Sample_PatientID = Column(String(length=200), nullable=True)
    Sample_PatientName = Column(String(length=200), nullable=True)
    Sample_Source = Column(String(length=200), nullable=True)
    Sample_CultureType = Column(String(length=200), nullable=True)
    Sample_RecvDate = Column(DateTime, nullable=True)
    Sample_LibPrepDate = Column(DateTime, nullable=True)
    Sample_SeqDate = Column(DateTime, nullable=True)
    Sample_ReportDate = Column(DateTime, nullable=True)
    Sample_LabTechnician = Column(
        String(length=200), nullable=True, default="")
    Sample_Contact = Column(String(length=400), nullable=True, default="")
    Report_Sequencer = Column(String(length=200), nullable=True, default="")
    Report_Method = Column(String(length=200), nullable=True, default="")
    Report_Pipeline = Column(String(length=200), nullable=True, default="")
    Report_Reference = Column(String(length=200), nullable=True, default="")
    Report_QualityControl = Column(
        String(length=200), nullable=True, default="")
    Report_Species = Column(String(length=200), nullable=True, default="")
    Report_Lineage = Column(String(length=200), nullable=True, default="")
    Report_Spligotype = Column(String(length=200), nullable=True, default="")
    Report_FinalResult = Column(String(length=200), nullable=True, default="")
    Report_AdditionalComment = Column(
        String(length=1000), nullable=True, default="")
    Report_DoctorName = Column(String(length=200), nullable=True, default="")
    Report_ReportLab = Column(String(length=200), nullable=True, default="")
    Report_LabAddress = Column(String(length=300), nullable=True, default="")
    user_id = Column(Integer, nullable=True, default=-1)


class AnalysisResult(Base, BaseMixin):      # Analysis Result (Drug)
    __tablename__ = "result_tb"
    Sample_Id = Column(Integer, nullable=True, default=0)
    Position = Column(Integer, nullable=True, default=0)
    Ref = Column(String(length=400), nullable=True, default="")
    Alt = Column(String(length=400), nullable=True, default="")
    Depth = Column(Integer, nullable=True, default=0)
    VarAlleleFreq = Column(Float, nullable=True, default=0)
    VarType = Column(String(length=200), nullable=True, default="")
    Gene = Column(String(length=200), nullable=True, default="")
    GeneID = Column(String(length=200), nullable=True, default="")
    Necleotide = Column(String(length=400), nullable=True, default="")
    AminoAcid = Column(String(length=400), nullable=True, default="")
    Tier = Column(Integer, nullable=True, default=0)
    AMK = Column(Integer, nullable=True, default=0)
    BDQ = Column(Integer, nullable=True, default=0)
    CAP = Column(Integer, nullable=True, default=0)
    CFZ = Column(Integer, nullable=True, default=0)
    DLM = Column(Integer, nullable=True, default=0)
    EMB = Column(Integer, nullable=True, default=0)
    ETO = Column(Integer, nullable=True, default=0)
    INH = Column(Integer, nullable=True, default=0)
    KAN = Column(Integer, nullable=True, default=0)
    LFX = Column(Integer, nullable=True, default=0)
    LZD = Column(Integer, nullable=True, default=0)
    MFX = Column(Integer, nullable=True, default=0)
    PZA = Column(Integer, nullable=True, default=0)
    RIF = Column(Integer, nullable=True, default=0)
    STM = Column(Integer, nullable=True, default=0)
    OverlapLv = Column(Integer, nullable=True, default=0)
    user_id = Column(Integer, nullable=True, default=-1)

class AnalysisTargetGeneDeletion(Base, BaseMixin):      # Analysis Target gene large deletion
    __tablename__ = "targetgenedeletion_tb"
    Sample_Id = Column(Integer, nullable=True, default=0)
    user_id = Column(Integer, nullable=True, default=-1)
    posmin = Column(Integer, nullable=True, default=0)
    posmax = Column(Integer, nullable=True, default=0)
    gene = Column(String(length=50), nullable=True, default="")


class Species(Base, BaseMixin):         # Analysis Species result
    __tablename__ = "species_tb"
    Sample_Id = Column(Integer, nullable=True, default=0)
    Stype = Column(Integer, nullable=True, default=0)
    Sname = Column(String(length=200), nullable=True, default="")
    map_read = Column(Integer, nullable=True, default=0)
    map_rate = Column(Float, nullable=True, default=0)
    user_id = Column(Integer, nullable=True, default=-1)


class WhoResult(Base, BaseMixin):       # WHO result
    __tablename__ = "who_tb"
    Gene = Column(String(length=200), nullable=True, default="")
    GeneID = Column(String(length=200), nullable=True, default="")
    StartPs = Column(Integer, nullable=True, default=0)
    EndPs = Column(Integer, nullable=True, default=0)
    Ref = Column(String(length=200), nullable=True, default="")
    Alt = Column(String(length=200), nullable=True, default="")
    VarType = Column(String(length=200), nullable=True, default="")
    Necleotide = Column(String(length=250), nullable=True, default="")
    AminoAcid = Column(String(length=250), nullable=True, default="")
    Tier = Column(Integer, nullable=True, default=0)
    AMK = Column(Integer, nullable=True, default=0)
    BDQ = Column(Integer, nullable=True, default=0)
    CAP = Column(Integer, nullable=True, default=0)
    CFZ = Column(Integer, nullable=True, default=0)
    DLM = Column(Integer, nullable=True, default=0)
    EMB = Column(Integer, nullable=True, default=0)
    ETO = Column(Integer, nullable=True, default=0)
    INH = Column(Integer, nullable=True, default=0)
    KAN = Column(Integer, nullable=True, default=0)
    LFX = Column(Integer, nullable=True, default=0)
    LZD = Column(Integer, nullable=True, default=0)
    MFX = Column(Integer, nullable=True, default=0)
    PZA = Column(Integer, nullable=True, default=0)
    RIF = Column(Integer, nullable=True, default=0)
    STM = Column(Integer, nullable=True, default=0)
    Note = Column(String(length=200), nullable=True, default="")
    Reference = Column(String(length=200), nullable=True, default="")
    Orderlev = Column(Integer, nullable=True, default=0)
    user_id = Column(Integer, nullable=True, default=0)
    db_name = Column(String(length=255), nullable=True, default="")

class SampleLog(Base, BaseMixin):       # Sample log
    __tablename__ = "samplelog_tb"
    sample_id = Column(Integer, nullable=True, default=0)
    user_id = Column(Integer, nullable=True, default=-1)
    message = Column(String(length=250), nullable=True, default="")


class SystemLog(Base, BaseMixin):       # System log
    __tablename__ = "systemlog_tb"
    user_id = Column(Integer, nullable=True, default=-1)
    message = Column(String(length=500), nullable=True, default="")


class AnalysisConfig(Base, BaseMixin):      # Analysis Configuration value
    __tablename__ = "config_tb"
    user_id = Column(Integer, nullable=True, default=-1)
    param = Column(String(length=100), nullable=True, default="")
    val = Column(String(length=100), nullable=True, default="")
