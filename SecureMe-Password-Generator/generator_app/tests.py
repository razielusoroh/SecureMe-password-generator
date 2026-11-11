"""
Automated tests for the SecureMe Password Generator.

Run from the project folder:   python manage.py test
"""

import json
import os
import time
from unittest import TestCase

from django.test import Client, SimpleTestCase

from . import generator as gen


# ---------------- Generator: random mode ----------------

class RandomModeTests(TestCase):

    def test_length(self):
        for length in (6, 12, 16, 64, 128):
            self.assertEqual(len(gen.generate_random(length=length)), length)

    def test_every_selected_type_present(self):
        for _ in range(200):
            pw = gen.generate_random(length=8)
            self.assertTrue(any(c.isupper() for c in pw))
            self.assertTrue(any(c.islower() for c in pw))
            self.assertTrue(any(c.isdigit() for c in pw))
            self.assertTrue(any(c in gen.SYMBOLS for c in pw))

    def test_digits_only(self):
        pw = gen.generate_random(length=20, upper=False, lower=False, symbols=False)
        self.assertTrue(pw.isdigit())

    def test_no_symbols(self):
        for _ in range(100):
            self.assertTrue(gen.generate_random(length=30, symbols=False).isalnum())

    def test_avoid_ambiguous(self):
        for _ in range(300):
            pw = gen.generate_random(length=64, avoid_ambiguous=True)
            self.assertFalse(set(pw) & gen.AMBIGUOUS)

    def test_no_types_selected(self):
        with self.assertRaises(gen.PasswordError):
            gen.generate_random(upper=False, lower=False, digits=False, symbols=False)

    def test_bad_length(self):
        for bad in (0, 5, 129, 1000, "16", None):
            with self.assertRaises(gen.PasswordError):
                gen.generate_random(length=bad)

    def test_unique(self):
        passwords = {gen.generate_random(length=16) for _ in range(5000)}
        self.assertEqual(len(passwords), 5000)

    def test_fast(self):
        start = time.perf_counter()
        for _ in range(1000):
            gen.generate_random(length=128)
        self.assertLess(time.perf_counter() - start, 2)


# ---------------- Generator: word mode ----------------

class WordModeTests(TestCase):

    def test_words_kept(self):
        pw = gen.generate_from_words("lagos sunset music", length=16).lower()
        for w in ("lagos", "sunset", "music"):
            self.assertIn(w, pw)

    def test_minimum_length(self):
        self.assertGreaterEqual(len(gen.generate_from_words("cat", length=20)), 20)

    def test_digit_and_symbol_added(self):
        for _ in range(100):
            pw = gen.generate_from_words("blue river", length=12)
            self.assertTrue(any(c.isdigit() for c in pw))
            self.assertTrue(any(c in gen.SYMBOLS for c in pw))

    def test_cleaning(self):
        self.assertEqual(gen.clean_words("red, green,  blue!!"), ["red", "green", "blue"])

    def test_empty(self):
        with self.assertRaises(gen.PasswordError):
            gen.generate_from_words("   ")

    def test_too_many(self):
        with self.assertRaises(gen.PasswordError):
            gen.generate_from_words("a b c d e f g")


# ---------------- Strength ----------------

class StrengthTests(TestCase):

    def test_labels(self):
        cases = [("", "weak"), ("abc", "weak"), ("password", "weak"),
                 ("Sunset2024", "medium"), ("Tq7#vL9!pX2@mR4z", "strong")]
        for pw, label in cases:
            self.assertEqual(gen.check_strength(pw)["label"], label, pw)

    def test_default_random_is_strong(self):
        for _ in range(100):
            pw = gen.generate_random(length=16)
            self.assertEqual(gen.check_strength(pw)["label"], "strong")

    def test_own_words_rated_honestly(self):
        words = ["lagos", "sunset", "music"]
        pw = gen.generate_from_words(words, length=16)
        self.assertLess(gen.check_strength(pw, words)["entropy"],
                        gen.check_strength(pw)["entropy"])


# ---------------- Django views ----------------

class ViewTests(SimpleTestCase):

    def post(self, data):
        return self.client.post("/api/generate/", json.dumps(data),
                                content_type="application/json")

    def test_home_page(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "SecureMe")

    def test_random(self):
        res = self.post({"mode": "random", "length": 20})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()["password"]), 20)

    def test_words(self):
        res = self.post({"mode": "words", "words": "moon tea", "length": 14})
        self.assertEqual(res.status_code, 200)
        self.assertIn("moon", res.json()["password"].lower())

    def test_error(self):
        res = self.post({"upper": False, "lower": False, "digits": False, "symbols": False})
        self.assertEqual(res.status_code, 400)
        self.assertIn("error", res.json())

    def test_bad_json(self):
        res = self.client.post("/api/generate/", "not json", content_type="application/json")
        self.assertEqual(res.status_code, 200)  # falls back to safe defaults

    def test_no_store_header(self):
        self.assertIn("no-store", self.post({})["Cache-Control"])

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get("/api/generate/").status_code, 405)

    def test_csrf_required(self):
        strict = Client(enforce_csrf_checks=True)
        res = strict.post("/api/generate/", "{}", content_type="application/json")
        self.assertEqual(res.status_code, 403)

    def test_nothing_written_to_disk(self):
        folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        before = set(os.listdir(folder))
        for _ in range(20):
            self.post({})
        self.assertEqual(before, set(os.listdir(folder)))

    def test_static_files_served(self):
        res = self.client.get("/static/generator_app/style.css")
        self.assertEqual(res.status_code, 200)
