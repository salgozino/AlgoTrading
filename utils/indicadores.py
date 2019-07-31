import pandas as pd
import numpy as np
from datetime import datetime
import logging
from utils.finance_tools import getOHLC

"""
Issues:
    * Mejoras: 
        - Agregar estimador estocastico
"""
def MACD(df,columna,short_window=12,long_window=26,smooth_signal=9):
    """
    Calculo del MACD, histograma y señal del precio de cierre
    input:
        * dataframe de pandas con columna de precio de cierre llamada "close"
    outputs dentro del mismo dataframe:
        * MACD
        * Signal
        * hist
    """
    df2 = df.copy()
    MACD = pd.DataFrame()
    df2['EMA{}'.format(short_window)] = df[columna].ewm(span=short_window).mean()
    df2['EMA{}'.format(short_window)].fillna(df2['EMA{}'.format(short_window)], inplace=True)
    df2['EMA{}'.format(long_window)] = df[columna].ewm(span=long_window).mean()
    df2['EMA{}'.format(long_window)].fillna(df2['EMA{}'.format(long_window)], inplace=True)
    MACD['MACD'] = df2['EMA{}'.format(short_window)] - df2['EMA{}'.format(long_window)]
    MACD['MACD_signal'] = MACD['MACD'].rolling(window=smooth_signal,min_periods=1).mean()
    MACD['MACD_diff'] = MACD['MACD'] - MACD['MACD_signal']
    return MACD
    
def RSI(df,columna,window_length=14):
    """
    Compute the RSI indicator (relative strenght index) from the price_close column
    window_length recommended = 14
    """
    RSI = pd.DataFrame(index = df.index)
    

    # Get rid of the first row, which is NaN since it did not have a previous 
    # row to calculate the differences
    delta = df[columna].diff()
    delta = delta[1:] 

    # Make the positive gains (up) and negative gains (down) Series
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0

    roll_up1 = up.ewm(window_length,min_periods=window_length).mean()
    roll_down1 = down.abs().ewm(window_length,min_periods=window_length).mean()

    # Calculate the RSI based on EWMA
    RSI['EWMA'] = 100.0 - (100.0 / (1.0 + roll_up1 / roll_down1))
    
    
    # Calculate the SMA
    roll_up2 = up.rolling(window=window_length,min_periods=window_length).mean()
    roll_down2 = down.abs().rolling(window=window_length,min_periods=window_length).mean()

    # Calculate the RSI based on SMA
    RSI['SMA'] = 100.0 - (100.0 / (1.0 + roll_up2 / roll_down2))
    
    # Completo los valores NaN con el primer valor
    RSI.fillna(method='ffill', inplace=True)
    
    return RSI

def puntos_pivot(ohlc):
    """
    P = (H + L + C)/3
    Nivel de Pivot = (Anterior High + Anterior Low + Anterior Close) / 3
    """
    puntos_pivot = (ohlc.high.shift(1) + ohlc.low.shift(1) + ohlc.close.shift(1)) / 3 
    return puntos_pivot

def tasa_implicita_online(price_spot,price_futuro,fecha_hoy=datetime.today(),fecha_vto=datetime(2019,datetime.today().month,28,23,59)):
    """
    Determino la tasa implicita de un unico valor
    """
    try:
        base = price_futuro - price_spot
        # print("Base",base)
        dias_vto = (fecha_vto - fecha_hoy).days
        dias_vto = 1 if dias_vto == 0 else dias_vto
        # print("Days",dias_vto)
        tasa = base/price_spot * 365/(dias_vto)
        print("Tasa: ",tasa)
        return tasa
    except:
        logging.exception("Error in the tasa_implicita_online indicator")

def tasa_implicita(df_futuro,df_spot,fecha_vto):
    """
    Determinación de la tasa implícita al día del vencimiento
    del futuro, considerando el precio del spot
    inputs:
        Cotización del Futuro (pandas series)
        Precio del Spot (pandas series)
        Fecha del día (datetime)
        Fecha del Vto (datetime)
    """

    ohlc_stock = getOHLC(df_futuro)
    ohlc_spot = getOHLC(df_spot)
    
    ohlc_stock.rename(columns={'close':'close_LA'}, inplace=True)
    ohlc_spot.rename(columns={'close':'close_IV'}, inplace=True)
    
    ohlc_stock.drop(['open','high','low'], axis = 1, inplace=True)
    ohlc_spot.drop(['open','high','low'], axis = 1, inplace=True)
    
    df = pd.concat([ohlc_stock, ohlc_spot], axis=1, join='inner')
    # df.dropna(inplace=True, axis=0)
    df['base'] = df.close_LA - df.close_IV
    
    df['dias_vto'] = (fecha_vto-df.index).days + 1
    
    df['tasa_implicita'] = df.base/df.close_IV *365/df.dias_vto
    
    df.dropna(inplace=True)
    # print(df)
    df = df[['tasa_implicita','close_LA']]
    df.rename(columns={'close_LA':'close'}, inplace=True)
    return df
    
def vwap(df,column_price_name, column_volume_name):
    vwap = pd.DataFrame(index=df.index)
    
    #Volumen ponderado por precio
    #Si existe un NaN lo completo con el valor siguiente
    df.fillna(method='ffill', inplace=True)
    q = df[column_volume_name].values
    p = df[column_price_name].values
    df['VWAP'] = (p * q).cumsum() / q.cumsum()
    return df
    
def ROC(df, n=2, column_name='Close'):
    """
    :param df: pandas.DataFrame
    :param n: cant. de offset
    :return: pandas.DataFrame
    """
    M = df[column_name].diff(n - 1)
    N = df[column_name].shift(n - 1)
    df['ROC'] = pd.Series(M / N, name='ROC_' + str(n))
    return df
    
def getVolbyPrice(df,column='price_LA',column_size = 'size_LA',delta_precio=25):
    min, max = df[column].min(), df[column].max()
    min = 0 if np.isnan(min) else min
    max = 1 if np.isnan(max) else max

    max = np.ceil(max/delta_precio)*delta_precio
    min = np.floor(min/delta_precio)*delta_precio
    delta = (max-min)//delta_precio
    delta = 1 if delta == 0 else delta
    # print('max',max,'min',min, 'delta',delta)
    
    if 'date_LA' in df.columns.values:
        df_unique = df.dropna()
        df_unique = df_unique.drop_duplicates(subset='date_LA')
    else:
        df_unique = df.copy()
    
    #print(df_unique)
    bins = np.arange(min, max, delta_precio)
    # print(bins)
    df_grouped = df_unique.groupby(pd.cut(df_unique[column], bins=bins, labels=bins[1:]))[column_size].sum()
    return df_grouped

def stochastic(df, column_name = 'close',window=14, smoothk=1,smoothd=3):
    """
    The stochastic oscillator is calculated using the following formula:
    %K = 100(C - L14)/(H14 - L14)
    Where:
    C = the most recent closing price
    L14 = the low of the 14 previous trading sessions
    H14 = the highest price traded during the same 14-day period
    %K= the current market rate for the currency pair
    %D = 3-period moving average of %K
        inputs:
            * df = dataframe with close price
    """
    df.fillna(method='ffill', inplace=True)
    stoch = pd.DataFrame(index=df.index)
    max, min = df[column_name].rolling(window=window).max(), df[column_name].rolling(window=window).min()
    stoch['k'] = 100*(df[column_name] - min)/(max-min)
    stoch['k'] = stoch.k.rolling(window=smoothk).mean()
    stoch['d'] = stoch.k.rolling(window=smoothd).mean()
    return stoch

def PP(df,ticker):
    """
    Determinación de Soportes y resistencais en función de precio de apertura y cierre. Es lo denominado, Puntos de Pivot en la literatura.
    
    R1 = (P x 2) – L
    S1 = (P x 2) – H
    R2 = P + (H - L) = P + (R1 - S1)
    S2 = P - (H - L) = P - (R1 - S1)

    donde:
    P: Nivel de Pivot
    L: Anterior Low
    H: Anterior High
    R1: Nivel de resistencia 1
    S1: Nivel de soporte 1
    R2: Nivel de resistencia 2
    S2: Nivel de soporte 2
    """
    df = df[df['Ticker']== ticker].drop_duplicates('LA_date')
    ohlc = getOHLC(df,'LA_price', 'LA_size')
    ohlc.dropna(inplace=True)
    pp = indicadores.puntos_pivot(ohlc)
    r1 = pp*2 - ohlc.low.shift(1)
    s1 = pp*2 - ohlc.high.shift(1)
    r2 = pp + r1 - s1
    s2 = pp - r1 + s1
    indicador = pd.concat([pp.rename('pp'), r1.rename('r1'), s1.rename('s1'), r2.rename('r2'), s2.rename('s2')], sort = False, axis = 1)
    
    end = datetime.now()
    # print(df.tail())
    # print(indicador.tail())
    # print('Perform the strategy takes ', end-start, 'seconds')
    return indicador
    

if __name__ == "__main__":
    from finance_tools import getOHLC
    from CSVtools import read_csvData
    df = pd.DataFrame()
    df = read_csvData('TestData.csv')
    ohlc = getOHLC(df)
    stocastico(ohlc)
