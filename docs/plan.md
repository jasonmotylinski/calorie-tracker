# Calorie Tracker

We are building a calorie tracking app to track daily calories towards goal, macro nutrients, and weekly progress. This app should be a basic version of the Calory iOS app.

## Technical Requirements

- Simple. Concise.
- Built in Python (Flask, following habitz platform conventions)
- Needs to be built for the web and mobile web. UI needs to be responsive
- Needs a database backend
- API-first development
- Must use gunicorn for production
- Uses SQLite but can switch to Postgres
- Requires user account creation and login
- Should integrate with popular online nutrition databases like USDA FoodData Central and Open Food Facts
- Implementation should be in the calorie-tracker folder, not the root folder of this project

## Functional Requirements

- User-friendly
- Should be able to track per meal (breakfast, lunch, dinner, and snacks)
- Should display progress for the given day in the week

---

## Implementation Plan

### Phase 1: Project Scaffolding & Auth

Set up the project structure following existing habitz conventions (app factory, blueprints, SQLAlchemy, Flask-Login).

#### Directory Structure

```
calorie-tracker/
├── run.py                     # Entry point (port 5002)
├── config.py                  # Config classes (Dev/Test/Prod)
├── requirements.txt
├── .env.example
├── .gitignore
├── CLAUDE.md                  # Component-specific guidance
├── docs/
│   └── plan.md
├── migrations/
├── instance/                  # SQLite DB lives here
└── app/
    ├── __init__.py            # create_app() factory
    ├── models.py              # All SQLAlchemy models
    ├── forms.py               # WTForms
    ├── auth.py                # Auth blueprint (login, register, logout)
    ├── main.py                # Main blueprint (dashboard)
    ├── food.py                # Food search & logging blueprint
    ├── api.py                 # JSON API blueprint
    ├── services/
    │   ├── __init__.py
    │   ├── nutrition.py       # USDA & Open Food Facts API clients
    │   └── stats.py           # Calorie/macro calculation helpers
    ├── templates/
    │   ├── base.html
    │   ├── home.html          # Landing page (unauthenticated)
    │   ├── dashboard.html     # Main daily view (authenticated)
    │   ├── auth/
    │   │   ├── login.html
    │   │   └── register.html
    │   └── food/
    │       ├── search.html
    │       └── log.html
    └── static/
        ├── css/
        │   ├── base.css
        │   ├── components.css
        │   └── pages.css
        ├── js/
        │   └── main.js
        └── favicon.svg
```

#### Tasks

1. **Create `config.py`** — Dev/Test/Prod config classes, load `.env` via python-dotenv
2. **Create `app/__init__.py`** — App factory with Flask-Login, Flask-Migrate, SQLAlchemy init, blueprint registration
3. **Create `run.py`** — Entry point on port 5002
4. **Create `requirements.txt`**:
   - Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF, Flask-Migrate
   - WTForms, email-validator, Werkzeug, python-dotenv
   - gunicorn, requests (for nutrition API calls)
5. **Create User model** (`app/models.py`) — id, email, username, password_hash, daily_calorie_goal, created_at
6. **Create auth blueprint** (`app/auth.py`) — register, login, logout routes
7. **Create auth templates** — login.html, register.html extending base.html
8. **Create base.html** — Responsive layout, mobile-first, nav bar, flash messages
9. **Initialize migrations** — `flask db init && flask db migrate`

### Phase 2: Data Models

#### Models

**User** (extends phase 1)
| Column | Type | Notes |
|--------|------|-------|
| id | Integer | PK |
| email | String(120) | Unique, not null |
| username | String(80) | Unique, not null |
| password_hash | String(255) | Not null |
| daily_calorie_goal | Integer | Default 2000 |
| protein_goal_pct | Integer | Default 30 (percent of calories) |
| carb_goal_pct | Integer | Default 40 |
| fat_goal_pct | Integer | Default 30 |
| created_at | DateTime | Default utcnow |

**FoodItem** — cached food data from external APIs
| Column | Type | Notes |
|--------|------|-------|
| id | Integer | PK |
| name | String(200) | Not null |
| brand | String(200) | Nullable |
| source | String(20) | 'usda', 'openfoodfacts', 'custom' |
| source_id | String(100) | External API ID |
| calories | Float | Per serving |
| protein_g | Float | Per serving |
| carbs_g | Float | Per serving |
| fat_g | Float | Per serving |
| fiber_g | Float | Nullable |
| serving_size | String(100) | e.g. "1 cup (240ml)" |
| serving_weight_g | Float | Grams per serving |
| created_at | DateTime | |

**FoodLog** — a single logged food entry
| Column | Type | Notes |
|--------|------|-------|
| id | Integer | PK |
| user_id | Integer | FK → User |
| food_item_id | Integer | FK → FoodItem |
| meal_type | String(20) | 'breakfast', 'lunch', 'dinner', 'snack' |
| servings | Float | Default 1.0 |
| logged_date | Date | The day this entry belongs to |
| logged_at | DateTime | Exact timestamp of logging |
| calories | Float | Computed: food_item.calories * servings |
| protein_g | Float | Computed at log time |
| carbs_g | Float | Computed at log time |
| fat_g | Float | Computed at log time |

> **Design note:** We store computed macro values on the log entry itself so that edits to the cached FoodItem don't retroactively change historical logs.

#### Tasks

1. **Define all models** in `app/models.py`
2. **Add `to_dict()` methods** on each model for API serialization
3. **Run migration** — `flask db migrate -m "add food models"`

### Phase 3: Nutrition API Integration

Build a service layer that searches USDA FoodData Central and Open Food Facts, normalizes results into a common format, and caches them as FoodItem records.

#### Service: `app/services/nutrition.py`

```
search_foods(query, page=1) → list[dict]
    - Searches USDA FoodData Central first (free API key required)
    - Falls back / supplements with Open Food Facts
    - Returns normalized results: {name, brand, calories, protein, carbs, fat, serving_size, source, source_id}

get_food_detail(source, source_id) → dict
    - Fetches full nutrition info for a specific food
    - Creates/updates FoodItem cache record
    - Returns FoodItem
```

#### External APIs

- **USDA FoodData Central** — `https://api.nal.usda.gov/fdc/v1/foods/search`
  - Free API key from https://fdc.nal.usda.gov/api-key-signup
  - Store key in `.env` as `USDA_API_KEY`
- **Open Food Facts** — `https://world.openfoodfacts.org/api/v2/search`
  - No API key required
  - Use `User-Agent` header per their guidelines

#### Tasks

1. **Create `app/services/nutrition.py`** — USDA client, Open Food Facts client, result normalization
2. **Add `USDA_API_KEY` to config** and `.env.example`
3. **Write food search API endpoint** (`GET /api/foods/search?q=chicken&page=1`)
4. **Write food detail API endpoint** (`GET /api/foods/<source>/<source_id>`)

### Phase 4: Food Logging API

Build the core CRUD API for logging food entries.

#### API Endpoints (`app/api.py`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/foods/search?q=&page=` | Search nutrition databases |
| GET | `/api/foods/<source>/<source_id>` | Get food detail |
| GET | `/api/log?date=YYYY-MM-DD` | Get all entries for a date |
| POST | `/api/log` | Log a food entry |
| PUT | `/api/log/<id>` | Update servings or meal type |
| DELETE | `/api/log/<id>` | Delete a log entry |
| GET | `/api/stats/daily?date=YYYY-MM-DD` | Daily totals & goal progress |
| GET | `/api/stats/weekly?date=YYYY-MM-DD` | Weekly summary (7 days ending on date) |
| PUT | `/api/user/goals` | Update calorie & macro goals |

#### Tasks

1. **Create `app/api.py`** — All JSON API routes behind `@login_required`
2. **Create `app/services/stats.py`** — Daily totals, weekly aggregation, macro breakdowns
3. **Test API endpoints** with sample data

### Phase 5: Dashboard UI

The main screen users see after login. Inspired by Calory's daily view.

#### Dashboard Layout (mobile-first)

```
┌─────────────────────────────┐
│  ◀  Mon, Feb 16  ▶          │  ← Date navigation
├─────────────────────────────┤
│                             │
│      ╭───────────╮          │
│      │   1,247   │          │  ← Circular progress ring
│      │  / 2,000  │          │     Calories consumed / goal
│      │   753 left│          │
│      ╰───────────╯          │
│                             │
│  Protein    Carbs     Fat   │  ← Macro progress bars
│  ████░░░  ██████░  ███░░░  │     With gram counts
│   72/150g  180/200g  45/67g │
│                             │
├─────────────────────────────┤
│  🌅 Breakfast        420cal │  ← Meal sections
│  ├─ Oatmeal (1.5 srv) 225  │     Expandable, show entries
│  └─ Banana (1 srv)    105  │
│                    [+ Add]  │
├─────────────────────────────┤
│  🌞 Lunch            520cal │
│  ├─ Chicken Salad     380  │
│  └─ Apple              90  │
│                    [+ Add]  │
├─────────────────────────────┤
│  🌙 Dinner              —  │
│                    [+ Add]  │
├─────────────────────────────┤
│  🍿 Snacks           307cal │
│  └─ Trail Mix         307  │
│                    [+ Add]  │
├─────────────────────────────┤
│                             │
│  Weekly Overview            │
│  M  T  W  T  F  S  S       │  ← Mini bar chart
│  █  █  █  ▄  ░  ░  ░       │     Filled = logged days
│                             │
└─────────────────────────────┘
```

#### Tasks

1. **Create `app/main.py`** — Dashboard route serving `dashboard.html`
2. **Create `dashboard.html`** — Full daily view with all sections above
3. **Create CSS** — Mobile-first responsive design, calorie ring (CSS/SVG), macro bars, meal cards
4. **Create `main.js`** — Date navigation (prev/next day), fetch daily data from API, render UI dynamically
5. **Swipe-to-delete** on food log entries (mobile UX)

### Phase 6: Food Search & Logging UI

The flow when a user taps "+ Add" on a meal section.

#### Search & Log Flow

```
[+ Add Breakfast] → Search Screen → Select Food → Adjust Servings → Logged ✓

Search Screen:
┌─────────────────────────────┐
│  ← Breakfast                │
├─────────────────────────────┤
│  🔍 Search foods...        │  ← Type-ahead search
├─────────────────────────────┤
│  Recent                     │  ← Recent foods (quick re-log)
│  ├─ Oatmeal        150cal  │
│  ├─ Banana          105cal │
│  └─ Coffee w/ milk   45cal │
├─────────────────────────────┤
│  Search Results             │  ← From USDA / Open Food Facts
│  ├─ Chicken Breast  165cal │
│  ├─ Chicken Thigh   209cal │
│  └─ ...                    │
└─────────────────────────────┘

Log Screen (after selecting a food):
┌─────────────────────────────┐
│  ← Chicken Breast           │
├─────────────────────────────┤
│  Serving: 1 cup (140g)     │
│           [ - ]  1.0  [ + ]│  ← Adjust servings
├─────────────────────────────┤
│  Calories     165           │
│  Protein      31g           │  ← Updates live as
│  Carbs         0g           │     servings change
│  Fat          3.6g          │
├─────────────────────────────┤
│  Meal: (•) Breakfast        │  ← Can switch meal type
│        ( ) Lunch            │
│        ( ) Dinner           │
│        ( ) Snack            │
├─────────────────────────────┤
│      [ Log Food ]           │
└─────────────────────────────┘
```

#### Tasks

1. **Create `app/food.py`** — Food blueprint with search page route
2. **Create `food/search.html`** — Search interface with recent foods
3. **Create `food/log.html`** — Serving adjustment and confirmation
4. **JavaScript** — Debounced type-ahead search hitting `/api/foods/search`, serving multiplier with live macro update
5. **Quick-log from recents** — Tap a recent food to instantly re-log with same servings

### Phase 7: User Settings

#### Settings Screen

```
┌─────────────────────────────┐
│  Settings                   │
├─────────────────────────────┤
│  Daily Calorie Goal         │
│  [ 2,000 ] cal              │
├─────────────────────────────┤
│  Macro Split                │
│  Protein:  [30]%  → 150g   │
│  Carbs:    [40]%  → 200g   │  ← Auto-calculates grams
│  Fat:      [30]%  → 67g    │     from calorie goal
├─────────────────────────────┤
│  Account                    │
│  Email: user@email.com      │
│  [ Change Password ]        │
├─────────────────────────────┤
│  [ Save ]                   │
└─────────────────────────────┘
```

#### Tasks

1. **Add settings route** to auth or main blueprint
2. **Create settings template** with goal editing form
3. **API endpoint** `PUT /api/user/goals` for saving goals
4. **Validation** — Macro percentages must sum to 100

### Phase 8: Polish & Production Readiness

1. **Custom food entry** — Allow users to manually enter nutrition info for foods not in databases
2. **Empty states** — Friendly messaging when no foods logged yet
3. **Error handling** — Graceful API failure fallbacks, offline-friendly messaging
4. **Loading states** — Skeleton screens / spinners during API calls
5. **Gunicorn config** — `gunicorn -w 2 -b 0.0.0.0:5002 run:app`
6. **CLAUDE.md** — Write component-level guidance doc
7. **Final migration audit** — Ensure schema is clean and migration chain is valid

---

## Implementation Order

| Phase | Description | Depends On |
|-------|-------------|------------|
| 1 | Project scaffolding & auth | — |
| 2 | Data models | Phase 1 |
| 3 | Nutrition API integration | Phase 2 |
| 4 | Food logging API | Phase 2, 3 |
| 5 | Dashboard UI | Phase 4 |
| 6 | Food search & logging UI | Phase 4, 5 |
| 7 | User settings | Phase 4 |
| 8 | Polish & production | All phases |

Phases 5, 6, and 7 can be worked on in parallel once Phase 4 is complete.
