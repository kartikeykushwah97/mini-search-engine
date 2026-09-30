import requests
import time
import heapq
from crawler.models import Page
from bs4 import BeautifulSoup
from django.utils import timezone
from datetime import timedelta
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser

def crawl_page(url, retries=2):
    
    for attempt in range(retries + 1):
        
        try:
            response = requests.get(url, timeout=10)

            print("Status:", response.status_code)
            
            if 500 <= response.status_code < 600:
                print("Server error. Attempt:", attempt + 1)

                if attempt < retries:
                    time.sleep(2 ** attempt)
                    continue

                print("Server failed after retries:", url)

                return {
                    "url": url,
                    "status_code": response.status_code,
                    "title": None,
                    "headings": [],
                    "text": "",
                    "links": [],
                    "link_details": [],
                    

                }
            if response.status_code != 200:
                
                return {
                    "url": url,
                    "status_code": response.status_code,
                    "title": None,
                    "headings": [],
                    "text": "",
                    "links": [],
                    "link_details": [],
                    

                }
            content_type = response.headers.get("Content-Type", "").lower()

            if "text/html" not in content_type:
                print("Skipping non-HTML content:", content_type)

                return {
                    "url": url,
                    "status_code": response.status_code,
                    "title": None,
                    "headings": [],
                    "text": "",
                    "links": [],
                    "link_details": [],
                    

                }
                    
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            title = soup.title.get_text(strip=True) if soup.title else None
            
            headings = [
                heading.get_text(strip=True) for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6" ])
            ] 
            
            text = soup.get_text(" ", strip=True)
            
            links = []
            link_details = []

            for link in soup.find_all("a"):
                href = link.get("href")
                
                if href:
                    full_url = urljoin(url, href)
                    links.append(full_url)
                    link_details.append({"url": full_url,
                                        "anchor_text": link.get_text(" ", strip=True)})
                    
            return {
                "url": url,
                "status_code": response.status_code,
                "title": title,
                "headings": headings,
                "text": text,
                "links": links,
                "link_details": link_details,
                
            }
        except requests.RequestException:
            print("Request failed. Attempt:", attempt + 1 )
            
            
            if attempt < retries:
                time.sleep(2 ** attempt)
        
    else:
        print("URL failed to respond:", url)

        return {
            "url": url,
            "status_code": None,
            "title": None,
            "headings": [],
            "text": "",
            "links": [],
            "link_details": [],
            

        }

def get_stored_links(page):
    return [
        {
            "url": link,
            "anchor_text": "",
        }
        for link in page.links
    ]
def should_recrawl(page):
    if page.last_crawled is None:
        return True
    if page.last_crawled < timezone.now() - timedelta(days=7):
        return True
    
    return False
    
def normalize_url(url):
    parts = urlparse(url)

    scheme = parts.scheme.lower()

    hostname = parts.hostname.lower() if parts.hostname else ""

    # Remove default ports
    if parts.port:
        if not (
            (scheme == "http" and parts.port == 80)
            or
            (scheme == "https" and parts.port == 443)
        ):
            hostname = f"{hostname}:{parts.port}"

    path = parts.path or "/"

    return urlunparse((
        scheme,
        hostname,
        path,
        parts.params,
        parts.query,
        ""  # Remove fragment
    ))
    
def get_robots_parser(start_url):
    parsed_url = urlparse(start_url)

    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

    rp = RobotFileParser()
    rp.set_url(robots_url)

    try:
        rp.read()
        print("robots.txt loaded:", robots_url)
        return rp

    except Exception:
        print("Could not load robots.txt")
        return None
    
    
def is_crawlable_url(url):
    parsed_url = urlparse(url)

    # Only allow HTTP and HTTPS
    if parsed_url.scheme not in ("http", "https"):
        return False

    # Ignore common non-web links
    blocked_extensions = (
        ".pdf", ".jpg", ".jpeg", ".png",
        ".gif", ".zip", ".mp3", ".mp4"
    )

    if parsed_url.path.lower().endswith(blocked_extensions):
        return False

    return True

def get_link_priority(anchor_text, url, depth):
    priority = depth
    
    text = anchor_text.lower()
    path = urlparse(url).path.lower()
    
    high_priority_words = {
        "documentation",
        "docs",
        "tutorial",
        "product",
        "guide"
    }
    low_priority_words = {
        "login",
        "logout",
        "admin",
        "privacy",
        "terms",
    } 
    
    if any(word in text for word in high_priority_words):
        priority -= 2   
    if any(word in text for word in low_priority_words):
        priority += 2
        
    if any(word in path for word in ("/docs/", "/documentation/", "/guide/")):
        priority -= 2
    if any(word in path for word in ("/login", "/logout", "/admin")):
        priority += 2
        
    return priority

        
def crawl(start_url, max_depth=2, delay=1):
    
    pages_blocked = 0
    pages_skipped = 0
    pages_fetched = 0
    html_pages = 0
    failed_pages = 0
    urls_queued = 0
    
    start_url = normalize_url(start_url)
    start_domain = urlparse(start_url).netloc
    robots_parser = get_robots_parser(start_url)
    

    queued = set()

    queue = []
    
    visited = set()
    pages = []
    
    incoming_links = {}
    
    def process_links(found_links, current_depth):
        nonlocal pages_skipped, urls_queued

        for link_data in found_links:
            new_url = normalize_url(link_data["url"])
            anchor_text = link_data["anchor_text"]

            if not is_crawlable_url(new_url):
                pages_skipped += 1
                continue

            new_domain = urlparse(new_url).netloc

            if new_domain != start_domain:
                continue

            incoming_links[new_url] = incoming_links.get(new_url, 0) + 1

            if new_url in visited or new_url in queued:
                continue

            existing_page = Page.objects.filter(url=new_url).first()

            if existing_page and not should_recrawl(existing_page):
                continue

            priority = get_link_priority(
                anchor_text,
                new_url,
                current_depth + 1
            )

            heapq.heappush(
                queue,
                (priority, new_url, current_depth + 1)
            )

            queued.add(new_url)
            urls_queued += 1
            
    existing_start_page = Page.objects.filter(url=start_url).first()
    
    if existing_start_page and not should_recrawl(existing_start_page):
        print("Start URL is fresh. Using stored links:", start_url)
        
        stored_links = get_stored_links(existing_start_page)
        
        process_links(stored_links, 0)
    
    else:    
        heapq.heappush(queue, (0, start_url, 0))
        queued.add(start_url)
        urls_queued += 1




    while queue:
        priority, url, depth = heapq.heappop(queue)
        
        if url in visited:
            continue
        
        if depth > max_depth:
            continue
        
        if robots_parser and not robots_parser.can_fetch("*", url):
            print("Blocked by robots.txt:", url)
            pages_blocked += 1
            continue
        
        visited.add(url)
        
        print("\nCrawling:", url)
        print("Depth:", depth)
        
        time.sleep(delay)
        
        page_data = crawl_page(url)
        pages_fetched += 1
        
        if page_data["status_code"] is None:
            failed_pages += 1
            
        elif page_data["status_code"] == 200 and page_data["title"] is not None:
            html_pages += 1
        
        pages.append(page_data)
        
        process_links(
            page_data["link_details"],
            depth
        )
    print("\n--- Crawl Summary ---")
    print("Pages fetched:", pages_fetched)
    print("HTML pages:", html_pages)
    print("Failed requests:", failed_pages)
    print("Pages blocked:", pages_blocked)
    print("Pages skipped:", pages_skipped)
    print("Incoming links:", incoming_links)
    print("URLs discovered:", urls_queued)            
    return pages, incoming_links

