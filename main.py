#!/usr/bin/env python
# -*- coding: utf-8 -*-

import polling2
import requests
import json
from web3 import Web3
import pandas as pd
from decouple import config
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import EdenBlock, Base

INFURA_ENDPOINT = config('INFURA_ENDPOINT')

engine = create_engine('sqlite:///eden.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

def get_latest_eth_block():
    infura_endpoint = INFURA_ENDPOINT
    my_provider = Web3.HTTPProvider(infura_endpoint)
    w3 = Web3(my_provider)
    block = w3.eth.get_block('latest')
    return block['number']

def eden_block_call():
    last_block = 0
    last_block_current = get_latest_eth_block()
    eden_blocks_df = pd.DataFrame()
    session = DBSession()
    while True:
        query = """
        query MyQuery($number_gte: BigInt!) {
          blocks(first:1000, where: {fromActiveProducer: true, number_gt: $number_gte}, orderBy: number, orderDirection: asc) {
            author
            difficulty
            gasLimit
            gasUsed
            hash
            id
            parentHash
            receiptsRoot
            size
            stateRoot
            timestamp
            unclesHash
            transactionsRoot
            totalDifficulty
            number
          }
        }
        """
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
    #eden_blocks_df = eden_blocks_df.set_index('number')
    #eden_blocks_df = eden_blocks_df.sort_index()
    for index, row in eden_blocks_df.iterrows():
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
    eden_blocks_df.to_csv('/Users/yazkhoury/Desktop/Github/Flashbots/Eden/eden-scraper/eden.csv')

eden_block_call()
