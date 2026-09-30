from django.urls import path
from crawler.views import page_list, page_detail

urlpatterns = [
    path("", page_list, name="page_list"),
    path("page/<int:page_id>", page_detail, name="page_detail"),
]
