from app.models import FoodItem, UsdaFood, db


def search_foods(query, page=1, page_size=20):
    """Search USDA SR Legacy database by food name. Returns list of result dicts."""
    words = query.split()
    if not words:
        return []

    q = UsdaFood.query
    for word in words:
        q = q.filter(UsdaFood.name.ilike(f'%{word}%'))

    offset = (page - 1) * page_size
    foods = q.order_by(UsdaFood.name).offset(offset).limit(page_size).all()
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
