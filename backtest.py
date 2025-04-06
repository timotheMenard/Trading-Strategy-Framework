import pandas as pd


class Backtest:
    def __init__(self, data, strategy, initial_cash=10000):
        """
        Init of Backtest, backtest a strategy given data and strategy

        Parameters:
        data (pd.DataFrame): A DataFrame with a DateTime index and at least the following columns:
            - 'Close': float, the closing price of the asset
            - 'High': float, the high price of the asset
            - 'Low': float, the low price of the asset
            - 'Volume': float, the trading volume
        """
        self.data = data
        self.strategy = strategy
        self.initial_cash = initial_cash
        self.trade_history = []
        self.trade_history_df = []

    def run(self):
        """
        Basic backtest that just follows the signals

        Returns:
        pd.DataFrame: A DataFrame containing:
            - 'Date': the current date in YYYY-MM-DD
            - 'price': the original closing prices
            - 'signal': binary signals (1 for buy, 0 for hold, -1 for sell)
            - 'position': 0 if not in a position, 1 if in a position
            - 'holdings': holdings at the current date
            - 'porfolio_value': cash + holdings
        """
        signals = self.strategy.generate_signals(self.data)
        portfolio = pd.DataFrame(index=signals.index)
        portfolio["price"] = signals["price"]
        portfolio["signal"] = signals["signal"]
        portfolio["cash"] = self.initial_cash
        portfolio["position"] = 0
        portfolio["holdings"] = 0
        portfolio["portfolio_value"] = self.initial_cash
        portfolio = portfolio.astype({"cash": float, "holdings": float, "portfolio_value": float})

        shares = 0
        cash = self.initial_cash
        entry_price = 0
        
        # Goes through every date
        for i in range(len(portfolio)):
            signal = portfolio["signal"].iloc[i]
            price = portfolio["price"].iloc[i]

            if signal == 1:  # Buy
                # Record entry and update cash / shares
                entry_price = price
                entry_date = portfolio.index[i]
                
                shares = cash // price
                cash -= shares * price
                
                self.trade_history.append({
                    'type': 'BUY',
                    'date': entry_date,
                    'price': price,
                    'shares': shares,
                    'value': shares * price,
                    'reason': 'BUY MA CROSSOVER'
                })
                
            elif signal == -1:  # Sell
                # Record exit
                reason = 'SELL MA CROSSOVER'

                if signals['take_profit'].iloc[i] == 1:
                    reason = 'TAKE PROFIT'
                elif signals['stop_loss'].iloc[i] == 1:
                    reason = 'STOP LOSS'
                elif signals['bearish'].iloc[i] == 1:
                    reason = 'BEARISH'
                
                self.trade_history.append({
                    'type': 'SELL',
                    'date': portfolio.index[i],
                    'price': price,
                    'shares': shares,
                    'value': shares * price,
                    'profit_loss': shares * (price - entry_price),
                    'profit_loss_pct': (price / entry_price - 1) * 100 if entry_price > 0 else 0,
                    'reason': reason
                })
                
                cash += shares * price
                shares = 0

            holdings = shares * price
            portfolio.at[portfolio.index[i], "cash"] = cash
            portfolio.at[portfolio.index[i], "position"] = shares
            portfolio.at[portfolio.index[i], "holdings"] = holdings
            portfolio.at[portfolio.index[i], "portfolio_value"] = cash + holdings

        # Convert trade history to DataFrame
        if self.trade_history:
            self.trade_history_df = pd.DataFrame(self.trade_history)
        else:
            self.trade_history_df = pd.DataFrame()

        return portfolio
