import matplotlib.pyplot as plt

"""
Plots portfolio value over time and then the signals (buy/sell) in a seperate plot using results
"""
class PortfolioPlotter:
    def __init__(self, results, short_ma=15, long_ma=20):
        self.results = results
        self.short_ma = short_ma
        self.long_ma = long_ma
        self.fig, self.ax = plt.subplots(figsize=(12, 6))
        self.plots = [self.plot_portfolio_value, self.plot_signals]
        self.current_plot_index = 0

        self.fig.canvas.mpl_connect("key_press_event", self.on_key)
        self.plots[self.current_plot_index]()

    def plot_portfolio_value(self):
        self.ax.clear()
        self.results["portfolio_value"].plot(ax=self.ax, title="Portfolio Value", color="blue")
        self.ax.set_xlabel("Date")
        self.ax.set_ylabel("Portfolio Value ($)")
        self.ax.grid(True)

    def plot_signals(self):
        self.ax.clear()
        self.results["short_ma"] = self.results["price"].rolling(window=self.short_ma).mean()
        self.results["long_ma"] = self.results["price"].rolling(window=self.long_ma).mean()

        self.results["price"].plot(ax=self.ax, label="Price", alpha=0.7)
        self.results["short_ma"].plot(ax=self.ax, label=f"Short MA ({self.short_ma})", linestyle="--")
        self.results["long_ma"].plot(ax=self.ax, label=f"Long MA ({self.long_ma})", linestyle="--")

        buy_signals = self.results[self.results["signal"] == 1]
        sell_signals = self.results[self.results["signal"] == -1]

        self.ax.plot(buy_signals.index, buy_signals["price"], "^", markersize=10, color="g", label="Buy")
        self.ax.plot(sell_signals.index, sell_signals["price"], "v", markersize=10, color="r", label="Sell")

        self.ax.set_title("Buy/Sell Signals")
        self.ax.set_xlabel("Date")
        self.ax.set_ylabel("Price")
        self.ax.legend()
        self.ax.grid(True)

    # To be able to switch between plots
    def on_key(self, event):
        if event.key in ["right", "n"]:
            self.current_plot_index = (self.current_plot_index + 1) % len(self.plots)
        elif event.key in ["left", "p"]:
            self.current_plot_index = (self.current_plot_index - 1) % len(self.plots)
        else:
            return
        self.plots[self.current_plot_index]()
        self.fig.canvas.draw()

    def show(self):
        plt.show()
