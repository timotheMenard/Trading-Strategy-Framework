import numpy as np
from plot_results import PortfolioPlotter

class PerformanceMetrics:
    def __init__(self, results, trades_df=None, risk_free_rate=0.01):
        # returns metrics given the results
        self.portfolio_series = results['portfolio_value']
        self.results = results
        self.trades_df = trades_df
        self.risk_free_rate = risk_free_rate

    def calculate_total_return(self):
        start_value = self.portfolio_series.iloc[0]
        end_value = self.portfolio_series.iloc[-1]
        return (end_value - start_value) / start_value

    def calculate_daily_returns(self):
        return self.portfolio_series.pct_change().dropna()

    def calculate_sharpe_ratio(self):
        daily_returns = self.calculate_daily_returns()
        excess_returns = daily_returns - (self.risk_free_rate / 252)
        return (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)

    def calculate_max_drawdown(self):
        peak = self.portfolio_series.expanding(min_periods=1).max()
        drawdown = (self.portfolio_series - peak) / peak
        return drawdown.min()

    def calculate_volatility(self):
        return self.calculate_daily_returns().std() * np.sqrt(252)

    def calculate_trade_metrics(self):
        if self.trades_df is None or 'profit_loss' not in self.trades_df.columns:
            return {}

        sells = self.trades_df
        total_trades = len(sells)
        winning_trades = (sells['profit_loss'] > 0).sum()
        losing_trades = (sells['profit_loss'] <= 0).sum()
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        avg_profit_loss = sells['profit_loss'].mean()
        avg_win = sells[sells['profit_loss'] > 0]['profit_loss'].mean() if winning_trades > 0 else 0
        avg_loss = sells[sells['profit_loss'] <= 0]['profit_loss'].mean() if losing_trades > 0 else 0
        by_reason = sells['reason'].value_counts().to_dict() if 'reason' in sells.columns else {}
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * abs(avg_loss)) if win_rate > 0 else 0

        return {
            'expectancy': expectancy,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_profit_loss': sells['profit_loss'].sum(),
            'avg_profit_loss': avg_profit_loss,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'by_reason': by_reason
        }

    def all_metrics(self):
        metrics = {
            'total_return': self.calculate_total_return(),
            'sharpe_ratio': self.calculate_sharpe_ratio(),
            'max_drawdown': self.calculate_max_drawdown(),
            'volatility': self.calculate_volatility()
        }

        if self.trades_df is not None:
            metrics.update(self.calculate_trade_metrics())

        return metrics
    
    def print_metrics(self, plot_results=False):
        metrics = self.all_metrics()
        for key, value in metrics.items():
            if isinstance(value, dict):
                print(f"{key.replace('_', ' ').title()}:")
                for subkey, subval in value.items():
                    print(f"  - {subkey}: {subval}")
            else:
                print(f"{key.replace('_', ' ').title()}: {value:.4f}")

        if plot_results:
            plt = PortfolioPlotter(self.results, short_ma=5, long_ma=10)
            plt.show()


