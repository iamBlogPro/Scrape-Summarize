# Web Scraping and Summarization Script

This script provides a comprehensive solution for web scraping and summarization using Python, Selenium, BeautifulSoup, Trafilatura, and OpenAI's GPT-3.5 Turbo. It automates the process of extracting relevant content from web pages, filtering and cleaning the data, and generating concise summaries using advanced natural language processing techniques.

## Features

- **Proxy Management**: Automatically loads and manages a list of proxies to avoid IP bans and ensure continuous scraping.
- **Headless Browser**: Uses Selenium with headless Chrome for efficient and seamless web scraping.
- **Content Extraction**: Employs Trafilatura to extract and clean textual content from web pages.
- **URL Filtering**: Filters out irrelevant URLs based on predefined criteria to ensure only relevant content is processed.
- **Summarization**: Utilizes OpenAI's GPT-3.5 Turbo to generate concise summaries of extracted content.
- **Logging**: Provides detailed logging for monitoring script execution and debugging purposes.
- **Configuration Management**: Stores configurable parameters such as API keys, file paths, and directories in a JSON settings file for easy modification.

## How it Works

### Prerequisites

Before running the script, ensure you have the following installed:

- Python 3.6+
- Selenium
- Selenium Wire
- BeautifulSoup4
- Trafilatura
- OpenAI
- Chromedriver (compatible with your version of Chrome)
- Retry (for retrying failed requests)

### Installation

1. **Clone the Repository**:

    ```sh
    git clone https://github.com/iamBlogPro/Scrape-Summarize.git
    cd Scrape-Summarize
    ```

2. **Install Required Packages**:

    ```sh
    pip install -r requirements.txt
    ```

3. **Download Chromedriver**:

    Download Chromedriver from [here](https://sites.google.com/chromium.org/driver/) and place it in the same directory as the script.

4. **Edit the `settings.json`**:

    Edit a `settings.json` file in the root directory with the following content:

    ```json
    {
      "openai_api_key": "your_openai_api_key",
      "output_directory": "Output_Folder_Name",
      "keywords_file": "keywords.csv",
      "proxy_file": "proxylist.txt"
    }
    ```

    Replace `"your_openai_api_key"` with your actual OpenAI API key

### Usage

1. **Prepare Input Files**:

    - **Keywords File (`keywords.csv`)**: A CSV file containing keywords to search for. Each keyword should be on a separate line without a header.
    - **Proxy File (`proxylist.txt`)**: A text file containing proxies in the format `ip:port:username:password`, one per line.

2. **Run the Script**:

    ```sh
    python magic.py
    ```

### Script Workflow

1. **Initialization**:
    - Loads settings from `settings.json`.
    - Sets up logging to capture script execution details.

2. **Proxy Management**:
    - Loads proxies from `proxylist.txt`.

3. **Keyword Processing**:
    - Reads keywords from `keywords.csv`.
    - For each keyword, it performs a Google search using Selenium.

4. **Content Extraction**:
    - Retrieves the page source and uses BeautifulSoup to extract URLs.
    - Filters URLs based on predefined criteria (e.g., domain, extensions, keywords).

5. **Data Extraction and Summarization**:
    - Extracts content from each URL using Trafilatura.
    - Cleans the extracted content.
    - Summarizes the content using OpenAI's GPT-3.5 Turbo.

6. **Output**:
    - Saves the summarized content to JSON files in the specified output directory.
    - Updates the `keywords.csv` file to remove processed keywords.

### Logging and Monitoring

- The script generates log files in the `logs` directory, which can be used to monitor its execution and troubleshoot any issues.

### Customization

- Modify the `settings.json` file to update the OpenAI API key, output directory, keywords file, and proxy file as needed.
- Adjust filtering criteria in the `get_links_with_beautifulsoup` function to refine URL selection based on your requirements.
