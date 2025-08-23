from datetime import datetime

class Event:
    def __init__(self, tipo, sorgente=None, payload=None):
        self.tipo = tipo              # es: "listbox_enter"
        self.sorgente = sorgente      # es: self.title o l'istanza stessa
        self.payload = payload or {}  # dizionario con dati extra

    def __repr__(self):
        return f"<Event tipo={self.tipo} sorgente={self.sorgente}>"

class ControllerW:
    def __init__(self):
        # Dizionario: nome_evento → lista di callback
        self._eventi = {}

    def registra_evento(self, nome_evento, callback):
        """
        Registra una funzione da chiamare quando viene emesso l'evento.
        """
        if nome_evento not in self._eventi:
            self._eventi[nome_evento] = []
        self._eventi[nome_evento].append(callback)

    def emetti_eventoOld(self, nome_evento, payload=None):
        """
        Emette un evento, chiamando tutte le funzioni registrate.
        """
        if nome_evento in self._eventi:
            for callback in self._eventi[nome_evento]:
                callback(payload)

    def emetti_evento(self, evento):
        """
        Emette un evento, chiamando tutte le funzioni registrate.
        """
        listeners = self._eventi.get(evento.tipo, [])
        for listener in listeners:
            listener(evento)