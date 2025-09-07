from datetime import datetime
from pathlib import Path
from config.year_loader import read_year

SRC_DIR = Path(__file__).resolve().parent.parent

CONFIG_DIR = SRC_DIR / "config"
DATA_DIR = SRC_DIR / "data_box"
PATH_CSV_SUPPLIERS = DATA_DIR / "data_suppliers.csv"
PATH_CSV_CLIENTS = DATA_DIR / "data_clients.csv"
PATH_YEAR = CONFIG_DIR / "year.csv"

# constant for listboxes generation
SCAD_LIST_HEAD = [("Calcolo", 'left'), ("Gennaio", 'right'), ("Febbraio", 'right'),
                  ("Marzo", 'right'), ("Aprile", 'right'), ("Maggio", 'right'),
                  ("Giugno", 'right'), ("Luglio", 'right'), ("Agosto", 'right'),
                  ("Settembre", 'right'), ("Ottobre", 'right'), ("Novembre", 'right'),
                  ("Dicembre", 'right')]

CLI_LIST_HEAD = [("Cliente", 'left'), ("Importo scadenza", 'right'),
                 ("Data scadenza", 'center'), ("Numero documento", 'left')]

FOR_LIST_HEAD = [("Fornitore", 'left'), ("Importo scadenza", 'right'),
                 ("Data scadenza", 'center'), ("Numero documento", 'left')]

# constant for year active
# YEAR_ACT = datetime.strptime(str(datetime.now().date()), "%Y-%m-%d").year # formato per XML ADE
class YearAct:
    YEAR_ACT = read_year()

# palette for widget of urwid
PALETTE = [
    ('activeListBox', 'black', 'light red'),
    ('activeLineBox', 'light red', 'default'),
    ('normalListBox', 'default', 'default'),
    ('header', 'black', 'light gray'),
    ('header_text', 'light red', 'default'),
    ('normal', 'default', 'default'),
    ('selected', 'black', 'light cyan'),
    ('popup', 'black', 'light cyan'),
    ('popup_title', 'white', 'light cyan'),
    ('buttonPopup', 'dark magenta', 'default'),
    ('toolbar_button', 'black', 'light gray'),
    ('toolbar_button_focus', 'white', 'dark blue'),
    ('toolbar_button_flash', 'black', 'yellow'),
    ('ok_button_focus', 'white', 'dark blue'),
    ('ok_button', 'light cyan', 'black'),
    ('cancel_button_focus', 'white', 'dark red'),
    ('cancel_button', 'light red', 'black'),
    ('info_text', 'light red', 'black'),
    ('side_text', 'light green', 'black'),
    ('path_style', 'white', 'black'),
    ("status_text_black", 'black', 'light gray'),
    ("status_text_red", 'dark red', 'light gray'),
    ("status_text_blue", 'dark blue', 'light gray')
]