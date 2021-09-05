#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, BYTEA
from decouple import config

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

class Epoch(Base):
    __tablename__ = 'epochs'
    id = Column(String(100), primary_key=True)
    finalized = Column(Boolean)
    epoch_number = Column(Integer)
    start_block = Column(String(100))
    end_block = Column(String(100))
    producer_blocks = Column(Integer)
    all_blocks = Column(Integer)
    producer_blocks_ratio = Column(Float)

class Distribution(Base):
    __tablename__ = 'distribution'
    id = Column(String(100), primary_key=True)
    distribution_number = Column(Integer)
    distributor = Column(String(100))
    timestamp = Column(DateTime)
    merkle_root = Column(String(100))
    metadata_url = Column(String(100))
    epoch_number = Column(Integer)
    token_total = Column(String(100))

class DistributionBalance(Base):
    __tablename__ = 'distribution_balance'
    id = Column(Integer, primary_key=True)
    miner = Column(String(100))
    balance_index = Column(Integer)
    distribution_number = Column(Integer)
    amount = Column(String(100))
    epoch_number = Column(Integer)

PSQL_ENDPOINT = config('PSQL_ENDPOINT')
engine = create_engine(PSQL_ENDPOINT)
Base.metadata.create_all(engine)
