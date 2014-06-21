from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (Table, Column, ForeignKey, UniqueConstraint,
                        Integer, String, DateTime, Boolean, MetaData)

metadata = MetaData()
Base = declarative_base(metadata=metadata)


class Job(Base):
    __tablename__ = 'job'
    id = Column(String(255), primary_key=True)
    description = Column(String(255))
    # maintainer
    # old runs
