from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Setup WebDriver for Firefox
def setup_driver():
    """Set up and return the Firefox WebDriver with anti-bot detection measures."""
    options = Options()
    
    # Set a realistic user agent
    options.set_preference("general.useragent.override", 
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Additional preferences to make the browser appear more human-like
    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference("useAutomationExtension", False)
    
    # Temporarily disable headless mode for debugging
    # options.add_argument("--headless")

    try:
        driver = webdriver.Firefox(options=options)
        logger.info("Firefox WebDriver initialized successfully")
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize WebDriver: {e}")
        raise

# Function to scrape opportunity numbers and URLs
def scrape_grants():
    driver = setup_driver()
    grants = []
    page_num = 1

    try:
        # Initial URL verification with correct URL
        target_url = "https://grants.gov/search-grants"  # Changed from www.grants.gov/web/grants/search-grants.html
        logger.info(f"Attempting to navigate to: {target_url}")
        
        driver.get(target_url)
        time.sleep(3)  # Allow time for any redirects
        
        current_url = driver.current_url
        logger.info(f"Current URL after navigation: {current_url}")
        
        # Log the initial page source to verify content
        logger.info("Page source at start:")
        logger.info(driver.page_source[:2000])  # First 2000 chars of page source
        
        if "page-not-found" in current_url:
            logger.error("Landed on 404 page - possible bot detection")
            return grants
            
        if current_url != target_url:
            logger.warning(f"Redirected to different URL: {current_url}")
        
        wait = WebDriverWait(driver, 20)

        # Verify we can interact with the page
        logger.info("Waiting for page to load...")
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        logger.info(f"Page title: {driver.title}")
        
        # Try to find the table container with better error handling
        logger.info("Looking for table container...")
        try:
            table_container = wait.until(EC.presence_of_element_located(
                (By.CLASS_NAME, "usa-table-container--scrollable")
            ))
            logger.info("Table container found successfully")
        except Exception as e:
            logger.error(f"Failed to find table container: {e}")
            logger.debug("Page source:")
            logger.debug(driver.page_source[:1000])
            return grants

        while True:
            logger.info(f"Scraping page {page_num}")

            # Wait for the grants table to be populated
            table = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".usa-table-container--scrollable table")
            ))
            
            # Get all grant rows
            rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
            logger.info(f"Found {len(rows)} grants on page {page_num}")

            if not rows:
                logger.warning("No rows found, something is wrong.")
                break

            for row in rows:
                try:
                    link_element = row.find_element(By.CSS_SELECTOR, "td a.usa-link")
                    opportunity_number = link_element.text.strip()
                    url_suffix = link_element.get_attribute("href")
                    full_url = f"https://grants.gov{url_suffix}" if url_suffix.startswith('/') else url_suffix
                    grants.append((opportunity_number, full_url))
                    logger.debug(f"Found grant: {opportunity_number}")
                except Exception as e:
                    logger.warning(f"Error processing row: {e}")
                    continue

            # Attempt to trigger pagination using JavaScript instead of clicking
            try:
                logger.info("Manually triggering next page event...")
                
                # Execute JavaScript to manually call the event that loads the next page
                pagination_result = driver.execute_script("""
                    let nextBtn = [...document.querySelectorAll("a.usa-pagination__link")]
                        .find(btn => btn.innerText.includes("NEXT"));
                    
                    if (!nextBtn) {
                        return "NO_NEXT_BUTTON";
                    }
                    
                    if (nextBtn.classList.contains("disabled")) {
                        return "DISABLED";
                    }
                    
                    let event = new Event('click', { bubbles: true });
                    nextBtn.dispatchEvent(event);
                    return "CLICKED";
                """)
                
                logger.info(f"Pagination result: {pagination_result}")
                
                if pagination_result == "NO_NEXT_BUTTON":
                    logger.info("No Next button found - reached end of results")
                    break
                elif pagination_result == "DISABLED":
                    logger.info("Next button is disabled - reached last page")
                    break
                elif pagination_result == "CLICKED":
                    time.sleep(3)  # Small delay for UI update
                    page_num += 1
                    logger.info(f"Successfully navigated to page {page_num}")
                else:
                    logger.error(f"Unexpected pagination result: {pagination_result}")
                    break

            except Exception as e:
                logger.error(f"Error triggering next page: {e}")
                break

    except Exception as e:
        logger.error(f"Unexpected error during scraping: {e}")
    finally:
        driver.quit()

    return grants

# Function to save results to CSV
def save_to_csv(grants, filename="grant_ids.csv"):
    try:
        with open(filename, "w", newline="", encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Opportunity Number", "Detail Page URL"])
            writer.writerows(grants)
        logger.info(f"Successfully saved {len(grants)} grants to {filename}")
    except Exception as e:
        logger.error(f"Error saving to CSV: {e}")

# Run scraper
if __name__ == "__main__":
    grants = scrape_grants()
    save_to_csv(grants)
    logger.info(f"Successfully extracted {len(grants)} grant IDs and URLs.")
