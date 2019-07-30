"""
Conections to the database.
The database has an table from each ticker.
At the moment, we have two tickers that we are receiveing the stock market data,
"RFX20Mar19" and "I.RFX20", with ahre the future price (BI, OF, LA) with the volumes, the LAST date, and the index price, with the date and the Index Value.
"""
import sqlite3
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def rename_table(table):
    return table.replace(".","").replace("-","").replace('/','').replace(" ","").upper()

def make_connection(db='rofex.db'):
    """
    Create the connection with the file
    """
    try:
        con = sqlite3.connect(db)
        # con.execute("PRAGMA journal_mode=WAL")
        #journal_mode=Wal prevent the writers lock the database for the readeers
        return con
    except sqlite3.Error as e:
        logger.error(e)
        create_db(db)
    return None

def create_db(db_file='rofex.db',schema='schema.sql'):
    with open(schema) as fp:
        con = make_connection(db_file)
        cur = con.cursor()
        cur.executescript(fp.read())

def create_ticket_table(table, db='rofex.db',conn=None):
    table = rename_table(table)
    if conn == None:
        conn = make_connection(db)
    query = "CREATE TABLE {} (date TIMESTAMP,BI_price REAL,BI_size INTEGER,LA_date TIMESTAMP,LA_price REAL,LA_size INTEGER, OF_price REAL,OF_size INTEGER,OI_date TIMESTAMP,OI_size INTEGER,SE_date TIMESTAMP,SE_price REAL,TV REAL);".format(table)
    c = conn.cursor()
    c.execute(query)
    logger.debug("Table {} was created in the DB".format(table))
    

def read_table(table='RFX20Mar19', db = 'rofex.db',conn = None):
    """
    Read all the data in the table specified.
    The table name is equivalent to the ticker of the asset.
    """
    table = rename_table(table)
    if conn == None:
        conn = make_connection(db)
    query = "SELECT * FROM {}".format(table)
    df = pd.read_sql(query, conn)
    return df

def read_table_old(table='RFX20Mar19', db = 'rofex.db',conn = None):
    """
    Read all the data in the table specified.
    The table name is equivalent to the ticker of the asset.
    """
    table = rename_table(table)
    if conn == None:
        conn = make_connection(db)
    query = "SELECT * FROM {}".format(table)
    df = pd.read_sql(query, conn)
    return df
    
def export_entire_table(df, table, db='rofex.db', conn = None):
    """
    Export the entire DF to a table, replacing all the data if the table already axist
    """
    table = rename_table(table)
    if conn == None:
        conn = make_connection(db)
    if isinstance(df,dict):
        df = pd.DataFrame([df])
        try:
            df.set_index('date',inplace=True)
        except:
            logger.debug("No date column for set index in new table")
    df.to_sql(table, conn, if_exists='replace')
    conn.commit()
    logger.info("New Table generated")
    
def append_rows(df,table, db='rofex.db', conn = None):
    """
    Append information to the table in the database.
    The code will look the last value in the table, and append the new values from the dataFrame
    """
    table = rename_table(table)
    if conn == None:
        conn = make_connection(db)
        # c = conn.cursor()
    try:
        df.to_sql(table, conn, if_exists='append')
    except:
        logger.error("Problems exporting the new data to de database. a new table is created.")
        export_entire_table(df,table,db,conn)
    
def read_ticker(table,start_date='',db='rofex.db',conn=None):
    """
    Read the information of a ticker, from the specified start date.
    The start date must be a string with the format '%Y-%m-%d'
    """
    table = rename_table(table)
    # print(ticker)
    if conn == None:
        # print('Opening Connection with the DB')
        conn = make_connection(db)
    if start_date == '':
        query = 'SELECT * FROM "{}"'.format(table)
    else:
        query = 'SELECT * FROM "{}" WHERE date>date("{}")'.format(table, start_date)
    df = pd.read_sql(query, conn)
    df.set_index('date',inplace=True)
    # print(df.tail()) 
    return df
    
def read_last_price(table,db='rofex.db',conn=None):
    """
    Read the last price of a ticker, from the DB
    """
    table = rename_table(table)
    if conn == None:
        conn = make_connection(db)
    query = 'SELECT LA_price FROM "{}" ORDER BY date DESC LIMIT 1'.format(table)
    c = conn.cursor()
    value = c.execute(query).fetchone()
    return value[0]

def read_last_row(table,db='rofex.db',conn=None):
    """
    Read the last price of a ticker, from the DB
    """
    table = rename_table(table)
    if conn == None:
        conn = make_connection(db)
        conn.row_factory = sqlite3.Row
    try:
        query = "SELECT * FROM {} ORDER BY date DESC LIMIT 1".format('"'+table+'"')
        c = conn.cursor()
        row = c.execute(query).fetchone()
        try:
            row = dict(row)
            return row
        except:
            return None
    except:
        logger.debug("The table was not found, a new one is created")
        create_ticket_table(table, db=db)
        return None
    

def read_last_row_df(ticker,db='rofex.db',conn=None):
    """
    Read the last price of a ticker, from the DB
    """
    ticker = rename_table(ticker)
    if conn == None:
        conn = make_connection(db)
    query = 'SELECT * FROM "{}" ORDER BY date DESC LIMIT 1'.format(ticker)
    df = pd.read_sql(query, conn)
    return df

def sql_append(data,table,db='rofex.db',conn = None):
    """
    En vez de hacer un append desde pandas, lo hago directamente desde sqlite, con la lista de data, antes de pasarlo por dataframe.
    """
    table = rename_table(table)
    if conn == None:
        conn = make_connection(db)
    cur = conn.cursor()
    query = "SELECT name FROM sqlite_master WHERE type='table' AND name='{}'".format(table);
    table_sql = cur.execute(query).fetchone()
    if isinstance(table_sql,tuple):
        table_sql = table_sql[0]
        
    try:
        if table_sql != None:
            if table_sql.upper() == table.upper():
                columns = ', '.join(data.keys())
                placeholders = ':'+', :'.join(data.keys())
                query = 'INSERT INTO %s (%s) VALUES (%s)' % (table,columns, placeholders)
                cur.execute(query, data)
                conn.commit()
            else:
                export_entire_table(data,table,db,conn)
        else:
            export_entire_table(data,table,db,conn)
    except:
        logger.exception("Missing the value due to error in sql_append: Table:{}; data:{}".format(table, data))

def read_all_tickers(db='rofex.db',conn=None):
    if conn == None:
        conn = make_connection(db)
    cur = conn.cursor()
    query = "SELECT name FROM sqlite_master WHERE type='table'";
    tickers = cur.execute(query).fetchall()
    ticks = []
    for t in tickers:
        ticks.append(t[0])
    return ticks

   
def read_orders(ticker, start_date='', db='rofex.db', conn=None):
    """
    Read the filled orders of a ticker, from the specified start date.
    The start date must be a string with the format '%Y-%m-%d'
    """
    
    if conn == None:
        conn = make_connection(db)
    if start_date == '':
        query = "SELECT date, avgPx, cumQty, side FROM ORDERREPORT WHERE instrumentId_symbol LIKE '{}' and STATUS = 'FILLED'".format(ticker)
    else:
        query = "SELECT date, avgPx, cumQty, side FROM ORDERREPORT WHERE instrumentId_symbol LIKE '{}' and STATUS = 'FILLED' and date>date('{}')".format(ticker, start_date)
    df = pd.read_sql(query, conn)
    #df.set_index('date',inplace=True)
    #print(df) 
    return df

if __name__ == '__main__':
    create_ticket_table("test",'../remarkets.db')