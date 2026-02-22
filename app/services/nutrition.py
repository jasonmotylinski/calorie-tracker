import sqlalchemy as sa

from app.models import FoodItem, UsdaFood, db


def _stem(word):
    """Strip common English plural suffixes so 'eggs' matches 'Egg', etc."""
    w = word.lower()
    if w.endswith('oes') and len(w) > 4:   # tomatoes → tomato
        return w[:-2]
    if w.endswith('ies') and len(w) > 4:   # berries → berr (good enough for ilike)
        return w[:-3] + 'y'
    if w.endswith('s') and not w.endswith('ss') and len(w) > 3:  # eggs → egg
        return w[:-1]
    return w


def _word_filter(word):
    """Match a word OR its stemmed form."""
    stem = _stem(word)
    if stem != word.lower():
        return sa.or_(UsdaFood.name.ilike(f'%{word}%'),
                      UsdaFood.name.ilike(f'%{stem}%'))
    return UsdaFood.name.ilike(f'%{word}%')


def search_foods(query, page=1, page_size=20):
    """Search USDA SR Legacy database by food name. Returns list of result dicts."""
    words = query.split()
    if not words:
        return []

    q = UsdaFood.query
    for word in words:
        q = q.filter(_word_filter(word))

    # Relevance ordering:
    #   0 = base food: name starts with stem (or stem+s) followed by comma
    #       "Egg, whole…" for "eggs", "Apples, raw…" for "apple"
    #   1 = starts with stem as word prefix ("Egg custards…", "Applebee's…")
    #   2 = stem appears elsewhere in name
    first_stem = _stem(words[0])
    first_word = words[0].lower()
    relevance = sa.case(
        (sa.or_(UsdaFood.name.ilike(f'{first_word},%'),
                UsdaFood.name.ilike(f'{first_stem},%'),
                UsdaFood.name.ilike(f'{first_stem}s,%')), 0),
        (sa.or_(UsdaFood.name.ilike(f'{first_word}%'),
                UsdaFood.name.ilike(f'{first_stem}%')), 1),
        else_=2,
    )
    offset = (page - 1) * page_size
    foods = q.order_by(relevance, UsdaFood.name).offset(offset).limit(page_size).all()
    return [food.to_search_result() for food in foods]


def get_or_create_food_item(data):
    """Find existing cached FoodItem or create one from search result data."""
    if data.get('source') and data.get('source_id'):
        existing = FoodItem.query.filter_by(
            source=data['source'],
            source_id=data['source_id']
        ).first()
        if existing:
            return existing

    item = FoodItem(
        name=data['name'],
        brand=data.get('brand'),
        source=data.get('source', 'custom'),
        source_id=data.get('source_id'),
        calories=data.get('calories', 0),
        protein_g=data.get('protein_g', 0),
        carbs_g=data.get('carbs_g', 0),
        fat_g=data.get('fat_g', 0),
        fiber_g=data.get('fiber_g'),
        serving_size=data.get('serving_size'),
        serving_weight_g=data.get('serving_weight_g'),
    )
    db.session.add(item)
    db.session.commit()
    return item
