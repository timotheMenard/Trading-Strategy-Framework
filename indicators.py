import numpy as np


def calculate_trend_indicators(data, trend_direction_threshold=5, window=14):

    ind = data.copy()

    #Calculate True Range
    ind['true_range'] = np.maximum(
        ind['High'] - ind['Low'],
        np.abs(ind['High'] - ind['Close'].shift(1)),
        np.abs(ind['Low'] - ind['Close'].shift(1))
    )

    # Calculate Directional Movement
    ind['+DM'] = np.where(
        (ind['Low'].diff() < ind['High'].diff()) & (ind['High'].diff() > 0),
        ind['High'].diff(),
        0
    )
    ind['-DM'] = np.where(
        (ind['Low'].diff() > ind['High'].diff()) & (ind['Low'].diff() > 0),
        ind['Low'].diff(),
        0
    )

    # Smooth calculations
    ind['+DM_smooth'] = ind['+DM'].rolling(window=window).sum()
    ind['-DM_smooth'] = ind['-DM'].rolling(window=window).sum()
    ind['true_range_smooth'] = ind['true_range'].rolling(window=window).sum()

    # Compute +DI, -DI
    ind['+DI'] = (ind['+DM_smooth'] / ind['true_range_smooth']) * 100
    ind['-DI'] = (ind['-DM_smooth'] / ind['true_range_smooth']) * 100

    # Calculate ADX
    ind['DX'] = (np.abs(ind['+DI'] - ind['-DI']) / (ind['+DI'] + ind['-DI'])) * 100
    ind['ADX'] = ind['DX'].rolling(window=window).mean()

    # Determine trend direction
    ind['trend_direction'] = np.where(
        ind['+DI'] > ind['-DI'] + trend_direction_threshold, 'bullish',
        np.where(ind['-DI'] > ind['+DI'] + trend_direction_threshold, 'bearish', 'neutral')
    )

    return ind[['trend_direction', 'ADX']]