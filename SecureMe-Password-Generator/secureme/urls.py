"""Project URL configuration: everything is handled by generator_app."""

from django.urls import include, path

urlpatterns = [
    path("", include("generator_app.urls")),
]
