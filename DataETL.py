import sqlite3
from datetime import time

import pandas


def EX2DB(filename, db_name, table_name, if_exists=None, db_index=False, index_col=None):
    if not isinstance(index_col, str):
        index_col = None
    if_exists = 'replace' if if_exists is None else if_exists
    with sqlite3.connect(db_name) as db:
        df = pandas.read_excel(filename, index_col=index_col)
        df.to_sql(table_name, db, if_exists=if_exists, index=db_index)
        db.commit()
    print("DB Created and data loaded successfully.")


def DB2DF(db_name, table_name, sym):
    with sqlite3.connect(db_name) as db:
        df = pandas.read_sql_query(f"select * from {table_name} where InstrumentIdentifier = '{sym}'", db)
    return df


def seg_data(df, start_h=9, start_m=15, end_h=15, end_m=30):
    start_time = time(start_h, start_m)
    end_time = time(end_h, end_m)
    dftouse = df.copy()
    dftouse['CreatedOn'] = pandas.to_datetime(dftouse['CreatedOn']).copy()
    filtered_df = dftouse[(dftouse['CreatedOn'].dt.time >= start_time) & (dftouse['CreatedOn'].dt.time <= end_time)]
    filtered_df.reset_index(inplace=True, drop=True)
    filtered_df.set_index('CreatedOn', inplace=True)
    return filtered_df



def change_df_tf(df, x_minutes=5):
    returning_df = df.resample(f'{x_minutes}T').agg({
        'OpenValue': 'first',
        'High': 'max',
        'Low': 'min',
        'CloseValue': 'last'
    }).ffill()
    return returning_df


def bb(df, window=20, std=1):
    curr_df = pandas.DataFrame()
    curr_df['MB'] = df['CloseValue'].rolling(window).mean().copy()
    # print(curr_df['MB'])
    curr_df['std'] = (df['CloseValue'].rolling(window).std()) * std
    # print(curr_df['std'])
    curr_df['UB'] = curr_df['MB'] + curr_df['std']
    # print(curr_df['UB'])
    curr_df['LB'] = curr_df['MB'] - curr_df['std']
    curr_df.drop('std', axis=1, inplace=True)
    return curr_df
