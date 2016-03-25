import requests
import io
import sys
import re
from bs4 import BeautifulSoup
INSPECTION_DOMAIN = 'http://info.kingcounty.gov'
INSPECTION_PATH = '/health/ehs/foodsafety/inspections/Results.aspx'
INSPECTION_PARAMS = {
    'Output': 'W',
    'Business_Name': '',
    'Business_Address': '',
    'Longitude': '',
    'Latitude': '',
    'City': '',
    'Zip_Code': '',
    'Inspection_Type': 'All',
    'Inspection_Start': '',
    'Inspection_End': '',
    'Inspection_Closed_Business': 'A',
    'Violation_Points': '',
    'Violation_Red_Points': '',
    'Violation_Descr': '',
    'Fuzzy_Search': 'N',
    'Sort': 'H',
}


def get_inspection_page(**kwargs):
    """Make a search to the inspection website with kwargs.

    Saves the webpage to 'search_results.txt'
    """
    url = INSPECTION_DOMAIN + INSPECTION_PATH
    params = INSPECTION_PARAMS.copy()
    for key, val in kwargs.items():
        if key in INSPECTION_PARAMS:
            params[key] = val
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    f = io.open('search_results.txt', 'w', encoding='utf8')
    f.write(resp.text)
    f.close()
    return resp.content, resp.encoding


def load_inspection_page():
    """Return content and encoding of the inspection search result file."""
    f = io.open('search_results.txt', 'r')
    content = f.read()
    encoding = f.encoding
    f.close()
    return content, encoding


def parse_source(htmlpage, encoding="utf8"):
    """Return html as BeautifulSoup object."""
    return BeautifulSoup(htmlpage, "html.parser", from_encoding=encoding)


def extract_data_listings(soup):
    """Return all the resutrant listings from results."""
    return soup.find_all('div', id=re.compile(r'PR[\d]+~'))


def has_two_tds(element):
    """Return true if element is a <tr> and has two <td> inside it."""
    return (element.name == 'tr' and
            len(element.find_all('<td>', recursive=False)) == 2)


def clean_data(cell):
    """Return the clean string of a html cell."""
    try:
        return cell.string.strip(' \n:-')
    except AttributeError:
        return u""


def extract_restaurant_metadata(elem):
    metadata_rows = elem.find('table').find_all(
        has_two_tds(elem), recursive=False)
    rdata = {}
    current_label = ''
    for row in metadata_rows:
        try:
            key_cell, val_cell = row.find_all('td', recursive=False)
        except ValueError:
            continue
        new_label = clean_data(key_cell)
        current_label = new_label if new_label else current_label
        rdata.setdefault(current_label, []).append(clean_data(val_cell))
    return rdata


if __name__ == '__main__':
    kwargs = {
        'Inspection_Start': '1/1/2015',
        'Inspection_End': '12/31/2015',
        'Zip_Code': '98042'
    }
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        html, encoding = load_inspection_page()
    else:
        html, encoding = get_inspection_page(**kwargs)
    soup = parse_source(html, encoding)
    listings = extract_data_listings(soup)
    for listing in listings:
        metadata = extract_restaurant_metadata(listing)
        print(metadata)
        print
