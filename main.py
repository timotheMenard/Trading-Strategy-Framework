from strategies.strategy1 import Strategy
from backtest import Backtest
from metrics import PerformanceMetrics
import pandas as pd

# Read the data from data folder
data = pd.read_csv("data/aapl.csv", index_col="Date", parse_dates=True)
#data = data.loc['2020-01-01':'2024-12-31']

# Run strategy
strategy = Strategy(short_window=5,
                                      long_window=20,
                                      adx_threshold=10,
                                      trend_direction_threshold=2,
                                      stop_loss_pct=0.01,
                                      take_profit_pct=0.02,
                                      enter_trade_threshold=3,
                                      exit_trade_theshold=6,
                                      volume_ma_period=20,
                                      volume_threshold=1)
bt = Backtest(data, strategy)
results = bt.run()

metrics = PerformanceMetrics(
    results=results,
    trades_df=bt.trade_history_df,
)

# prints the metrics and a plot to see where the trades happened
metrics.print_metrics(plot_results=True)


