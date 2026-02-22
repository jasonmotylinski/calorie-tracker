"""
One-time import script: seeds UsdaFood table from USDA SR Legacy CSVs.

Run from the calorie-tracker directory:
    python scripts/import_usda.py
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import UsdaFood, db

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'data', 'usda')

# Nutrient IDs we care about (USDA SR Legacy Nutr_No -> model field)
NUTRIENT_FIELDS = {
    '208': 'calories',
    '203': 'protein_g',
    '204': 'fat_g',
    '205': 'carbs_g',
    '291': 'fiber_g',
}


def _clean(value):
    return value.strip().strip('"')


def load_food_groups():
    groups = {}
    with open(os.path.join(DATA_DIR, 'FD_GROUP.csv'), newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            groups[_clean(row['FdGrp_Cd'])] = _clean(row['FdGrp_desc'])
    return groups


def load_nutrients():
    """Returns {ndb_no: {field: value}} for the 5 nutrients we need."""
    print('Loading NUT_DATA.csv (this takes a moment)...')
    nutrients = {}
    with open(os.path.join(DATA_DIR, 'NUT_DATA.csv'), newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            nutr_no = _clean(row['Nutr_No'])
            if nutr_no not in NUTRIENT_FIELDS:
                continue
            ndb_no = _clean(row['NDB_No'])
            field = NUTRIENT_FIELDS[nutr_no]
            val = float(row['Nutr_Val']) if row['Nutr_Val'].strip() else 0.0
            if ndb_no not in nutrients:
                nutrients[ndb_no] = {}
            nutrients[ndb_no][field] = val
    return nutrients


def load_weights():
    """Returns {ndb_no: (description, grams)} using the first serving entry per food."""
    weights = {}
    with open(os.path.join(DATA_DIR, 'WEIGHT.csv'), newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            ndb_no = _clean(row['NDB_No'])
            if ndb_no in weights:
                continue  # keep seq=1 (first row per food)
            gm_wgt = row['Gm_Wgt'].strip()
            if not gm_wgt:
                continue
            amount = _clean(row['Amount'])
            desc = _clean(row['Msre_Desc'])
            serving_label = f"{amount} {desc}".strip()
            weights[ndb_no] = (serving_label, float(gm_wgt))
    return weights


def run():
    app = create_app()
    with app.app_context():
        db.create_all()

        groups = load_food_groups()
        nutrients = load_nutrients()
        weights = load_weights()

        print('Clearing existing USDA foods...')
        UsdaFood.query.delete()
        db.session.commit()

        print('Importing FOOD_DES.csv...')
        batch = []
        with open(os.path.join(DATA_DIR, 'FOOD_DES.csv'), newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                ndb_no = _clean(row['NDB_No'])
                fd_grp_cd = _clean(row['FdGrp_Cd'])
                nutr = nutrients.get(ndb_no, {})
                weight = weights.get(ndb_no)

                batch.append(UsdaFood(
                    ndb_no=ndb_no,
                    name=_clean(row['Long_Desc']),
                    food_group=groups.get(fd_grp_cd),
                    calories=nutr.get('calories', 0),
                    protein_g=nutr.get('protein_g', 0),
                    carbs_g=nutr.get('carbs_g', 0),
                    fat_g=nutr.get('fat_g', 0),
                    fiber_g=nutr.get('fiber_g'),
                    serving_description=weight[0] if weight else None,
                    serving_weight_g=weight[1] if weight else None,
                ))

        db.session.bulk_save_objects(batch)
        db.session.commit()
        print(f'Done. Imported {len(batch)} foods.')


if __name__ == '__main__':
    run()
