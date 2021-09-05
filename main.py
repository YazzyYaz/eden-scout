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
from collections import defaultdict

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker

from models import EdenBlock, Epoch, Base, Distribution, DistributionBalance

INFURA_ENDPOINT = config('INFURA_ENDPOINT')
PSQL_ENDPOINT = config('PSQL_ENDPOINT')

engine = create_engine(PSQL_ENDPOINT)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


def query_to_dict(rset):
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)
    return result

def get_web3_provider():
    infura_endpoint = INFURA_ENDPOINT
    my_provider = Web3.HTTPProvider(infura_endpoint)
    w3 = Web3(my_provider)
    return w3

def get_latest_eth_block():
	eden_db_last_block = session.query(EdenBlock).filter(EdenBlock.block_number).order_by(desc(EdenBlock.block_number)).limit(1).all()
	if eden_db_last_block != []:
		eden_db_last_block = eden_db_last_block[0].block_number
	w3 = get_web3_provider()
	latest_eth_block = w3.eth.get_block('latest')['number']
	if eden_db_last_block == []:
		eden_db_last_block = 0
	if latest_eth_block > eden_db_last_block:
		return latest_eth_block
	else:
		return None

def get_latest_distribution_number():
    eden_db_last_number_query = session.query(Distribution).order_by(desc(Distribution.distribution_number)).limit(1).all()
    if eden_db_last_number_query != []:
        eden_last_number = eden_db_last_number_query[0].distribution_number
        return eden_last_number
    else:
        return 0

query_dict = {
    'block': 'block.graphql',
    'distribution': 'distribution.graphql',
    'epoch': 'epoch.graphql'
}

eden_governance_api = 'https://api.thegraph.com/subgraphs/name/eden-network/governance'
eden_distribution_api = 'https://api.thegraph.com/subgraphs/name/eden-network/distribution'
eden_network_api = 'https://api.thegraph.com/subgraphs/name/eden-network/network'


def ipfs_link_cleanup(raw_uri):
    final_ipfs_link = "https://ipfs.io/ipfs/" + raw_uri.split('//')[1]
    return final_ipfs_link

def graph_query_call(api, query, variables=None):
    request = requests.post(api, json={'query': query, 'variables': variables})
    if request.status_code == 200:
        return request.json()
    else:
        Exception('Query failed. return code is {}. {}'.format(request.status_code, query))

def fetch_query(query):
    query_file = query_dict.get(query)
    with open(query_file, 'r') as file:
        data = file.read()
        return data

def eden_block_call():
    last_block = 0
    last_block_current = get_latest_eth_block()
    eden_blocks_df = pd.DataFrame()
    while True:
        query = fetch_query('block')
        variables = {'number_gt': last_block}
        block_result = graph_query_call(eden_governance_api, query, variables)
        eden_blocks_df_temp = pd.DataFrame.from_dict(block_result['data']['blocks'])
        eden_blocks_df = eden_blocks_df.append(eden_blocks_df_temp)
        last_block = int(eden_blocks_df.iloc[-1]['number'])
        if last_block >= last_block_current:
            break
    eden_blocks_df = eden_blocks_df.drop_duplicates()
    logging.info('Eden Blocks Pulled To DataFrame')
    logging.info('Adding Eden Blocks To Database Now')
    for index, row in eden_blocks_df.iterrows():
        block_id_query = session.query(EdenBlock).filter(EdenBlock.id==row['id']).limit(1).all() or None
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
    query = fetch_query('epoch')
    epoch_result = graph_query_call(eden_governance_api, query)
    eden_epochs_df = pd.DataFrame.from_dict(epoch_result['data']['epoches'])
    logging.info('Eden Epochs Pulled To DataFrame')
    logging.info('Adding Eden Epochs To Database Now')
    for index, row in eden_epochs_df.iterrows():
        epoch_id_query = session.query(Epoch).filter(Epoch.id==row['id']).limit(1).all() or None
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
    logging.info('Epochs Added To Database Now')

def eden_distribution_call():
    eden_distribution = pd.DataFrame()
    session = DBSession()
    distribution_number = get_latest_distribution_number()
    if distribution_number is None:
        distribution_number = 0
    query = fetch_query('distribution')
    variables = {'number_gt': distribution_number}
    distribution_result = graph_query_call(eden_distribution_api, query, variables)
    distribution_df = pd.DataFrame.from_dict(distribution_result['data']['distributions'])
    distribution_df['final_metadata_url'] = distribution_df['metadataURI'].apply(lambda row: ipfs_link_cleanup(row) )
    logging.info('Eden Distribution Pulled To DataFrame')
    logging.info('Adding Eden Distribution To Database Now')
    for index, row in distribution_df.iterrows():
        distribution_id_query = session.query(Distribution).filter(Distribution.id==row['id']).all() or None
        if distribution_id_query is None:
            ipfs_json = requests.get(row['final_metadata_url']).json()
            distribution_entry = Distribution(
                id = row['id'],
                distribution_number = row['distributionNumber'],
                distributor = str(row['distributor']),
                timestamp = datetime.fromtimestamp(int(row['timestamp'])),
                merkle_root = row['merkleRoot'],
                metadata_url = row['final_metadata_url'],
                epoch_number = ipfs_json['epoch']
            )
            session.add(distribution_entry)
            session.commit()
            for key, value in ipfs_json['balances'].items():
                distribution_balance_entry = DistributionBalance(
                    miner = key,
                    balance_index = value['index'],
                    distribution_number = int(row['distributionNumber']),
                    amount = value['amount'],
                    epoch_number = ipfs_json['epoch']
                )
                session.add(distribution_balance_entry)
                session.commit()
    logging.info('Eden Distribution Added to the Database')

eden_block_call()
eden_epoch_call()
eden_distribution_call()
