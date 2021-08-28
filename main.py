#!/usr/bin/env python
# -*- coding: utf-8 -*-

import polling2
import requests
import json
from web3 import Web3
import pandas as pd
from decouple import config

INFURA_ENDPOINT = config('INFURA_ENDPOINT')

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
            fromActiveProducer
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
    eden_blocks_df = eden_blocks_df.set_index('number')
    eden_blocks_df = eden_blocks_df.sort_index()
    eden_blocks_df.to_csv('/Users/yazkhoury/Desktop/Github/Flashbots/Eden/eden-scraper/eden.csv')

eden_block_call()
