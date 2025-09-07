from pathlib import Path
import csv

def read_year():
    path_year = Path(__file__).resolve().parent.parent / "config" / "year.csv"
    try:
        with path_year.open(newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                active = row.get("active")
                if active:
                    return int(active)
    except Exception as e:
        print(f"Errore nella lettura del file year.csv: {e}")
    return None  # oppure un valore di default, tipo datetime.now().year