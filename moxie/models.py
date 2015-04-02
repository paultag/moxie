#  Copyright (c) Paul R. Tagliamonte <tag@pault.ag>, 2015
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

from sqlalchemy.orm import relationship
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (Table, Column, ForeignKey, UniqueConstraint,
                        Integer, String, DateTime, Boolean, MetaData,
                        Interval, DateTime, Text)

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
    manual = Column(Boolean)
    tags = Column(postgresql.ARRAY(Text))

    trigger_id = Column(Integer, ForeignKey('job.id'))
    trigger = relationship("Job", foreign_keys=[trigger_id])

    env_id = Column(Integer, ForeignKey('env_set.id'))
    env = relationship(
        "EnvSet",
        foreign_keys=[env_id],
        backref='jobs'
    )

    volumes_id = Column(Integer, ForeignKey('volume_set.id'))
    volumes = relationship(
        "VolumeSet",
        foreign_keys=[volumes_id],
        backref='jobs'
    )

    link_id = Column(Integer, ForeignKey('link_set.id'))
    links = relationship(
        "LinkSet",
        foreign_keys=[link_id],
        backref='jobs'
    )

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


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    email = Column(String(255), unique=True)
    fingerprint = Column(String(255), unique=True)


class Run(Base):
    __tablename__ = 'run'
    id = Column(Integer, primary_key=True)
    failed = Column(Boolean)
    job_id = Column(Integer, ForeignKey('job.id'))
    job = relationship("Job", foreign_keys=[job_id], backref='runs')
    log = Column(Text)
    start_time = Column(DateTime)
    end_time = Column(DateTime)


class LinkSet(Base):
    __tablename__ = 'link_set'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)


class Link(Base):
    __tablename__ = 'link'
    id = Column(Integer, primary_key=True)

    link_set_id = Column(Integer, ForeignKey('link_set.id'))
    link_set = relationship("LinkSet", foreign_keys=[link_set_id], backref='links')

    remote = Column(String(255))
    alias = Column(String(255))


class EnvSet(Base):
    __tablename__ = 'env_set'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)


class VolumeSet(Base):
    __tablename__ = 'volume_set'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)


class Env(Base):
    __tablename__ = 'env'
    id = Column(Integer, primary_key=True)

    env_set_id = Column(Integer, ForeignKey('env_set.id'))
    env_set = relationship("EnvSet", foreign_keys=[env_set_id], backref='values')

    key = Column(String(255))
    value = Column(String(255))


class Volume(Base):
    __tablename__ = 'volume'
    id = Column(Integer, primary_key=True)

    volume_set_id = Column(Integer, ForeignKey('volume_set.id'))
    volume_set = relationship("VolumeSet", foreign_keys=[volume_set_id], backref='values')

    host = Column(String(255))
    container = Column(String(255))
