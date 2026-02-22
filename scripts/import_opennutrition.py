"""
One-time import: seeds UsdaFood table from OpenNutrition TSV.

Run from the calorie-tracker directory:
    python scripts/import_opennutrition.py
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import UsdaFood, db
from sqlalchemy import text

TSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'data', 'opennutrition', 'opennutrition_foods.tsv',
)

BATCH_SIZE = 2000


def _serving(raw):
    """Return (description, weight_g) from the serving JSON field."""
    try:
        s = json.loads(raw)
    except (ValueError, TypeError):
        return None, None

    common = s.get('common', {})
    metric = s.get('metric', {})

    desc = None
    if common.get('quantity') and common.get('unit'):
        qty = common['quantity']
        unit = common['unit']
        desc = f"{int(qty) if qty == int(qty) else qty} {unit}"

    weight_g = None
    if metric.get('unit') == 'g' and metric.get('quantity'):
        weight_g = float(metric['quantity'])

    return desc, weight_g


def _alternate_names(raw):
    """Return a single space-joined string of all alternate name tokens."""
    try:
        names = json.loads(raw)
    except (ValueError, TypeError):
        return None
    if not names:
        return None
    return ' '.join(n.lower() for n in names if n)


def run():
    app = create_app()
    with app.app_context():
        print('Dropping and recreating UsdaFood table...')
        UsdaFood.__table__.drop(db.engine, checkfirst=True)
        db.create_all()

        print(f'Reading {TSV_PATH}...')
        batch = []
        imported = skipped = 0

        with open(TSV_PATH, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                try:
                    nutr = json.loads(row['nutrition_100g'])
                except (ValueError, TypeError):
                    skipped += 1
                    continue

                calories = nutr.get('calories') or 0
                if not calories:
                    skipped += 1
                    continue

                serving_desc, serving_weight = _serving(row.get('serving', ''))

                batch.append(UsdaFood(
                    food_id=row['id'],
                    name=row['name'].strip(),
                    food_type=row.get('type'),
                    alternate_names=_alternate_names(row.get('alternate_names', '[]')),
                    barcode=row.get('ean_13') or None,
                    calories=float(calories),
                    protein_g=float(nutr.get('protein') or 0),
                    carbs_g=float(nutr.get('carbohydrates') or 0),
                    fat_g=float(nutr.get('total_fat') or 0),
                    fiber_g=float(nutr.get('dietary_fiber')) if nutr.get('dietary_fiber') else None,
                    serving_description=serving_desc,
                    serving_weight_g=serving_weight,
                ))

                if len(batch) >= BATCH_SIZE:
                    db.session.bulk_save_objects(batch)
                    db.session.commit()
                    imported += len(batch)
                    batch = []
                    print(f'  {imported:,} imported, {skipped:,} skipped...', end='\r')

        if batch:
            db.session.bulk_save_objects(batch)
            db.session.commit()
            imported += len(batch)

        print(f'\nDone. {imported:,} foods imported, {skipped:,} skipped (no calories).')

        print('Building FTS5 search index...')
        db.session.execute(text('DROP TABLE IF EXISTS usda_food_fts'))
        db.session.execute(text("""
            CREATE VIRTUAL TABLE usda_food_fts USING fts5(
                food_id UNINDEXED,
                food_type UNINDEXED,
                name,
                alternate_names,
                tokenize='unicode61 remove_diacritics 1'
            )
        """))
        db.session.execute(text("""
            INSERT INTO usda_food_fts(food_id, food_type, name, alternate_names)
            SELECT food_id, food_type, name, COALESCE(alternate_names, '')
            FROM usda_food
        """))
        db.session.commit()
        print('FTS5 index built.')


if __name__ == '__main__':
    run()
