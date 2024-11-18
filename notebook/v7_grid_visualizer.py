import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display

class GridVisualizer:
    def __init__(self, start_balance, wallet_exposure_limit, start_price):
        self.start_balance = start_balance
        self.wallet_exposure_limit = wallet_exposure_limit
        self.start_price = start_price

    def calculate_entry_grid(self):
        entry_prices = []
        entry_quantities = []
        entry_exposures = []
        entry_costs = []
        
        # Initial Entry
        price = self.start_price
        size = self.entry_initial_qty_pct
        costs = price * self.wallet_exposure_limit * self.entry_initial_qty_pct
        entry_prices.append(price)
        entry_quantities.append(size)
        entry_costs.append(costs)
        wallet_exposure = sum(entry_costs) / self.start_balance
        entry_exposures.append(wallet_exposure)
        
        stop = False
        while not stop:
            ratio = wallet_exposure / self.wallet_exposure_limit
            modifier = (1 + (ratio * self.entry_grid_spacing_weight))
            
            old_price = price
            price = price * (1 - (self.entry_grid_spacing_pct * modifier))
            size = sum(entry_quantities) * self.entry_grid_double_down_factor
            costs = price * size
            wallet_exposure = (sum(entry_costs) + costs) / self.start_balance
            
            if wallet_exposure <= self.wallet_exposure_limit and price > 0:
                entry_prices.append(price)
                entry_quantities.append(size)
                entry_costs.append(costs)
                entry_exposures.append(wallet_exposure)
            else:
                if (wallet_exposure > self.wallet_exposure_limit) or (old_price > 0 and price < 0):
                    entry_prices.append(price)
                    we_remaining = self.wallet_exposure_limit - entry_exposures[-1]
                    funds_remaining = we_remaining * self.start_balance
                    size = funds_remaining / price
                    costs = price * size
                    entry_quantities.append(size)
                    entry_costs.append(costs)
                    wallet_exposure = sum(entry_costs) / self.start_balance
                    entry_exposures.append(wallet_exposure)
                stop = True
                
            if price <= 1:
                stop = True
                
        return entry_prices, entry_quantities, entry_costs, entry_exposures
    
    def calculate_close_grid(self):
        close_grid_tp_prices = []
        close_grid_tp_quantities = []
        
        num_tp_levels = int(1 / self.close_grid_qty_pct)
        if(num_tp_levels * self.close_grid_qty_pct < 1):
            num_tp_levels += 1
        num_tp_levels = max(num_tp_levels, 1)
        
        tp_prices = np.linspace(
            self.start_price * (1 + self.close_grid_min_markup),
            self.start_price * (1 + self.close_grid_min_markup + self.close_grid_markup_range),
            num_tp_levels
        )
        
        for tp_price in tp_prices:
            close_grid_tp_prices.append(tp_price)
            if tp_price == tp_prices[-1]:
                qty_pct = 1.0 - sum(close_grid_tp_quantities)
            else:
                qty_pct = self.close_grid_qty_pct
            close_grid_tp_quantities.append(qty_pct)
            
        return close_grid_tp_prices, close_grid_tp_quantities

    def create_visualization(self):
        entry_prices, entry_quantities, entry_costs, entry_exposures = self.calculate_entry_grid()
        close_grid_tp_prices, close_grid_tp_quantities = self.calculate_close_grid()

        fig, ax = plt.subplots(figsize=(8, 6))

        # Plot the start price line
        ax.axhline(y=self.start_price, color='purple', linewidth=4, label='Start Price')

        # Plot the entry grid range
        ax.axhspan(entry_prices[0], entry_prices[-1], alpha=0.1, color='red', label='Entry Grid')

        # Plot the close grid range
        close_grid_start = self.start_price * (1 + self.close_grid_min_markup)
        close_grid_stop = self.start_price * (1 + self.close_grid_min_markup + self.close_grid_markup_range)
        ax.axhspan(close_grid_start, close_grid_stop, alpha=0.1, color='green', label='Close Grid')

        # Plot the entry grid lines
        for price in entry_prices:
            ax.axhline(y=price, color='red', linestyle='--', linewidth=1)

        # Plot the close grid lines
        for price in close_grid_tp_prices:
            ax.axhline(y=price, color='green', linestyle=':', linewidth=1)

        # Set the plot title, axis labels, and legend
        ax.set_title('Entry and Close Grids Visualization')
        ax.set_xlabel('Time')
        ax.set_ylabel('Price')
        ax.legend()

        return fig, entry_prices, entry_quantities, entry_costs, entry_exposures, close_grid_tp_prices, close_grid_tp_quantities

    def display_statistics(self, entry_prices, close_grid_tp_prices):
        stats = {
            'Number of Entry Levels': len(entry_prices),
            'Number of Close TP Levels': len(close_grid_tp_prices),
            'Entry Prices Range': f"{min(entry_prices):.2f} - {max(entry_prices):.2f}",
            'Entry Grid Size': f"{100 - min(entry_prices)/max(entry_prices)*100:.2f}%",
            'Close TP Prices Range': f"{min(close_grid_tp_prices):.2f} - {max(close_grid_tp_prices):.2f}",
            'Close Grid Size': f"{(max(close_grid_tp_prices)-min(close_grid_tp_prices))/min(close_grid_tp_prices)*100:.2f}%"
        }
        return pd.DataFrame.from_dict(stats, orient='index', columns=['Value'])

    def display_entry_grid(self, entry_prices, entry_quantities, entry_costs, entry_exposures):
        entry_pos_sizes = np.cumsum(entry_quantities)
        return pd.DataFrame({
            'Entry Price': [f"{price:.2f}" for price in entry_prices],
            'Quantity': [f"{qty:.2f}" for qty in entry_quantities],
            'Pos_Size': [f"{size:.2f}" for size in entry_pos_sizes],
            'Cost': [f"{cost:.2f}" for cost in entry_costs],
            'WE': [f"{exp*100:.2f}%" for exp in entry_exposures]
        })

    def display_close_grid(self, close_grid_tp_prices, close_grid_tp_quantities):
        return pd.DataFrame({
            'Close TP Price': [f"{price:.2f}" for price in close_grid_tp_prices],
            'Quantity': [f"{qty*100:.2f}%" for qty in close_grid_tp_quantities]
        })

def initialize(side):    
    # Initialize the visualizer with your parameters
    visualizer = GridVisualizer(
        start_balance=config['backtest']['starting_balance'],
        wallet_exposure_limit=config['bot'][side]['total_wallet_exposure_limit'],
        start_price=100
    )

    # Set grid parameters
    visualizer.entry_grid_spacing_pct = config['bot'][side]['entry_grid_spacing_pct']
    visualizer.entry_grid_spacing_weight = config['bot'][side]['entry_grid_spacing_weight']
    visualizer.entry_grid_double_down_factor = config['bot'][side]['entry_grid_double_down_factor']
    visualizer.entry_initial_qty_pct = config['bot'][side]['entry_initial_qty_pct']
    visualizer.close_grid_markup_range = config['bot'][side]['close_grid_markup_range']
    visualizer.close_grid_min_markup = config['bot'][side]['close_grid_min_markup']
    visualizer.close_grid_qty_pct = config['bot'][side]['close_grid_qty_pct']

    # Create visualization and get all data
    fig, entry_prices, entry_quantities, entry_costs, entry_exposures, close_prices, close_quantities = visualizer.create_visualization()

    # Display the visualization
    plt.show(fig)
    
    # # Display statistics and grids
    statistics = visualizer.display_statistics(entry_prices, close_prices)
    entry_grid = visualizer.display_entry_grid(entry_prices, entry_quantities, entry_costs, entry_exposures)
    close_grid = visualizer.display_close_grid(close_prices, close_quantities)
    print("Statistics:")
    print(statistics)
    print("\nEntry Grid:")
    print(entry_grid)
    print("\nClose Grid:")
    print(close_grid)

print ("Just a basic indication of the grid, not adjusted per symbol / exchange\n")
if config['bot']['long']['total_wallet_exposure_limit'] > 0 and config['bot']['long']['n_positions'] > 0:
    print("long:")
    initialize('long')
    
if config['bot']['short']['total_wallet_exposure_limit'] > 0 and config['bot']['short']['n_positions'] > 0:
    print("short:")
    initialize('short')
