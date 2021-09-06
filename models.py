#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from sqlalchemy import Column, ForeignKey, BigInteger, String, Boolean, DateTime, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, BYTEA
from decouple import config

Base = declarative_base()

class EdenBlock(Base):
    __tablename__ = 'eden_block'
    block_number = Column(BigInteger, primary_key=True)
    id = Column(String(100))
    author = Column(String(100))
    difficulty = Column(String(100))
    gas_limit = Column(BigInteger)
    gas_used = Column(BigInteger)
    block_hash = Column(String(100))
    from_active_producer = Column(Boolean)
    parent_hash = Column(String(100))
    uncle_hash = Column(String(100))
    size = Column(BigInteger)
    state_root = Column(String(100))
    timestamp = Column(DateTime)
    total_difficulty = Column(String(100))
    transactions_root = Column(String(100))
    receipts_root = Column(String(100))

class Epoch(Base):
    __tablename__ = 'epochs'
    id = Column(String(100), primary_key=True)
    finalized = Column(Boolean)
    epoch_number = Column(BigInteger)
    start_block = Column(String(100))
    end_block = Column(String(100))
    producer_blocks = Column(BigInteger)
    all_blocks = Column(BigInteger)
    producer_blocks_ratio = Column(Float)

class Distribution(Base):
    __tablename__ = 'distribution'
    id = Column(String(100), primary_key=True)
    distribution_number = Column(BigInteger)
    distributor = Column(String(100))
    timestamp = Column(DateTime)
    merkle_root = Column(String(100))
    metadata_url = Column(String(100))
    epoch_number = Column(BigInteger)
    token_total = Column(String(100))

class DistributionBalance(Base):
    __tablename__ = 'distribution_balance'
    id = Column(BigInteger, primary_key=True)
    miner = Column(String(100))
    balance_index = Column(BigInteger)
    distribution_number = Column(BigInteger)
    amount = Column(String(100))
    epoch_number = Column(BigInteger)

PSQL_ENDPOINT = config('PSQL_ENDPOINT')
engine = create_engine(PSQL_ENDPOINT)
Base.metadata.create_all(engine)
