#!/usr/bin/python3
# file name .......... main_view.py
# scope .............. Main module for generating the text-based graphical 
# .................... interface (view)
# language ........... Python 3.11.2
# author ............. Stefano Alemani
# date ............... 14-08-2025
# version ............ 0.6.0

import urwid
import view.widget_class
import view.popup as popup
import control.widget_control
import csv
from models.data_provider import DataProvider
from datetime import datetime
from config.constants import SCAD_LIST_HEAD, CLI_LIST_HEAD, FOR_LIST_HEAD
class MainView(urwid.WidgetWrap):

    """
    Classe per creare interfaccia utente. Unisce e richiama i vari widget nelle
    classi esterne.
    """    
    def __init__(self, dati_clienti, dati_fornitori, dati_table_head, app):
        # istanzia il controller per eventi widget
        self.controller = control.widget_control.ControllerW()
        # registra eventi per tutte le listbox (gli altri widget singoli 
        # vengono registrati nelle funzioni private dedicate)
        self.controller.registra_evento("listbox_enter", self.on_listbox_enter)
        
        self.app = app

        # organizza e inizializza i dati
        self.dati_clienti = dati_clienti
        self.dati_fornitori = dati_fornitori
        self.dati_clienti_sel = self._select_clients(dati_clienti)
        self.dati_fornitori_sel = self._select_providers(dati_fornitori)

        # genera tutti i widget della schermata principale
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

    def _select_clients(self, dati):
        # ritorna dati per comporre la listbox clienti:
        # r[8] - Cessionario, r[1] - ImportoTotaleDocumento,
        # r[2] - DataScadenzaPagamento, r[3] - Numero  

        # dati con tutti i campi e non solo con i campi per la visualizzazione
        self.all_sel_client_data = dati

        return [(r[8], r[1], r[2], r[3]) for r in dati]

    def _select_providers(self, dati):
        # ritorna dati per comporre la listbox clienti:
        # r[1] - Denominazione, r[1] - ImportoTotaleDocumento,
        # r[2] - DataScadenzaPagamento, r[3] - Numero  

        # dati con tutti i campi e non solo con i campi per la visualizzazione
        self.all_sel_provider_data = dati

        return [(r[0], r[1], r[2], r[3]) for r in dati]

    def _build_toolbar(self, app):
        # crea toolbar
        toolbar = view.widget_class.ToolBar(app, self.controller)
        self.controller.registra_evento("selezione_effettuata", toolbar.run_event)
        return toolbar

    def _build_scad_list(self, app, dati_table_head):
        # crea listBox scadenze
        box = view.widget_class.MakeListBox("Scadenze", "col", app, self.controller)
        box.refresh_listbox(SCAD_LIST_HEAD, dati_table_head)
        return box

    def _build_cli_list(self, app):
        # crea listBox fatture clienti
        box = view.widget_class.MakeListBox("Fatture clienti", "row", app, self.controller)        
        box.refresh_listbox(CLI_LIST_HEAD, self.dati_clienti_sel)
        return urwid.AttrMap(box, 'normal', 'normal')

    def _build_for_list(self, app):
        # crea listBox fatture fornitori
        box = view.widget_class.MakeListBox("Fatture fornitori", "row", app, self.controller)
        box.refresh_listbox(FOR_LIST_HEAD, self.dati_fornitori_sel)
        return urwid.AttrMap(box, 'normal', 'normal')

    def _build_cli_for_columns(self):
        # ritorna le due listbox for_list e cli_list affiancate in colonna per
        # usare urwid.Pile
        return urwid.Columns([self.for_list, self.cli_list])

    def _build_status_bar(self):
        # crea la status bar
        bar = view.widget_class.MakeStatusBar()
        self.controller.registra_evento("text-statusbar", self.show_current_focus)
        return urwid.BoxAdapter(bar, height=1)

    def update_cli_list(self, nuovi_dati):
        # Aggiorna i dati filtrati per la listbox clienti
        
        self.dati_clienti_sel = self._select_clients(nuovi_dati)
        
        # Estrai il widget interno da AttrMap
        cli_listbox = self.cli_list.original_widget

        # Aggiorna il contenuto della ListBox
        cli_listbox.refresh_listbox(CLI_LIST_HEAD, self.dati_clienti_sel)

        # Reset della selezione e focus
        cli_listbox.selectedRow = 0
        cli_listbox._update_highlighting()

    def update_for_list(self, nuovi_dati):
        # Aggiorna i dati filtrati per la listbox fornitori
        
        self.dati_fornitori_sel = self._select_providers(nuovi_dati)
       
        # Estrai il widget interno da AttrMap
        for_listbox = self.for_list.original_widget

        # Aggiorna il contenuto della ListBox
        for_listbox.refresh_listbox(FOR_LIST_HEAD, self.dati_fornitori_sel)

        # Reset della selezione e focus
        for_listbox.selectedRow = 0
        for_listbox._update_highlighting()

    def on_listbox_enter(self, evento):
        # funzione richiamata per evento "enter" su un elemento delle listbox
        id_listbox = evento.sorgente
        dati = evento.payload
        if id_listbox == "Scadenze":
            self.select_invoice_for_month(dati) # listbox scad_list
        elif id_listbox == "Fatture fornitori":
            self.show_provider_details(dati) # listbox for_list
        elif id_listbox == "Fatture clienti":
            self.show_client_details(dati) # listbox cli_list
        else:
            print(f"Evento da sorgente sconosciuta: {id_listbox}")

    def show_current_focus(self, evento):
        # funzione per gestire i messaggi nella statusbar che arrivano dal
        # controller
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

    def show_client_details(self, payload):
        # funzione richiamata dal controller (all'invio) della listbox clienti
        # mostra popup dettagli clienti con i dati passati in argomento
        selected_item = payload["dati"]
        try:
            self._view_popup(self.all_sel_client_data[selected_item], "C")
        except IndexError:
            return
    
    def show_provider_details(self, payload):
        # funzione richiamata dal controller (all'invio) della listbox fornitori
        # mostra popup dettagli fornitori con i dati passati in argomento
        selected_item = payload["dati"]
        try:
            self._view_popup(self.all_sel_provider_data[selected_item], "F")
        except IndexError:
            return

    def select_invoice_for_month(self, payload):
        mese = payload.get("mese")
        try:
            mese = int(mese)
        except (TypeError, ValueError):
            return

        def estrai_mese(data_str):
            try:
                return datetime.strptime(data_str, "%d-%m-%Y").month
            except:
                return None
        if mese == 1:
            self.dati_dett_fornitori = self.dati_fornitori
            self.dati_dett_clienti = self.dati_clienti
        else:
            self.dati_dett_fornitori = [
                row for row in self.dati_fornitori
                if estrai_mese(row[2]) is not None and estrai_mese(row[2]) == mese - 1
            ]
            self.dati_dett_clienti = [
                row for row in self.dati_clienti
                if estrai_mese(row[2]) is not None and estrai_mese(row[2]) == mese - 1
            ]

        # Ricostruisci righe visive
        alignment_for = [x[1] for x in FOR_LIST_HEAD]
        alignment_cli = [x[1] for x in CLI_LIST_HEAD]

        dati_dett_fornitori = [(dati_dett_fornitori)
                              for dati_dett_fornitori in self.dati_dett_fornitori]        

        dati_dett_clienti = [(dati_dett_clienti)
                              for dati_dett_clienti in self.dati_dett_clienti]

        self.update_for_list(dati_dett_fornitori)
        self.update_cli_list(dati_dett_clienti)

    def _view_popup(self, entry, widget_id):
        def format_details(label, name, piva, importo, scadenza, numero, data_doc, totale, tipo_doc):
            return f"""
            {label}: {name}
            P.IVA: {piva}

            Importo scadenza: {importo}
            Data Scadenza:    {scadenza}

            Numero Documento: {numero}
            Data documento:   {data_doc}
            Tipo documento:   {tipo_doc}

            Totale documento: {totale}
            """

        try:
            if widget_id == "F":
                details = format_details(
                    "Fornitore", entry[0], entry[4], entry[1], entry[2],
                    entry[3], entry[5], entry[6], entry[7]
                )
            elif widget_id == "C":
                details = format_details(
                    "Cliente", entry[8], entry[9], entry[1], entry[2],
                    entry[3], entry[5], entry[6], entry[7]
                )
            else:
                return False
        except IndexError:
            return False

        popup_det = popup.PopUpDetails(self.app)
        response = urwid.Text(details)
        close_button = urwid.Button("Chiudi", popup_det.close_popup)
        close_button_style = urwid.AttrMap(close_button, 'buttonPopup')
        view = urwid.Filler(urwid.Pile([response, close_button_style]))
        popup_det.show_popup("Dettagli fattura", view)