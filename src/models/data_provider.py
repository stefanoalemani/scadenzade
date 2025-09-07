#!/usr/bin/python3
# file name .......... data_provider.py
# scope .............. main class for manage data (model)
# languag ............ Python 3.11.2
# author ............. Stefano Alemani
# date ............... 14-08-2025
# version ............ 0.6.0

from models import scadenz
import models.readwrite_csv_xml as rwcsvxml
import traceback
from config.constants import PATH_CSV_SUPPLIERS, PATH_CSV_CLIENTS

class DataProvider():
    '''
    Class provider of all data. Read from file or from other data and return data.
    In MVC is model. From this class recall other functions inside in other 
    files like: add_scad.py, read_csv_xml.py, scadenz.py. 
    All in "models" directory.
    '''
    def __init__(self):
        pass

    def start_data(self):
        try:
            data_suppliers, data_clients = self._load_csv_data()
            dati_table_head = self._build_table_head()
            return {
                "data_clients": data_clients,
                "data_suppliers": data_suppliers,
                "dati_table_head": dati_table_head
            }
        except Exception:
            print("Errore durante l'inizializzazione dei dati:")
            traceback.print_exc()
            return None

    def _load_csv_data(self):
        try:
            data_suppliers = rwcsvxml.read_csv_clifor(PATH_CSV_SUPPLIERS)
            data_clients = rwcsvxml.read_csv_clifor(PATH_CSV_CLIENTS)
        except FileNotFoundError:
            print("File CSV non trovato. Creo file vuoti.")
            rwcsvxml.make_csv_default_clifor()
            data_suppliers = rwcsvxml.read_csv_clifor(PATH_CSV_SUPPLIERS)
            data_clients = rwcsvxml.read_csv_clifor(PATH_CSV_CLIENTS)
        except ValueError:
            raise ValueError("Errore nella conversione dei dati CSV.")
        return data_suppliers, data_clients

    def _build_table_head(self):
        active_year = self.get_year_active()
        scad_gen = scadenz.ViewScadGen(PATH_CSV_SUPPLIERS)

        scadenze_for = ["Fornitori"] + list(scad_gen.scad_cli_for(active_year))
        scad_gen.change_file(PATH_CSV_CLIENTS)
        scadenze_cli = ["Clienti"] + list(scad_gen.scad_cli_for(active_year))

        differenze = ["Differenza"]
        for i in range(1, len(scadenze_for)):
            try:
                diff = float(scadenze_cli[i]) - float(scadenze_for[i])
                differenze.append(f"{diff:.2f}")
            except ValueError:
                differenze.append("Errore")

        return [tuple(scadenze_for), tuple(scadenze_cli), tuple(differenze)]

    def get_csv_path(self):
        #return dictionary like: 
        #{'clienti': ['/home/stefano/workarea/adeRead/xml-box/clienti'], 
        #'fornitori': ['/home/stefano/workarea/adeRead/xml-box/fornitori']}        
        return rwcsvxml.read_csv_path()
        
    def set_csv_path(self, path_cli_for):
        try:
            rwcsvxml.write_csv_path(path_cli_for)
            return True
        except Exception as e:
            print(f"Percorso non valido: {e}")
            return False

    def ensure_csv_path_exists(self):
        rwcsvxml.ensure_csv_path_exists()

    def make_year_active(self):
        data = self._build_table_head
        print (data)
       
    def get_year_active(self):
        year = rwcsvxml.read_year()
        return int(year['active'])
                
    def set_year_active(self, year):
        # set active year. Data input like: 2025
        rwcsvxml.write_year({'active': [year]})
        
    def get_years_available(self):
        years = rwcsvxml.read_year()
        return years['available']
                
    def set_years_available(self, years):
        # set list of available years. Data input list like: [1999, 2000, 2015]
        rwcsvxml.write_year({'available': [years]})        