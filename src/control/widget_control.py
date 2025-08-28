from datetime import datetime
from models.scadenz import ScadDati
from models.data_provider import DataProvider
from config.constants import PATH_CSV_FORNITORI, PATH_CSV_CLIENTI

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
            scadenzclass.xml_to_csv(PATH_CSV_FORNITORI)

            scadenzclass.change_file(start_path[1])
            scadenzclass.read_xml()
            scadenzclass.xml_to_csv(PATH_CSV_CLIENTI)
            return True
        except Exception as e:
            print(f"Errore durante la contabilizzazione: {e}")
            return False

class Event:
    """
    Class for event data
    """
    def __init__(self, tipo, sorgente=None, payload=None):
        self.tipo = tipo              # es: "listbox_enter"
        self.sorgente = sorgente      # es: self.title o l'istanza stessa
        self.payload = payload or {}  # dizionario con dati extra

    def __repr__(self):
        return f"<Event tipo={self.tipo} sorgente={self.sorgente}>"

class ControllerW:
    """
    Class for manage event and do some event
    """
    def __init__(self):
        # Dizionario: nome_evento → lista di callback
        self._eventi = {}
        self.account_invoices = AccountInvoices()
        self.data_provider = DataProvider()

    def registra_evento(self, nome_evento, callback):
        """
        Registra una funzione da chiamare quando viene emesso l'evento.
        """
        if nome_evento not in self._eventi:
            self._eventi[nome_evento] = []
        self._eventi[nome_evento].append(callback)

    def emetti_evento(self, evento):
        """
        Emette un evento, scorrendo tutte le funzioni registrate.
        """
        listeners = self._eventi.get(evento.tipo, [])
        for listener in listeners:
            listener(evento)

    def elabora_fatture(self, start_path, sorgente_widget):
        esito = self.account_invoices.make_csv(start_path)
        tipo = "Info" if esito else "Warning"
        messaggio = "Elaborazione terminata con successo" if esito else "Elaborazione non riuscita"        
        evento = Event("text-statusbar", sorgente_widget, {tipo: messaggio})
        self.emetti_evento(evento)
        
    def get_start_paths(self):
        try:
            path_dict = self.data_provider.get_csv_path()
            fornitori = path_dict.get("fornitori", [])
            clienti = path_dict.get("clienti", [])
            if clienti and fornitori:
                return [fornitori[0], clienti[0]]
            else:
                return ["", ""]
        except Exception as e:
            print(f"Errore nel controller: {e}")
            return ["", ""]

    def set_start_paths(self, path):
        return self.data_provider.set_csv_path(path)
        
    def get_years_available(self):
        return list(self.data_provider.get_years_available())