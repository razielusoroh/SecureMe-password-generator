# SecureMe – Random Password Generator

A Python (Django) web application that generates strong, unique passwords for SecureMe Inc.
Student: Raziel Usoroh (Student1616520)

## Features
- Random passwords with a chosen length (6–128) and character types (A–Z, a–z, 0–9, symbols)
- Option to avoid look-alike characters (1 l I 0 O o)
- Memorable passwords built from your own words
- Strength meter: weak / medium / strong, with tips
- One-click copy to clipboard
- Nothing is stored or logged: no database, no files, no cookies holding passwords

## Run it
```
pip install -r requirements.txt
python manage.py runserver
```
Then open http://127.0.0.1:8000 in any browser. Press Ctrl + C to stop.

No `migrate` step is needed: the project deliberately has no database.

## Run the tests
```
python manage.py test
```

## Login credentials / database
None. The app has no accounts and deliberately uses no database, because the
specification requires that no passwords are ever stored.
