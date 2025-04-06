import pandas as pd
import numpy as np
import itertools
from joblib import Parallel, delayed
from tqdm import tqdm
from strategies.strategy1 import Strategy
from backtest import Backtest
from metrics import PerformanceMetrics
import time

def run_single_backtest(params, data, param_keys):
    """Run a single backtest with the given parameters"""
    short_window, long_window, adx_threshold, trend_direction_threshold, stop_loss_pct, take_profit_pct, enter_trade_threshold, exit_trade_threshold, volume_ma_period, volume_threshold= params
    
    # Skip invalid combinations (short_window >= long_window)
    if short_window >= long_window:
        return None
    
    strategy = Strategy(
        short_window=short_window,
        long_window=long_window,
        adx_threshold=adx_threshold,
        trend_direction_threshold=trend_direction_threshold,
        stop_loss_pct=stop_loss_pct,
        take_profit_pct=take_profit_pct,
        enter_trade_threshold=enter_trade_threshold,
        exit_trade_theshold=exit_trade_threshold,
        volume_ma_period=volume_ma_period,
        volume_threshold=volume_threshold
    )
    
    bt = Backtest(data, strategy)
    results = bt.run()
    
    metrics = PerformanceMetrics(results=results, trades_df=bt.trade_history_df)
    all_metrics = metrics.all_metrics()
    
    # Check if any trades were made
    if bt.trade_history_df.empty:
        param_dict = dict(zip(param_keys, params))
        param_dict.update({
            'total_return': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'total_trades': 0,
            'win_rate': 0,
            'expectancy': 0,
            'composite_score': 0
        })
        return param_dict
    
    # Calculate expectancy
    win_rate = all_metrics.get('win_rate', 0)
    avg_win = all_metrics.get('avg_win', 0)
    avg_loss = abs(all_metrics.get('avg_loss', 0)) if all_metrics.get('avg_loss', 0) < 0 else 0
    expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss) if win_rate > 0 else 0
    
    # Create result dictionary
    param_dict = dict(zip(param_keys, params))
    param_dict.update({
        'total_return': all_metrics.get('total_return', 0),
        'sharpe_ratio': all_metrics.get('sharpe_ratio', 0),
        'max_drawdown': all_metrics.get('max_drawdown', 0),
        'total_trades': all_metrics.get('total_trades', 0),
        'win_rate': win_rate,
        'expectancy': expectancy
    })
    
    # Calculate score
    param_dict['composite_score'] = (
        param_dict['sharpe_ratio'] * 0.25 + 
        param_dict['total_return'] * 0.25 + 
        param_dict['win_rate'] * 0.1 + 
        param_dict['expectancy'] * 0.3 + 
        (param_dict['max_drawdown'] * 0.1)  # drawdown is negative
    )
    
    return param_dict

def run_grid_search_sequential(param_combinations, data, param_keys):
    """Run backtests sequentially with a progress bar"""
    results = []
    for params in tqdm(param_combinations, desc="Testing Parameters"):
        result = run_single_backtest(params, data.copy(), param_keys)
        if result is not None:
            results.append(result)
    return results

def grid_search(data, param_grid, use_parallel=True, n_jobs=-1):
    """
    Perform grid search to find optimal parameters
    
    Parameters:
    data: Market data
    param_grid: Dictionary of parameter ranges to search
    use_parallel: Whether to use parallel processing
    n_jobs: Number of parallel jobs (-1 for all available cores)
    
    Returns:
    pd.DataFrame: Results of grid search, sorted by specified metrics
    """
    # Generate all parameter combinations
    keys = list(param_grid.keys())
    param_combinations = list(itertools.product(*param_grid.values()))
    
    total_combinations = len(param_combinations)
    print(f"Running grid search with {total_combinations} parameter combinations...")
    
    start_time = time.time()
    
    if use_parallel:
        print(f"Using parallel processing with {n_jobs} jobs...")
        # Run in parallel using joblib
        results = Parallel(n_jobs=n_jobs)(
            delayed(run_single_backtest)(params, data.copy(), keys) 
            for params in tqdm(param_combinations, desc="Testing Parameters")
        )
        # Filter out None results
        results = [r for r in results if r is not None]
    else:
        print("Using sequential processing...")
        # Run sequentially with progress bar
        results = run_grid_search_sequential(param_combinations, data, keys)
    
    elapsed_time = time.time() - start_time
    print(f"Grid search completed in {elapsed_time:.2f} seconds")
    
    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    
    if results_df.empty:
        print("No valid parameter combinations found!")
        return pd.DataFrame()
    
    # Sort by composite score
    return results_df.sort_values('composite_score', ascending=False)

if __name__ == "__main__":
    # Load data
    data = pd.read_csv("data/msft.csv", index_col="Date", parse_dates=True)
    
    # Training period: use first 70% of data
    train_size = int(len(data) * 0.7)
    train_data = data.iloc[:train_size]
    test_data = data.iloc[train_size:]
    
    print(f"Data loaded. Total periods: {len(data)}, Training periods: {len(train_data)}, Testing periods: {len(test_data)}")
    
    # Parameter grid
    param_grid = {
        'short_window': [5, 10, 15],
        'long_window': [20, 50, 80],
        'adx_threshold': [10, 15, 20, 25],
        'trend_direction_threshold': [2, 5],
        'stop_loss_pct': [0.01, 0.02],
        'take_profit_pct': [0.02, 0.03, 0.05],
        'enter_trade_threshold': [3, 4, 5],
        'exit_trade_threshold': [5, 6, 7, 8, 9],
        'volume_ma_period': [5, 10, 20],
        'volume_threshold': [1, 1.5, 2]
    }
    
    # Run grid search on training data
    print("Running grid search on training data...")
    results = grid_search(train_data, param_grid, use_parallel=True, n_jobs=-1)
    
    # Display top 10 parameter combinations
    print("\nTop 10 Parameter Combinations:")
    if len(results) > 0:
        print(results.head(10))
        
        # Save results
        results.to_csv("grid_search_results.csv")
        
        # Get best parameters
        best_params = results.iloc[0]
        print("\nBest Parameters:")
        print(f"Short Window: {best_params['short_window']}")
        print(f"Long Window: {best_params['long_window']}")
        print(f"ADX Threshold: {best_params['adx_threshold']}")
        print(f"Trend Direction Threshold: {best_params['trend_direction_threshold']}")
        print(f"Stop Loss %: {best_params['stop_loss_pct']}")
        print(f"Take Profit %: {best_params['take_profit_pct']}")
        print(f"\nPerformance Metrics on Training Data:")
        print(f"Total Return: {best_params['total_return']:.4f}")
        print(f"Sharpe Ratio: {best_params['sharpe_ratio']:.4f}")
        print(f"Max Drawdown: {best_params['max_drawdown']:.4f}")
        print(f"Total Trades: {int(best_params['total_trades'])}")
        print(f"Win Rate: {best_params['win_rate']:.4f}")
        print(f"Expectancy: {best_params['expectancy']:.4f}")
        
        # Validate on test data
        print("\nValidating best parameters on test data...")
        best_strategy = Strategy(
            short_window=int(best_params['short_window']),
            long_window=int(best_params['long_window']),
            adx_threshold=best_params['adx_threshold'],
            trend_direction_threshold=best_params['trend_direction_threshold'],
            stop_loss_pct=best_params['stop_loss_pct'],
            take_profit_pct=best_params['take_profit_pct']
        )
        
        test_bt = Backtest(test_data, best_strategy)
        test_results = test_bt.run()
        test_metrics = PerformanceMetrics(results=test_results, trades_df=test_bt.trade_history_df)
        test_all_metrics = test_metrics.all_metrics()
        
        print(f"\nPerformance Metrics on Test Data:")
        print(f"Total Return: {test_all_metrics.get('total_return', 0):.4f}")
        print(f"Sharpe Ratio: {test_all_metrics.get('sharpe_ratio', 0):.4f}")
        print(f"Max Drawdown: {test_all_metrics.get('max_drawdown', 0):.4f}")
        
        trade_metrics = test_metrics.calculate_trade_metrics()
        print(f"Total Trades: {trade_metrics.get('total_trades', 0)}")
        print(f"Win Rate: {trade_metrics.get('win_rate', 0):.4f}")
    else:
        print("No valid parameter combinations found.")