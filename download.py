import yfinance as yf

ticker = 'AAPL'

data = yf.download(ticker, start='2010-01-01', end='2025-01-01')

data.to_csv('data/aapl.csv')