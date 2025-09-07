#!/usr/bin/python3
# nome programma ..... scadenzade
# nome file .......... scadenzade.py
# scopo .............. main file for initialize software
# linguaggio ......... Python 3.11.2
# librerie ........... urwid 2.1.2-4 based on curses per Python 3
# autore ............. Stefano Alemani - Made in partnership with Copilot
# data ............... 22-07-2025
# versione ........... 0.9.0

import urwid
import view.main_view as view_ui
from config.constants import PALETTE
import models.data_provider as data_provider

class MainApp:
    """
    Classe per avviare e terminare il loop dell'applicazione. Richiama la costruzione 
    dell'interfaccia tramite MainView passando i dati e la sua istanza.
    """
    def __init__(self, data_clients, data_suppliers, dati_table_head, run=True):
        # richiama "view" per creare user interface
        self.main = view_ui.MainView(data_clients, data_suppliers, dati_table_head, self)
        self.loop = urwid.MainLoop(self.main, PALETTE, unhandled_input=self.exit_on_q)
        if run:
            self.run() # auto avvia l'applicazione

    def run(self):
        self.loop.run()

    def exit_on_q(self, key):
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()

def main():
    data_class = data_provider.DataProvider()
    dati = data_class.start_data()
    if dati:
        MainApp(dati["data_clients"], dati["data_suppliers"], dati["dati_table_head"])        
    else:
        print("Errore nell'inizializzazione dei dati.")

if __name__ == '__main__':
    main()

#def get_data():
#    out_data = data_provider.DataProvider()
#    out_data.set_year_active(2025)
#    out_data.set_years_available([2024, 2025, 2026])
    
#if __name__ == "__main__" :
#    get_data()
