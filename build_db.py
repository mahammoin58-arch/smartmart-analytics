"""Build data/smartmart.db (SQLite star schema) from the clean data."""
from src.clean import load_raw, clean
from src import db

df, _ = clean(load_raw())
con = db.build_db(df, "data/smartmart.db")
con.commit()
print("Database built: data/smartmart.db")
