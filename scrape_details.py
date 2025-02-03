import csv
import time
import logging
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from parser import parse_grant_details  # Importing our proven parsing logic

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Setup WebDriver for Firefox
def setup_driver():
    """Set up and return the Firefox WebDriver."""
    options = Options()
    options.add_argument("--headless")  # Run in headless mode for efficiency
    
    try:
        driver = webdriver.Firefox(options=options)
        logger.info("Firefox WebDriver initialized successfully")
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize WebDriver: {e}")
        raise

# Function to load grant IDs from CSV
def load_grant_urls(filename="grant_ids.csv"):
    """Load grant IDs and URLs from CSV file."""
    grants = []
    try:
        with open(filename, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader)  # Skip header row
            for row in reader:
                if len(row) < 2:
                    continue
                grants.append({"opportunity_number": row[0], "url": row[1]})
        logger.info(f"Loaded {len(grants)} grant URLs from {filename}")
    except Exception as e:
        logger.error(f"Error loading grant URLs: {e}")
    return grants

# Function to scrape grant details
def scrape_grant_details(grant, driver):
    """Visit grant detail page and extract data."""
    try:
        driver.get(grant["url"])
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)  # Allow content to load
        
        html_content = driver.page_source
        details = parse_grant_details(html_content)  # Using our proven parser
        
        # Add opportunity number and URL
        details["opportunity_number"] = grant["opportunity_number"]
        details["detail_page_url"] = grant["url"]
        
        logger.info(f"Scraped details for {grant['opportunity_number']}")
        return details
    except Exception as e:
        logger.error(f"Error scraping {grant['opportunity_number']}: {e}")
        return None

# Function to save grant details to CSV
def save_to_csv(data, filename="grant_details.csv"):
    """Save scraped grant details to CSV."""
    try:
        if not data:
            logger.warning("No data to save!")
            return
        
        # Get all unique fields from the dataset
        fieldnames = list(set().union(*(grant.keys() for grant in data)))

        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        logger.info(f"Successfully saved {len(data)} grants to {filename}")
    except Exception as e:
        logger.error(f"Error saving grant details to CSV: {e}")

# Main function
def main():
    driver = setup_driver()
    grants = load_grant_urls()
    grant_details = []

    for index, grant in enumerate(grants, start=1):
        logger.info(f"Processing {index}/{len(grants)}: {grant['opportunity_number']}")
        details = scrape_grant_details(grant, driver)
        if details:
            grant_details.append(details)
        
        if index % 10 == 0:  # Save every 10 grants to avoid data loss
            save_to_csv(grant_details)

    driver.quit()
    save_to_csv(grant_details)  # Final save

if __name__ == "__main__":
    main()
