import requests
import typing
import logging

CONNECT_TIMEOUT = 5
READ_TIMEOUT = 30
BASE_URL_v3: str = "https://financialmodelingprep.com/api/v3/"
BASE_URL_v4: str = "https://financialmodelingprep.com/api/v4/"
DEFAULT_LIMIT: int = 10

PERIOD_VALUES: typing.List = [
    "annual",
    "quarter",
]
TIME_DELTA_VALUES: typing.List = [
    "1min",
    "5min",
    "15min",
    "30min",
    "1hour",
    "4hour",
]
INDUSTRY_VALUES: typing.List = [
    "Entertainment",
    "Oil & Gas Midstream",
    "Semiconductors",
    "Specialty Industrial Machinery",
    "Banks Diversified",
    "Consumer Electronics",
    "Software Infrastructure",
    "Broadcasting",
    "Computer Hardware",
    "Building Materials",
    "Resorts & Casinos",
    "Auto Manufacturers",
    "Internet Content & Information",
    "Insurance Diversified",
    "Telecom Services",
    "Metals & Mining",
    "Capital Markets",
    "Steel",
    "Footwear & Accessories",
    "Household & Personal Products",
    "Other Industrial Metals & Mining",
    "Oil & Gas E&P",
    "Banks Regional",
    "Drug Manufacturers General",
    "Internet Retail",
    "Communication Equipment",
    "Semiconductor Equipment & Materials",
    "Oil & Gas Services",
    "Chemicals",
    "Electronic Gaming & Multimedia",
    "Oil & Gas Integrated",
    "Credit Services",
    "Online Media",
    "Business Services",
    "Biotechnology",
    "Grocery Stores",
    "Oil & Gas Equipment & Services",
    "REITs",
    "Copper",
    "Software Application",
    "Home Improvement Retail",
    "Pharmaceutical Retailers",
    "Communication Services",
    "Oil & Gas Drilling",
    "Electronic Components",
    "Packaged Foods",
    "Information Technology Services",
    "Leisure",
    "Specialty Retail",
    "Oil & Gas Refining & Marketing",
    "Tobacco",
    "Financial Data & Stock Exchanges",
    "Insurance Specialty",
    "Beverages Non-Alcoholic",
    "Asset Management",
    "REIT Diversified",
    "Residential Construction",
    "Travel & Leisure",
    "Gold",
    "Discount Stores",
    "Confectioners",
    "Medical Devices",
    "Banks",
    "Independent Oil & Gas",
    "Airlines",
    "Travel Services",
    "Aerospace & Defense",
    "Retail Apparel & Specialty",
    "Diagnostics & Research",
    "Trucking",
    "Insurance Property & Casualty",
    "Health Care Plans",
    "Consulting Services",
    "Aluminum",
    "Beverages Brewers",
    "REIT Residential",
    "Education & Training Services",
    "Apparel Retail",
    "Railroads",
    "Apparel Manufacturing",
    "Staffing & Employment Services",
    "Utilities Diversified",
    "Agricultural Inputs",
    "Restaurants",
    "Drug Manufacturers General Specialty & Generic",
    "Financial Conglomerates",
    "Personal Services",
    "Thermal Coal",
    "REIT Office",
    "Advertising Agencies",
    "Farm & Heavy Construction Machinery",
    "Consumer Packaged Goods",
    "Publishing",
    "Specialty Chemicals",
    "Engineering & Construction",
    "Utilities Independent Power Producers",
    "Utilities Regulated Electric",
    "Medical Instruments & Supplies",
    "Building Products & Equipment",
    "Packaging & Containers",
    "REIT Mortgage",
    "Department Stores",
    "Insurance Life",
    "Luxury Goods",
    "Auto Parts",
    "Autos",
    "REIT Specialty",
    "Integrated Freight & Logistics",
    "Security & Protection Services",
    "Utilities Regulated Gas",
    "Airports & Air Services",
    "Farm Products",
    "REIT Healthcare Facilities",
    "REIT Industrial",
    "Metal Fabrication",
    "Scientific & Technical Instruments",
    "Solar",
    "REIT Hotel & Motel",
    "Medical Distribution",
    "Medical Care Facilities",
    "Agriculture",
    "Food Distribution",
    "Health Information Services",
    "Industrial Products",
    "REIT Retail",
    "Conglomerates",
    "Health Care Providers",
    "Waste Management",
    "Beverages Wineries & Distilleries",
    "Marine Shipping",
    "Real Estate Services",
    "Tools & Accessories",
    "Auto & Truck Dealerships",
    "Industrial Distribution",
    "Uranium",
    "Lodging",
    "Electrical Equipment & Parts",
    "Gambling",
    "Specialty Business Services",
    "Recreational Vehicles",
    "Furnishings",
    "Fixtures & Appliances",
    "Forest Products",
    "Silver",
    "Business Equipment & Supplies",
    "Medical Instruments & Equipment",
    "Utilities Regulated",
    "Coking Coal",
    "Insurance Brokers",
    "Rental & Leasing Services",
    "Lumber & Wood Production",
    "Medical Diagnostics & Research",
    "Pollution & Treatment Controls",
    "Transportation & Logistics",
    "Other Precious Metals & Mining",
    "Brokers & Exchanges",
    "Beverages Alcoholic",
    "Mortgage Finance",
    "Utilities Regulated Water",
    "Manufacturing Apparel & Furniture",
    "Retail Defensive",
    "Real Estate Development",
    "Paper & Paper Products",
    "Insurance Reinsurance",
    "Homebuilding & Construction",
    "Coal",
    "Electronics & Computer Distribution",
    "Health Care Equipment & Services",
    "Education",
    "Employment Services",
    "Textile Manufacturing",
    "Real Estate Diversified",
    "Consulting & Outsourcing",
    "Utilities Renewable",
    "Tobacco Products",
    "Farm & Construction Machinery",
    "Shell Companies",
    "N/A",
    "Advertising & Marketing Services",
    "Capital Goods",
    "Insurance",
    "Industrial Electrical Equipment",
    "Utilities",
    "Pharmaceuticals",
    "Biotechnology & Life Sciences",
    "Infrastructure Operations",
    "Energy",
    "NULL",
    "Property Management",
    "Auto Dealerships",
    "Apparel Stores",
    "Mortgage Investment",
    "Software & Services",
    "Industrial Metals & Minerals",
    "Media & Entertainment",
    "Diversified Financials",
    "Consumer Services",
    "Commercial  & Professional Services",
    "Electronics Wholesale",
    "Retailing",
    "Automobiles & Components",
    "Materials",
    "Real Estate",
    "Food",
    "Beverage & Tobacco",
    "Closed-End Fund Debt",
    "Transportation",
    "Food & Staples Retailing",
    "Consumer Durables & Apparel",
    "Technology Hardware & Equipment",
    "Telecommunication Services",
    "Semiconductors & Semiconductor Equipment",
]
SECTOR_VALUES: typing.List = [
    "Communication Services",
    "Energy",
    "Technology",
    "Industrials",
    "Financial Services",
    "Basic Materials",
    "Consumer Cyclical",
    "Consumer Defensive",
    "Healthcare",
    "Real Estate",
    "Utilities",
    "Financial",
    "Building",
    "Industrial Goods",
    "Pharmaceuticals",
    "Services",
    "Conglomerates",
    "Media",
    "Banking",
    "Airlines",
    "Retail",
    "Metals & Mining",
    "Textiles",
    "Apparel & Luxury Goods",
    "Chemicals",
    "Biotechnology",
    "Electrical Equipment",
    "Aerospace & Defense",
    "Telecommunication",
    "Machinery",
    "Food Products",
    "Insurance",
    "Logistics & Transportation",
    "Health Care",
    "Beverages",
    "Consumer products",
    "Semiconductors",
    "Automobiles",
    "Trading Companies & Distributors",
    "Commercial Services & Supplies",
    "Construction",
    "Auto Components",
    "Hotels",
    "Restaurants & Leisure",
    "Life Sciences Tools & Services",
    "Communications",
    "Industrial Conglomerates",
    "Professional Services",
    "Road & Rail",
    "Tobacco",
    "Paper & Forest",
    "Packaging",
    "Leisure Products",
    "Transportation Infrastructure",
    "Distributors",
    "Marine",
    "Diversified Consumer Services",
]
SERIES_TYPE_VALUES: typing.List = [
    "line",
]
TECHNICAL_INDICATORS_TIME_DELTA_VALUES: typing.List = [
    "1min",
    "5min",
    "15min",
    "30min",
    "1hour",
    "4hour",
    "daily",
]
STATISTICS_TYPE_VALUES: typing.List = [
    "sma",
    "ema",
    "wma",
    "dema",
    "tema",
    "williams",
    "rsa",
    "adx",
    "standardDeviation",
]
FINANCIAL_STATEMENT_FILENAME: str = "financial_statement.zip"
CASH_FLOW_STATEMENT_FILENAME: str = "cash_flow_statement.csv"
INCOME_STATEMENT_FILENAME: str = "income_statement.csv"
BALANCE_SHEET_STATEMENT_FILENAME: str = "balance_sheet_statement.csv"
INCOME_STATEMENT_AS_REPORTED_FILENAME: str = "income_statement_as_reported.csv"
BALANCE_SHEET_STATEMENT_AS_REPORTED_FILENAME: str = "balance_sheet_as_reported.csv"
CASH_FLOW_STATEMENT_AS_REPORTED_FILENAME: str = "cash_flow_as_reported.csv"
SEC_RSS_FEEDS_FILENAME: str = "sec_rss_feeds.csv"
SP500_CONSTITUENTS_FILENAME: str = "sp500_constituents.csv"
NASDAQ_CONSTITUENTS_FILENAME: str = "nasdaq_constituents.csv"
DOWJONES_CONSTITUENTS_FILENAME: str = "dowjones_constituents.csv"

def __return_json_v3(
    path: str, query_vars: typing.Dict
) -> typing.Optional[typing.List]:
    """
    Query URL for JSON response for v3 of FMP API.

    :param path: Path after TLD of URL
    :param query_vars: Dictionary of query values (after "?" of URL)
    :return: JSON response
    """
    url = f"{BASE_URL_v3}{path}"
    return_var = None
    try:
        response = requests.get(
            url, params=query_vars, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT)
        )
        if len(response.content) > 0:
            return_var = response.json()

        if len(response.content) == 0 or (
            isinstance(return_var, dict) and len(return_var.keys()) == 0
        ):
            logging.warning("Response appears to have no data.  Returning empty List.")
            return_var = []

    except requests.Timeout:
        logging.error(f"Connection to {url} timed out.")
    except requests.ConnectionError:
        logging.error(
            f"Connection to {url} failed:  DNS failure, refused connection or some other connection related "
            f"issue."
        )
    except requests.TooManyRedirects:
        logging.error(
            f"Request to {url} exceeds the maximum number of predefined redirections."
        )
    except Exception as e:
        logging.error(
            f"A requests exception has occurred that we have not yet detailed an 'except' clause for.  "
            f"Error: {e}"
        )

    return return_var

def __return_json_v4(
    path: str, query_vars: typing.Dict
) -> typing.Optional[typing.List]:
    """
    Query URL for JSON response for v4 of FMP API.

    :param path: Path after TLD of URL
    :param query_vars: Dictionary of query values (after "?" of URL)
    :return: JSON response
    """
    url = f"{BASE_URL_v4}{path}"
    return_var = None
    try:
        response = requests.get(
            url, params=query_vars, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT)
        )
        if len(response.content) > 0:
            return_var = response.json()

        if len(response.content) == 0 or (
            isinstance(return_var, dict) and len(return_var.keys()) == 0
        ):
            logging.warning("Response appears to have no data.  Returning empty List.")
            return_var = []

    except requests.Timeout:
        logging.error(f"Connection to {url} timed out.")
    except requests.ConnectionError:
        logging.error(
            f"Connection to {url} failed:  DNS failure, refused connection or some other connection related "
            f"issue."
        )
    except requests.TooManyRedirects:
        logging.error(
            f"Request to {url} exceeds the maximum number of predefined redirections."
        )
    except Exception as e:
        logging.error(
            f"A requests exception has occurred that we have not yet detailed an 'except' clause for.  "
            f"Error: {e}"
        )
    return return_var

def __validate_period(value: str) -> str:
    """
    Check to see if passed string is in the list of possible time periods.
    :param value: Period name.
    :return: Passed value or No Return
    """
    valid_values = PERIOD_VALUES
    if value in valid_values:
        return value
    else:
        logging.error(f"Invalid period value: {value}.  Valid options: {valid_values}")

def __validate_sector(value: str) -> str:
    """
    Check to see if passed string is in the list of possible Sectors.
    :param value: Sector name.
    :return: Passed value or No Return
    """
    valid_values = SECTOR_VALUES
    if value in valid_values:
        return value
    else:
        logging.error(f"Invalid sector value: {value}.  Valid options: {valid_values}")

def __validate_industry(value: str) -> str:
    """
    Check to see if passed string is in the list of possible Industries.
    :param value: Industry name.
    :return: Passed value or No Return
    """
    valid_values = INDUSTRY_VALUES
    if value in valid_values:
        return value
    else:
        logging.error(
            f"Invalid industry value: {value}.  Valid options: {valid_values}"
        )

def __validate_time_delta(value: str) -> str:
    """
    Check to see if passed string is in the list of possible Time Deltas.
    :param value: Time Delta name.
    :return: Passed value or No Return
    """
    valid_values = TIME_DELTA_VALUES
    if value in valid_values:
        return value
    else:
        logging.error(
            f"Invalid time_delta value: {value}.  Valid options: {valid_values}"
        )

def __validate_series_type(value: str) -> str:
    """
    Check to see if passed string is in the list of possible Series Type.
    :param value: Series Type name.
    :return: Passed value or No Return
    """
    valid_values = SERIES_TYPE_VALUES
    if value in valid_values:
        return value
    else:
        logging.error(
            f"Invalid series_type value: {value}.  Valid options: {valid_values}"
        )

def __validate_technical_indicators_time_delta(value: str) -> str:
    """Exactly like set_time_delta() method but adds 'daily' as an option.
    :param value: Indicators Time Delta name.
    :return: Passed value or No Return
    """
    valid_values = TECHNICAL_INDICATORS_TIME_DELTA_VALUES
    if value in valid_values:
        return value
    else:
        logging.error(
            f"Invalid time_delta value: {value}.  Valid options: {valid_values}"
        )

def mapper_cik_name(
    apikey: str,
    name: str,
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /mapper-cik-name/ API.

    List with names and their CIK

    :param apikey: Your API key.
    :param name: String of name.
    :return: A list of dictionaries.
    """
    path = f"mapper-cik-name/"
    query_vars = {"apikey": apikey}
    if name:
        query_vars["name"] = name
    return __return_json_v4(path=path, query_vars=query_vars)

def mapper_cik_company(
    apikey: str,
    ticker: str,
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /mapper-cik-company/ API.

    Company CIK mapper

    :param apikey: Your API key.
    :param ticker: String of name.
    :return: A list of dictionaries.
    """
    path = f"mapper-cik-company/{ticker}"
    query_vars = {"apikey": apikey}
    return __return_json_v4(path=path, query_vars=query_vars)

def cik_list(apikey: str) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /cik_list/ API.

    Complete list of all institutional investment managers by cik
    :param apikey: Your API key.
    :return: A list of dictionaries.
    """
    path = f"cik_list"
    query_vars = {"apikey": apikey}
    return __return_json_v3(path=path, query_vars=query_vars)

def cik_search(apikey: str, name: str) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /cik-search/ API.

    FORM 13F cik search by name
    :param apikey: Your API key.
    :param name: Name
    :return: A list of dictionaries.
    """
    path = f"cik-search/{name}"
    query_vars = {"apikey": apikey}
    return __return_json_v3(path=path, query_vars=query_vars)

def company_profile(
    apikey: str, symbol: str
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /profile/ API.

    Gather this company's information.
    :param apikey: Your API key.
    :param symbol: Ticker of Company.
    :return: A list of dictionaries.
    """
    path = f"profile/{symbol}"
    query_vars = {"apikey": apikey}
    return __return_json_v3(path=path, query_vars=query_vars)

def key_executives(
    apikey: str, symbol: str
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /key-executives/ API.

    Gather info about company's key executives.
    :param apikey: Your API Key.
    :param symbol: Ticker of company.
    :return: A list of dictionaries.
    """
    path = f"key-executives/{symbol}"
    query_vars = {"apikey": apikey}
    return __return_json_v3(path=path, query_vars=query_vars)

def search(
    apikey: str, query: str = "", limit: int = DEFAULT_LIMIT, exchange: str = ""
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /search/ API.

    Search via ticker and company name.
    :param apikey: Your API key.
    :param query: Whole or fragment of Ticker or Name of company.
    :param limit: Number of rows to return.
    :param exchange: Stock exchange to search.
    :return: A list of dictionaries.
    """
    path = f"search/"
    query_vars = {
        "apikey": apikey,
        "limit": limit,
        "query": query,
        "exchange": exchange,
    }
    return __return_json_v3(path=path, query_vars=query_vars)

def search_ticker(
    apikey: str, query: str = "", limit: int = DEFAULT_LIMIT, exchange: str = ""
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /search-ticker/ API.

    Search only via ticker.
    :param apikey: Your API key.
    :param query: Whole or fragment of Ticker.
    :param limit: Number of rows to return.
    :param exchange:Stock exchange to search.
    :return: A list of dictionaries.
    """
    path = f"search-ticker/"
    query_vars = {
        "apikey": apikey,
        "limit": limit,
        "query": query,
        "exchange": exchange,
    }
    return __return_json_v3(path=path, query_vars=query_vars)

def financial_statement(
    apikey: str, symbol: str, filename: str = FINANCIAL_STATEMENT_FILENAME
) -> None:
    """
    Query FMP /financial-statements/ API.

    Download company's financial statement.
    :param apikey: Your API key.
    :param symbol: Ticker of company.
    :param filename: Name of saved file.
    :return: A list of dictionaries.
    """
    path = f"financial-statements/{symbol}"
    query_vars = {
        "apikey": apikey,
        "datatype": "zip",  # Only ZIP format is supported.
    }
    response = requests.get(f"{BASE_URL_v3}{path}", params=query_vars)
    open(filename, "wb").write(response.content)
    logging.info(f"Saving {symbol} financial statement as {filename}.")

def income_statement(
    apikey: str,
    symbol: str,
    period: str = "annual",
    limit: int = DEFAULT_LIMIT,
    download: bool = False,
    filename: str = INCOME_STATEMENT_FILENAME,
) -> typing.Union[typing.List[typing.Dict], None]:
    """
    Query FMP /income-statement/ API.

    Display or download company's income statement.
    :param apikey: Your API key.
    :param symbol: Company ticker.
    :param period: 'quarter' or 'annual'.
    :param limit: Number of rows to return.
    :param download: True/False
    :param filename: Name of saved file.
    :return: A list of dictionaries.
    """
    path = f"income-statement/{symbol}"
    query_vars = {"apikey": apikey, "limit": limit, "period": __validate_period(period)}
    if download:
        query_vars["datatype"] = "csv"  # Only CSV is supported.
        response = requests.get(f"{BASE_URL_v3}{path}", params=query_vars)
        open(filename, "wb").write(response.content)
        logging.info(f"Saving {symbol} financial statement as {filename}.")
    else:
        return __return_json_v3(path=path, query_vars=query_vars)

def balance_sheet_statement(
    apikey: str,
    symbol: str,
    period: str = "annual",
    limit: int = DEFAULT_LIMIT,
    download: bool = False,
    filename: str = BALANCE_SHEET_STATEMENT_FILENAME,
) -> typing.Union[typing.List[typing.Dict], None]:
    """
    Query FMP /balance-sheet-statement/ API.

    Display or download company's balance sheet statement.
    :param apikey: Your API key.
    :param symbol: Company ticker.
    :param period: 'quarter' or 'annual'.
    :param limit: Number of rows to return.
    :param download: True/False
    :param filename: Name of saved file.
    :return: A list of dictionaries.
    """
    path = f"balance-sheet-statement/{symbol}"
    query_vars = {"apikey": apikey, "limit": limit, "period": __validate_period(period)}
    if download:
        query_vars["datatype"] = "csv"  # Only CSV is supported.
        response = requests.get(f"{BASE_URL_v3}{path}", params=query_vars)
        open(filename, "wb").write(response.content)
        logging.info(f"Saving {symbol} financial statement as {filename}.")
    else:
        return __return_json_v3(path=path, query_vars=query_vars)

def cash_flow_statement(
    apikey: str,
    symbol: str,
    period: str = "annual",
    limit: int = DEFAULT_LIMIT,
    download: bool = False,
    filename: str = CASH_FLOW_STATEMENT_FILENAME,
) -> typing.Union[typing.List[typing.Dict], None]:
    """
    Query FMP /cash-flow-statement/ API.

    Display or download company's cash flow statement.
    :param apikey: Your API key.
    :param symbol: Company ticker.
    :param period: 'quarter' or 'annual'.
    :param limit: Number of rows to return.
    :param download: True/False
    :param filename: Name of saved file.
    :return: A list of dictionaries.
    """
    path = f"cash-flow-statement/{symbol}"
    query_vars = {"apikey": apikey, "limit": limit, "period": __validate_period(period)}
    if download:
        query_vars["datatype"] = "csv"  # Only CSV is supported.
        response = requests.get(f"{BASE_URL_v3}{path}", params=query_vars)
        open(filename, "wb").write(response.content)
        logging.info(f"Saving {symbol} financial statement as {filename}.")
    else:
        return __return_json_v3(path=path, query_vars=query_vars)

def financial_statement_symbol_lists(
    apikey: str,
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /financial-statement-symbol-lists/ API.

    List of symbols that have financial statements.
    :param apikey: Your API key.
    :return: A list of dictionaries.
    """
    path = f"financial-statement-symbol-lists"
    query_vars = {"apikey": apikey}
    return __return_json_v3(path=path, query_vars=query_vars)

def income_statement_growth(
    apikey: str,
    symbol: str,
    limit: int = DEFAULT_LIMIT,
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /income-statement-growth/ API.

    Growth stats for company's income statement.
    :param apikey: Your API key.
    :param symbol: Company ticker.
    :param limit: Number of rows to return.
    :return: A list of dictionaries.
    """
    path = f"income-statement-growth/{symbol}"
    query_vars = {
        "apikey": apikey,
        "limit": limit,
    }
    return __return_json_v3(path=path, query_vars=query_vars)

def balance_sheet_statement_growth(
    apikey: str, symbol: str, limit: int = DEFAULT_LIMIT
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /balance-sheet-statement-growth/ API.

    Growth stats for company's balance sheet statement.
    :param apikey: Your API key.
    :param symbol: Company ticker.
    :param limit: Number of rows to return.
    :return: A list of dictionaries.
    """
    path = f"balance-sheet-statement-growth/{symbol}"
    query_vars = {
        "apikey": apikey,
        "limit": limit,
    }
    return __return_json_v3(path=path, query_vars=query_vars)

def cash_flow_statement_growth(
    apikey: str, symbol: str, limit: int = DEFAULT_LIMIT
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /cash-flow-statement-growth/ API.

    Growth stats for company's cash flow statement.
    :param apikey: Your API key.
    :param symbol: Company ticker.
    :param limit: Number of rows to return.
    :return: A list of dictionaries.
    """
    path = f"cash-flow-statement-growth/{symbol}"
    query_vars = {
        "apikey": apikey,
        "limit": limit,
    }
    return __return_json_v3(path=path, query_vars=query_vars)

def income_statement_as_reported(
    apikey: str,
    symbol: str,
    period: str = "annual",
    limit: int = DEFAULT_LIMIT,
    download: bool = False,
    filename: str = INCOME_STATEMENT_AS_REPORTED_FILENAME,
) -> typing.Union[typing.List[typing.Dict], None]:
    """
    Query FMP /income-statement-as-reported/ API.

    Company's "as reported" income statement.
    :param apikey: Your API key.
    :param symbol: Company ticker.
    :param period: 'annual' or 'quarter'
    :param limit: Number of rows to return.
    :param download: True/False
    :param filename: Name of saved file.
    :return: A list of dictionaries.
    """
    path = f"income-statement-as-reported/{symbol}"
    query_vars = {
        "apikey": apikey,
        "limit": limit,
        "period": __validate_period(value=period),
    }
    if download:
        query_vars["datatype"] = "csv"  # Only CSV is supported.
        response = requests.get(f"{BASE_URL_v3}{path}", params=query_vars)
        open(filename, "wb").write(response.content)
        logging.info(f"Saving {symbol} financial statement as {filename}.")
    else:
        return __return_json_v3(path=path, query_vars=query_vars)

def balance_sheet_statement_as_reported(
    apikey: str,
    symbol: str,
    period: str = "annual",
    limit: int = DEFAULT_LIMIT,
    download: bool = False,
    filename: str = BALANCE_SHEET_STATEMENT_AS_REPORTED_FILENAME,
) -> typing.Union[typing.List[typing.Dict], None]:
    """
    Query FMP /balance-sheet-statement-as-reported/ API.

    Company's "as reported" balance sheet statement.
    :param apikey: Your API key.
    :param symbol: Company ticker.
    :param period: 'annual' or 'quarter'
    :param limit: Number of rows to return.
    :param download: True/False
    :param filename: Name of saved file.
    :return: A list of dictionaries.
    """
    path = f"balance-sheet-statement-as-reported/{symbol}"
    query_vars = {
        "apikey": apikey,
        "limit": limit,
        "period": __validate_period(value=period),
    }
    if download:
        query_vars["datatype"] = "csv"  # Only CSV is supported.
        response = requests.get(f"{BASE_URL_v3}{path}", params=query_vars)
        open(filename, "wb").write(response.content)
        logging.info(f"Saving {symbol} financial statement as {filename}.")
    else:
        return __return_json_v3(path=path, query_vars=query_vars)

def cash_flow_statement_as_reported(
    apikey: str,
    symbol: str,
    period: str = "annual",
    limit: int = DEFAULT_LIMIT,
    download: bool = False,
    filename: str = CASH_FLOW_STATEMENT_AS_REPORTED_FILENAME,
) -> typing.Union[typing.List[typing.Dict], None]:
    """
    Query FMP /cash-flow-statement-as-reported/ API.

    Company's "as reported" cash flow statement.
    :param apikey: Your API key.
    :param symbol: Company ticker.
    :param period: 'annual' or 'quarter'
    :param limit: Number of rows to return.
    :param download: True/False
    :param filename: Name of saved file.
    :return: A list of dictionaries.
    """
    path = f"cash-flow-statement-as-reported/{symbol}"
    query_vars = {
        "apikey": apikey,
        "limit": limit,
        "period": __validate_period(value=period),
    }
    if download:
        query_vars["datatype"] = "csv"  # Only CSV is supported.
        response = requests.get(f"{BASE_URL_v3}{path}", params=query_vars)
        open(filename, "wb").write(response.content)
        logging.info(f"Saving {symbol} financial statement as {filename}.")
    else:
        return __return_json_v3(path=path, query_vars=query_vars)

def financial_statement_full_as_reported(
    apikey: str,
    symbol: str,
    period: str = "annual",
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /financial-statement-full-as-reported/ API.

    Company's "as reported" full income statement.
    :param apikey: Your API key.
    :param symbol: Company ticker.
    :param period: 'annual' or 'quarter'
    :return: A list of dictionaries.
    """
    path = f"financial-statement-full-as-reported/{symbol}"
    query_vars = {"apikey": apikey, "period": __validate_period(value=period)}
    return __return_json_v3(path=path, query_vars=query_vars)

def financial_ratios_ttm(
    apikey: str, symbol: str
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FmP /ratios-ttm/ API.

    :param apikey: Your API key
    :param symbol: Company ticker
    :return: A list of dictionaries.
    """
    path = f"ratios-ttm/{symbol}"
    query_vars = {"apikey": apikey}
    return __return_json_v3(path=path, query_vars=query_vars)

def financial_ratios(
    apikey: str,
    symbol: str,
    period: str = "annual",
    limit: int = DEFAULT_LIMIT,
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FmP /ratios/ API.

    :param apikey: Your API key.
    :param symbol: Company ticker.
    :param period: 'annual' or 'quarter'
    :param limit: Number of rows to return.
    :return: A list of dictionaries.
    """
    path = f"ratios/{symbol}"
    query_vars = {
        "apikey": apikey,
        "limit": limit,
        "period": __validate_period(value=period),
    }
    return __return_json_v3(path=path, query_vars=query_vars)

def enterprise_values(
    apikey: str,
    symbol: str,
    period: str = "annual",
    limit: int = DEFAULT_LIMIT,
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /enterprise-values/ API.

    :param apikey: Your API key.
    :param symbol: Company ticker.
    :param period: 'annual' or 'quarter'
    :param limit: Number of rows to return.
    :return: A list of dictionaries.
    """
    path = f"enterprise-values/{symbol}"
    query_vars = {
        "apikey": apikey,
        "limit": limit,
        "period": __validate_period(value=period),
    }
    return __return_json_v3(path=path, query_vars=query_vars)

def key_metrics_ttm(
    apikey: str,
    symbol: str,
    limit: int = DEFAULT_LIMIT,
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /key-metrics-ttm/ API

    :param apikey: Your API key.
    :param symbol: Company ticker.
    :param limit: Number of rows to return.
    :return: A list of dictionaries.
    """
    path = f"key-metrics-ttm/{symbol}"
    query_vars = {"apikey": apikey, "limit": limit}
    return __return_json_v3(path=path, query_vars=query_vars)

def key_metrics(
    apikey: str,
    symbol: str,
    period: str = "annual",
    limit: int = DEFAULT_LIMIT,
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /key-metrics/ API

    :param apikey: Your API key.
    :param symbol: Company ticker.
    :param period: 'annual' or 'quarter'
    :param limit: Number of rows to return.
    :return: A list of dictionaries.
    """
    path = f"key-metrics/{symbol}"
    query_vars = {
        "apikey": apikey,
        "limit": limit,
        "period": __validate_period(value=period),
    }
    return __return_json_v3(path=path, query_vars=query_vars)

def financial_growth(
    apikey: str,
    symbol: str,
    period: str = "annual",
    limit: int = DEFAULT_LIMIT,
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /financial-growth/ API.

    :param apikey: Your API key.
    :param symbol: Company ticker.
    :param period: 'annual' or 'quarter'
    :param limit: Number of rows to return.
    :return: A list of dictionaries.
    """
    path = f"financial-growth/{symbol}"
    query_vars = {
        "apikey": apikey,
        "limit": limit,
        "period": __validate_period(value=period),
    }
    return __return_json_v3(path=path, query_vars=query_vars)

def rating(apikey: str, symbol: str) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /rating/ API.

    :param apikey: Your API key.
    :param symbol: Company ticker.
    :return: A list of dictionaries.
    """
    path = f"rating/{symbol}"
    query_vars = {"apikey": apikey}
    return __return_json_v3(path=path, query_vars=query_vars)

def historical_rating(
    apikey: str,
    symbol: str,
    limit: int = DEFAULT_LIMIT,
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /historical-rating/ API.

    :param apikey: Your API key.
    :param symbol: Company ticker.
    :param limit: Number of rows to return.
    :return: A list of dictionaries.
    """
    path = f"historical-rating/{symbol}"
    query_vars = {"apikey": apikey, "limit": limit}
    return __return_json_v3(path=path, query_vars=query_vars)

def discounted_cash_flow(
    apikey: str, symbol: str
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /discounted-cash-flow/ API.

    :param apikey: Your API key.
    :param symbol: Company ticker.
    :return: A list of dictionaries.
    """
    path = f"discounted-cash-flow/{symbol}"
    query_vars = {"apikey": apikey}
    return __return_json_v3(path=path, query_vars=query_vars)

def historical_discounted_cash_flow(
    apikey: str,
    symbol: str,
    period: str = "annual",
    limit: int = DEFAULT_LIMIT,
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /historical-discounted-cash-flow/ API.

    :param apikey: Your API key.
    :param symbol: Company ticker.
    :param period: 'annual' or 'quarter'
    :param limit: Number of rows to return.
    :return: A list of dictionaries.
    """
    path = f"historical-discounted-cash-flow/{symbol}"
    query_vars = {
        "apikey": apikey,
        "limit": limit,
        "period": __validate_period(value=period),
    }
    return __return_json_v3(path=path, query_vars=query_vars)

def historical_daily_discounted_cash_flow(
    apikey: str, symbol: str, limit: int = DEFAULT_LIMIT
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /historical-daily-discounted-cash-flow/ API.

    :param apikey: Your API key.
    :param symbol: Company ticker.
    :param limit: Number of rows to return.
    :return: A list of dictionaries.
    """
    path = f"historical-daily-discounted-cash-flow/{symbol}"
    query_vars = {"apikey": apikey, "limit": limit}
    return __return_json_v3(path=path, query_vars=query_vars)

def market_capitalization(
    apikey: str, symbol: str
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /market-capitalization/ API.

    :param apikey: Your API key.
    :param symbol: Company ticker.
    :return: A list of dictionaries.
    """
    path = f"market-capitalization/{symbol}"
    query_vars = {"apikey": apikey}
    return __return_json_v3(path=path, query_vars=query_vars)

def historical_market_capitalization(
    apikey: str, symbol: str, limit: int = DEFAULT_LIMIT
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /historical-market-capitalization/ API.

    :param apikey: Your API key.
    :param symbol: Company ticker.
    :param limit: Number of rows to return.
    :return: A list of dictionaries.
    """
    path = f"historical-market-capitalization/{symbol}"
    query_vars = {"apikey": apikey, "limit": limit}
    return __return_json_v3(path=path, query_vars=query_vars)

def symbols_list(apikey: str) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /stock/list/ API

    :param apikey: Your API key.
    :return: A list of dictionaries.
    """
    path = f"stock/list"
    query_vars = {"apikey": apikey}
    return __return_json_v3(path=path, query_vars=query_vars)

def stock_news(
    apikey: str,
    tickers: typing.Union[str, typing.List] = "",
    limit: int = DEFAULT_LIMIT,
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /stock_news/ API.

    :param apikey: Your API key.
    :param tickers: List of ticker symbols.
    :param limit: Number of rows to return.
    :return: A list of dictionaries.
    """
    path = f"stock_news"
    query_vars = {"apikey": apikey, "limit": limit}
    if tickers:
        if type(tickers) is list:
            tickers = ",".join(tickers)
        query_vars["tickers"] = tickers
    return __return_json_v3(path=path, query_vars=query_vars)

def earnings_surprises(
    apikey: str, symbol: str
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /earnings-surprises/ API.

    :param apikey: Your API key.
    :param symbol: Company ticker.
    :return: A list of dictionaries.
    """
    path = f"earnings-surprises/{symbol}"
    query_vars = {"apikey": apikey}
    return __return_json_v3(path=path, query_vars=query_vars)

def earning_call_transcript(
    apikey: str, symbol: str, year: int, quarter: int
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /earning_call_transcript/ API.

    :param apikey: Your API key.
    :param symbol: Company ticker.
    :param year: Year of the transcripts
    :param quarter: Quarter of the transcripts
    :return: A list of dictionaries.
    """
    path = f"earning_call_transcript/{symbol}"
    query_vars = {"apikey": apikey, "year": year, "quarter": quarter}
    return __return_json_v3(path=path, query_vars=query_vars)

def batch_earning_call_transcript(
    apikey: str, symbol: str, year: int
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /batch_earning_call_transcript/ API.

    :param apikey: Your API key.
    :param symbol: Company ticker.
    :param year: Year of the transcripts
    :return: A list of dictionaries.
    """
    path = f"batch_earning_call_transcript/{symbol}"
    query_vars = {"apikey": apikey, "year": year}
    return __return_json_v4(path=path, query_vars=query_vars)

def earning_call_transcripts_available_dates(
    apikey: str, symbol: str
) -> typing.Optional[typing.List[typing.List]]:
    """
    Query FMP /earning_call_transcript/ API.

    :param apikey: Your API key.
    :param symbol: Company ticker.
    :return: A list of lists.
    """
    path = f"earning_call_transcript"
    query_vars = {"apikey": apikey, "symbol": symbol}
    return __return_json_v4(path=path, query_vars=query_vars)

def sec_filings(
    apikey: str, symbol: str, filing_type: str = "", limit: int = DEFAULT_LIMIT
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /sec_filings/ API.

    :param apikey: Your API key.
    :param symbol: Company ticker.
    :param filing_type: Name of filing.
    :param limit: Number of rows to return.
    :return: A list of dictionaries.
    """
    path = f"sec_filings/{symbol}"
    query_vars = {"apikey": apikey, "type": filing_type, "limit": limit}
    return __return_json_v3(path=path, query_vars=query_vars)

def press_releases(
    apikey: str, symbol: str, limit: int = DEFAULT_LIMIT
) -> typing.Optional[typing.List[typing.Dict]]:
    """
    Query FMP /press-releases/ API.

    :param apikey: Your API key.
    :param symbol: Company ticker.
    :param limit: Number of rows to return.
    :return: A list of dictionaries.
    """
    path = f"press-releases/{symbol}"
    query_vars = {"apikey": apikey, "limit": limit}
    return __return_json_v3(path=path, query_vars=query_vars)
