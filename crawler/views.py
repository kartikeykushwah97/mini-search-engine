import re
from django.utils import timezone
from django.db import transaction
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.core.paginator import Paginator
from .models import Page, IndexEntry
from crawler.forms import CrawlForm, SearchForm
from .crawler import crawl

STOP_WORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "is",
    "are",
    "was",
    "were",
    "of",
    "to",
    "in",
    "on",
    "for",
    "with",
    "at",
    "by",
    "from",
}

def tokenize(text):
    return re.findall(r"\b\w+\b", text.lower())

@transaction.atomic
def build_database_index(pages):
    pages = list(pages)
    
    IndexEntry.objects.all().delete()
    
    for page in pages:
        word_counts = {}
        
        for word in tokenize(page.text):
            word_counts[word] = word_counts.get(word, 0) + 1
       
        for word, frequency in word_counts.items():
            IndexEntry.objects.create(
                word=word,
                page=page,
                frequency=frequency
            )

def create_snippet(text, query, length=150):
    if not text or not query:
        return ""

    pattern = rf"\b{re.escape(query)}\b"

    match = re.search(pattern, text, flags=re.IGNORECASE)

    if not match:
        return escape(text[:length])

    position = match.start()

    start = max(0, position - 60)
    end = min(len(text), match.end() + 90)

    snippet = text[start:end]

    if start > 0:
        snippet = "... " + snippet

    if end < len(text):
        snippet += " ..."

    highlighted_snippet = re.sub(
        pattern,
        lambda match: f"<mark>{escape(match.group())}</mark>",
        snippet,
        flags=re.IGNORECASE
    )

    return mark_safe(highlighted_snippet)


def search_index(query):
    words = tokenize(query)
    
    if not words:
        return set()
    
    results = set(
        IndexEntry.objects.filter(word=words[0]).values_list("page_id", flat=True))
     
    
    for word in words[1:]:
        page_ids = set(
            IndexEntry.objects.filter(word=word).values_list("page_id", flat=True)
        )
        
        results = results & page_ids
    
    return results

def page_list(request):
    pages = Page.objects.all()
    
    
    crawl_form = CrawlForm()
    search_form = SearchForm(request.GET or None)
    
    if request.method == "POST":
        crawl_form = CrawlForm(request.POST)
        
        if crawl_form.is_valid():
            start_url = crawl_form.cleaned_data["start_url"]
            max_depth = crawl_form.cleaned_data["max_depth"]
            
            crawled_pages, incoming_links = crawl(start_url, max_depth)
            
            for page_data in crawled_pages:
                Page.objects.update_or_create(
                    url=page_data["url"],
                    defaults={
                        "status_code": page_data["status_code"],
                        "title": page_data["title"],
                        "headings": page_data["headings"],
                        "text": page_data["text"],
                        "links": page_data["links"],
                        "incoming_links": incoming_links.get(page_data["url"], 0),
                        "last_crawled": timezone.now(),
                    }
                )
            build_database_index(Page.objects.all())
            pages = Page.objects.all()
    
    if search_form.is_valid():
            query = search_form.cleaned_data["query"]
            search_terms = [ term for term in query.split() if term.lower() not in STOP_WORDS]
            
            if not search_terms:
                pages = Page.objects.none()

            else:    
                page_ids = search_index(" ".join(search_terms))
                pages = Page.objects.filter(
                    pk__in=list(page_ids)
                )
                             
                for page in pages:
                    score = 0

                    for term in search_terms:
                        pattern = rf"\b{re.escape(term)}\b"

                        # Base relevance
                        if re.search(pattern, page.title or "", re.IGNORECASE):
                            score += 10

                        if re.search(pattern, " ".join(page.headings or []), re.IGNORECASE):
                            score += 5

                        if re.search(pattern, page.text or "", re.IGNORECASE):
                            score += 1

                        
                        frequency = IndexEntry.objects.filter(
                            word=term,
                            page=page
                        ).values_list("frequency", flat=True).first()
                        
                        frequency = frequency or 0 

                        frequency_bonus = min(frequency, 5)
                        score += frequency_bonus
                        
                    link_bonus = min(page.incoming_links, 10)
                    score += link_bonus

                    page.relevance = score
                    page.snippet = create_snippet(page.text, query)   
                    
                pages = sorted(
                    pages,
                    key=lambda page: (-page.relevance, page.title or "")
                )
            
    total_pages = Page.objects.count()
            
    successful_pages = Page.objects.filter(
        status_code = 200
    ).count()
    
    error_pages = Page.objects.filter(
    Q(status_code__isnull=True) | ~Q(status_code=200)
    ).count()
    
    paginator = Paginator(pages, 10)
    
    page_number = request.GET.get("page")
    
    pages = paginator.get_page(page_number)

    
        
    return render(request, "crawler/page_list.html", {
        "pages": pages, 
        "crawl_form" : crawl_form,
        "search_form" : search_form,
        "total_pages" : total_pages,
        "successful_pages" : successful_pages,
        "error_pages" : error_pages,
        })
    
def page_detail(request, page_id):
    page = get_object_or_404(Page, id=page_id)
    
    return render(request, 'crawler/page_detail.html', {"page":page})