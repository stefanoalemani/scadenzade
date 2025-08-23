#!/usr/bin/python3
# nome programma ..... main_view
# nome file .......... main_view.py
# scopo .............. interfaccia grafica testuale (view) per scadenz.py
# linguaggio ......... Python 3.11.2
# librerie ........... urwid 2.1.2-4 basata su curses per Python 3
# autore ............. Stefano Alemani - Creato in collaborazione con Copilot
# data ............... 22-07-2025
# versione ........... 0.9.0

import urwid
import view.widget_class
import view.popup as popup
import control.widget_control
import csv
from models.data_provider import DataProvider
from datetime import datetime

class MainView(urwid.WidgetWrap):

    """
    Classe per creare interfaccia utente. Unisce e richiama i vari widget nelle
    classi esterne.
    """
    SCAD_LIST_HEAD = [("Calcolo", 'left'), ("Gennaio", 'right'), ("Febbraio", 'right'),
                      ("Marzo", 'right'), ("Aprile", 'right'), ("Maggio", 'right'),
                      ("Giugno", 'right'), ("Luglio", 'right'), ("Agosto", 'right'),
                      ("Settembre", 'right'), ("Ottobre", 'right'), ("Novembre", 'right'),
                      ("Dicembre", 'right')]

    CLI_LIST_HEAD = [("Cliente", 'left'), ("Importo scadenza", 'right'),
                     ("Data scadenza", 'center'), ("Numero documento", 'left')]

    FOR_LIST_HEAD = [("Fornitore", 'left'), ("Importo scadenza", 'right'),
                     ("Data scadenza", 'center'), ("Numero documento", 'left')]

    def __init__(self, dati_clienti, dati_fornitori, dati_table_head, app):
        # istanzia il controller per eventi widget
        self.controller = control.widget_control.ControllerW()
        # registra eventi per tutte le listbox (gli altri widget singoli 
        # vengono registrati nelle funzioni private dedicate)
        self.controller.registra_evento("listbox_enter", self.on_listbox_enter)
        
        self.app = app
        
        self.dati_clienti = dati_clienti
        self.dati_fornitori = dati_fornitori
        self.dati_clienti_sel = self._filtra_clienti(dati_clienti)
        self.dati_fornitori_sel = self._filtra_fornitori(dati_fornitori)

        self.toolbar = self._build_toolbar(app)
        self.scad_list = self._build_scad_list(app, dati_table_head)
        self.cli_list = self._build_cli_list(app)
        self.for_list = self._build_for_list(app)
        self.cli_for_list = self._build_cli_for_columns()
        self.status_bar = self._build_status_bar()

        self.view = urwid.Pile([
            ('pack', self.toolbar),
            ('weight', 2, self.scad_list),
            ('weight', 2, self.cli_for_list),
            ('pack', self.status_bar)
        ])

        self.view.focus_position = 0
        super().__init__(self.view)

    def _filtra_clienti(self, dati):
        # ritorna dati per comporre la listbox clienti:
        # r[8] - Cessionario, r[1] - ImportoTotaleDocumento,
        # r[2] - DataScadenzaPagamento, r[3] - Numero  

        # dati con tutti i campi e non solo con i campi per la visualizzazione
        self.dati_clienti_sel_intero = dati
        return [(r[8], r[1], r[2], r[3]) for r in dati]

    def _filtra_fornitori(self, dati):
        # ritorna dati per comporre la listbox clienti:
        # r[1] - Denominazione, r[1] - ImportoTotaleDocumento,
        # r[2] - DataScadenzaPagamento, r[3] - Numero  
        self.dati_fornitori_sel_intero = dati
        return [(r[0], r[1], r[2], r[3]) for r in dati]

    def _build_toolbar(self, app):
        # toolbar
        toolbar = view.widget_class.ToolBar(app, self.controller)
        self.controller.registra_evento("selezione_effettuata", toolbar.run_event)
        return toolbar

    def _build_scad_list(self, app, dati_table_head):
        # listBox scadenze
        box = view.widget_class.MakeListBox("Scadenze", "col", app, self.controller)
        box.refresh_listbox(self.SCAD_LIST_HEAD, dati_table_head)
        return box

    def _build_cli_list(self, app):
        # listBox fatture clienti
        box = view.widget_class.MakeListBox("Fatture clienti", "row", app, self.controller)        
        #box.head_content(self.CLI_LIST_HEAD, self.dati_clienti_sel)
        box.refresh_listbox(self.CLI_LIST_HEAD, self.dati_clienti_sel)
        return urwid.AttrMap(box, 'normal', 'normal')

    def _build_for_list(self, app):
        # listBox fatture fornitori
        box = view.widget_class.MakeListBox("Fatture fornitori", "row", app, self.controller)
        box.refresh_listbox(self.FOR_LIST_HEAD, self.dati_fornitori_sel)
        return urwid.AttrMap(box, 'normal', 'normal')

    def _build_cli_for_columns(self):
        # ritorna le due listbox for_list e cli_list affiancate in colonna per
        # usare urwid.Pile
        return urwid.Columns([self.for_list, self.cli_list])

    def _build_status_bar(self):
        # status bar
        bar = view.widget_class.MakeStatusBar()
        self.controller.registra_evento("text-statusbar", self.mostra_focus_corrente)
        return urwid.BoxAdapter(bar, height=1)

    def aggiorna_cli_list(self, nuovi_dati):
        # Aggiorna i dati filtrati
        
        self.dati_clienti_sel = self._filtra_clienti(nuovi_dati)
        
        # Estrai il widget interno da AttrMap
        cli_listbox = self.cli_list.original_widget

        # Aggiorna il contenuto della ListBox
        cli_listbox.refresh_listbox(self.CLI_LIST_HEAD, self.dati_clienti_sel)

        # Reset della selezione e focus
        cli_listbox.selectedRow = 0
        cli_listbox._aggiorna_evidenziazione()

    def aggiorna_for_list(self, nuovi_dati):
        # Aggiorna i dati filtrati
        
        self.dati_fornitori_sel = self._filtra_fornitori(nuovi_dati)
       
        # Estrai il widget interno da AttrMap
        for_listbox = self.for_list.original_widget

        # Aggiorna il contenuto della ListBox
        for_listbox.refresh_listbox(self.FOR_LIST_HEAD, self.dati_fornitori_sel)

        # Reset della selezione e focus
        for_listbox.selectedRow = 0
        for_listbox._aggiorna_evidenziazione()

    def on_listbox_enter(self, evento):
        # funzione richiamata per evento "enter" su un elemento delle listbox
        id_listbox = evento.sorgente
        dati = evento.payload
        if id_listbox == "Scadenze":
            self.filtra_fatture_per_mese(dati)
        elif id_listbox == "Fatture clienti":
            self.mostra_dettagli_clienti(dati)
        elif id_listbox == "Fatture fornitori":
            self.mostra_dettagli_fornitori(dati)
        else:
            print(f"Evento da sorgente sconosciuta: {id_listbox}")

    def mostra_focus_corrente(self, evento):
        payload = getattr(evento, "payload", {})
        if payload.get("Info"):
            messaggio = payload.get("Info", "")
            self.status_bar.update_status(f"Info: {messaggio}")
            return
        if payload.get("Warning"):
            messaggio = payload.get("Warning", "Info")
            self.status_bar.update_status(f"Warning: {messaggio}", "Warning")
            return

        focus_widget = self.view.get_focus()

        if focus_widget == self.scad_list:
            stato = "seleziona il mese con i tasti \u2190 \u2192 e premi invio per filtrare le fatture. Scendi con \u2191 \u2193"
        elif focus_widget == self.cli_for_list:
            stato = ("scegli una fattura con i tasti \u2191 \u2193 e premi "
                     "invio per i dettagli della fatture selezionata")
        elif focus_widget == self.toolbar:
            stato = "imposta anno di riferimento, scegli path, contabilizza, o esci"
        else:
            stato = ""

        self.status_bar.update_status(f"Info: {stato}")        

    def mostra_dettagli_clienti(self, payload):
        selected_item = payload["dati"]
        try:
            self._view_popup(self.dati_clienti_sel_intero[selected_item], "C")
        except IndexError:
            return
    
    def mostra_dettagli_fornitori(self, payload):
        selected_item = payload["dati"]
        try:
            self._view_popup(self.dati_fornitori_sel_intero[selected_item], "F")
        except IndexError:
            return

    def filtra_fatture_per_mese(self, payload):
        mese = payload.get("mese")
        try:
            mese = int(mese)
        except (TypeError, ValueError):
            return

        def estrai_mese(data_str):
            try:
                return datetime.strptime(data_str, "%Y-%m-%d").month
            except:
                return None
        if mese == 1:
            self.dati_dett_clienti = self.dati_clienti
            self.dati_dett_fornitori = self.dati_fornitori
        else:
            self.dati_dett_clienti = [
                row for row in self.dati_clienti
                if estrai_mese(row[2]) is not None and estrai_mese(row[2]) == mese - 1
            ]
            self.dati_dett_fornitori = [
                row for row in self.dati_fornitori
                if estrai_mese(row[2]) is not None and estrai_mese(row[2]) == mese - 1
            ]

        # Ricostruisci righe visive
        alignment_cli = [x[1] for x in self.CLI_LIST_HEAD]
        alignment_for = [x[1] for x in self.FOR_LIST_HEAD]

        dati_dett_clienti = [(dati_dett_clienti)
                              for dati_dett_clienti in self.dati_dett_clienti]

        dati_dett_fornitori = [(dati_dett_fornitori)
                              for dati_dett_fornitori in self.dati_dett_fornitori]        

        self.aggiorna_cli_list(dati_dett_clienti)
        self.aggiorna_for_list(dati_dett_fornitori)

    def _view_popup(self, entry, widget_id):
        if widget_id == "F":
            details = f"""
                    Fornitore: {entry[0]} 
                    P.IVA:     {entry[4]} 

                    Importo scadenza: {entry[1]} 
                    Data Scadenza: {entry[2]} 

                    Numero Documento: {entry[3]}
                    Data documento: {entry[5]}
                    Tipo documento: {entry[7]}

                    Totale documento: {entry[6]} 
                    """
        elif widget_id == "C":
            details = f"""
                    Cliente: {entry[8]} 
                    P.IVA:     {entry[9]} 
        
                    Importo scadenza: {entry[1]} 
                    Data Scadenza: {entry[2]} 
        
                    Numero Documento: {entry[3]}
                    Data documento: {entry[5]}
                    Tipo documento: {entry[7]}

                    Totale documento: {entry[6]} 
                    """ 
        else:
            return False

        popup_det = popup.PopUpDetails (self.app)
        response = urwid.Text(details)
        close_button = urwid.Button("Chiudi", popup_det.close_popup)
        close_button_style = urwid.AttrMap(close_button, 'buttonPopup')
        view = urwid.Filler(urwid.Pile([response, close_button_style]))
        popup_det.show_popup("Dettagli fattura", view)