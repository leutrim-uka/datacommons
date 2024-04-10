"""
Wikipedia Article Extractor

This module extracts Wikipedia articles and stored the HTML as a text file.
The MediaWiki API is used. Requests are made asynchronously, thus throttling 
should be set to prevent server overloading. Default rate limit is 200req/s.

A directory named "data" will be created within your current working directory.
All extracted wiki files will be stored in individual folders within the "data"
directory.
"""

import asyncio
from time import time
import os
import aiometer
import httpx
import argparse
from functools import partial

parser = argparse.ArgumentParser()

parser.add_argument(
    'city_list_filepath', type=str,
    help='Path to the text file containing the list of cities'
)

parser.add_argument(
    'project_name', type=str,
    help='Project identifier to be included in requests header. Requied by MediaWikiAPI'
)

parser.add_argument(
    'email', type=str,
    help='Your personal email address will be included in requests header to MediaWikiAPI'
)

parser.add_argument(
    'max_requests_per_second', type=int,
    help='Maximum requests made to WikiMediaAPI in a second. Defaults to 200. Refer to docs.'
)


def read_txt(src: str, encoding='utf-8') -> list:
    """
    Reads a text file into a list. Each element is a row.
    
    Args:
        src (str): Path to .txt file
        
    Returns:
        content (list): List of text rows from the text file
    """
    with open(src, encoding=encoding) as txt_file:
        content = txt_file.readlines()
        content = [c.replace('\n', '') for c in content]        
    
    return content


def to_file(content: list, path: str, dump: str = True) -> bool:
    """
    Writes given content to a text file. Requires destination path.
    Lines separated with newlines.
    
    Args:
        content (list): List of strings to write
        path (str): Location to store file
        
    Returns:
        bool
    """
    if not path.endswith('.txt'):
        print("Path should end with .txt")
        return False
    
    if dump:
        with open(path, 'w', encoding='utf-8') as file:
            file.write(content)
    else:    
        with open(path, 'w', encoding='utf-8') as file:
            for line in content:
                file.write(f"{line}\n")
            
    if not os.path.isfile(path):
        print("File not created!")
        return False


async def scrape(title, session, headers):
    base_url = "https://en.wikipedia.org/api/rest_v1/page/html/"

    path = os.path.join("data2", title)
    if not os.path.exists(path):
        os.makedirs(path)
    url = os.path.join(base_url, title)
    path = os.path.join(path, f"{title}_html.txt")
    response = await session.get(url, headers=headers)
    response = response.text
    to_file(response, path)
    return response


async def run(citydistlist: list, headers: dict, rate_limit_per_sec: int = 200):
    """
    Controls the requests made to the server. Provides throttling support to the
    specified number per second.
    """
    _start = time()
    
    # HTTPX allows concurrent (async) requests; faster
    session = httpx.AsyncClient()
    
    scrape_with_headers = partial(scrape, session=session, headers=headers)
    
    results = await aiometer.run_on_each(
        scrape_with_headers, 
        citydistlist,
        max_per_second=rate_limit_per_sec,  # here we can set max rate per second
    )
    print(f"finished {len(citydistlist)} requests in {time() - _start:.2f} seconds")
    return results


def main(
        path_to_citylist: str = 'data/citydistlist.txt',
        project_name: str = '',
        contact_email: str = '',
        max_requests_per_second: int = 200
    ):

    
    headers = {
        'user-agent': f'{project_name} ({contact_email})'
    }

    citydistlist = read_txt(path_to_citylist)
    citydistlist = citydistlist[:5]
    
    asyncio.run(run(citydistlist, headers, max_requests_per_second))


if __name__ == "__main__":
    # parse arguments
    args = parser.parse_args()
    
    print("Wikipedia extraction started")
    print("Files will be written to disk as they are received")
    
    main(
        args.city_list_filepath,
        args.project_name,
        args.email,
        args.max_requests_per_second
    )
    