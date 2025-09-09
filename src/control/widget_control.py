from datetime import datetime
from models.scadenz import ScadDati
from models.data_provider import DataProvider
from config.constants import PATH_CSV_SUPPLIERS, PATH_CSV_CLIENTS

class AccountInvoices:
    """
    Class to account for XML invoices and create CSV files so you can work on 
    them and not on the original XML files
    """
    def __init__(self):
        pass

    def make_csv(self, start_path):
        try:
            scadenzclass = ScadDati(start_path[0])
            scadenzclass.read_xml()
            scadenzclass.xml_to_csv(PATH_CSV_SUPPLIERS)
            years_deadlines_suppliers = scadenzclass.sniff_years() # legge gli anni delle scadenze fatture fornitori

            scadenzclass.change_file(start_path[1])
            scadenzclass.read_xml()
            scadenzclass.xml_to_csv(PATH_CSV_CLIENTS)
            years_deadlines_client = scadenzclass.sniff_years() # legge gli anni delle scadenze fatture clienti
            
            # trova dalle fatture gli anni delle scadenze e le mette negli anni disponibili in years.csv
            merge_years = [years_deadlines_suppliers, years_deadlines_client]
            flat_list = [year for sublist in merge_years for year in sublist]
            list_years = sorted(set(flat_list))
            scadenzclass.write_years_csv(datetime.now().year, list_years)
            return True
            
        except Exception as e:
            print(f"Errore durante la contabilizzazione: {e}")
            return False

class Event:
    """
    Class for event data
    """
    def __init__(self, tipology, source=None, payload=None):
        self.tipology = tipology              # es: "listbox_enter"
        self.source = source      # es: self.title o l'istanza stessa
        self.payload = payload or {}  # dizionario con dati extra

    def __repr__(self):
        return f"<Event tipology={self.tipology} source={self.source}>"

class ControllerW:
    """
    Class for manage event and do some event
    """
    def __init__(self):
        # Dizionario: name_event → lista di callback
        self._events = {}
        self.account_invoices = AccountInvoices()
        self.data_provider = DataProvider()

    def rec_event(self, name_event, callback):
        """
        Registra una funzione da chiamare quando viene emesso l'event.
        """
        if name_event not in self._events:
            self._events[name_event] = []
        self._events[name_event].append(callback)

    def emit_event(self, event):
        """
        Emette un event, scorrendo tutte le funzioni registrate.
        """
        listeners = self._events.get(event.tipology, [])
        for listener in listeners:
            listener(event)

    def make_invoices(self, start_path, sorgente_widget):
        result = self.account_invoices.make_csv(start_path)
        tipology = "Info" if result else "Warning"
        message = "Elaborazione terminata con successo" if result else "Elaborazione non riuscita"        
        event = Event("text-statusbar", sorgente_widget, {tipology: message})
        self.emit_event(event)
        
    def get_start_paths(self):
        try:
            path_dict = self.data_provider.get_csv_path()
            suppliers = path_dict.get("suppliers", [])
            clients = path_dict.get("clients", [])
            if clients and suppliers:
                return [suppliers[0], clients[0]]
            else:
                return ["", ""]
        except Exception as e:
            print(f"Errore nel controller: {e}")
            return ["", ""]

    def set_start_paths(self, path):
        return self.data_provider.set_csv_path(path)
        
    def get_years_available(self):
        return list(self.data_provider.get_years_available())
        
    def set_years_act(self, year):
        return self.data_provider.set_year_active(year)

    def manage_select_scadence(self, payload):
        event = Event(
            tipology="richiesta_filtro_scadenze",
            source=self,
            payload=payload  # contiene "mese" e "year"
        )
        self.emit_event(event)
        
    def update_year_and_select(self, year, month=1):
        # 1. Aggiorna l’anno
        year_event = Event(
            tipology="anno_aggiornato",
            source=self,
            payload={"anno": year}
        )
        self.emit_event(year_event)

        # 2. Filtra i dati con il nuovo anno impostato
        event_filter = Event(
            tipology="richiesta_filtro_scadenze",
            source=self,
            payload={"month": month, "year": year}
        )
        self.emit_event(event_filter)