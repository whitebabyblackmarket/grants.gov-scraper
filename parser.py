"""
Handles parsing of scraped HTML content from grants.gov
"""
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from utilities import setup_logger
import re

logger = setup_logger(__name__)

def safe_extract_text(element: Optional[BeautifulSoup], class_name: str) -> Optional[str]:
    """
    Safely extract text from a BeautifulSoup element
    
    Args:
        element: BeautifulSoup element to extract from
        class_name: Class name for logging context
        
    Returns:
        Optional[str]: Extracted text or None if extraction fails
    """
    if not element:
        logger.debug(f"No element found for {class_name}")
        return None
        
    try:
        text = element.text.strip()
        return text if text else None
    except AttributeError as e:
        logger.warning(f"Failed to extract text from {class_name}: {e}")
        return None

def clean_amount(amount_str: Optional[str]) -> Optional[str]:
    """
    Clean and standardize amount strings
    """
    if not amount_str:
        return None
    try:
        # Remove currency symbols, commas, and whitespace
        cleaned = re.sub(r'[^\d.]', '', amount_str)
        return cleaned if cleaned else None
    except Exception as e:
        logger.warning(f"Failed to clean amount string '{amount_str}': {e}")
        return None

def validate_grant_data(grant_data: Dict[str, Any]) -> bool:
    """
    Validate required fields in grant data
    
    Args:
        grant_data: Dictionary containing grant information
        
    Returns:
        bool: True if all required fields are present and valid
    """
    required_fields = ['title', 'opportunity_number', 'detail_page_url']
    
    for field in required_fields:
        if not grant_data.get(field):
            logger.warning(f"Missing required field: {field}")
            return False
    
    return True

def parse_search_results(html_content: str) -> List[Dict[str, Any]]:
    """
    Parses HTML content from grants.gov search results table.
    
    Args:
        html_content: Raw HTML content from the search results page
        
    Returns:
        List[Dict[str, Any]]: List of parsed grant dictionaries
    """
    if not html_content:
        logger.warning("Empty HTML content provided")
        return []
        
    grants = []
    try:
        logger.info("Starting to parse search results")
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.find('table', class_='usa-table')
        
        if not table:
            logger.warning("No results table found in HTML content")
            return []
            
        rows = table.find_all('tr')[1:]  # Skip header row
        logger.info(f"Found {len(rows)} grant rows to parse")
        
        for idx, row in enumerate(rows, 1):
            try:
                logger.debug(f"Parsing row {idx}/{len(rows)}")
                cols = row.find_all("td")
                if len(cols) < 6:
                    logger.warning(f"Skipping row with insufficient columns: {len(cols)}")
                    continue

                # Extract opportunity number and detail page URL more carefully
                opportunity_link = cols[0].find("a", class_="usa-link")
                if not opportunity_link:
                    logger.warning(f"No opportunity link found in row {idx}")
                    continue
                    
                opportunity_number = opportunity_link.text.strip()
                detail_url = opportunity_link.get("href", "").strip()
                
                if not detail_url:
                    logger.warning(f"No detail URL found for opportunity {opportunity_number}")
                    continue
                    
                # Build full URL
                detail_url = f"https://grants.gov{detail_url}"
                logger.debug(f"Found detail URL for {opportunity_number}: {detail_url}")

                # Extract basic grant information
                grant = {
                    "opportunity_number": opportunity_number,
                    "detail_page_url": detail_url,
                    "title": safe_extract_text(cols[1], "title"),
                    "agency": safe_extract_text(cols[2], "agency"),
                    "status": safe_extract_text(cols[3], "status"),
                    "posted_date": safe_extract_text(cols[4], "posted_date"),
                    "close_date": safe_extract_text(cols[5], "close_date"),
                }

                # Extract additional fields if available
                try:
                    details_div = cols[1].find('div', class_='grant-details')
                    if details_div:
                        # Extract award information
                        award_info = details_div.find('div', class_='award-info')
                        if award_info:
                            grant["award_ceiling"] = clean_amount(
                                safe_extract_text(award_info.find('span', class_='ceiling'), "award_ceiling")
                            )
                            grant["award_floor"] = clean_amount(
                                safe_extract_text(award_info.find('span', class_='floor'), "award_floor")
                            )

                        # Extract additional metadata
                        grant["eligibility"] = safe_extract_text(
                            details_div.find('div', class_='eligibility'), "eligibility"
                        )
                        grant["funding_instrument"] = safe_extract_text(
                            details_div.find('div', class_='funding-instrument'), "funding_instrument"
                        )
                        grant["category"] = safe_extract_text(
                            details_div.find('div', class_='category'), "category"
                        )
                except Exception as e:
                    logger.debug(f"Could not extract additional fields for grant {opportunity_number}: {e}")

                # Validate all required fields
                if not validate_grant_data(grant):
                    logger.warning(f"Skipping grant {opportunity_number} with missing required fields")
                    continue

                grants.append(grant)
                logger.debug(f"Successfully parsed grant {opportunity_number} with {len(grant)} fields")

            except Exception as e:
                logger.error(f"Error parsing row {idx}: {e}", exc_info=True)
                continue

        logger.info(f"Successfully parsed {len(grants)} grants with detail URLs")
        return grants

    except Exception as e:
        logger.error(f"Error parsing search results: {e}", exc_info=True)
        return []

def parse_grant_details(html_content: str) -> Dict[str, Any]:
    """
    Parses detailed grant information from a grant's details page.
    
    Args:
        html_content: HTML content of the grant details page
        
    Returns:
        Dict[str, Any]: Parsed grant details or empty dict if parsing fails
    """
    if not html_content:
        logger.warning("Received empty HTML content for grant details")
        return {}

    try:
        logger.info("Starting to parse grant details")
        soup = BeautifulSoup(html_content, 'html.parser')
        details = {}

        # Look for synopsis in the correct section
        try:
            synopsis_header = soup.find('h2', string='Opportunity Synopsis')
            if synopsis_header:
                synopsis_section = synopsis_header.find_next('div')
                if synopsis_section:
                    details['synopsis'] = synopsis_section.text.strip()
                    logger.debug("Successfully extracted synopsis")
        except Exception as e:
            logger.debug(f"Could not extract synopsis: {e}")

        # Define sections to extract with their headers
        sections = {
            "general": {
                "header": "General Information",
                "required_fields": []
            },
            "eligibility": {
                "header": "Eligibility",
                "required_fields": ["Eligible Applicants"]
            },
            "additional": {
                "header": "Additional Information",
                "required_fields": []
            }
        }

        def extract_table_data(soup: BeautifulSoup, section_name: str, header_text: str) -> Dict[str, Any]:
            """Helper function to extract and validate section data"""
            section_data = {}
            try:
                header = soup.find('h2', string=header_text)
                if not header:
                    logger.debug(f"Could not find {header_text} section")
                    return {}

                table = header.find_next("table")
                if not table:
                    logger.debug(f"No table found for {header_text} section")
                    return {}

                for row in table.find_all("tr"):
                    cols = row.find_all("td")
                    if len(cols) != 2:
                        logger.debug(f"Skipping malformed row in {section_name}")
                        continue

                    key = cols[0].text.strip().rstrip(':')
                    value_cell = cols[1]
                    
                    # Check for links first
                    links = value_cell.find_all("a")
                    if links:
                        value = {
                            "text": value_cell.text.strip() or None,
                            "urls": [link.get("href", "").strip() for link in links if link.get("href")]
                        }
                    else:
                        # Handle multi-line text
                        value = "\n".join(
                            line.strip() 
                            for line in value_cell.stripped_strings
                        ) or None

                    if value:
                        section_data[key] = value
                        logger.debug(f"Extracted {key} from {section_name}")

            except Exception as e:
                logger.error(f"Error extracting {section_name} data: {e}")
                
            return section_data

        # Extract data from each section
        for section_name, section_info in sections.items():
            section_data = extract_table_data(soup, section_name, section_info["header"])
            details.update(section_data)

        return details

    except Exception as e:
        logger.error(f"Error parsing grant details: {e}", exc_info=True)
        return {} 