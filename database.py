__author__ = 'willi'

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

Base = declarative_base()

class Comparison(Base):
    __tablename__ = 'comparisons'
    id = Column(Integer, primary_key=True)

    http_url = Column(String)
    https_url = Column(String)

    similarityvalue1 = Column(Float)
    similarityvalue2 = Column(Float)

    http_url_id = Column(Integer)
    https_url_id = Column(Integer)

    rank = Column(Integer)

    code = Column(String)


class Result(Base):
    __tablename__ = 'results'
    id = Column(Integer, primary_key=True)

    uid = Column(String)
    ip = Column(String)
    useragent = Column(String)

    req_time = Column(DateTime)
    res_time = Column(DateTime)

    validity = Column(Boolean)
    reason = Column(String)
    reason_changed = Column(Boolean)

    matnr = Column(String)

    comparison_id = Column(Integer, ForeignKey("comparisons.id"))
    comparison = relationship("Comparison", backref=backref("results"))

class Redirect(Base):
    __tablename__ = 'redirects'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)

    url = Column(String)
    code = Column(Integer)
    redirect = Column(String)