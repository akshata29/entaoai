import logging, json, os
import azure.functions as func
import openai
import tempfile
import uuid
import pinecone
from redis.commands.search.field import VectorField, TagField, TextField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
import numpy as np
from typing import Any, Callable, Dict, List, Optional
import itertools
import json
import math
import os
import pandas as pd
import re
import requests
import tempfile
import zipfile
from bs4 import BeautifulSoup
from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout, RetryError
from tqdm import tqdm
from typing import List
from urllib3.util import Retry
import cssutils
from pathos.pools import ProcessPool
from lxml import html
from html.parser import HTMLParser
from Utilities.azureBlob import upsertMetadata, uploadBlob
from Utilities.envVars import *

redisUrl = "redis://default:" + RedisPassword + "@" + RedisAddress + ":" + RedisPort
regex_flags = re.IGNORECASE | re.DOTALL | re.MULTILINE

class HtmlStripper(HTMLParser):
    """
    Strips HTML tags
    """

    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)

    def strip_tags(self, html):
        self.feed(html)
        return self.get_data()
    
class ExtractItems:
    # def __init__(
    #         self,
    #         remove_tables: bool,
    #         items_to_extract: List,
    #         raw_files_folder: str,
    #         extracted_files_folder: str,
    #         skip_extracted_filings: bool
    # ):

    #     self.remove_tables = remove_tables
    #     self.items_list = [
    #         '1', '1A', '1B', '2', '3', '4', '5', '6', '7', '7A',
    #         '8', '9', '9A', '9B', '10', '11', '12', '13', '14', '15'
    #     ]
    #     self.items_to_extract = items_to_extract if items_to_extract else self.items_list
    #     self.raw_files_folder = raw_files_folder
    #     self.extracted_files_folder = extracted_files_folder
    #     self.skip_extracted_filings = skip_extracted_filings

    @staticmethod
    def strip_html(html_content):
        """
        Strips the html content to get clean text
        :param html_content: The HTML content
        :return: The clean HTML content
        """

        # TODO: Check if flags are required in the following regex
        html_content = re.sub(r'(<\s*/\s*(div|tr|p|li|)\s*>)', r'\1\n\n', html_content)
        html_content = re.sub(r'(<br\s*>|<br\s*/>)', r'\1\n\n', html_content)
        html_content = re.sub(r'(<\s*/\s*(th|td)\s*>)', r' \1 ', html_content)
        html_content = HtmlStripper().strip_tags(html_content)


        return html_content

    @staticmethod
    def remove_multiple_lines(text):
        """
        Replaces consecutive new lines with a single new line
        and consecutive whitespace characters with a single whitespace
        :param text: String containing the financial text
        :return: String without multiple newlines
        """

        text = re.sub(r'(( )*\n( )*){2,}', '#NEWLINE', text)
        text = re.sub(r'\n', ' ', text)
        text = re.sub(r'(#NEWLINE)+', '\n', text).strip()
        text = re.sub(r'[ ]{2,}', ' ', text)

        return text

    @staticmethod
    def clean_text(text):
        """
        Clean the text of various unnecessary blocks of text
        Substitute various special characters
        :param text: Raw text string
        :return: String containing normalized, clean text
        """

        text = re.sub(r'[\xa0]', ' ', text)
        text = re.sub(r'[\u200b]', ' ', text)

        text = re.sub(r'[\x91]', '‘', text)
        text = re.sub(r'[\x92]', '’', text)
        text = re.sub(r'[\x93]', '“', text)
        text = re.sub(r'[\x94]', '”', text)
        text = re.sub(r'[\x95]', '•', text)
        text = re.sub(r'[\x96]', '-', text)
        text = re.sub(r'[\x97]', '-', text)
        text = re.sub(r'[\x98]', '˜', text)
        text = re.sub(r'[\x99]', '™', text)

        text = re.sub(r'[\u2010\u2011\u2012\u2013\u2014\u2015]', '-', text)

        def remove_whitespace(match):
            ws = r'[^\S\r\n]'
            return f'{match[1]}{re.sub(ws, r"", match[2])}{match[3]}{match[4]}'

        # Fix broken section headers
        text = re.sub(r'(\n[^\S\r\n]*)(P[^\S\r\n]*A[^\S\r\n]*R[^\S\r\n]*T)([^\S\r\n]+)((\d{1,2}|[IV]{1,2})[AB]?)',
                      remove_whitespace, text, flags=re.IGNORECASE)
        text = re.sub(r'(\n[^\S\r\n]*)(I[^\S\r\n]*T[^\S\r\n]*E[^\S\r\n]*M)([^\S\r\n]+)(\d{1,2}[AB]?)',
                      remove_whitespace, text, flags=re.IGNORECASE)

        text = re.sub(r'(ITEM|PART)(\s+\d{1,2}[AB]?)([\-•])', r'\1\2 \3 ', text, flags=re.IGNORECASE)

        # Remove unnecessary headers
        text = re.sub(r'\n[^\S\r\n]*'
                      r'(TABLE\s+OF\s+CONTENTS|INDEX\s+TO\s+FINANCIAL\s+STATEMENTS|BACK\s+TO\s+CONTENTS|QUICKLINKS)'
                      r'[^\S\r\n]*\n',
                      '\n', text, flags=regex_flags)

        # Remove page numbers and headers
        text = re.sub(r'\n[^\S\r\n]*[-‒–—]*\d+[-‒–—]*[^\S\r\n]*\n', '\n', text, flags=regex_flags)
        text = re.sub(r'\n[^\S\r\n]*\d+[^\S\r\n]*\n', '\n', text, flags=regex_flags)

        text = re.sub(r'[\n\s]F[-‒–—]*\d+', '', text, flags=regex_flags)
        text = re.sub(r'\n[^\S\r\n]*Page\s[\d*]+[^\S\r\n]*\n', '', text, flags=regex_flags)

        return text

    @staticmethod
    def calculate_table_character_percentages(table_text):
        """
        Calculate character type percentages contained in the table text
        :param table_text: The table text
        :return non_blank_digits_percentage: Percentage of digit characters
        :return spaces_percentage: Percentage of space characters
        """
        digits = sum(c.isdigit() for c in table_text)
        # letters   = sum(c.isalpha() for c in table_text)
        spaces = sum(c.isspace() for c in table_text)

        if len(table_text) - spaces:
            non_blank_digits_percentage = digits / (len(table_text) - spaces)
        else:
            non_blank_digits_percentage = 0

        if len(table_text):
            spaces_percentage = spaces / len(table_text)
        else:
            spaces_percentage = 0

        return non_blank_digits_percentage, spaces_percentage

    @staticmethod
    def remove_html_tables(items_to_extract, doc_10k, is_html):
        """
        Remove HTML tables that contain numerical data
        Note that there are many corner-cases in the tables that have text data instead of numerical
        :param doc_10k: The 10-K html
        :param is_html: Whether the document contains html code or just plain text
        :return: doc_10k: The 10-K html without numerical tables
        """

        if is_html:
            tables = doc_10k.find_all('table')

            items_list = []
            for item_index in items_to_extract:
                if item_index == '9A':
                    item_index = item_index.replace('A', r'[^\S\r\n]*A(?:\(T\))?')
                elif 'A' in item_index:
                    item_index = item_index.replace('A', r'[^\S\r\n]*A')
                elif 'B' in item_index:
                    item_index = item_index.replace('B', r'[^\S\r\n]*B')
                items_list.append(item_index)

            # Detect tables that have numerical data
            for tbl in tables:

                tbl_text = ExtractItems.clean_text(ExtractItems.strip_html(str(tbl)))
                item_index_found = False
                for item_index in items_list:
                    if len(list(re.finditer(rf'\n[^\S\r\n]*ITEM\s+{item_index}[.*~\-:\s]', tbl_text, flags=regex_flags))) > 0:
                        item_index_found = True
                        break
                if item_index_found:
                    continue

                trs = tbl.find_all('tr', attrs={'style': True}) + \
                      tbl.find_all('td', attrs={'style': True}) + \
                      tbl.find_all('th', attrs={'style': True})

                background_found = False

                for tr in trs:
                    # Parse given cssText which is assumed to be the content of a HTML style attribute
                    style = cssutils.parseStyle(tr['style'])

                    if (style['background']
                        and style['background'].lower() not in ['none', 'transparent', '#ffffff', '#fff', 'white']) \
                        or (style['background-color']
                            and style['background-color'].lower() not in ['none', 'transparent', '#ffffff', '#fff', 'white']):
                        background_found = True
                        break

                trs = tbl.find_all('tr', attrs={'bgcolor': True}) + tbl.find_all('td', attrs={
                    'bgcolor': True}) + tbl.find_all('th', attrs={'bgcolor': True})

                bgcolor_found = False
                for tr in trs:
                    if tr['bgcolor'].lower() not in ['none', 'transparent', '#ffffff', '#fff', 'white']:
                        bgcolor_found = True
                        break

                if bgcolor_found or background_found:
                    tbl.decompose()

        else:
            doc_10k = re.sub(r'<TABLE>.*?</TABLE>', '', str(doc_10k), flags=regex_flags)

        return doc_10k

    @staticmethod
    def parse_item(items_to_extract, text, item_index, next_item_list, positions):
        """
        Parses Item N for a 10-K text
        :param text: The 10-K text
        :param item_index: Number of the requested Item/Section of the 10-K text
        :param next_item_list: List of possible next 10-K item sections
        :param positions: List of the end positions of previous item sections
        :return: item_section: The item/section as a text string
        """

        if item_index == '9A':
            item_index = item_index.replace('A', r'[^\S\r\n]*A(?:\(T\))?')
        elif 'A' in item_index:
            item_index = item_index.replace('A', r'[^\S\r\n]*A')
        elif 'B' in item_index:
            item_index = item_index.replace('B', r'[^\S\r\n]*B')

        # Depending on the item_index, search for subsequent sections.

        # There might be many 'candidate' text sections between 2 Items.
        # For example, the Table of Contents (ToC) still counts as a match when searching text between 'Item 3' and 'Item 4'
        # But we do NOT want that specific text section; We want the detailed section which is *after* the ToC

        possible_sections_list = []
        for next_item_index in next_item_list:
            if possible_sections_list:
                break
            if next_item_index == '9A':
                next_item_index = next_item_index.replace('A', r'[^\S\r\n]*A(?:\(T\))?')
            elif 'A' in next_item_index:
                next_item_index = next_item_index.replace('A', r'[^\S\r\n]*A')
            elif 'B' in next_item_index:
                next_item_index = next_item_index.replace('B', r'[^\S\r\n]*B')

            for match in list(re.finditer(rf'\n[^\S\r\n]*ITEM\s+{item_index}[.*~\-:\s]', text, flags=regex_flags)):
                offset = match.start()

                possible = list(re.finditer(
                    rf'\n[^\S\r\n]*ITEM\s+{item_index}[.*~\-:\s].+?([^\S\r\n]*ITEM\s+{str(next_item_index)}[.*~\-:\s])',
                    text[offset:], flags=regex_flags))
                if possible:
                    possible_sections_list += [(offset, possible)]

        # Extract the wanted section from the text
        item_section, positions = ExtractItems.get_item_section(possible_sections_list, text, positions)

        # If item is the last one (usual case when dealing with EDGAR's old .txt files), get all the text from its beginning until EOF.
        if positions:
            if item_index in items_to_extract and item_section == '':
                item_section = ExtractItems.get_last_item_section(item_index, text, positions)
            elif item_index == '15':  # Item 15 is the last one, get all the text from its beginning until EOF
                item_section = ExtractItems.get_last_item_section(item_index, text, positions)

        return item_section.strip(), positions

    @staticmethod
    def get_item_section(possible_sections_list, text, positions):
        """
        Throughout a list of all the possible item sections, it returns the biggest one, which (probably) is the correct one.
        :param possible_sections_list: List containing all the possible sections betweewn Item X and Item Y
        :param text: The whole text
        :param positions: List of the end positions of previous item sections
        :return: The correct section
        """

        item_section = ''
        max_match_length = 0
        max_match = None
        max_match_offset = None

        # Find the match with the largest section
        for (offset, matches) in possible_sections_list:
            for match in matches:
                match_length = match.end() - match.start()
                if positions:
                    if match_length > max_match_length and offset + match.start() >= positions[-1]:
                        max_match = match
                        max_match_offset = offset
                        max_match_length = match_length
                elif match_length > max_match_length:
                    max_match = match
                    max_match_offset = offset
                    max_match_length = match_length

        # Return the text section inside that match
        if max_match:
            if positions:
                if max_match_offset + max_match.start() >= positions[-1]:
                    item_section = text[max_match_offset + max_match.start(): max_match_offset + max_match.regs[1][0]]
            else:
                item_section = text[max_match_offset + max_match.start(): max_match_offset + max_match.regs[1][0]]
            positions.append(max_match_offset + max_match.end() - len(max_match[1]) - 1)

        return item_section, positions

    @staticmethod
    def get_last_item_section(item_index, text, positions):
        """
        Returns the text section starting through a given item. This is useful in cases where Item 15 is the last item
        and there is no Item 16 to indicate its ending. Also, it is useful in cases like EDGAR's old .txt files
        (mostly before 2005), where there there is no Item 15; thus, ITEM 14 is the last one there.
        :param item_index: The index of the item/section in the 10-K ('14' or '15')
        :param text: The whole 10-K text
        :param positions: List of the end positions of previous item sections
        :return: All the remaining text until the end, starting from the specified item_index
        """

        item_list = list(re.finditer(rf'\n[^\S\r\n]*ITEM\s+{item_index}[.\-:\s].+?', text, flags=regex_flags))

        item_section = ''
        for item in item_list:
            if item.start() >= positions[-1]:
                item_section = text[item.start():].strip()
                break

        return item_section

    @staticmethod
    def extract_items(filing_metadata, remove_tables, items_to_extract, raw_files_folder):
        try:
            """
            Extracts all items/sections for a 10-K file and writes it to a CIK_10K_YEAR.json file (eg. 1384400_10K_2017.json)
            :param filing_metadata: a pandas series containing all filings metadata
            """

            absolute_10k_filename = os.path.join(raw_files_folder, filing_metadata['filename'])
            logging.info(f'Extracting items from {absolute_10k_filename}...')

            with open(absolute_10k_filename, 'r', errors='backslashreplace') as file:
                content = file.read()

            # Remove all embedded pdfs that might be seen in few old 10-K txt annual reports
            content = re.sub(r'<PDF>.*?</PDF>', '', content, flags=regex_flags)

            documents = re.findall('<DOCUMENT>.*?</DOCUMENT>', content, flags=regex_flags)

            doc_10k = None
            found_10k, is_html = False, False
            for doc in documents:
                doc_type = re.search(r'\n[^\S\r\n]*<TYPE>(.*?)\n', doc, flags=regex_flags)
                doc_type = doc_type.group(1) if doc_type else None
                if doc_type.startswith('10'):
                    doc_10k = BeautifulSoup(doc, 'lxml')
                    is_html = (True if doc_10k.find('td') else False) and (True if doc_10k.find('tr') else False)
                    if not is_html:
                        doc_10k = doc
                    found_10k = True
                    break

            if not found_10k:
                if documents:
                    logging.info(f'\nCould not find document type 10K for {filing_metadata["filename"]}')
                doc_10k = BeautifulSoup(content, 'lxml')
                is_html = (True if doc_10k.find('td') else False) and (True if doc_10k.find('tr') else False)
                if not is_html:
                    doc_10k = content

            # if not is_html and not documents:
            if filing_metadata['filename'].endswith('txt') and not documents:
                logging.info(f'\nNo <DOCUMENT> tag for {filing_metadata["filename"]}')

            # For non html clean all table items
            if remove_tables:
                doc_10k = ExtractItems.remove_html_tables(items_to_extract, doc_10k, is_html=is_html)

            json_content = {
                'cik': filing_metadata['CIK'],
                'company': filing_metadata['Company'],
                'filing_type': filing_metadata['Type'],
                'filing_date': filing_metadata['Date'],
                'period_of_report': filing_metadata['Period of Report'],
                'sic': filing_metadata['SIC'],
                'state_of_inc': filing_metadata['State of Inc'],
                'state_location': filing_metadata['State location'],
                'fiscal_year_end': filing_metadata['Fiscal Year End'],
                'filing_html_index': filing_metadata['html_index'],
                'htm_filing_link': filing_metadata['htm_file_link'],
                'complete_text_filing_link': filing_metadata['complete_text_file_link'],
                'filename': filing_metadata['filename']
            }
            for item_index in items_to_extract:
                json_content[f'item_{item_index}'] = ''

            text = ExtractItems.strip_html(str(doc_10k))
            text = ExtractItems.clean_text(text)

            positions = []
            all_items_null = True
            for i, item_index in enumerate(items_to_extract):
                next_item_list = items_to_extract[i+1:]
                item_section, positions = ExtractItems.parse_item(items_to_extract, text, item_index, next_item_list, positions)
                item_section = ExtractItems.remove_multiple_lines(item_section)

                if item_index in items_to_extract:
                    if item_section != '':
                        all_items_null = False
                    json_content[f'item_{item_index}'] = item_section

            if all_items_null:
                logging.info(f'\nCould not extract any item for {absolute_10k_filename}')
                return None

            return json_content
        except Exception as e:
            logging.info("Exception in Process Items " + str(e))


    @staticmethod
    def process_filing(filing_metadata, remove_tables, items_to_extract, raw_files_folder, extracted_files_folder, skip_extracted_filings):
        try:
            json_filename = f'{filing_metadata["filename"].split(".")[0]}.json'
            logging.info(f'Processing {json_filename}...')
            absolute_json_filename = os.path.join(extracted_files_folder, json_filename)
            if skip_extracted_filings and os.path.exists(absolute_json_filename):
                return 0

            logging.info("Extract Items")
            json_content = ExtractItems.extract_items(filing_metadata, remove_tables, items_to_extract, raw_files_folder)

            if json_content is not None:
                with open(absolute_json_filename, 'w') as filepath:
                    json.dump(json_content, filepath, indent=4)
        except Exception as e:
            logging.info("Exception in Process Filing " + str(e))

        return 1
    
def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    logging.info(f'{context.function_name} HTTP trigger function processed a request.')
    if hasattr(context, 'retry_context'):
        logging.info(f'Current retry count: {context.retry_context.retry_count}')

        if context.retry_context.retry_count == context.retry_context.max_retry_count:
            logging.info(
                f"Max retries of {context.retry_context.max_retry_count} for "
                f"function {context.function_name} has been reached")

    try:
        indexType = req.params.get('indexType')
        indexNs = req.params.get('indexNs')
        body = json.dumps(req.get_json())
    except ValueError:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

    if body:
        pinecone.init(
            api_key=PineconeKey,  # find at app.pinecone.io
            environment=PineconeEnv  # next to api key in console
        )

        # Once we can get the Milvus index running in Azure, we can use this

        result = ComposeResponse(indexType, indexNs, body)
        return func.HttpResponse(result, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

def ComposeResponse(indexType, indexNs, jsonData):
    values = json.loads(jsonData)['values']

    logging.info("Calling Compose Response")
    # Prepare the Output before the loop
    results = {}
    results["values"] = []

    for value in values:
        outputRecord = TransformValue(indexType, indexNs, value)
        if outputRecord != None:
            results["values"].append(outputRecord)
    return json.dumps(results, ensure_ascii=False)

def requestRetrySession(
		retries=5,
		backoff_factor=0.5,
		status_forcelist=(400, 401, 403, 500, 502, 503, 504, 505),
		session=None
):
	"""
	Retries the HTTP GET method in case of some specific HTTP errors.
	:param retries: Time of retries
	:param backoff_factor: The amount of delay after each retry
	:param status_forcelist: The error codes that the script should retry; Otherwise, it won't retry
	:param session: the requests session
	:return: the new session
	"""
	session = session or requests.Session()
	retry = Retry(
		total=retries,
		read=retries,
		connect=retries,
		backoff_factor=backoff_factor,
		status_forcelist=status_forcelist,
	)
	adapter = HTTPAdapter(max_retries=retry)
	session.mount('http://', adapter)
	session.mount('https://', adapter)
	return session

def download(
		url,
		filename,
		download_folder,
		user_agent
):
	"""
	Downloads the filing to the specified directory with the naming convention below:
	<CIK-KEY_YEAR_FILING-TYPE.EXTENSION_TYPE> (e.g.: 1000229_2018_10K.html)
	:param url: The URL to download
	:param filename: The Central Index Key (CIK) of the company
	:param download_folder:
	:param user_agent: the User-agent that will be declared to SEC EDGAR
	Note that we save files based on the years that they report to
	Most companies submit their reports on the end of December of the current year (2021 for example)
	However, if a company submits its report on the start of the next year (2022), then
	this will be saved as COMPANY_CIK_FILING-TYPE_2022.htm
	"""

	filepath = os.path.join(download_folder, filename)

	try:
		retries_exceeded = True
		for _ in range(5):
			session = requests.Session()
			request = requestRetrySession(
				retries=5, backoff_factor=0.2, session=session
			).get(url=url, headers={'User-agent': user_agent})
			# request = requests.get(html_index, headers={'User-Agent': ua.random})

			if 'will be managed until action is taken to declare your traffic.' not in request.text:
				retries_exceeded = False
				break

		if retries_exceeded:
			logging.debug(f'Retries exceeded, could not download "{filename}" - "{url}"')
			return False

	except (RequestException, HTTPError, ConnectionError, Timeout, RetryError) as err:
		logging.debug(f'Request for {url} failed due to network-related error: {err}')
		return False

	with open(filepath, 'wb') as f:
		f.write(request.content)

	# Check that MD5 hash is correct
	# if hashlib.md5(open(filepath, 'rb').read()).hexdigest() != headers._headers[1][1].strip('"'):
	# 	LOGGER.info(f'Wrong MD5 hash for file: {abs_filename} - {url}')

	return True

def crawl(
		filing_types,
		series,
		raw_filings_folder,
		user_agent
):
	"""
	Crawls the EDGAR HTML indexes
	:param filing_types: list of filing types to download
	:param series: A single series with info for specific filings
	:param raw_filings_folder: Raw filings folder path
	:param user_agent: the User-agent that will be declared to SEC EDGAR
	:return: the .htm or .txt files
	"""

	html_index = series['html_index']

	# Create a BeautifulSoup instance using the 'lxml' parser
	try:
		retries_exceeded = True
		for _ in range(5):
			session = requests.Session()
			request = requestRetrySession(
				retries=5, backoff_factor=0.2, session=session
			).get(url=html_index, headers={'User-agent': user_agent})

			if 'will be managed until action is taken to declare your traffic.' not in request.text:
				retries_exceeded = False
				break

		if retries_exceeded:
			logging.debug(f'Retries exceeded, could not download "{html_index}"')
			return None

	except (RequestException, HTTPError, ConnectionError, Timeout, RetryError) as err:
		logging.debug(f'Request for {html_index} failed due to network-related error: {err}')
		return None

	soup = BeautifulSoup(request.content, 'lxml')

	# Crawl the soup and search it later for the Period of Report
	try:
		list_of_forms = soup.find_all('div', {'class': ['infoHead', 'info']})
	except (HTMLParseError, Exception) as e:
		list_of_forms = None

	period_of_report = None
	for form in list_of_forms:
		if form.attrs['class'][0] == 'infoHead' and form.text == 'Filing Date':
			series['Filing Date'] = form.nextSibling.nextSibling.text

		if form.attrs['class'][0] == 'infoHead' and form.text == 'Period of Report':
			period_of_report = form.nextSibling.nextSibling.text
			series['Period of Report'] = period_of_report

	if period_of_report is None:
		logging.debug(f'Can not crawl "Period of Report" for {html_index}')
		return None

	# Assign metadata to dataframe
	try:
		company_info = soup.find('div', {'class': ['companyInfo']}).find('p', {'class': ['identInfo']}).text
	except (HTMLParseError, Exception) as e:
		company_info = None

	try:
		for info in company_info.split('|'):
			info_splits = info.split(':')
			if info_splits[0].strip() in ['State of Incorp.', 'State of Inc.', 'State of Incorporation.']:
				series['State of Inc'] = info_splits[1].strip()
			if info_splits[0].strip() == ['State location']:
				series['State location'] = info_splits[1].strip()
	except (ValueError, Exception) as e:
		pass

	fiscal_year_end_regex = re.search(r'Fiscal Year End: *(\d{4})', company_info)
	if fiscal_year_end_regex is not None:
		series['Fiscal Year End'] = fiscal_year_end_regex.group(1)

	# Crawl for the Sector Industry Code (SIC)
	try:
		sic = soup.select_one('.identInfo a[href*="SIC"]')
		if sic is not None:
			series['SIC'] = sic.text
	except (HTMLParseError, Exception) as e:
		pass

	# https://www.sec.gov/cgi-bin/browse-edgar?CIK=0001000228
	# https://data.sec.gov/submissions/CIK0001000228.json
	with open(os.path.join('', 'companies_info.json')) as f:
		company_info_dict = json.load(fp=f)

	cik = series['CIK']
	if cik not in company_info_dict:
		company_url = f"https://www.sec.gov/cgi-bin/browse-edgar?CIK={cik}"
		try:
			retries_exceeded = True
			for _ in range(5):
				session = requests.Session()
				request = requestRetrySession(
					retries=5, backoff_factor=0.2, session=session
				).get(url=company_url, headers={'User-agent': user_agent})

				if 'will be managed until action is taken to declare your traffic.' not in request.text:
					retries_exceeded = False
					break

			if retries_exceeded:
				logging.debug(f'Retries exceeded, could not download "{company_url}"')
				return None

		except (RequestException, HTTPError, ConnectionError, Timeout, RetryError) as err:
			logging.debug(f'Request for {company_url} failed due to network-related error: {err}')
			return None

		company_info_dict[cik] = {
			'Company Name': None,
			'SIC': None,
			'State location': None,
			'State of Inc': None,
			'Fiscal Year End': None
		}
		company_info_soup = BeautifulSoup(request.content, 'lxml')

		company_info = company_info_soup.find('div', {'class': ['companyInfo']})
		if company_info is not None:
			company_info_dict[cik]['Company Name'] = str(company_info.find('span', {'class': ['companyName']}).contents[0]).strip()
			company_info_contents = company_info.find('p', {'class': ['identInfo']}).contents

			for idx, content in enumerate(company_info_contents):
				if ';SIC=' in str(content):
					company_info_dict[cik]['SIC'] = content.text
				if ';State=' in str(content):
					company_info_dict[cik]['State location'] = content.text
				if 'State of Inc' in str(content):
					company_info_dict[cik]['State of Inc'] = company_info_contents[idx + 1].text
				if 'Fiscal Year End' in str(content):
					company_info_dict[cik]['Fiscal Year End'] = str(content).split()[-1]

		with open(os.path.join('', 'companies_info.json'), 'w') as f:
			json.dump(obj=company_info_dict, fp=f, indent=4)

	if pd.isna(series['SIC']):
		series['SIC'] = company_info_dict[cik]['SIC']
	if pd.isna(series['State of Inc']):
		series['State of Inc'] = company_info_dict[cik]['State of Inc']
	if pd.isna(series['State location']):
		series['State location'] = company_info_dict[cik]['State location']
	if pd.isna(series['Fiscal Year End']):
		series['Fiscal Year End'] = company_info_dict[cik]['Fiscal Year End']

	# Crawl the soup for the financial files
	try:
		all_tables = soup.find_all('table')
	except (HTMLParseError, Exception) as e:
		return None

	'''
	Tables are of 2 kinds. 
	The 'Document Format Files' table contains all the htms, jpgs, pngs and txts for the reports.
	The 'Data Format Files' table contains all the xml instances that contain structured information.
	'''
	for table in all_tables:

		# Get the htm/html/txt files
		if table.attrs['summary'] == 'Document Format Files':
			htm_file_link, complete_text_file_link, link_to_download = None, None, None
			filing_type = None

			for tr in table.find_all('tr')[1:]:
				# If it's the specific document type (e.g. 10-K)
				if tr.contents[7].text in filing_types:
					filing_type = tr.contents[7].text
					if tr.contents[5].contents[0].attrs['href'].split('.')[-1] in ['htm', 'html']:
						htm_file_link = 'https://www.sec.gov' + tr.contents[5].contents[0].attrs['href']
						series['htm_file_link'] = str(htm_file_link)
						break

				# Else get the complete submission text file
				elif tr.contents[3].text == 'Complete submission text file':
					filing_type = series['Type']
					complete_text_file_link = 'https://www.sec.gov' + tr.contents[5].contents[0].attrs['href']
					series['complete_text_file_link'] = str(complete_text_file_link)
					break

			if htm_file_link is not None:
				# In case of iXBRL documents, a slight URL modification is required
				if 'ix?doc=/' in htm_file_link:
					link_to_download = htm_file_link.replace('ix?doc=/', '')
					series['htm_file_link'] = link_to_download
					file_extension = "htm"
				else:
					link_to_download = htm_file_link
					file_extension = htm_file_link.split('.')[-1]

			elif complete_text_file_link is not None:
				link_to_download = complete_text_file_link
				file_extension = link_to_download.split('.')[-1]

			if link_to_download is not None:
				filing_type = re.sub(r"[\-/\\]", '', filing_type)
				accession_num = os.path.splitext(os.path.basename(series['complete_text_file_link']))[0]
				filename = f"{str(series['CIK'])}_{filing_type}_{period_of_report[:4]}_{accession_num}.{file_extension}"

				# Download the file
				success = download(
					url=link_to_download,
					filename=filename,
					download_folder=raw_filings_folder,
					user_agent=user_agent
				)
				if success:
					series['filename'] = filename
				else:
					return None
			else:
				return None

	return series

def getSpecificIndicies(
		tsv_filenames,
		filing_types,
		user_agent,
		cik_tickers=None,
):
	"""
	Loops through all the indexes and keeps only the rows/Series for the specific filing types
	:param tsv_filenames: the indices filenames
	:param filing_types: list of filing types to download. e.g. ['10-K', '10-K405', '10-KT']
	:param user_agent: the User-agent that will be declared to SEC EDGAR
	:param cik_tickers: list of CIKs or Tickers
	:return: a final dataframe which has Series only for the specific indices
	"""

	ciks = []

	if cik_tickers is not None:
		if isinstance(cik_tickers, str):
			if os.path.exists(cik_tickers) and os.path.isfile(cik_tickers):  # If filepath
				with open(cik_tickers) as f:
					cik_tickers = [line.strip() for line in f.readlines() if line.strip() != '']
			else:
				logging.debug(f'Please provide a valid cik_ticker file path')

	if isinstance(cik_tickers, List) and len(cik_tickers):
		company_tickers_url = 'https://www.sec.gov/files/company_tickers.json'

		session = requests.Session()
		try:
			request = requestRetrySession(
				retries=5, backoff_factor=0.2, session=session
			).get(url=company_tickers_url, headers={'User-agent': user_agent})
		except (RequestException, HTTPError, ConnectionError, Timeout, RetryError) as err:
			logging.info(f'Failed downloading "{company_tickers_url}" - {err}')

		company_tickers = json.loads(request.content)
		ticker2cik = {company['ticker']: company['cik_str'] for company in company_tickers.values()}
		ticker2cik = dict(sorted(ticker2cik.items(), key=lambda item: item[0]))

		for c_t in cik_tickers:
			if isinstance(c_t, int) or c_t.isdigit():  # If CIK
				ciks.append(str(c_t))
			else:
				if c_t in ticker2cik:
					ciks.append(str(ticker2cik[c_t]))  # If Ticker
				else:
					logging.debug(f'Could not find CIK for "{c_t}"')

	dfs_list = []

	for filepath in tsv_filenames:
		#logging.info(f'Loading index file: {filepath} ...')
		# Load the index file
		df = pd.read_csv(
			filepath,
			sep='|',
			header=None,
			dtype=str,
			names=[
				'CIK', 'Company', 'Type', 'Date', 'complete_text_file_link', 'html_index',
				'Filing Date', 'Period of Report', 'SIC', 'htm_file_link',
				'State of Inc', 'State location', 'Fiscal Year End', 'filename'
			]
		)

		df['complete_text_file_link'] = 'https://www.sec.gov/Archives/' + df['complete_text_file_link'].astype(str)
		df['html_index'] = 'https://www.sec.gov/Archives/' + df['html_index'].astype(str)

		# Filter by filing type
		df = df[df.Type.isin(filing_types)]

		# Filter by CIK
		if len(ciks):
			df = df[(df.CIK.isin(ciks))]

		dfs_list.append(df)

	return pd.concat(dfs_list) if (len(dfs_list) > 1) else dfs_list[0]

def downloadIndices(
		start_year: int,
		end_year: int,
		quarters: List,
		skip_present_indices: bool,
		indices_folder: str,
		user_agent: str
):
	base_url = "https://www.sec.gov/Archives/edgar/full-index/"

	logging.info('Downloading EDGAR Index files')

	for quarter in quarters:
		if quarter not in [1, 2, 3, 4]:
			raise Exception(f'Invalid quarter "{quarter}"')

	first_iteration = True
	while True:
		failed_indices = []
		for year in range(start_year, end_year + 1):
			for quarter in quarters:
				if year == datetime.now().year and quarter > math.ceil(datetime.now().month / 3):
					break
				index_filename = f'{year}_QTR{quarter}.tsv'
				if skip_present_indices and os.path.exists(os.path.join(indices_folder, index_filename)):
					if first_iteration:
						logging.info(f'Skipping {index_filename}')
					continue

				url = f'{base_url}/{year}/QTR{quarter}/master.zip'

				with tempfile.TemporaryFile(mode="w+b") as tmp:
					session = requests.Session()
					try:
						request = requestRetrySession(
							retries=5, backoff_factor=0.2, session=session
						).get(url=url, headers={'User-agent': user_agent})
					except requests.exceptions.RetryError as e:
						logging.info(f'Failed downloading "{index_filename}" - {e}')
						failed_indices.append(index_filename)
						continue

					tmp.write(request.content)
					with zipfile.ZipFile(tmp).open("master.idx") as f:
						lines = [line.decode('latin-1') for line in itertools.islice(f, 11, None)]
						lines = [line.strip() + '|' + line.split('|')[-1].replace('.txt', '-index.html') for line in lines]

					with open(os.path.join(indices_folder, index_filename), 'w+', encoding='utf-8') as f:
						f.write(''.join(lines))
						logging.info(f'{index_filename} downloaded')

		first_iteration = False
		if len(failed_indices) > 0:
			logging.info(f'Could not download the following indices:\n{failed_indices}')
			user_input = input('Retry (Y/N): ')
			if user_input in ['Y', 'y', 'yes']:
				logging.info(f'Retry downloading failed indices')
			else:
				break
		else:
			break
		
def EdgarIngestion(indexType, indexNs, value):
    try:
        """
        The main method iterates all over the tsv index files that are generated
        and calls a crawler method for each one of them.
        """

        config = json.loads(json.dumps(value))['edgar_crawler']
        extractConfig = json.loads(json.dumps(value))['extract_items']

        raw_filings_folder = os.path.join(tempfile.gettempdir(), config['raw_filings_folder'])
        indices_folder = os.path.join(tempfile.gettempdir(), config['indices_folder'])

        if len(config['filing_types']) == 0:
            logging.info(f'Please provide at least one filing type')
            return "Please provide at least one filing type"

        # If the indices and/or download folder doesn't exist, create them
        if not os.path.isdir(indices_folder):
            os.mkdir(indices_folder)
        if not os.path.isdir(raw_filings_folder):
            os.mkdir(raw_filings_folder)

        if not os.path.isfile(os.path.join('', 'companies_info.json')):
            with open(os.path.join('', 'companies_info.json'), 'w') as f:
                json.dump(obj={}, fp=f)

        downloadIndices(
            start_year=config['start_year'],
            end_year=config['end_year'],
            quarters=config['quarters'],
            skip_present_indices=config['skip_present_indices'],
            indices_folder=indices_folder,
            user_agent=config['user_agent']
        )

      # Filter out years that are not related
        tsv_filenames = []
        for year in range(config['start_year'], config['end_year'] + 1):
            for quarter in config['quarters']:
                filepath = os.path.join(indices_folder, f'{year}_QTR{quarter}.tsv')

                if os.path.isfile(filepath):
                    tsv_filenames.append(filepath)

        logging.info(tsv_filenames)
        # Get the indices that are specific to your needs
        df = getSpecificIndicies(
                tsv_filenames=tsv_filenames,
                filing_types=config['filing_types'],
                cik_tickers=config['cik_tickers'],
                user_agent=config['user_agent']
        )

        logging.info(df)
        old_df = df
        series_to_download = []
        for _, series in tqdm(df.iterrows(), total=len(df), ncols=100):
            series_to_download.append((series.to_frame()).T)      
      
        df = pd.concat(series_to_download) if (len(series_to_download) > 1) else series_to_download[0]
        # Make a list for each series of them
        list_of_series = []
        for i in range(len(df)):
            list_of_series.append(df.iloc[i])
            logging.info(f'\nDownloading {len(df)} filings...\n')
	    
        final_series = []
        for series in tqdm(list_of_series, ncols=100):
            series = crawl(
                series=series,
                filing_types=config['filing_types'],
                raw_filings_folder=raw_filings_folder,
                user_agent=config['user_agent']
            )
            if series is not None:
                final_series.append((series.to_frame()).T)
                final_df = pd.concat(final_series) if (len(final_series) > 1) else final_series[0]

        filingMetadata = final_df.to_json(orient="records")
        #logging.info(f'\nFilings metadata exported to {filingMetadata}')

        if len(final_series) < len(list_of_series):
            logging.info(
                f'\nDownloaded {len(final_series)} / {len(list_of_series)} filings. '
                f'Rerun the script to retry downloading the failed filings.'
            )
	    

        filingMetadataDf = final_df.replace({np.nan: None})

        extracted_filings_folder = os.path.join(tempfile.gettempdir(), extractConfig['extracted_filings_folder'])

        if not os.path.isdir(extracted_filings_folder):
            os.mkdir(extracted_filings_folder)

        logging.info(f'Starting extraction...\n')

        listOfSeries = list(zip(*filingMetadataDf.iterrows()))[1]

        removeTables = extractConfig['remove_tables']
        itemsToExtract = extractConfig['items_to_extract']
        skipExtractedFilings = extractConfig['skip_extracted_filings']

        extractedFilings = []
        for series in listOfSeries:
            extractedItems = ExtractItems.extract_items(series, remove_tables=removeTables, items_to_extract=itemsToExtract, 
                                                    raw_files_folder=raw_filings_folder)
            logging.info("Extracted the data")
            jsonFileName = f'{series["filename"].split(".")[0]}.json'
            logging.info("Json file name is " + jsonFileName)
            uploadBlob(OpenAiDocConnStr, SecDocContainer, series['CIK'] + '\\' + jsonFileName, json.dumps(extractedItems), "application/json")
            metadata = {'embedded': 'false'}
            upsertMetadata(OpenAiDocConnStr, SecDocContainer, series['CIK'] + '\\' + jsonFileName, metadata)
            #extractedFilings.append(extractedItems)

        # extraction = ExtractItems(
        #     remove_tables=extractConfig['remove_tables'],
        #     items_to_extract=extractConfig['items_to_extract'],
        #     raw_files_folder=raw_filings_folder,
        #     extracted_files_folder=extracted_filings_folder,
        #     skip_extracted_filings=extractConfig['skip_extracted_filings']
        # )

        # with ProcessPool(processes=1) as pool:
        #     processed = list(tqdm(
        #         pool.imap(extraction.process_filing, listOfSeries),
        #         total=len(listOfSeries),
        #         ncols=100)
        #     )

        logging.info(f'\nItem extraction is completed successfully.')
        #return json.loads(json.dumps(extractedFilings))
        return "Item extraction is completed successfully."

      
    except Exception as e:
      logging.error(e)
      return func.HttpResponse(
            "Error getting files",
            status_code=500
      )

def TransformValue(indexType, indexNs, record):
    logging.info("Calling Transform Value")
    try:
        recordId = record['recordId']
    except AssertionError  as error:
        return None

    # Validate the inputs
    try:
        assert ('data' in record), "'data' field is required."
        data = record['data']
        assert ('text' in data), "'text' field is required in 'data' object."

    except KeyError as error:
        return (
            {
            "recordId": recordId,
            "errors": [ { "message": "KeyError:" + error.args[0] }   ]
            })
    except AssertionError as error:
        return (
            {
            "recordId": recordId,
            "errors": [ { "message": "AssertionError:" + error.args[0] }   ]
            })
    except SystemError as error:
        return (
            {
            "recordId": recordId,
            "errors": [ { "message": "SystemError:" + error.args[0] }   ]
            })

    try:
        # Getting the items from the values/data/text
        value = data['text']

        summaryResponse = EdgarIngestion(indexType, indexNs, value)
        return ({
            "recordId": recordId,
            "data": {
                "text": summaryResponse
                    }
            })

    except:
        return (
            {
            "recordId": recordId,
            "errors": [ { "message": "Could not complete operation for record." }   ]
            })
