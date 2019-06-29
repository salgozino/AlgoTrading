import pandas as pd
from datetime import datetime

"""
Issues:
    * Importantes:
        
    * Mejoras:
    
"""

def getOHLC(df,column_name_price = 'LA_price', column_name_size = 'LA_size',period='1Min'):

    try:
        df.drop_duplicates(subset='date_LA', keep='first', inplace=True)
    except:
        pass
    if 'date_LA' in df.columns.names:
        df.set_index('date_LA', inplace=True)
        df.index.names = ['date']
    
    df.index = pd.to_datetime(df.index)
    ohlc = df[column_name_price].resample(period).ohlc()
    try:
        vol  = df[column_name_size].resample(period).sum()

        ohlcv = pd.concat([ohlc, vol], axis=1, join_axes=[ohlc.index])
        ohlcv.rename(columns={column_name_size:'volume'}, inplace=True)
        return ohlcv
    except:
        return ohlc
    
    
def total_returns(df, start_date = datetime.today(), end_date = datetime.now(), column_name = 'close'):
    """
    Determinación de los retornos de una inversión, entre fecha inicial y fecha final. Para la columna especificada
    Se debe ingresar con:
        df = dataframe, donde su index debe ser en formate fecha.
        start_date = fecha de inicio de posición, en formate datetime. Si no es especificada, se considera la primera hora del día de hoy
        end_date = fecha de fin de posición, en formato datetime. Si no es especificada se asigna el momento actual
        column_name = Columna sobre el cual calcular el retorno, normalmente, columna close.
    """ 
    returns = df[column_name].diff().copy()
    returns.fillna(0, inplace=True)
    returns.sort_index(inplace=True)
    returns.truncate(before=end_date, after=start_date)
    return returns
    
def pct_returns(df,start_date = datetime.today(), end_date = datetime.now(), column_name = 'close'):
    """
    Determinación de los retornos porcentuales de una inversión, entre fecha inicial y fecha final. Para la columna especificada
    Se debe ingresar con:
        df = dataframe, donde su index debe ser en formate fecha.
        start_date = fecha de inicio de posición, en formate datetime. Si no es especificada, se considera la primera hora del día de hoy
        end_date = fecha de fin de posición, en formato datetime. Si no es especificada se asigna el momento actual
        column_name = Columna sobre el cual calcular el retorno, normalmente, columna close.
    """
    returns = df[column_name].pct_change(1)
    returns.fillna(0, inplace=True)
    returns.sort_index(inplace=True)
    returns.truncate(before=end_date, after=start_date)
    return returns
    
if __name__ == '__main__':
    import pandas as pd
    from CSVtools import *
    df = read_csvData('TestData.csv')
    # print(df.tail())
    ohlc = getOHLC(df)
    # print(ohlc.taisl())
    returns = total_returns(ohlc)
    print(returns)
    print('Total Returns: ', returns.sum())
    pct_returns = pct_returns(ohlc)
    print(pct_returns)
    print('Total Returns, %: ', pct_returns.sum()*100)
    