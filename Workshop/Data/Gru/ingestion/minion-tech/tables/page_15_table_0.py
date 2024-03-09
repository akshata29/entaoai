
import pandas as pd

data = {
    'Assets': ['Cash and Cash Equivalents', 'Accounts Receivable', 'Inventory', 'Prepaid Expenses', 'Property, Plant, and Equipment', 'Total Assets'],
    'Amount (USD)': [500000, 300000, 400000, 100000, 1200000, 2500000],
    'Liabilities and Equity': ['Accounts Payable', 'Accrued Liabilities', 'Long-term Debt', 'Total Liabilities', 'Equity', 'Total Liabilities and Equity'],
    'Amount (USD)': [300000, 200000, 1700000, 2200000, 300000, 2500000]
}

df_balance_sheet_123456 = pd.DataFrame(data)
