#!/usr/bin/python3
# file name .......... main_view.py
# scope .............. all widget class for make UI
# language ........... Python 3.11.2
# author ............. Stefano Alemani
# date ............... 14-08-2025
# version ............ 0.6.0

import urwid
import os
import csv
import view.popup
import control.widget_control
from functools import partial
from datetime import datetime
from config.constants import YearAct
# anno di riferimento

class ToolBar(urwid.WidgetWrap):
    """
    classe per generare la toolbar con le funzionalità: Percorso dati, Elabora
    fatture, Esci
    """
    def __init__(self, app, controller):
        # istanza principale "app = MainApp"
        self.app = app
        self.controller = controller
        self.start_path = None
        self.year_act = YearAct.YEAR_ACT
        self.index = 0

        labels = [f"Anno: {self.year_act}", "Percorso dati", "Elabora fatture", "Esci"]
        button_widgets = []

        # genera i 3 Button (con i nomi in labels)
        for i, label in enumerate(labels):
            btn = urwid.Button(label, on_press=self.on_button_press, user_data=label)
            btn._label.align = 'center'
            if i == 0:
                self.year_button = btn  # salva il bottone "Anno"
            wrapped_btn = urwid.AttrMap(btn, 'toolbar_button', focus_map='toolbar_button_focus')
            button_widgets.append(wrapped_btn)
    
        # gestione grafica della "toolbar": Allinea i 3 bottoni in colonna
        self.toolbar = urwid.Columns(button_widgets, focus_column=self.index)
        padded = urwid.Padding(self.toolbar, left=1, right=1)
        super().__init__(padded)

    def on_button_press(self, button, user_data):
        # Trova il bottone cliccato nella lista
        for i, item in enumerate(self.toolbar.contents):
            if item[0].original_widget == button:
                # Cambia temporaneamente l'attributo
                self.toolbar.contents[i] = (
                    urwid.AttrMap(button, 'toolbar_button_flash'),
                    self.toolbar.options()
                )

                # Dopo 0.5 secondi, ripristina lo stile normale
                def reset_flash(loop, user_data):
                    self.toolbar.contents[i] = (
                        urwid.AttrMap(button, 'toolbar_button', focus_map='toolbar_button_focus'),
                        self.toolbar.options()
                    )
                    self.app.loop.draw_screen()

                self.app.loop.set_alarm_in(0.5, reset_flash)
                break
                # Emetti l'event come prima
        #self.controller.emit_event("selezione_effettuata", {"action": user_data})
        event = control.widget_control.Event(
            tipology="selezione_effettuata",
            source=self,
            payload={"action": user_data}
        )
        self.controller.emit_event(event)

    # richiama le funzioni indicate quando si avvia event 
    # (è la funzione di chiamata registrata in _build_toolbar di MainView)
    def run_event(self, event):
        action = event.payload.get("action", "")
        if action[:4] == "Anno":
            self.handle_select_years()
        elif action == "Percorso dati":
            self.handle_data_path()
        elif action == "Elabora fatture":
            self.handle_elaborate_invoice()
        elif action == "Esci":
            self.handle_exit()

    def handle_select_years(self):
        years_available = self.controller.get_years_available()
        selyear = SelectYears(years=years_available, year_act=self.year_act, on_close=self.on_year_selected_update)
        self.popup = view.popup.PopUpDetails(self.app)
        self.popup.show_popup(head="Seleziona anno di riferimento", layout=selyear)        

    def handle_data_path(self):
        self.start_path = self.controller.get_start_paths()
        pop = view.popup.PopUpDetails(self.app)
        def on_path_selected(new_path):
            def close_popup(loop, user_data):
                pop.close_popup()
            # Salva il nuovo percorso nel file
            success = self.controller.set_start_paths({
                "suppliers": [new_path[0]],
                "clients": [new_path[1]]
            })
            if success:
                if not new_path or len(new_path) < 2:
                    return
                self.start_path = new_path
                event = control.widget_control.Event("text-statusbar", self, {
                    "Info": "Percorso salvato correttamente"
                })
            else:
                event = control.widget_control.Event("text-statusbar", self, {
                    "Warning": "Errore nel salvataggio del percorso"
                })
    
            self.controller.emit_event(event)
            self.app.loop.set_alarm_in(1.0, close_popup)
    
        selector = DirectorySelector(start_path=self.start_path, on_close=on_path_selected)
        pop.show_popup(head="Percorso", layout=selector)

    def on_year_selected_update(self, year):
        if year:
            self.year_button.set_label(f"Anno: {year}")
            self.year_act = year
            # Prima aggiorna l’anno, poi filtra
            self.controller.update_year_and_select(year)
        else:
            print("Selezione annullata.")
        self.popup.close_popup()
        
    def close(self, value):
        print("Chiusura con:", value)

    def handle_elaborate_invoice(self):
        start_path = self.controller.get_start_paths()
        if not start_path:
            event = control.widget_control.Event("text-statusbar", self, {
                "Warning": "Percorso dati non trovato o incompleto. Seleziona prima 'Percorso dati'"
            })
            self.controller.emit_event(event)
            return

        pop = view.popup.PopUpDetails(self.app)

        def on_compute_complete(confirmed, result):
            def close_popup(loop, user_data):
                pop.close_popup()

            tipology = "Info" if result else "Warning"
            message = (
                "Elaborazione annullata dall'utente" if not confirmed else
                "Elaborazione terminata con successo" if result else
                "Elaborazione non riuscita"
            )
            event = control.widget_control.Event("text-statusbar", self, {tipology: message})
            self.controller.emit_event(event)
            self.app.loop.set_alarm_in(1.0, close_popup)

        contab = MakeInvoiceCsv(start_path=start_path, on_close=on_compute_complete)
        pop.show_popup(head="Contabilizzazione", layout=contab)

    def handle_exit(self):
        # Mostra message nella status bar
        event = control.widget_control.Event("text-statusbar", self, {"Info": "Uscita in corso..."})
        self.controller.emit_event(event)

        def exit_after_flash(loop, user_data):
            # funzione per uscire dal loop dopo x secondi invocati da self.app.loop.set_alarm_in...
            raise urwid.ExitMainLoop()
        # Dopo 0.5 secondi, chiude l'app
        self.app.loop.set_alarm_in(0.5, exit_after_flash)

    def render(self, size, focus=False):
        # Override di render per gestire il focus;
        # Evita di emettere l’event "text-statusbar" troppe volte al focus
        if focus and not getattr(self, "_focus_emesso", False):
            #self.controller.emit_event("text-statusbar", {"widget": self})
            event = control.widget_control.Event(
                tipology="text-statusbar",
                source=self,
                payload={"widget": self}
            )
            self.controller.emit_event(event)
            self._focus_emesso = True
        elif not focus:
            self._focus_emesso = False
            
        return super().render(size, focus)

    def selectable(self):
        # Metodo per rendere selezionabile l'oggetto Toolbar, di default non lo è
        return True
        
class SelectYears(urwid.WidgetWrap):
    def __init__(self, years, year_act, on_close=None):
        self.on_close = on_close
        self.selected_year = None  # Qui memorizziamo l'anno selezionato
        # Gruppo di RadioButton per selezione singola
        self.year_act = year_act # inizializza la variabile year_act in modo che 
                                 # se non viene modificata rimane quella iniziale
        self.year_buttons = []
        radio_group = []

        for year in years:
            is_selected = (str(year) == str(self.year_act))
            btn = urwid.RadioButton(radio_group, str(year), state=is_selected, on_state_change=self.on_year_selected)
            self.year_buttons.append(btn)
            if is_selected:
                self.selected_year = str(year)  # ← imposta subito il value iniziale            

        list_box = urwid.ListBox(urwid.SimpleFocusListWalker(self.year_buttons))
        list_box = urwid.BoxAdapter(list_box, height=5)  # Altezza fissa

        list_linebox = urwid.LineBox(list_box, title="Elenco anni")

        ok_btn = urwid.Button("Conferma selezione")
        ok_btn._label.align = 'center'

        cancel_btn = urwid.Button("Annullare")
        cancel_btn._label.align = 'center'

        urwid.connect_signal(ok_btn, 'click', self.confirm)
        urwid.connect_signal(cancel_btn, 'click', self.cancel)

        styled_ok_btn = urwid.AttrMap(ok_btn, 'ok_button', focus_map='ok_button_focus')
        styled_cancel_btn = urwid.AttrMap(cancel_btn, 'cancel_button', focus_map='cancel_button_focus')
        centered_ok_btn = urwid.Padding(styled_ok_btn, align='center', width=('relative', 50))
        centered_cancel_btn = urwid.Padding(styled_cancel_btn, align='center', width=('relative', 50))

        self.view = urwid.Filler(urwid.Pile([
            ('pack', list_linebox),
            urwid.Divider(),
            ('pack', centered_ok_btn),
            ('pack', centered_cancel_btn)
        ]))

        super().__init__(self.view)

    def on_year_selected(self, radio_button, new_state):
        if new_state:
            self.selected_year = radio_button.get_label()

    def confirm(self, button):
        if not self.selected_year:
            self.selected_year = str(self.year_act)
        if self.on_close:
            set_year = control.widget_control.ControllerW()
            set_year.set_years_act(self.selected_year)
            self.on_close(self.selected_year)
                    
    def cancel(self, button):
        if self.on_close:
            self.on_close(self.year_act)

class MakeListBox(urwid.WidgetWrap):
    def __init__(self, title, selection_mode, app, controller):
        self.title = title
        self.selection_mode = selection_mode
        self.app = app
        self.controller = controller
        self.year_act = YearAct.YEAR_ACT
        self.selected_row = 0
        self.selected_col = 0
        self.widget_list = []

        self.listbox = urwid.ListBox(urwid.SimpleFocusListWalker(self.widget_list))
        self.list_linebox = urwid.LineBox(self.listbox, title=title)
        super().__init__(self.list_linebox)

    def _log_focus_state(self, context=""):
        try:
            _, index = self.listbox.get_focus()
        except Exception as e:
            print(f"[{context}] Errore nel focus: {e}")

    def _safe_set_focus(self, index):
        try:
            self.listbox.set_focus(index)
            self._log_focus_state(f"set_focus({index}) OK")
        except IndexError:
            try:
                self.listbox.set_focus(0)
                self._log_focus_state("fallback a 0")
            except Exception as e:
                print(f"[fallback] Errore: {e}")
   
    def refresh_listbox(self, head=[], content=[]):
        head_widgets = [urwid.Text(label, align=align) for label, align in head]
        self.header_widget = urwid.AttrMap(urwid.Columns(head_widgets), 'header')

        alignments = [a[1] for a in head]
        self.content_widgets = [
            RowColumns(row, alignments, parent=self, row_index=i)
            for i, row in enumerate(content)
        ]

        self.widget_list = [self.header_widget] + self.content_widgets
        self.listbox.body.clear()
        self.listbox.body.extend(self.widget_list)

        self.selected_row = 0
        #self.selected_col = 0

        if self.selection_mode == "row":
            self._safe_set_focus(self.selected_row + 1 if self.content_widgets else 0)
        elif self.selection_mode == "col":
            self._safe_set_focus(0)

        self._update_highlighting()

    def update_year_active(self, new_year):
        self.year_act = new_year

    def _update_highlighting(self):
        for i, row in enumerate(self.content_widgets):
            for j, cell in enumerate(row.cells):
                if self.selection_mode == "row" and i == self.selected_row:
                    cell.set_attr_map({None: 'selected'})
                elif self.selection_mode == "col" and j == self.selected_col:
                    cell.set_attr_map({None: 'selected'})
                else:
                    cell.set_attr_map({None: 'normal'})

    def _select_row_by_mouse(self, index):
        self.selected_row = index
        self._safe_set_focus(index + 1)  # +1 per intestazione
        self._update_highlighting()

    def keypress(self, size, key):
        match key:
            case 'left' | 'right':
                self._manage_move_column(key)
            case 'up' | 'down':
                self._manage_move_row(key)
            case 'enter':
                self._manage_enter()
            case _:
                return super().keypress(size, key)

    def _manage_move_column(self, key):
        step = 1 if key == 'right' else -1
        if self.content_widgets:
            num_columns = len(self.content_widgets[0].cells)
            self.selected_col = (self.selected_col + step) % num_columns
            self._update_highlighting()

        if self.selection_mode == "row":
            self.app.main.cli_supp_list.focus_position = 1 if key == 'right' else 0

    def _manage_move_row(self, key):
        self._w.base_widget.set_focus(0)
        if self.selection_mode == "row":
            if key == 'up':
                if self.selected_row == 0:
                    self.app.main.view.focus_position = 1
                self.selected_row = max(0, self.selected_row - 1)
            elif key == 'down':
                max_row = len(self.content_widgets) - 1
                self.selected_row = min(max_row, self.selected_row + 1)
            self._safe_set_focus(self.selected_row + 1)
            self._update_highlighting()
        elif self.selection_mode == "col":
            self.app.main.view.focus_position = 0 if key == 'up' else 2

    def _manage_enter(self):
        if self._focus_on_deadlines():
            self._filter_deadlines()
        else:
            self._show_popup_details()

    def _focus_on_deadlines(self):
        return self.app.main.view.focus_position == 1

    def _filter_deadlines(self):
        month = self.selected_col + 1
        event = control.widget_control.Event(
            tipology="listbox_enter",
            source=self.title,
            payload={"month": month, "year": self.year_act}
        )
        self.controller.emit_event(event)

    def _show_popup_details(self):
        focus_pos = self.app.main.cli_supp_list.focus_position
        row = self.selected_row
        event = control.widget_control.Event(
            tipology="listbox_enter",
            source=self.title,
            payload={"detail": focus_pos, "data": row}
        )
        self.controller.emit_event(event)

    def render(self, size, focus=False):
        self._log_focus_state("render")
        if focus:
            try:
                self.listbox.get_focus()
            except IndexError:
                self._safe_set_focus(0)

            event = control.widget_control.Event(
                tipology="text-statusbar",
                source=self,
                payload={"Messaggi": self}
            )
            self.controller.emit_event(event)

            new_listbox = urwid.AttrMap(
                urwid.LineBox(self.listbox, title=self.title, title_attr='activeListBox'),
                'activeLineBox'
            )
        else:
            new_listbox = urwid.AttrMap(
                urwid.LineBox(self.listbox, title=self.title, title_attr='normalListBox'),
                'normal'
            )

        self._w = new_listbox
        return super().render(size, focus)

class Cell(urwid.Text):
    """classe Cell per visualizzare le singole celle della ListBox "ScadList" 
       in modo da rendere possibile la selezione per colonne
    """
    def __init__(self, text, align="right"):
        super().__init__(str(text), align)
                
class RowColumns(urwid.WidgetWrap):
    """Riga composta da celle, selezionabile con il mouse."""
    def __init__(self, values, alignments, parent=None, row_index=0):
        self.parent = parent
        self.row_index = row_index
        self.cells = self._create_cells(values, alignments)

        row_widget = urwid.Columns(self.cells)
        super().__init__(row_widget)

    def _create_cells(self, values, alignments):
        """Crea le celle con stile normal/selected."""
        cells = []
        for value, align in zip(values, alignments):
            cell = Cell(value, align=align)
            styled_cell = urwid.AttrMap(cell, 'normal', 'selected')
            cells.append(styled_cell)
        return cells

    def selectable(self):
        return True

    def mouse_event(self, size, event, button, x, y, focus):
        if event == 'mouse press' and self.parent:
            self.parent._select_row_by_mouse(self.row_index)
            return True
        return False
        
class MakeInvoiceCsv(urwid.WidgetWrap):
    def __init__(self, start_path=".", on_close=None):
        self.on_close = on_close
        self.start_path = start_path
        text_info = urwid.LineBox(urwid.Text("Contabilizzare fatture XML presenti nei percorsi:", align='center'))
        text_info_path_F = urwid.Text(f"Fornitori: {self.start_path[0]}", align='center')
        text_info_path_C = urwid.Text(f"Clienti: {self.start_path[1]}", align='center')
        
        ok_btn = urwid.Button("Conferma contabilizzazione")
        ok_btn._label.align = 'center'

        cancel_btn = urwid.Button("Annullare")
        cancel_btn._label.align = 'center'

        urwid.connect_signal(ok_btn, 'click', self.confirm)
        urwid.connect_signal(cancel_btn, 'click', self.cancel)
        styled_ok_btn = urwid.AttrMap(ok_btn, 'ok_button', focus_map='ok_button_focus')
        styled_cancel_btn = urwid.AttrMap(cancel_btn, 'cancel_button', focus_map='cancel_button_focus')
        centered_ok_btn = urwid.Padding(styled_ok_btn, align='center', width=('relative', 50))
        centered_cancel_btn = urwid.Padding(styled_cancel_btn, align='center', width=('relative', 50))
        
        self.account_invoices = control.widget_control.AccountInvoices()
        
        self.view = urwid.Filler(urwid.Pile([
            ('weight', 1, text_info),
            (urwid.Divider()),
            (text_info_path_F),
            (urwid.Divider()),
            (text_info_path_C),
            (urwid.Divider()),
            ('pack', centered_ok_btn),
            ('pack', centered_cancel_btn)
        ]))
        
        super().__init__(self.view)
        
    def confirm(self, button):
        if self.on_close:
            result = self.make_csv()
            self.on_close(True, result)  # True = utente ha confirmed

    def cancel(self, button):
        if self.on_close:
            self.on_close(False, None)  # False = utente ha annullato

    def make_csv(self):
        try:
            self.account_invoices.make_csv(self.start_path)
            return True
        except:
            return False

class DirectorySelector(urwid.WidgetWrap):
    def __init__(self, start_path=".", on_close=None):
        try:
            self.pathL = os.path.abspath(start_path[0])
            self.pathR = os.path.abspath(start_path[1])
        except IndexError:
            self.pathL = self.pathR = os.getcwd()

        self.on_close = on_close

        self.header = urwid.AttrMap(urwid.Text("Seleziona una directory"), 'header_text', focus_map='header_text')
        self.listboxL = urwid.ListBox(self.get_items(self.pathL, 'L'))
        self.listboxR = urwid.ListBox(self.get_items(self.pathR, 'R'))
        self.viewCol = urwid.Columns([self.listboxL, self.listboxR])

        # Bottone unico di conferma
        confirm_btn = urwid.Button("Conferma entrambi i percorsi")
        confirm_btn._label.align = 'center'
        urwid.connect_signal(confirm_btn, 'click', self.confirm_both)
        styled_btn = urwid.AttrMap(confirm_btn, 'ok_button', focus_map='ok_button_focus')
        centered_btn = urwid.Padding(styled_btn, align='center', width=('relative', 50))

        self.view = urwid.Pile([
            ('weight', 2, self.viewCol),
            ('pack', centered_btn)
        ])
        
        super().__init__(self.view)

    def get_items(self, path, side):
        try:
            items = sorted([d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))])
        except FileNotFoundError:
            path = os.getcwd()
            items = sorted([d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))])
        except PermissionError:
            items = []

        widgets = []

        if os.path.dirname(path) != path:
            up_button = urwid.Button(".. (su)")
            urwid.connect_signal(up_button, 'click', partial(self.go_up, side))
            #urwid.connect_signal(up_button, 'click', lambda btn: self.go_up(side, btn))
            widgets.append(urwid.AttrMap(up_button, None, focus_map='reversed'))

        for item in items:
            full_path = os.path.join(path, item)
            button = urwid.Button(item)
            urwid.connect_signal(button, 'click', partial(self.enter_dir, side, full_path))
            #urwid.connect_signal(button, 'click', lambda btn: self.enter_dir(side, full_path, btn))
            widgets.append(urwid.AttrMap(button, 'ok_button', focus_map='reversed'))

#        if side == "L": side="fatture xml FORNITORI"
#        if side == "R": side="fatture xml CLIENTI"

#        textPath = urwid.AttrMap(urwid.Text(f"percorso per {side} selezionato: {path}"), 'info_text', focus_map='info_text')
#        textPath = urwid.LineBox(textPath)

        if side == "L":
            side_label = "fatture xml FORNITORI"
            style = 'side_text'
        elif side == "R":
            side_label = "fatture xml CLIENTI"
            style = 'side_text'

        # Costruisci il testo con markup
        text_markup = [
            ('info_text', "percorso per "),
            (style, side_label),
            ('info_text', " selezionato: "),
            ('path_style', path)
        ]

        text_widget = urwid.Text(text_markup)
        textPath = urwid.AttrMap(text_widget, 'info_text')
        textPath = urwid.LineBox(textPath)

        widgets.extend([urwid.Divider(), textPath, urwid.Divider()])
        return urwid.SimpleFocusListWalker(widgets)

    def confirm_both(self, button):
        if self.on_close:
            self.on_close([self.pathL, self.pathR])
                        
    def refresh(self, target):
        if target == 'L':
            self.listboxL.body = self.get_items(self.pathL, 'L')
        elif target == 'R':
            self.listboxR.body = self.get_items(self.pathR, 'R')

    def go_up(self, side, button):
        if side == 'L':
            self.pathL = os.path.dirname(self.pathL)
            self.refresh('L')
        elif side == 'R':
            self.pathR = os.path.dirname(self.pathR)
            self.refresh('R')

    def enter_dir(self, side, path, button):
        if side == 'L':
            self.pathL = path
            self.refresh('L')
        elif side == 'R':
            self.pathR = path
            self.refresh('R')

class MakeStatusBar(urwid.WidgetWrap):
    """
    Barra di stato a riga singola, con testo dinamico
    """
    def __init__(self):
        self.text = urwid.Text("", align='left')  # o 'center' o 'right' se preferisci

        # Applica uno stile
        styled_text = urwid.AttrMap(self.text, "status_text_black")

        # Layout semplice: una riga
        filler = urwid.Filler(styled_text, valign='top')

        super().__init__(filler)

    def update_status(self, message="", level="Info"):
        color_map = {
            "Info": "status_text_black",
            "Warning": "status_text_red",
            "error": "status_text_blue"
        }
        style = color_map.get(level)
        self._w = urwid.Filler(urwid.AttrMap(self.text, style))
        self.text.set_text(message)