import pandas as pd
import numpy as np
from indicators import calculate_trend_indicators

class Strategy:
    def __init__(self, short_window=10, long_window=30, adx_threshold=20, trend_direction_threshold=5, stop_loss_pct=0.05, 
                 take_profit_pct=0.1, enter_trade_threshold=4., exit_trade_theshold=4., volume_ma_period=20, volume_threshold=1.5):
        """
        Initialise the trading strategy with configurable parameters.
        
        Parameters:
        short_window : Period for the short-term moving average, default 10
        long_window : Period for the long-term moving average, default 30
        adx_threshold : Threshold for the Average Directional Index to confirm trend strength, default 20
        trend_direction_threshold : Threshold used to determine trend direction, default 5
        stop_loss_pct : Percentage for stop loss orders (0.05 = 5%), default 0.05
        take_profit_pct : Percentage for take profit orders (0.1 = 10%), default 0.1
        enter_trade_threshold : Minimum score required to enter a trade, default 4.0
        exit_trade_theshold : Minimum score required to exit a trade, default 4.0
        volume_ma_period : Period for volume moving average calculation, default 20
        volume_threshold : Threshold for strong volume confirmation, default 1.5
        """
        self.enter_trade_threshold = enter_trade_threshold
        self.exit_trade_theshold = exit_trade_theshold
        self.short_window = short_window
        self.long_window = long_window
        self.adx_threshold = adx_threshold
        self.volume_ma_period = volume_ma_period
        self.volume_threshold = volume_threshold
        self.trend_direction_threshold = trend_direction_threshold
        self.in_position = False
        self.stop_loss_pct = stop_loss_pct  
        self.take_profit_pct = take_profit_pct  

    # Scoring to exit a trade
    def calculate_exit_score(self, price_change, short_ma, long_ma, trend_direction):
        score = 0
        
        # Stop loss - highest priority
        if price_change <= -self.stop_loss_pct:
            score += 4 
        
        # Take profit
        if price_change >= self.take_profit_pct:
            score += 3
        
        # MA crossover
        if short_ma < long_ma:
            score += 2
        
        # Trend reversal
        if trend_direction == 'bearish':
            score += 1.5
        
        return score
    
    def should_exit_trade(self, price_change, short_ma, long_ma, trend_direction):
        score = self.calculate_exit_score(price_change, short_ma, long_ma, trend_direction)
        return score >= self.exit_trade_theshold  


    # Calculate volume score
    def calculate_volume_score(self, current_volume, avg_volume):
        """
        Calculate a score based on relative volume strength
        
        Returns:
        float: 0-1 points based on volume strength
        """
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        if volume_ratio >= self.volume_threshold:
            return 1  # Strong volume confirmation
        elif volume_ratio >= 1.0:
            return .5 
        else:
            return 0  
        
    # Scoring to enter a trade
    def calculate_enter_score(self, adx, trend_direction, signal, volume_score):
        score = 0
          
        if adx > self.adx_threshold:
            score += 2
        elif adx > (self.adx_threshold * 0.8):  
            score += 1
        
        # Trend direction score
        if trend_direction == 'bullish':
            score += 2
        elif trend_direction == 'neutral':
            score += 0.5
        
        # Signal score
        if signal == 1:
            score += 2

        score += volume_score
        
        return score

    # Decision based on score
    def should_enter_trade(self, adx, trend_direction, signal, volume_score):
        score = self.calculate_enter_score(adx, trend_direction, signal, volume_score)
        return score >= self.enter_trade_threshold 

    def generate_signals(self, data):
        """
        Generate trading signals based on moving average crossovers, trend direction/strength and volume

        Parameters:
        data (pd.DataFrame): A DataFrame with a DateTime index and at least the following column:
            - 'Close': float, the closing price of the asset
            - 'High': float, the closing price of the asset
            - 'Low': float, the closing price of the asset
            - 'Volume': float, the trading volume

        Returns:
        pd.DataFrame: A DataFrame containing:
            - 'price': the original closing prices
            - 'signal': binary signals (1 for buy, 0 for hold, -1 for sell)
            - 'stop_loss': 1 if trade exit by stop loss, else 0
            - 'take_profit': 1 if trade exit by take profit, else 0
        """

        trend_data = calculate_trend_indicators(data, self.trend_direction_threshold)

        signals = pd.DataFrame(index=data.index)
        signals["price"] = data["Close"]
        
        # Calculate moving averages
        signals["short_ma"] = data["Close"].rolling(window=self.short_window).mean()
        signals["long_ma"] = data["Close"].rolling(window=self.long_window).mean()

        # Use np.where to create signal based on moving average relationship
        signals['raw_signal'] = np.where(signals['short_ma'] > signals['long_ma'], 1, 0)

        # Shift the signal by one period for more realism, nan's to 0
        signals['raw_signal'] = signals['raw_signal'].shift(1).fillna(0)

        # Calculate volume indicators
        signals["volume"] = data["Volume"]
        signals["volume_ma"] = data["Volume"].rolling(window=self.volume_ma_period).mean()
        
        # Calculate volume ratio (current volume / average volume)
        signals["volume_ratio"] = signals["volume"] / signals["volume_ma"]
        
        # Calculate volume score
        signals["volume_score"] = signals.apply(
            lambda x: self.calculate_volume_score(x["volume"], x["volume_ma"]) 
            if not pd.isna(x["volume_ma"]) else 0, 
            axis=1
        )

        # Initialise columns and variables
        signals["signal"] = 0
        signals["stop_loss"] = 0
        signals["take_profit"] = 0
        signals["bearish"] = 0
        signals["volume_signal"] = 0
        in_position = False
        entry_price = 0

        for i in range(1, len(signals)):

            # Get trend indicators for current row
            adx = trend_data['ADX'].iloc[i]
            trend_direction = trend_data['trend_direction'].iloc[i]
            raw_signal = signals["raw_signal"].iloc[i]
            volume_score = signals["volume_score"].iloc[i]

            # Enter trade score
            enter_trade = self.should_enter_trade(adx, trend_direction, raw_signal, volume_score)

            if not in_position:
                if enter_trade:
                    # Enter trade
                    signals.at[signals.index[i], "signal"] = 1
                    signals.at[signals.index[i], "volume_signal"] = volume_score
                    entry_price = signals["price"].iloc[i]
                    in_position = True
            else:
                current_price = signals["price"].iloc[i]
                price_change = (current_price - entry_price) / entry_price

                # Exit trade score
                exit_trade = self.should_exit_trade(price_change, signals["short_ma"].iloc[i], signals["long_ma"].iloc[i], trend_direction)
                # This is what was used before, more strict than scoring
                exit_conditions = (
                    (price_change <= -self.stop_loss_pct) or  # Stop loss
                    (price_change >= self.take_profit_pct) or  # Take profit
                    (signals["short_ma"].iloc[i] < signals["long_ma"].iloc[i]) or  # MA crossover
                    (trend_direction == 'bearish')  # Trend reversal
                )

                if exit_conditions:
                    # To collect data on why the the exit happened
                    if price_change <= -self.stop_loss_pct:
                        signals.at[signals.index[i], "stop_loss"] = 1
                    elif price_change >= self.take_profit_pct:
                        signals.at[signals.index[i], "take_profit"] = 1
                    elif trend_direction == 'bearish':
                        signals.at[signals.index[i], "bearish"] = 1

                    signals.at[signals.index[i], "signal"] = -1
                    in_position = False
                    entry_price = 0

        signals.drop(columns=["raw_signal", "short_ma", "long_ma"], inplace=True)

        return signals