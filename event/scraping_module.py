from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict
from api import scrape_website, scrape_html_content

router = APIRouter(
    prefix="/scraping",
    tags=["scraping"]   
)


class ScrapeRequest(BaseModel):
    url: str
    selectors: Optional[Dict[str, str]] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    wait_time: Optional[int] = 5  # Wait time in seconds for page to load
    headless: Optional[bool] = True  # Run browser in headless mode


class ScrapeHTMLRequest(BaseModel):
    html_content: str
    selectors: Optional[Dict[str, str]] = None


@router.post("/scrape-url")
async def scrape_url(request: ScrapeRequest, http_request: Request):
    """
    Scrape a website by URL with optional location tracking.
    
    Example selectors:
    {
        "title": "h1",
        "articles": ".article-title",
        "prices": ".price"
    }
    
    Location tracking (optional):
    - Provide latitude and longitude to track where scraping was performed
    - Optionally provide user_id and ip_address for additional context
    - If ip_address is not provided, it will be automatically extracted from the request
    
    Selenium options:
    - wait_time: Seconds to wait for page to load (default: 5)
    - headless: Run browser in headless mode (default: True)
    """
    try:
        # Automatically extract IP address if not provided
        ip_address = request.ip_address
        if not ip_address:
            # Try to get IP from various headers (for proxies/load balancers)
            forwarded_for = http_request.headers.get("X-Forwarded-For")
            if forwarded_for:
                ip_address = forwarded_for.split(",")[0].strip()
            else:
                real_ip = http_request.headers.get("X-Real-IP")
                if real_ip:
                    ip_address = real_ip
                else:
                    ip_address = http_request.client.host if http_request.client else None
        
        result = await scrape_website(
            url=request.url,
            selectors=request.selectors,
            latitude=request.latitude,
            longitude=request.longitude,
            user_id=request.user_id,
            ip_address=ip_address,
            wait_time=request.wait_time,
            headless=request.headless if request.headless is not None else True
        )
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        result["success"] = True
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scrape website: {str(e)}"
        )


@router.post("/scrape-html")
async def scrape_html(request: ScrapeHTMLRequest):
    """
    Scrape HTML content string.
    
    Example selectors:
    {
        "title": "h1",
        "content": ".main-content"
    }
    """
    try:
        result = scrape_html_content(request.html_content, request.selectors)
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        result["success"] = True
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scrape HTML: {str(e)}"
        )
