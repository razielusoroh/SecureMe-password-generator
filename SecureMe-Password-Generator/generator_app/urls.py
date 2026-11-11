from django.conf import settings
from django.urls import path, re_path
from django.views.static import serve

from . import views

app_name = "generator_app"

urlpatterns = [
    path("", views.index, name="index"),
    path("api/generate/", views.api_generate, name="generate"),
    path("api/strength/", views.api_strength, name="strength"),
    # Serve CSS/JS directly so the app runs with DEBUG off on a local machine.
    re_path(r"^static/(?P<path>.*)$", serve,
            {"document_root": settings.BASE_DIR / "generator_app" / "static"}),
]
