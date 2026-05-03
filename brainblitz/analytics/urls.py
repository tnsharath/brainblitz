from django.urls import path

from . import views

app_name = "analytics"

urlpatterns = [
    path("demo/", views.demo, name="demo"),
]
