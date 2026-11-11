"""
Views for the SecureMe Password Generator.

Passwords are generated in memory, returned once in the JSON response
and then forgotten. Nothing is saved to a database, file or log.
Requests must be POST so options never appear in URLs or history.
"""

import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from . import generator as gen


@require_GET
def index(request):
    return render(request, "generator_app/index.html", {
        "min_length": gen.MIN_LENGTH,
        "max_length": gen.MAX_LENGTH,
        "max_words": gen.MAX_WORDS,
    })


def _read_json(request):
    try:
        data = json.loads(request.body or b"{}")
        return data if isinstance(data, dict) else {}
    except (ValueError, UnicodeDecodeError):
        return {}


def _to_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@require_POST
def api_generate(request):
    data = _read_json(request)
    mode = data.get("mode", "random")
    length = _to_int(data.get("length"), 16)
    opts = {
        "digits": bool(data.get("digits", True)),
        "symbols": bool(data.get("symbols", True)),
        "avoid_ambiguous": bool(data.get("avoid_ambiguous", False)),
    }

    known_words = None
    try:
        if mode == "words":
            known_words = gen.clean_words(data.get("words", ""))
            password = gen.generate_from_words(known_words, length=length, **opts)
        else:
            password = gen.generate_random(
                length=length,
                upper=bool(data.get("upper", True)),
                lower=bool(data.get("lower", True)),
                **opts,
            )
    except gen.PasswordError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse({
        "password": password,
        "strength": gen.check_strength(password, known_words),
    })


@require_POST
def api_strength(request):
    data = _read_json(request)
    return JsonResponse(gen.check_strength(str(data.get("password", ""))))
