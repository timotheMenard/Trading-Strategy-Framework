# Trading Strategy Framework

This project implements a way to develop, optimise and backtest trading strategies.

--------

## Overview

It has:  
- A scoring-based trading strategy implementation  
- Backtesting capabilities with detailed performance metrics  
- Parameter optimisation through grid search  
- Visualisation tools for portfolio performance and trade signals  

The framework is designed to be modular, allowing to easily add new strategies or extend existing ones.

-----------------

## Project Structure

```
├── backtest.py             Backtesting engine  
├── download.py             Download market data  
├── grid_search.py          Parameter optimisation through grid search  
├── indicators.py           Technical indicator calculations  
├── main.py                 Entry point to run a single strategy  
├── metrics.py              Performance metrics calculation  
├── plot_results.py         Visualisation tools  
├── strategies/  
│   └── strategy1.py        Implementation of a scoring-based strategy  
└── data/                   Where the downloaded data is stored  
```

--------

## Features

- **Scoring-Based Entry/Exit System**: Uses a weighted scoring system considering multiple factors to make trading decisions  
- **Technical Indicators**: Includes trend detection using ADX, moving averages, and volume analysis  
- **Risk Management**: Configurable stop-loss and take-profit levels  
- **Performance Metrics**: Metrics that include Sharpe ratio, max drawdown, win rate, and trade-specific analytics  
- **Parameter Optimisation**: Grid search with parallel processing for finding optimal strategy parameters  
- **Visualisation**: Tools to visualise portfolio performance and trading signals  

----------

## How to Use

Run:

```bash
$ python download.py
```

This will download a csv file in the data folder that has data on the AAPL stock market from 2010–2025.
Then:

```bash
$ python main.py
```

This will run one iteration of the strategy and show all the metrics and plot_results.
(I have manually changed the head of the csv file to accommodate the code)
From:

```
Price,Close,High,Low,Open,Volume  
Ticker,AAPL,AAPL,AAPL,AAPL,AAPL  
Date,,,,,
```

To:

```
Date,Close,High,Low,Open,Volume
```

## Strategy Details

The trading strategy is based on a scoring system that considers:

- **Trend Strength and Direction**: Using ADX and DI indicators  
- **Moving Average Crossovers**: Short and long-term moving averages  
- **Volume Confirmation**: Volume relative to recent average  
- **Risk Management**: Configurable stop-loss and take-profit levels  

---

## Entry Criteria

The strategy calculates an entry score based on:

- ADX value compared to threshold (trend strength)  
- Trend direction (bullish/bearish/neutral)  
- Moving average signal (crossover)  
- Volume confirmation  

A trade is entered when the score exceeds the configured threshold.

---

## Exit Criteria

Trades are exited based on:

- Stop-loss hit  
- Take-profit hit  
- Moving average crossover (bearish)  
- Trend reversal  

_I have implemented a score based exit but not using it._

---

## Performance Metrics

The framework calculates:

- **Total Return**: Overall portfolio return  
- **Sharpe Ratio**: Risk-adjusted return  
- **Max Drawdown**: Largest peak-to-trough decline  
- **Volatility**: Standard deviation of returns  
- **Trade Statistics**: Win rate, average win/loss, trade expectancy  
- **Exit Reasons**: Breakdown of why trades were closed  

---

## Requirements

- `pandas`  
- `numpy`  
- `matplotlib`  
- `joblib` (for parallel processing)  
- `tqdm` (for progress bars)  
- `yfinance` (for the data)


## Possible Improvements

- Add more technical indicators  
- Implement machine learning-based strategies  
- Implement a better way to search for hyperparameters as grid search is brute force 