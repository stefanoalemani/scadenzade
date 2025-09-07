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
from config.constants import SCAD_LIST_HEAD, CLI_LIST_HEAD, FOR_LIST_HEAD, YearAct

class MainView(urwid.WidgetWrap):
    def __init__(self, data_clients, data_suppliers, data_table_head, app):
        self.app = app
        self.controller = control.widget_control.ControllerW()

        # Registrazione eventi
        self.controller.rec_event("listbox_enter", self.on_listbox_enter)
        self.controller.rec_event("richiesta_filtro_scadenze", self.select_invoice_month_year)
        self.controller.rec_event("anno_aggiornato", self.update_year)
        self.controller.rec_event("text-statusbar", self.show_current_focus)

        # Dati iniziali
        self.year_act = YearAct.YEAR_ACT
        self.data_clients = data_clients
        self.data_suppliers = data_suppliers
        self.data_table_head = data_table_head

        self.data_clients_sel = self._select_clients(data_clients)
        self.data_suppliers_sel = self._select_providers(data_suppliers)

        # Costruzione interfaccia
        self.toolbar = self._build_toolbar(app)
        self.scad_list = self._build_scad_list(app, data_table_head)
        self.clients_list = self._build_cli_list(app)
        self.suppliers_list = self._build_for_list(app)
        self.cli_supp_list = self._build_cli_for_columns()
        self.status_bar = self._build_status_bar()

        self.view = urwid.Pile([
            ('pack', self.toolbar),
            ('weight', 2, self.scad_list),
            ('weight', 2, self.cli_supp_list),
            ('pack', self.status_bar)
        ])
        self.view.focus_position = 0
        
        # emette evento per filtrare subito l'anno
        self.controller.emit_event(control.widget_control.Event(
            tipology="richiesta_filtro_scadenze",
            source=self,
            payload={"month": 1, "year": self.year_act}
        ))
        super().__init__(self.view)

    def _select_clients(self, data):
        self.all_sel_clients_data = data
        return [(r[8], r[1], r[2], r[3]) for r in data]

    def _select_providers(self, data):
        self.all_sel_suppliers_data = data
        return [(r[0], r[1], r[2], r[3]) for r in data]

    def _select_scad_list(self):
        pass

    def _build_toolbar(self, app):
        toolbar = view.widget_class.ToolBar(app, self.controller)
        self.controller.rec_event("selezione_effettuata", toolbar.run_event)
        return toolbar

    def _build_scad_list(self, app, data_table_head):
        box = view.widget_class.MakeListBox("Scadenze", "col", app, self.controller)
        #box.refresh_listbox(SCAD_LIST_HEAD, data_table_head)
        return box

    def _build_cli_list(self, app):
        box = view.widget_class.MakeListBox("Fatture clienti", "row", app, self.controller)
        #box.refresh_listbox(CLI_LIST_HEAD, self.data_clients_sel)
        return urwid.AttrMap(box, 'normal', 'normal')

    def _build_for_list(self, app):
        box = view.widget_class.MakeListBox("Fatture fornitori", "row", app, self.controller)
        #box.refresh_listbox(FOR_LIST_HEAD, self.data_suppliers_sel)
        return urwid.AttrMap(box, 'normal', 'normal')

    def _build_cli_for_columns(self):
        return urwid.Columns([self.suppliers_list, self.clients_list])

    def _build_status_bar(self):
        bar = view.widget_class.MakeStatusBar()
        return urwid.BoxAdapter(bar, height=1)

    def update_listbox(self, listbox_widget, head, content):
        box = getattr(listbox_widget, "original_widget", listbox_widget)
        box.refresh_listbox(head, content)
        box.selectedRow = 0
        box._update_highlighting()
    
    def update_year(self, evento):
        self.year_act = evento.payload.get("anno")        
        self.status_bar.update_status(f"Info: selezionato anno {self.year_act}")
        # Propaga l’anno alle listbox
        self.scad_list.update_year_active(self.year_act)
        self.clients_list.original_widget.update_year_active(self.year_act)
        self.suppliers_list.original_widget.update_year_active(self.year_act)

    def on_listbox_enter(self, event):
        id_listbox = event.source
        data = event.payload
        if id_listbox == "Scadenze":
            select_event = control.widget_control.Event(
                tipology="richiesta_filtro_scadenze",
                source=self,
                payload=data
            )
            self.select_invoice_month_year(select_event)

        elif id_listbox == "Fatture fornitori":
            self.show_suppliers_details(data)

        elif id_listbox == "Fatture clienti":
            self.show_clients_details(data)

    def select_invoice_month_year(self, event):
        payload = event.payload
        month = payload.get("month")
        year = payload.get("year")  # usa l’anno aggiornato
        try:
            month = int(month)
            year = int(year)
        except (TypeError, ValueError):
            return

        # [debug] self.status_bar.update_status(f"Info: da select, {month}{year}")

        def select_mese_anno(data_str):
            try:
                data = datetime.strptime(data_str, "%d-%m-%Y")
                return data.month, data.year
            except ValueError:
                return None, None

        def select_data(date, month, year):
            if month == 1:
                return [row for row in date if select_mese_anno(row[2])[1] == year]
            else:
                return [row for row in date if select_mese_anno(row[2]) == (month - 1, year)]
        
        data_detail_clients = select_data(self.data_clients, month, year)
        data_detail_suppliers = select_data(self.data_suppliers, month, year)

        data_detail_suppliers = self._select_providers(data_detail_suppliers)
        data_detail_clients = self._select_clients(data_detail_clients)

        # Aggiorna scad_list con dati ricalcolati per l’anno selezionato
        self.data_table_head = DataProvider()
        data_head = self.data_table_head._build_table_head()
        self.update_listbox(self.scad_list, SCAD_LIST_HEAD, data_head)

        # Aggiorna le altre listbox
        self.update_listbox(self.clients_list, CLI_LIST_HEAD, data_detail_clients)
        self.update_listbox(self.suppliers_list, FOR_LIST_HEAD, data_detail_suppliers)

    def show_current_focus(self, evento):
        payload = evento.payload or {}
        if payload.get("Info"):
            self.status_bar.update_status(f"Info: {payload['Info']}")
            return
        if payload.get("Warning"):
            self.status_bar.update_status(f"Warning: {payload['Warning']}", "Warning")
            return

        focus_widget = self.view.get_focus()
        if focus_widget == self.scad_list:
            state = "seleziona il mese con ← → e premi invio per filtrare le fatture"
        elif focus_widget == self.cli_supp_list:
            state = "scegli una fattura con ↑ ↓ e premi invio per i dettagli"
        elif focus_widget == self.toolbar:
            state = "imposta anno di riferimento, scegli path, contabilizza, o esci"
        else:
            state = ""

        self.status_bar.update_status(f"Info: {state}")

    def show_clients_details(self, payload):
        selected_item = payload.get("data")
        try:
            self._view_popup(self.all_sel_clients_data[selected_item], "C")
        except IndexError:
            pass

    def show_suppliers_details(self, payload):
        selected_item = payload.get("data")
        try:
            self._view_popup(self.all_sel_suppliers_data[selected_item], "F")
        except IndexError:
            pass

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
                details = format_details("Fornitore", entry[0], entry[4], entry[1], entry[2], entry[3], entry[5], entry[6], entry[7])
            elif widget_id == "C":
                details = format_details("Cliente", entry[8], entry[9], entry[1], entry[2], entry[3], entry[5], entry[6], entry[7])
            else:
                return
        except IndexError:
            return

        popup_det = popup.PopUpDetails(self.app)
        response = urwid.Text(details)
        close_button = urwid.Button("Chiudi", popup_det.close_popup)
        close_button_style = urwid.AttrMap(close_button, 'buttonPopup')
        view = urwid.Filler(urwid.Pile([response, close_button_style]))
        popup_det.show_popup("Dettagli fattura", view)

