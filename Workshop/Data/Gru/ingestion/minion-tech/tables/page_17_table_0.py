
import pandas as pd

data = {
    'Description': [
        'Product Sales', 'Total Revenue', 'Material Costs', 'Labor (Manufacturing)',
        'Total COGS', 'Gross Profit', 'R&D', 'Marketing', 'General and Administrative',
        'Total Operating Expenses', 'Operating Income', 'Interest Expense',
        'Total Other Expenses', 'Net Income Before Taxes', 'Taxes (20%)', 'Net Income'
    ],
    'Amount (USD)': [
        4200000, 4200000, 1200000, 1000000, 2200000, 2000000, 600000, 300000,
        900000, 1800000, 200000, 100000, 100000, 100000, 20000, 80000
    ]
}

df_profit_loss_2023_3927364 = pd.DataFrame(data)
