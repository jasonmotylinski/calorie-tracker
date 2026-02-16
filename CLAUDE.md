# Calorie Tracker — CLAUDE.md

## Commands

```bash
# Run dev server
cd calorie-tracker && source venv/bin/activate
python run.py                          # http://localhost:5002

# Database migrations
export FLASK_APP=run.py
flask db migrate -m "description"
flask db upgrade

# Production
gunicorn -w 2 -b 0.0.0.0:5002 run:app
```

## Architecture

Flask app factory in `app/__init__.py` → `create_app()`. Port 5002.

### Blueprints

| Blueprint | File | Prefix | Purpose |
|-----------|------|--------|---------|
| auth | `app/auth.py` | `/` | Login, register, logout |
| main | `app/main.py` | `/` | Dashboard, settings |
| food | `app/food.py` | `/food` | Food search & log pages |
| api | `app/api.py` | `/api` | JSON API (all CRUD) |

### Models (`app/models.py`)

- **User** — Auth, calorie/macro goals
- **FoodItem** — Cached food data from USDA/OpenFoodFacts/custom
- **FoodLog** — User's logged entries with computed macros

### Services (`app/services/`)

- **nutrition.py** — USDA FoodData Central + Open Food Facts API clients
- **stats.py** — Daily totals, weekly summary calculations

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/foods/search?q=` | Search nutrition databases |
| GET | `/api/foods/<id>` | Get cached food item |
| GET | `/api/foods/recent` | User's recently logged foods |
| GET | `/api/log?date=` | Get log entries for a date |
| POST | `/api/log` | Create log entry |
| PUT | `/api/log/<id>` | Update log entry |
| DELETE | `/api/log/<id>` | Delete log entry |
| GET | `/api/stats/daily?date=` | Daily totals |
| GET | `/api/stats/weekly?date=` | Weekly summary |
| PUT | `/api/user/goals` | Update calorie/macro goals |

## Config & Environment

- `.env` — `SECRET_KEY`, `USDA_API_KEY`, `FLASK_ENV`
- Get a free USDA API key at https://fdc.nal.usda.gov/api-key-signup

## Frontend

- Vanilla JS, Jinja2 templates, custom CSS
- Mobile-first responsive design
- Color palette: warm botanical greens + terracotta accents
- Fonts: Outfit (display) + DM Sans (body)
