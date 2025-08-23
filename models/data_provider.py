#!/usr/bin/python3
# file name .......... data_provider.py
# scope .............. main class for manage data (model)
# languag ............ Python 3.11.2
# author ............. Stefano Alemani
# date ............... 14-08-2025
# version ............ 0.5.0

from models import scadenz
import models.readwrite_csv_xml as rwcsvxml
import traceback

class DataProvider():
    '''
    Class provider of all data. Read from file or from other data and return data.
    In MVC is model. From this class recall other functions inside in other 
    files like: add_scad.py, read_csv_xml.py, scadenz.py. 
    All in "models" directory.
    '''
    def __init__(self):
        self.path_fornitori = "./data_box/dati_fornitori.csv"
        self.path_clienti = "./data_box/dati_clienti.csv"

    def start_data(self):
        try:
            dati_fornitori, dati_clienti = self._load_csv_data()
            dati_table_head = self._build_table_head()
            return {
                "dati_clienti": dati_clienti,
                "dati_fornitori": dati_fornitori,
                "dati_table_head": dati_table_head
            }
        except Exception:
            print("Errore durante l'inizializzazione dei dati:")
            traceback.print_exc()
            return None

    def _load_csv_data(self):
        try:
            dati_fornitori = rwcsvxml.read_csv_clifor(self.path_fornitori)
            dati_clienti = rwcsvxml.read_csv_clifor(self.path_clienti)
        except FileNotFoundError:
            print("File CSV non trovato. Creo file vuoti.")
            rwcsvxml.make_csv_default_clifor()
            dati_fornitori = rwcsvxml.read_csv_clifor(self.path_fornitori)
            dati_clienti = rwcsvxml.read_csv_clifor(self.path_clienti)
        except ValueError:
            raise ValueError("Errore nella conversione dei dati CSV.")
        return dati_fornitori, dati_clienti

    def _build_table_head(self):
        active_year = self.get_year_active()
        scad_gen = scadenz.ViewScadGen(self.path_fornitori)

        scadenze_for = ["Fornitori"] + list(scad_gen.scad_cli_for(active_year))
        scad_gen.change_file(self.path_clienti)
        scadenze_cli = ["Clienti"] + list(scad_gen.scad_cli_for(active_year))

        differenze = ["Differenza"]
        for i in range(1, len(scadenze_for)):
            try:
                diff = float(scadenze_cli[i]) - float(scadenze_for[i])
                differenze.append(f"{diff:.2f}")
            except ValueError:
                differenze.append("Errore")

        return [tuple(scadenze_for), tuple(scadenze_cli), tuple(differenze)]

    def set_csv_path(self, path_cli_for):
        try:
            rwcsvxml.write_csv_path(path_cli_for)
            return True
        except Exception as e:
            print(f"Percorso non valido: {e}")
            return False

    def get_csv_path(self):
        #return dictionary like: 
        #{'clienti': ['/home/stefano/workarea/adeRead/xml-box/fornitori'], 
        #'fornitori': ['/home/stefano/workarea/adeRead/xml-box/clienti']}
        return rwcsvxml.read_csv_path("./config/path.csv")
        
    def get_year_active(self):
        return int(rwcsvxml.read_year()["active"])
                
    def set_year_active(self, year):
        # set active year. Data input like: 2025
        rwcsvxml.write_year({'active': [year]})
        
    def set_years_available(self, years):
        # set list of available years. Data input list like: [1999, 2000, 2015]
        rwcsvxml.write_year({'available': [years]})
        
    def start_data_old(self):
        """
        Inizializza i dati leggendo dai file CSV dati_fornitori e dati_clienti
        e restituisce i dati in dizionario così formattati (esempio):
        
        {'dati_clienti': [('RAMAC UTENSILI S.A.S.', '2930.77', '2025-01-20', 
        'FPR 1/25', '06855330152', '2025-01-20', '2930.77', 'MP05', 'O.M.S.  
        SNC', '06594700152'), ('RAMAC UTENSILI S.A.S.', '3946.03', '2025-02-19',
        'FPR 10/25', '06855330152', '2025-02-24', '3946.03', 'MP05', 'O.M.S.  
        SNC', '06594700152') ... ], 
        
        'dati_fornitori': [('DAPHNE IMPIANTI S.R.L.', '308.66', '2025-01-22', 
        '1', '02198400414', '2025-01-22', '308.66', 'MP01',
        'RAMAC UTENSILI SAS', '06855330152'), ('DETER SRL', '59.43', 
        '2025-01-31', '2025.FD159.SEDE', '08055800158', '2025-01-31', 
        '59.43', 'MP05', 'RAMAC UTENSILI SAS', '06855330152') ... ],
        
        'dati_table_head': [('Fornitori', '2930.77', '4185.80', '2275.31', 
        '5404.63', '11754.59', '15470.08', '14559.48', '3548.16', '20742.91', 
        '10161.63', '7079.64', '0.00'), ('Differenza', '2562.68', '4021.24', 
        '-1708.86', '-4211.70', '1002.68', '4405.48', '5211.05', '3136.90', 
        '107.80', '3943.51', '7079.64', '0.00')]}
        """
        try:
            # Prova a leggere i file CSV
            dati_fornitori = rwcsvxml.read_csv_clifor("./data_box/dati_fornitori.csv")
            dati_clienti = rwcsvxml.read_csv_clifor("./data_box/dati_clienti.csv")
        except FileNotFoundError:
            print("Errore: file CSV non trovato. Creo file vuoti, contabilizzare fatture XML per i dati")
            rwcsvxml.make_csv_default_clifor() # crea file vuoti non esistenti
            dati_fornitori = rwcsvxml.read_csv_clifor("./data_box/dati_fornitori.csv")
            dati_clienti = rwcsvxml.read_csv_clifor("./data_box/dati_clienti.csv")
        except ValueError:
            print("Errore: problema nella conversione dei dati.")
            return
        except Exception as e:
            print(f"Errore generico: {e}")
            return

        # organizza i dati e genera le scadenze clienti e fornitori nelle 
        # variabili scadenze_cli e scadenze_for, inoltre genera dati_table_head 
        # che permette di avere dati pronti per la visualizzazione del saldo
        # mensile delle fatture
        active_year = self.get_year_active()        
        make_scadenze = scadenz.ViewScadGen("./data_box/dati_fornitori.csv")
        dati_table_head = []
        # Raggruppa scadenze fornitori e clienti
        scadenze_for = list(make_scadenze.scad_cli_for(active_year))
        scadenze_for.insert(0, "Fornitori")
        dati_table_head.append(tuple(scadenze_for))

        # Cambia file "attivo"
        make_scadenze.change_file("./data_box/dati_clienti.csv")
        # Raggruppa scadenze fornitori e clienti
        scadenze_cli = list(make_scadenze.scad_cli_for(active_year))
        scadenze_cli.insert(0, "Clienti")
        dati_table_head.append(tuple(scadenze_cli))

        dati_parziali = []
        for x in range(len(scadenze_for) - 1):
            try:
                differenza = "{0:.2f}".format(round(float(scadenze_cli[x+1]) - float(scadenze_for[x+1]), 2))
            except ValueError:
                differenza = "Errore"
            dati_parziali.append(differenza)

        dati_parziali.insert(0, "Differenza")
        dati_table_head.append(tuple(dati_parziali))

        dati_out = dict([("dati_clienti", dati_clienti),
                    ("dati_fornitori", dati_fornitori),
                    ("dati_table_head", dati_table_head)
                ])
        return (dati_out)
