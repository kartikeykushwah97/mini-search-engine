from django import forms

class CrawlForm(forms.Form):
    start_url = forms.URLField(
        label="Starting URL",
        widget=forms.URLInput(attrs={
            "placeholder": "https://example.com"
        })
    )
    
    max_depth = forms.IntegerField(
        label="Maximum Depth",
        min_value=0,
        initial=2,
    
    )
    
    
class SearchForm(forms.Form):
    query = forms.CharField(
        label="",
        max_length=100,
        widget=forms.TextInput(attrs={
            "placeholder": "Search crawled pages...."
        })
    )