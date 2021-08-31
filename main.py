#!/usr/bin/env python
# -*- coding: utf-8 -*-

import polling2
import requests
import json
from web3 import Web3
import pandas as pd
from decouple import config
from datetime import datetime
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import EdenBlock, Epoch, Base

INFURA_ENDPOINT = config('INFURA_ENDPOINT')

engine = create_engine('sqlite:///eden.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

def get_web3_provider():
    infura_endpoint = INFURA_ENDPOINT
    my_provider = Web3.HTTPProvider(infura_endpoint)
    w3 = Web3(my_provider)
    return w3

def get_latest_eth_block():
    eden_db_last_block = session.query(EdenBlock).filter(EdenBlock.block_number).order_by(desc(EdenBlock.block_number)).limit(1).all
    w3 = get_web3_provider()
    latest_eth_block = w3.eth.get_block('latest')['number']
    if latest_eth_block > eden_db_last_block:
        return latest_eth_block
    else:
        return None

query_dict = {
    'block': 'block.graphql',
    'epoch': 'epoch.graphql'
}

def fetch_query(query):
    query_file = query_dict.get(query)
    with open(query_file, 'r') as file:
        data = file.read()
        return data

def eden_block_call():
    last_block = 0
    last_block_current = get_latest_eth_block()
    if last_block_current is None:
        return
    eden_blocks_df = pd.DataFrame()
    session = DBSession()
    while True:
        query = fetch_query('block')
        print(last_block)
        variables = {"number_gte": last_block}
        url = 'https://api.thegraph.com/subgraphs/name/eden-network/governance'
        r = requests.post(url, json={'query': query, 'variables': variables})
        block_result = r.json()
        eden_blocks_df_temp = pd.DataFrame.from_dict(block_result['data']['blocks'])
        eden_blocks_df = eden_blocks_df.append(eden_blocks_df_temp)
        last_block = int(eden_blocks_df.iloc[-1]['number'])
        if last_block >= last_block_current:
            break
    eden_blocks_df = eden_blocks_df.drop_duplicates()
    logging.info('Eden Blocks Pulled To DataFrame')
    logging.info('Adding Eden Blocks To Database Now')
    for index, row in eden_blocks_df.iterrows():
        block_id_query = session.query(EdenBlock).filter(EdenBlock.id==row['id']) or None
        if block_id_query is None:
            eden_block_entry = EdenBlock(
                id = row['id'],
                author = row['author'],
                difficulty = row['difficulty'],
                gas_limit = row['gasLimit'],
                gas_used = row['gasUsed'],
                block_hash = row['hash'],
                block_number = row['number'],
                parent_hash = row['parentHash'],
                uncle_hash = row['unclesHash'],
                size = row['size'],
                state_root = row['stateRoot'],
                timestamp = datetime.fromtimestamp(int(row['timestamp'])),
                total_difficulty = row['totalDifficulty'],
                transactions_root = row['transactionsRoot'],
                receipts_root = row['receiptsRoot']
            )
            session.add(eden_block_entry)
            session.commit()
    logging.info('Eden Blocks Added To Database Now')

def eden_epoch_call():
    eden_epochs_df = pd.DataFrame()
    session = DBSession()
    query = fetch_query('epoch')
    url = 'https://api.thegraph.com/subgraphs/name/eden-network/governance'
    r = requests.post(url, json={'query': query})
    epoch_result = r.json()
    print(epoch_result)
    eden_epochs_df = pd.DataFrame.from_dict(epoch_result['data']['epoches'])
    logging.info('Eden Epochs Pulled To DataFrame')
    logging.info('Adding Eden Epochs To Database Now')
    for index, row in eden_epochs_df.iterrows():
        epoch_id_query = session.query(Epoch).filter(Epoch.id==row['id']).all() or None
        if epoch_id_query is None and row['finalized'] == True:
            epoch_entry = Epoch(
                id = row['id'],
                finalized = row['finalized'],
                start_block = row['startBlock']['id'],
                end_block = row['endBlock']['id'],
                producer_blocks = row['producerBlocks'],
                all_blocks = row['allBlocks'],
                producer_blocks_ratio = row['producerBlocksRatio']
            )
            session.add(epoch_entry)
            session.commit()

eden_epoch_call()
