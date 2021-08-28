#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class EdenBlock(Base):
    __tablename__ = 'eden_block'
    id = Column(String(100), primary_key=True)
    author = Column(String(100))
    difficulty = Column(Integer)
    gas_limit = Column(Integer)
    gas_used = Column(Integer)
    block_hash = Column(String(100))
    block_number = Column(Integer)
    from_active_producer = Column(Boolean)
    parent_hash = Column(String(100))
    uncle_hash = Column(String(100))
    size = Column(Integer)
    state_root = Column(String(100))
    timestamp = Column(DateTime)
    total_difficulty = Column(Integer)
    transactions_root = Column(String(100))
    receipts_root = Column(String(100))

engine = create_engine('sqlite:///eden.db')
Base.metadata.create_all(engine)
