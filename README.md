# Mini Search Engine

A Django-based mini search engine that demonstrates the core concepts behind a search system: **web crawling, indexing, information retrieval, ranking, and result presentation**.

The project crawls web pages, stores their content in a database, builds an inverted index, and allows users to search the crawled pages through a Django web interface.

## Features

### Web Crawler

* Same-domain crawling
* Configurable crawl depth
* URL normalization
* `robots.txt` support
* Request timeout handling
* Automatic retries for temporary failures
* Exponential backoff
* Politeness delay between requests
* HTML content-type filtering
* Duplicate URL prevention
* Priority-based URL crawling
* Incoming-link counting
* Freshness-based recrawling

### Search Engine

* Database-backed inverted index
* Tokenization and case-insensitive search
* Stop-word filtering
* Multi-word AND search
* Term-frequency-based relevance
* Title and heading relevance
* Incoming-link relevance
* Search result snippets
* Query-term highlighting
* Pagination

### Django Application

* Crawl form with configurable depth
* Search interface
* Crawled-page details
* Crawl statistics
* SQLite database persistence
* Bootstrap-based interface

## Project Architecture

```text
User
 │
 ├── Start Crawl
 │        │
 │        ▼
 │   URL Normalization
 │        │
 │        ▼
 │   robots.txt Check
 │        │
 │        ▼
 │   Priority Queue
 │        │
 │        ▼
 │   Web Crawler
 │        │
 │        ├── Retry Handling
 │        ├── HTML Filtering
 │        ├── Content Extraction
 │        └── Link Discovery
 │
 ▼
Django Database
 │
 ├── Page
 │     ├── URL
 │     ├── Title
 │     ├── Headings
 │     ├── Text
 │     ├── Links
 │     ├── Status
 │     └── Incoming Links
 │
 └── IndexEntry
       ├── Word
       ├── Page
       └── Frequency

Search Query
 │
 ▼
Tokenization
 │
 ▼
Inverted Index
 │
 ▼
Matching Pages
 │
 ▼
Relevance Scoring
 │
 ├── Title match
 ├── Heading match
 ├── Body match
 ├── Term frequency
 └── Incoming links
 │
 ▼
Sorted Search Results
 │
 ▼
Snippet + Highlighting
```

## Technologies Used

* **Python**
* **Django**
* **SQLite**
* **Requests**
* **BeautifulSoup**
* **Bootstrap**
* **HTML/CSS**

## Project Structure

```text
search_engine/
│
├── manage.py
├── db.sqlite3
│
├── crawler/
│   ├── admin.py
│   ├── apps.py
│   ├── crawler.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   ├── migrations/
│   └── templates/
│       └── crawler/
│           ├── page_detail.html
│           └── page_list.html
│
└── search_engine/
    ├── settings.py
    ├── urls.py
    ├── asgi.py
    └── wsgi.py
```

## How It Works

### 1. Crawling

The user provides a starting URL and maximum crawl depth.

The crawler normalizes URLs, checks `robots.txt`, and uses a priority queue to determine which URLs should be crawled first.

Only HTTP/HTTPS URLs from the same domain are followed.

### 2. Content Extraction

For each HTML page, the crawler extracts:

* Page title
* Headings
* Visible text
* Links
* Anchor text
* HTTP status code

Non-HTML resources such as images, PDFs, videos, and ZIP files are skipped.

### 3. Database Storage

Crawled pages are stored using the Django `Page` model.

The crawler also stores incoming-link counts and the last crawl time.

Pages that were crawled recently can be skipped during future crawls, reducing unnecessary requests.

### 4. Indexing

After crawling, the application builds a database-backed inverted index using the `IndexEntry` model.

For example:

```text
python → Page 27 → frequency 64
python → Page 28 → frequency 19
python → Page 29 → frequency 35
```

This allows the search system to find pages containing a word without scanning every page's complete text.

### 5. Searching

The search query is tokenized and common stop words are removed.

For a multi-word query, the search engine finds pages containing **all search terms**.

For example:

```text
python django
```

requires a page to contain both `python` and `django`.

### 6. Ranking

Matching pages receive a relevance score based on several signals:

* Title match
* Heading match
* Body-text match
* Term frequency
* Number of incoming links

Higher-scoring pages are displayed first.

### 7. Results

The application displays:

* Page title
* URL
* HTTP status
* Relevance score
* Text snippet
* Highlighted search terms

Pagination is used to display results in manageable groups.

## Running the Project

Clone or download the project and install the required packages:

```bash
pip install django requests beautifulsoup4
```

Run database migrations:

```bash
python manage.py migrate
```

Start the development server:

```bash
python manage.py runserver
```

Open the application in a browser:

```text
http://127.0.0.1:8000/
```

Enter a starting URL, select the crawl depth, and start crawling.

After crawling, search the indexed pages using the search box.

## Example Search Flow

```text
Crawl Python documentation
        ↓
Pages stored in SQLite
        ↓
IndexEntry records created
        ↓
Search: python
        ↓
Matching page IDs retrieved
        ↓
Pages ranked
        ↓
Relevant snippets displayed
```

## Limitations

This project is intentionally a small-scale search engine for learning and demonstration purposes.

It currently:

* Crawls one domain at a time
* Uses SQLite rather than a distributed database
* Rebuilds the complete search index after a crawl
* Uses a relatively simple relevance-scoring algorithm
* Does not implement advanced search features such as stemming, semantic search, or machine-learning-based ranking

These limitations keep the project understandable while demonstrating the fundamental components of a search engine.

## Learning Outcomes

Through this project, I implemented and worked with:

* Web crawling
* URL normalization
* `robots.txt`
* HTTP error handling
* Retry mechanisms
* Priority queues
* Graph-like link relationships
* Database persistence
* Inverted indexes
* Information retrieval
* Relevance scoring
* Text tokenization
* Django ORM
* Django forms and templates
* Pagination
* Search-result snippets

## Future Improvements

Possible future improvements include:

* Incremental index updates instead of rebuilding the complete index
* More advanced ranking algorithms
* Phrase search
* Fuzzy search
* Better duplicate-content detection
* Search filters
* Larger-scale storage using PostgreSQL or another search-oriented database
* Distributed crawling
