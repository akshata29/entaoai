
import pandas as pd

data = {
    'Product': ['Freeze Ray', 'Rocket Boots', 'Bubble Gun'],
    'Cost (USD)': [100000, 150000, 80000],
    'Sales (USD)': [500000, 450000, 300000],
    'Profit (USD)': [150000, 120000, 100000],
    'Gross Margin (%)': [70, 60, 66.7],
    'Net Margin (%)': [30, 26.7, 33.3]
}

df_best_selling_products_123456 = pd.DataFrame(data)
