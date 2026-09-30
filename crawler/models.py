from django.db import models

class Page(models.Model):
    url = models.URLField(unique=True)
    status_code = models.IntegerField()
    title = models.TextField(null=True, blank=True)
    headings = models.JSONField(default=list)
    text = models.TextField(blank=True)
    links = models.JSONField(default=list)
    incoming_links = models.PositiveIntegerField(default=0)
    last_crawled = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.title or self.url
    
class IndexEntry(models.Model):
    word = models.CharField(max_length=100)
    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    frequency = models.PositiveIntegerField(default=0)
    
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
            fields=["word", "page"],
            name="unique_word_page"
            )
        ]