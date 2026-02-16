# Calorie Tracker

A mobile-first calorie and macro tracking app built with Flask and SQLite.

## Features

- **Daily Tracking** - Log calories and macros per meal (breakfast, lunch, dinner, snacks)
- **Food Search** - Search USDA FoodData Central and Open Food Facts databases
- **Calorie Ring** - Visual daily progress with SVG calorie ring
- **Macro Bars** - Track protein, carbs, and fat against goals
- **Weekly Overview** - Bar chart showing daily totals across the week
- **Custom Foods** - Add your own food entries with full nutrition info
- **Goal Setting** - Configurable calorie goal and macro percentage split

## Setup

### Requirements
- Python 3.10+
- pip

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your SECRET_KEY and USDA_API_KEY

# Initialize database
export FLASK_APP=run.py
flask db upgrade

# Run development server
python run.py
```

The app will be available at `http://localhost:5002`

### USDA API Key

Get a free API key at https://fdc.nal.usda.gov/api-key-signup and add it to your `.env` file. Open Food Facts works without a key.

## Usage

1. **Register** an account
2. **Set Goals** - Configure daily calorie target and macro split (protein/carbs/fat %)
3. **Add Food** - Tap "+ Add Food" on any meal section
4. **Search** - Search by name or pick from recent foods
5. **Adjust Servings** - Set serving count before logging
6. **Track Progress** - View daily ring, macro bars, and weekly chart

## Tech Stack

- **Backend** - Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Login
- **Database** - SQLite (Postgres-ready)
- **Frontend** - Jinja2 templates, vanilla JavaScript, custom CSS
- **APIs** - USDA FoodData Central, Open Food Facts
- **Auth** - Werkzeug password hashing, session-based login

## Development

Start with debug mode:
```bash
python run.py
```

## Production

```bash
gunicorn -w 2 -b 0.0.0.0:5002 run:app
```

Or use the provided scripts:
```bash
scripts/prod/server.sh    # Run via gunicorn with unix socket
scripts/prod/deploy.sh    # Pull, install deps, migrate, restart
```
