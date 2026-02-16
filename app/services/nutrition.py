import requests
from flask import current_app

from app.models import FoodItem, db

USDA_SEARCH_URL = 'https://api.nal.usda.gov/fdc/v1/foods/search'
USDA_DETAIL_URL = 'https://api.nal.usda.gov/fdc/v1/food/{fdc_id}'
OFF_SEARCH_URL = 'https://world.openfoodfacts.org/cgi/search.pl'
OFF_PRODUCT_URL = 'https://world.openfoodfacts.org/api/v2/product/{code}.json'

OFF_HEADERS = {
    'User-Agent': 'Habitz CalorieTracker/1.0 (https://github.com/habitz)'
}


def _extract_usda_nutrient(nutrients, nutrient_id):
    for n in nutrients:
        if n.get('nutrientId') == nutrient_id:
            return n.get('value', 0)
    return 0


def search_usda(query, page=1, page_size=10):
    api_key = current_app.config.get('USDA_API_KEY')
    if not api_key:
        return []

    resp = requests.get(USDA_SEARCH_URL, params={
        'api_key': api_key,
        'query': query,
        'pageSize': page_size,
        'pageNumber': page,
        'dataType': ['Survey (FNDDS)', 'Branded'],
    }, timeout=10)

    if resp.status_code != 200:
        return []

    results = []
    for food in resp.json().get('foods', []):
        nutrients = food.get('foodNutrients', [])
        results.append({
            'name': food.get('description', '').title(),
            'brand': food.get('brandName') or food.get('brandOwner'),
            'source': 'usda',
            'source_id': str(food.get('fdcId', '')),
            'calories': _extract_usda_nutrient(nutrients, 1008),
            'protein_g': _extract_usda_nutrient(nutrients, 1003),
            'carbs_g': _extract_usda_nutrient(nutrients, 1005),
            'fat_g': _extract_usda_nutrient(nutrients, 1004),
            'fiber_g': _extract_usda_nutrient(nutrients, 1079),
            'serving_size': food.get('servingSize'),
            'serving_size_unit': food.get('servingSizeUnit', 'g'),
        })

    return results


def search_openfoodfacts(query, page=1, page_size=10):
    resp = requests.get(OFF_SEARCH_URL, params={
        'search_terms': query,
        'search_simple': 1,
        'action': 'process',
        'json': 1,
        'page': page,
        'page_size': page_size,
        'fields': 'code,product_name,brands,nutriments,serving_size',
    }, headers=OFF_HEADERS, timeout=10)

    if resp.status_code != 200:
        return []

    results = []
    for product in resp.json().get('products', []):
        n = product.get('nutriments', {})
        name = product.get('product_name')
        if not name:
            continue
        results.append({
            'name': name,
            'brand': product.get('brands'),
            'source': 'openfoodfacts',
            'source_id': product.get('code', ''),
            'calories': n.get('energy-kcal_serving') or n.get('energy-kcal_100g', 0),
            'protein_g': n.get('proteins_serving') or n.get('proteins_100g', 0),
            'carbs_g': n.get('carbohydrates_serving') or n.get('carbohydrates_100g', 0),
            'fat_g': n.get('fat_serving') or n.get('fat_100g', 0),
            'fiber_g': n.get('fiber_serving') or n.get('fiber_100g'),
            'serving_size': product.get('serving_size'),
            'serving_size_unit': 'g',
        })

    return results


def search_foods(query, page=1):
    results = []
    try:
        results.extend(search_usda(query, page))
    except Exception:
        pass
    try:
        results.extend(search_openfoodfacts(query, page))
    except Exception:
        pass
    return results


def get_or_create_food_item(data):
    """Find existing cached FoodItem or create one from search result data."""
    if data.get('source') and data.get('source_id'):
        existing = FoodItem.query.filter_by(
            source=data['source'],
            source_id=data['source_id']
        ).first()
        if existing:
            return existing

    serving = data.get('serving_size')
    if serving and data.get('serving_size_unit'):
        serving = f"{serving}{data['serving_size_unit']}"

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
        serving_size=serving,
        serving_weight_g=data.get('serving_weight_g'),
    )
    db.session.add(item)
    db.session.commit()
    return item
