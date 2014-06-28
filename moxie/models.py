from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (Table, Column, ForeignKey, UniqueConstraint,
                        Integer, String, DateTime, Boolean, MetaData,
                        Interval, DateTime)

metadata = MetaData()
Base = declarative_base(metadata=metadata)


class Job(Base):
    __tablename__ = 'job'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)
    description = Column(String(255))
    command = Column(String(255))
    image = Column(String(255))
    scheduled = Column(DateTime)
    interval = Column(Interval)
    active = Column(Boolean)

    maintainer_id = Column(Integer, ForeignKey('maintainer.id'))
    maintainer = relationship(
        "Maintainer",
        foreign_keys=[maintainer_id],
        backref='jobs'
    )


class Maintainer(Base):
    __tablename__ = 'maintainer'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    email = Column(String(255), unique=True)


class Run(Base):
    __tablename__ = 'run'
    id = Column(Integer, primary_key=True)
    failed = Column(Boolean)
    job_id = Column(Integer, ForeignKey('job.id'))
    job = relationship("Job", foreign_keys=[job_id], backref='runs')


class JobEnv(Base):
    __tablename__ = 'job_env'
    id = Column(Integer, primary_key=True)

    job_id = Column(Integer, ForeignKey('job.id'))
    job = relationship("Job", foreign_keys=[job_id], backref='env')

    key = Column(String(255))
    value = Column(String(255))
