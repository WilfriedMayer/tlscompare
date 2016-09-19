"""This file generates the DDL for a specific sqlalchemy engine (sqlite)"""

__author__ = 'willi'

from database import Base
from sqlalchemy import create_engine

def dump(sql, *multiparams, **params):
    print sql.compile(dialect=engine.dialect)

engine = create_engine('sqlite://', strategy='mock', executor=dump)
Base.metadata.create_all(engine, checkfirst=False)