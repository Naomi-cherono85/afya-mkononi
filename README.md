# Afya Mkononi

AI-powered patient support for smarter clinic workflows.

Afya Mkononi (*Swahili: "health in hand"*) is a 4-week MVP healthcare assistant that
provides general health guidance, supports appointment booking, and sets reminders —
while escalating emergencies to professional care. See `docs/` for full specs.

## Status

Week 1 — Foundation + Product Docs. Pre-MVP.

## Tech stack

- Python 3.11+ / Django 5.x
- Django REST Framework
- PostgreSQL 15+
- Anthropic Claude (via SDK)
- Tailwind CSS (CDN) for the v1 UI
- Render for deployment

See `docs/solution-design-document.md` for the full architecture.

## Local setup

```bash
# 1. Clone
git clone https://github.com/Naomi-cherono85/afya-mkononi.git
cd afya-mkononi/backend

# 2. Virtualenv
python -m venv myvenv
myvenv\Scripts\activate          # Windows
# source myvenv/bin/activate     # macOS / Linux

# 3. Install deps
pip install -r requirements.txt

# 4. Configure env
copy .env.example .env           # then edit .env with real values

# 5. Create local PostgreSQL DB matching DATABASE_URL in .env
#    (default: afya_mkononi_dev)

# 6. Migrate + run
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Visit http://127.0.0.1:8000/admin/ to confirm Django admin loads.

## Project layout

```
afya-mkononi/
├── backend/
│   ├── afya_mkononi/        # Django project package (settings, urls, wsgi)
│   ├── apps/                # Django apps (added in Week 2)
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env                 # local secrets (gitignored)
│   └── .env.example
├── docs/                    # PRD, SDD, API design, database design, user journeys
└── README.md
```

## Documentation

- [Product Requirements](docs/product-requirements-document.md)
- [Solution Design](docs/solution-design-document.md)
- [Database Design](docs/database-design.md)
- [API Design](docs/api-design.md)
- [User Journeys](docs/user-journeys.md)
- [Implementation Plan](docs/implementation-plan.md)

## License

MIT
