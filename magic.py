import csv
import os
import random
import json
import logging
from selenium.webdriver.chrome.service import Service
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import re
import trafilatura
from openai import OpenAI
from datetime import datetime
import time
import platform
from retrying import retry

# Load settings from settings.json
with open('settings.json', 'r') as f:
    settings = json.load(f)

OPENAI_API_KEY = settings["openai_api_key"]
OUTPUT_DIRECTORY = settings["output_directory"]
KEYWORDS_FILE = settings["keywords_file"]
PROXY_FILE = settings["proxy_file"]

# Setup basic configuration for logging
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Get the current time to include in the log file name
current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# Setup basic configuration for logging
log_file = os.path.join(log_dir, f'scraper_{current_time}.log')
logging.basicConfig(level=logging.INFO, 
                    filename=log_file, 
                    filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('seleniumwire').setLevel(logging.WARNING)

def load_proxies(proxy_file):
    logging.info("Loading proxies from %s", proxy_file)
    proxy_list = []
    try:
        with open(proxy_file, 'r') as file:
            for line in file:
                parts = line.strip().split(':')
                if len(parts) == 4:
                    ip, port, username, password = parts
                    proxy_list.append({
                        'http': f'http://{username}:{password}@{ip}:{port}',
                        'https': f'https://{username}:{password}@{ip}:{port}',
                    })
    except Exception as e:
        logging.error("Failed to load proxies: %s", e)
    else:
        logging.info("Successfully loaded %d proxies.", len(proxy_list))
    return proxy_list

def get_random_proxy(proxies):
    if not proxies:
        return None
    return random.choice(proxies)

def setup_selenium_wire_options(proxy):
    options = {
        'proxy': {
            'http': proxy['http'],
            'https': proxy['https'],
            'no_proxy': 'localhost,127.0.0.1',
        }
    }
    return options

def get_chromedriver_path():
    system = platform.system()
    if system == 'Windows':
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chromedriver.exe')
    elif system == 'Darwin':
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chromedriver')
    elif system == 'Linux':
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chromedriver')
    else:
        raise Exception(f"Unsupported OS: {system}")

def setup_webdriver(proxy=None):
    chromedriver_path = get_chromedriver_path()
    service = Service(executable_path=chromedriver_path)
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    
    if proxy:
        selenium_wire_options = setup_selenium_wire_options(proxy)
    else:
        selenium_wire_options = None

    try:
        driver = webdriver.Chrome(service=service, options=chrome_options, seleniumwire_options=selenium_wire_options)
        logging.info("WebDriver initialized successfully.")
    except Exception as e:
        logging.error("Failed to initialize WebDriver: %s", e)
        raise SystemExit(e)
    return driver

@retry(stop_max_attempt_number=3, wait_fixed=2000)
def fetch_url_with_retry(url):
    downloaded = trafilatura.fetch_url(url)
    return downloaded

def clean_text(text):
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_with_trafilatura(url):
    logging.info("Extracting content from URL: %s", url)
    try:
        downloaded = fetch_url_with_retry(url)
        if downloaded:
            content = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
            if content:
                cleaned_content = clean_text(content)
                if len(cleaned_content) > 400:
                    logging.info("Content extracted successfully from URL: %s", url)
                    return cleaned_content
                else:
                    logging.warning("Content from URL: %s is less than 400 characters, skipping.", url)
                    return None
            else:
                logging.warning("Failed to extract content from URL: %s", url)
        else:
            logging.warning("Failed to download content from URL: %s", url)
    except Exception as e:
        logging.error("Error extracting content from URL %s: %s", url, e)
    return None

def get_links_with_beautifulsoup(driver):
    logging.info("Retrieving page source for URL extraction")
    skip_domains = ["reddit.com", "vcahospitals.com", "istockphoto.com", "petcarerx.com", "purina.com", "groupon.com", "youtube.com", "tiktok.com", "facebook.com", "twitter.com", "chewy.com", "rover.com", "amazon.com", "quora.com", "walmart.com", "petsmart.com", "linkedin.com", "petco.com", "goodrx.com", "www.premierinn.com", "en.parkopedia.co.uk", "accuweather.com", "theknot.com", "hotels.com", "www.bluecross.org", "www.thesalonringwood.co.uk", "expedia.com", "expedia.co.uk", "trivago.com", "costco.com"]
    skip_extensions = [".gov", ".in", ".gov.uk", ".uk"]
    skip_words = ["collections", "login", "signin", "advisor", "gov"]

    try:
        html = driver.page_source
        logging.info("Page source retrieved successfully.")
    except Exception as e:
        logging.error("Failed to retrieve page source: %s", e)
        return []

    try:
        soup = BeautifulSoup(html, 'lxml')
        logging.info("HTML parsed successfully with BeautifulSoup.")
    except Exception as e:
        logging.error("Failed to parse HTML with BeautifulSoup: %s", e)
        return []

    links = soup.find_all('a', attrs={'jsname': 'UWckNb'})
    logging.info("Found %d links in the page source.", len(links))
    urls = [link.get('href') for link in links[:8]]  # Get the first 8 URLs
    logging.info("Extracted initial %d URLs.", len(urls))

    filtered_urls = [
        url for url in urls 
        if not any(domain in url for domain in skip_domains) 
        and not any(url.endswith(ext) for ext in skip_extensions)
        and not any(word in url for word in skip_words)
    ]
    logging.info("Filtered URLs count after initial filter: %d", len(filtered_urls))

    additional_attempts = 0
    while len(filtered_urls) < 5 and len(filtered_urls) < len(links):
        additional_attempts += 1
        more_links = links[len(filtered_urls):len(filtered_urls) + 5]
        more_urls = [link.get('href') for link in more_links]
        filtered_urls += [
            url for url in more_urls 
            if not any(domain in url for domain in skip_domains) 
            and not any(url.endswith(ext) for ext in skip_extensions)
            and not any(word in url for word in skip_words)
        ]
        logging.info("Filtered URLs count after additional filtering attempt %d: %d", additional_attempts, len(filtered_urls))
        if additional_attempts > 10:
            logging.warning("Reached maximum number of additional filtering attempts.")
            break

    filtered_urls = filtered_urls[:5]  # Limit to 5 URLs
    for url in filtered_urls:
        logging.info("Retained URL: %s", url)

    if not filtered_urls:
        logging.warning("No URLs retained after filtering.")
    else:
        logging.info("Filtered URLs: %s", filtered_urls)

    return filtered_urls

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def summarize_text(text):
    logging.info("Summarizing text with OpenAI GPT-3.5 Turbo")
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {"role": "system", "content": "You excel in extracting context and key information from long pieces of web page data provided to you. You ignore any mention of the website, any promotional material. You retain key information guides, crucial information or information that readers love and need to know etc. You remove headings, footers, copyright notices etc. You don't return any other information. Just the key information in a list form."},
                {"role": "user", "content": f"Extract key information from the following text: {text}"}
            ],
            temperature=0.7,  # Adjust the creativity of the response
            max_tokens=1000,  # Limit the length of the summary
            top_p=1.0,
            frequency_penalty=0.5,
            presence_penalty=0.5
        )
        summary = completion.choices[0].message.content.strip()
        return summary
    except Exception as e:
        logging.error(f"Failed to summarize text with OpenAI GPT-3.5 Turbo: %s", e)
        return None

def process_keyword(keyword, proxies):
    proxy = get_random_proxy(proxies)
    driver = setup_webdriver(proxy) if proxy else setup_webdriver()
    driver.get(f'https://www.google.com/search?q={keyword}')
    links = get_links_with_beautifulsoup(driver)
    contents = extract_contents_from_links(links)
    save_contents_to_json(keyword, contents)
    driver.quit()

def extract_contents_from_links(links):
    contents = []
    for link in links:
        content = extract_with_trafilatura(link)
        if content:
            summary = summarize_text(content)
            if summary:
                contents.append({'url': link, 'summary': summary})
    return contents

def save_contents_to_json(keyword, contents):
    if contents:
        os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
        file_path = os.path.join(OUTPUT_DIRECTORY, f'{keyword}.json')
        with open(file_path, 'w') as outfile:
            json.dump(contents, outfile, indent=4)
        logging.info("Data for keyword '%s' successfully written to %s", keyword, file_path)

def main():
    logging.info("Script started")
    try:
        proxies = load_proxies(PROXY_FILE)
        if not proxies:
            logging.warning("No proxies loaded. Proceeding without proxies.")
        
        if not os.path.exists(KEYWORDS_FILE):
            logging.error("%s not found. Exiting script.", KEYWORDS_FILE)
            return

        with open(KEYWORDS_FILE, 'r') as f:
            keywords = [row[0] for row in csv.reader(f) if row]  # Assumes no header

        for keyword in keywords:
            logging.info("Processing keyword: %s", keyword)
            try:
                process_keyword(keyword, proxies)
            except Exception as e:
                logging.error("An error occurred while processing keyword %s: %s", keyword, e)
            finally:
                time.sleep(random.uniform(1, 3))  # Introduce a delay to reduce the chance of proxy bans

            # Remove the processed keyword from the list
            keywords.remove(keyword)
            with open(KEYWORDS_FILE, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows([[k] for k in keywords])

    except Exception as e:
        logging.error("An unexpected error occurred: %s", e)
    logging.info("Script completed")

if __name__ == "__main__":
    main()
