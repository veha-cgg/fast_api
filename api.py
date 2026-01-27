import httpx
from bs4 import BeautifulSoup
from typing import Optional, Dict, List
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import time


def _get_chrome_driver(headless: bool = True):
    """
    Create and configure Chrome WebDriver for scraping.
    
    Args:
        headless: Whether to run browser in headless mode (default: True)
    
    Returns:
        Configured Chrome WebDriver instance
    """
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument("--headless")
    
    # Additional options for Docker/containerized environments
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # User agent to avoid detection
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        # Try to use ChromeDriver from PATH first
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except WebDriverException:
        # Fallback: try with service
        try:
            service = Service()
            driver = webdriver.Chrome(service=service, options=chrome_options)
            return driver
        except WebDriverException:
            # Final fallback: use webdriver-manager to auto-download ChromeDriver
            try:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                return driver
            except Exception as e:
                raise Exception(f"Failed to initialize Chrome WebDriver: {str(e)}. Make sure Chrome is installed.")


async def scrape_website(
    url: str, 
    selectors: Optional[Dict[str, str]] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    wait_time: Optional[int] = 5,
    headless: bool = True
) -> Dict:
    """
    Scrape a website using Selenium and extract data based on CSS selectors.
    Also tracks the location where the scraping was performed.
    
    Args:
        url: The URL of the website to scrape
        selectors: Optional dictionary of CSS selectors to extract specific elements
                   Example: {"title": "h1", "links": "a", "images": "img"}
        latitude: Optional latitude coordinate for location tracking
        longitude: Optional longitude coordinate for location tracking
        user_id: Optional user ID to associate with the scraping
        ip_address: Optional IP address for location tracking
        wait_time: Optional wait time in seconds for page to load (default: 5)
        headless: Whether to run browser in headless mode (default: True)
    
    Returns:
        Dictionary containing scraped data with location information and page path
    """
    driver = None
    try:
        # Initialize Chrome WebDriver
        driver = _get_chrome_driver(headless=headless)
        
        # Navigate to URL
        driver.get(url)
        
        # Wait for page to load
        if wait_time:
            time.sleep(wait_time)
        
        # Get the current page URL/path (after any redirects)
        current_url = driver.current_url
        page_path = driver.execute_script("return window.location.pathname")
        page_hash = driver.execute_script("return window.location.hash")
        full_path = page_path + page_hash if page_hash else page_path
        
        # Get page source (after JavaScript execution)
        page_source = driver.page_source
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')
        
        result = {
            "url": url,
            "current_url": current_url,
            "page_path": page_path,
            "full_path": full_path,
            "status_code": None,  # Selenium doesn't provide HTTP status code directly
            "title": driver.title if driver.title else (soup.title.string if soup.title else None),
            "meta_description": None,
            "links": [],
            "images": [],
            "text_content": None,
            "custom_data": {},
            "scraped_at": datetime.now().isoformat(),
            "location": None
        }
        
        # Track location if coordinates are provided
        if latitude is not None and longitude is not None:
            location_result = await track_user_location(
                latitude=latitude,
                longitude=longitude,
                user_id=user_id,
                ip_address=ip_address
            )
            result["location"] = location_result
        
        # Extract meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            result["meta_description"] = meta_desc.get("content")
        
        # Extract all links
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            # Convert relative URLs to absolute
            if href.startswith("/"):
                href = f"{current_url.rstrip('/')}{href}"
            elif not href.startswith("http"):
                href = f"{current_url.rstrip('/')}/{href.lstrip('/')}"
            
            result["links"].append({
                "text": link.get_text(strip=True),
                "href": href
            })
        
        # Extract all images
        for img in soup.find_all("img", src=True):
            src = img.get("src", "")
            # Convert relative URLs to absolute
            if src.startswith("/"):
                src = f"{current_url.rstrip('/')}{src}"
            elif not src.startswith("http"):
                src = f"{current_url.rstrip('/')}/{src.lstrip('/')}"
            
            result["images"].append({
                "alt": img.get("alt", ""),
                "src": src
            })
        
        # Extract main text content (remove script and style tags)
        for script in soup(["script", "style"]):
            script.decompose()
        result["text_content"] = soup.get_text(separator=" ", strip=True)
        
        # Extract custom data based on selectors
        if selectors:
            for key, selector in selectors.items():
                try:
                    # Try using Selenium first for dynamic content
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        if len(elements) == 1:
                            result["custom_data"][key] = elements[0].text.strip()
                        else:
                            result["custom_data"][key] = [elem.text.strip() for elem in elements]
                    else:
                        # Fallback to BeautifulSoup
                        soup_elements = soup.select(selector)
                        if soup_elements:
                            if len(soup_elements) == 1:
                                result["custom_data"][key] = soup_elements[0].get_text(strip=True)
                            else:
                                result["custom_data"][key] = [elem.get_text(strip=True) for elem in soup_elements]
                except Exception as e:
                    result["custom_data"][key] = f"Error extracting {key}: {str(e)}"
        
        return result
        
    except WebDriverException as e:
        return {
            "url": url,
            "error": f"Selenium WebDriver error: {str(e)}",
            "success": False
        }
    except Exception as e:
        return {
            "url": url,
            "error": f"An error occurred: {str(e)}",
            "success": False
        }
    finally:
        # Always close the browser
        if driver:
            try:
                driver.quit()
            except:
                pass


def scrape_html_content(html_content: str, selectors: Optional[Dict[str, str]] = None) -> Dict:
    """
    Scrape HTML content string and extract data based on CSS selectors.
    
    Args:
        html_content: HTML content as string
        selectors: Optional dictionary of CSS selectors
    
    Returns:
        Dictionary containing scraped data
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        result = {
            "title": soup.title.string if soup.title else None,
            "links": [],
            "images": [],
            "text_content": None,
            "custom_data": {}
        }
        
        # Extract all links
        for link in soup.find_all("a", href=True):
            result["links"].append({
                "text": link.get_text(strip=True),
                "href": link["href"]
            })
        
        # Extract all images
        for img in soup.find_all("img", src=True):
            result["images"].append({
                "alt": img.get("alt", ""),
                "src": img["src"]
            })
        
        # Extract main text content
        for script in soup(["script", "style"]):
            script.decompose()
        result["text_content"] = soup.get_text(separator=" ", strip=True)
        
        # Extract custom data based on selectors
        if selectors:
            for key, selector in selectors.items():
                elements = soup.select(selector)
                if elements:
                    if len(elements) == 1:
                        result["custom_data"][key] = elements[0].get_text(strip=True)
                    else:
                        result["custom_data"][key] = [elem.get_text(strip=True) for elem in elements]
        
        return result
        
    except Exception as e:
        return {
            "error": f"An error occurred: {str(e)}",
            "success": False
        }

async def track_user_location(
    latitude: float,
    longitude: float,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    additional_data: Optional[Dict] = None
) -> Dict:
    """
    Track user location based on GPS coordinates.
    
    Args:
        latitude: Latitude coordinate (required)
        longitude: Longitude coordinate (required)
        user_id: Optional user ID to associate with the location
        ip_address: Optional IP address for additional tracking
        additional_data: Optional dictionary with additional location metadata
                        (e.g., accuracy, altitude, speed, timestamp)
    
    Returns:
        Dictionary containing location tracking information
    """
    try:
        location_data = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "coordinates": {
                "latitude": latitude,
                "longitude": longitude
            },
            "user_id": user_id,
            "ip_address": ip_address,
            "additional_data": additional_data or {}
        }
        
        # Validate coordinates
        if not (-90 <= latitude <= 90):
            return {
                "success": False,
                "error": "Invalid latitude. Must be between -90 and 90.",
                "coordinates": {"latitude": latitude, "longitude": longitude}
            }
        
        if not (-180 <= longitude <= 180):
            return {
                "success": False,
                "error": "Invalid longitude. Must be between -180 and 180.",
                "coordinates": {"latitude": latitude, "longitude": longitude}
            }
        
        # Optionally get location details from IP if provided
        if ip_address:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    # Using ipapi.co as a free geolocation service
                    response = await client.get(f"https://ipapi.co/{ip_address}/json/")
                    if response.status_code == 200:
                        ip_data = response.json()
                        location_data["ip_location"] = {
                            "city": ip_data.get("city"),
                            "region": ip_data.get("region"),
                            "country": ip_data.get("country_name"),
                            "country_code": ip_data.get("country_code"),
                            "timezone": ip_data.get("timezone"),
                            "ip_latitude": ip_data.get("latitude"),
                            "ip_longitude": ip_data.get("longitude")
                        }
            except Exception as e:
                location_data["ip_location_error"] = f"Could not fetch IP location: {str(e)}"
        
        return location_data
        
    except Exception as e:
        return {
            "success": False,
            "error": f"An error occurred while tracking location: {str(e)}",
            "coordinates": {"latitude": latitude, "longitude": longitude}
        }        