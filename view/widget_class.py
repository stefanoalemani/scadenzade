import urwid
import os
import csv
import view.popup
import control.widget_control
from models.scadenz import ScadDati
from functools import partial
from datetime import datetime

# anno di riferimento
YEAR_ACT = datetime.strptime(str(datetime.now().date()), "%Y-%m-%d").year

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
        self.index = 0

        labels = [f"Anno: {YEAR_ACT}", "Percorso dati", "Elabora fatture", "Esci"]
        button_widgets = []

        # genera i 3 Button (con i nomi in labels)
        for i, label in enumerate(labels):
            btn = urwid.Button(label, on_press=self.on_button_press, user_data=label)
            btn._label.align = 'center'
            if i == 0:
                self.anno_button = btn  # salva il bottone "Anno"
            wrapped_btn = urwid.AttrMap(btn, 'toolbar_button', focus_map='toolbar_button_focus')
            button_widgets.append(wrapped_btn)
    
        # gestione grafica della "toolbar": Allinea i 3 bottoni in colonna
        self.toolbar = urwid.Columns(button_widgets, focus_column=self.index)
        padded = urwid.Padding(self.toolbar, left=1, right=1)
        super().__init__(padded)
    # alla pressione di un pulsante... versione semplice
    # def on_button_press(self, button, user_data):
    #    self.controller.emetti_evento("selezione_effettuata", {"azione": user_data})
    # versione con il flash!
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
                # Emetti l'evento come prima
        #self.controller.emetti_evento("selezione_effettuata", {"azione": user_data})
        evento = control.widget_control.Event(
            tipo="selezione_effettuata",
            sorgente=self,
            payload={"azione": user_data}
        )
        self.controller.emetti_evento(evento)

    # al keypress (invocato da on_button_press che richiama il controller eventi)
    # verifica il tasto premuto ed emette in caso di enter il 
    # segnale per far generare un "click" sul bottone in focus. Negli altri casi 
    # si sposta a destra o sinistra con i tasti freccia.

    #def keypress(self, size, key):
    #    if key == 'enter':
    #        # button = self.toolbar.contents[self.toolbar.focus_col][0]
    #        # urwid.emit_signal(button, 'click', button)
    #        button = self.toolbar.contents[self.toolbar.focus_col][0].original_widget
    #        self.on_button_press(button, button.get_label())
    # soluzione ibrida per mantere click mouse attivo:
    def keypress(self, size, key):
        if key == 'enter':
            button = self.toolbar.contents[self.toolbar.focus_col][0]
            urwid.emit_signal(button.original_widget, 'click', button.original_widget)
        elif key == 'left':
            self.index = max(0, self.index - 1)
            self.toolbar.focus_column = self.index
        elif key == 'right':
            self.index = min(len(self.toolbar.contents) - 1, self.index + 1)
            self.toolbar.focus_column = self.index
        else:
            return key
        return super().keypress(size, key)

    # richiama le funzioni indicate quando si avvia evento
    def run_event(self, evento):
        azione = evento.payload.get("azione", "")
        if azione[:4] == "Anno":
            self.handle_select_years()
        elif azione == "Percorso dati":
            self.handle_percorso_dati()
        elif azione == "Elabora fatture":
            self.handle_elabora_fatture()
        elif azione == "Esci":
            self.handle_esci()

    def handle_percorso_dati(self):
        try:
            with open("path", "r", newline="", encoding="utf-8") as f:
                self.start_path = []
                reader = csv.DictReader(f, delimiter=";")
                for riga in reader:
                    self.start_path.append(riga["clienti"])
                    self.start_path.append(riga["fornitori"])
        except FileNotFoundError:
            with open("path", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["clienti", "fornitori"], delimiter=";")
                writer.writeheader()
            self.handle_percorso_dati()  # richiama se stesso dopo aver creato il file
        except Exception as e:
            print(f"Errore nel file: {e}")

        pop = view.popup.PopUpDetails(self.app)
        selector = DirectorySelector(start_path=self.start_path, on_close=pop.close_popup)
        pop.show_popup(headtext="Percorso", layout=selector)

    def handle_select_years(self):
        def on_year_selected(year):
            self.popup.close_popup(button=None)
            if year:
                print("Anno selezionato:", year)
                self.selected_year = year
                self.anno_button.set_label(f"Anno: {year}")
            else:
                print("Selezione annullata.")

        selyear = SelectYears(on_close=on_year_selected)
        self.popup = view.popup.PopUpDetails(self.app)
        self.popup.show_popup(headtext="Seleziona anno di riferimento", layout=selyear)

        
    def chiusura(self, valore):
        print("Chiusura con:", valore)
                
    def handle_elabora_fatture(self):
        if not self.start_path:
            # Mostra messaggio nella status bar
            evento = control.widget_control.Event("text-statusbar", self, {"Warning": "Percorso dati non caricato. Seleziona prima 'Percorso dati'"})
            self.controller.emetti_evento(evento)
            return
        pop = view.popup.PopUpDetails(self.app)
        contab = MakeInvoiceCsv(start_path=self.start_path, on_close=pop.close_popup)
        pop.show_popup(headtext="Contabilizzazione", layout=contab)

    def handle_esci(self):
        # Mostra messaggio nella status bar
        evento = control.widget_control.Event("text-statusbar", self, {"Info": "Uscita in corso..."})
        self.controller.emetti_evento(evento)

        def esci_dopo_flash(loop, user_data):
            # funzione per uscire dal loop dopo x secondi invocati da self.app.loop.set_alarm_in...
            raise urwid.ExitMainLoop()
        # Dopo 0.5 secondi, chiude l'app
        self.app.loop.set_alarm_in(0.5, esci_dopo_flash)


    def render(self, size, focus=False):
        # Override di render per gestire il focus;
        # Evita di emettere l’evento "text-statusbar" troppe volte al focus
        if focus and not getattr(self, "_focus_emesso", False):
            #self.controller.emetti_evento("text-statusbar", {"widget": self})
            evento = control.widget_control.Event(
                tipo="text-statusbar",
                sorgente=self,
                payload={"widget": self}
            )
            self.controller.emetti_evento(evento)
            self._focus_emesso = True
        elif not focus:
            self._focus_emesso = False
        return super().render(size, focus)

    def selectable(self):
        # Metodo per rendere selezionabile l'oggetto Toolbar, di default non lo è
        return True
        
class SelectYears(urwid.WidgetWrap):
    def __init__(self, start_path=".", on_close=None):
        self.on_close = on_close
        self.start_path = start_path
        self.selected_year = None  # Qui memorizziamo l'anno selezionato

        years = [2024, 2025, 2026]

        # Gruppo di RadioButton per selezione singola
        self.year_buttons = []
        radio_group = []
        for year in years:
            btn = urwid.RadioButton(radio_group, str(year), on_state_change=self.on_year_selected)
            self.year_buttons.append(btn)

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
        if self.selected_year:
            print(f"Anno selezionato: {self.selected_year}")
            if self.on_close:
                self.on_close(self.selected_year)
        else:
            print("Nessun anno selezionato.")

    def cancel(self, button):
        if self.on_close:
            self.on_close(None)

class MakeListBox(urwid.WidgetWrap):
    def __init__(self, title, selection_mode, app, controller):
        self.title = title
        self.selection_mode = selection_mode
        self.app = app
        self.controller = controller

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
        self.selected_col = 0

        if self.selection_mode == "row":
            self._safe_set_focus(self.selected_row + 1 if self.content_widgets else 0)
        elif self.selection_mode == "col":
            self._safe_set_focus(0)

        self._aggiorna_evidenziazione()

    def _aggiorna_evidenziazione(self):
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
        self._aggiorna_evidenziazione()

    def keypress(self, size, key):
        match key:
            case 'left' | 'right':
                self._gestisci_movimento_colonna(key)
            case 'up' | 'down':
                self._gestisci_movimento_riga(key)
            case 'enter':
                self._gestisci_enter()
            case _:
                return super().keypress(size, key)

    def _gestisci_movimento_colonna(self, key):
        step = 1 if key == 'right' else -1
        if self.content_widgets:
            num_colonne = len(self.content_widgets[0].cells)
            self.selected_col = (self.selected_col + step) % num_colonne
            self._aggiorna_evidenziazione()

        if self.selection_mode == "row":
            self.app.main.cli_for_list.focus_position = 1 if key == 'right' else 0

    def _gestisci_movimento_riga(self, key):
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
            self._aggiorna_evidenziazione()
        elif self.selection_mode == "col":
            self.app.main.view.focus_position = 0 if key == 'up' else 2

    def _gestisci_enter(self):
        if self._focus_su_scadenze():
            self._filtra_scadenze()
        else:
            self._mostra_popup_dettaglio()

    def _focus_su_scadenze(self):
        return self.app.main.view.focus_position == 1

    def _filtra_scadenze(self):
        mese = self.selected_col + 1
        evento = control.widget_control.Event(
            tipo="listbox_enter",
            sorgente=self.title,
            payload={"mese": mese}
        )
        self.controller.emetti_evento(evento)

    def _mostra_popup_dettaglio(self):
        focus_pos = self.app.main.cli_for_list.focus_position
        row = self.selected_row
        evento = control.widget_control.Event(
            tipo="listbox_enter",
            sorgente=self.title,
            payload={"detail": focus_pos, "dati": row}
        )
        self.controller.emetti_evento(evento)

    def render(self, size, focus=False):
        self._log_focus_state("render")
        if focus:
            try:
                self.listbox.get_focus()
            except IndexError:
                self._safe_set_focus(0)

            evento = control.widget_control.Event(
                tipo="text-statusbar",
                sorgente=self,
                payload={"Messaggi": self}
            )
            self.controller.emetti_evento(evento)

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

class MakeListBoxOld(urwid.WidgetWrap):
    def __init__(self, title, selection_mode, app, controller):
        self.title = title
        self.selection_mode = selection_mode
        self.app = app
        self.controller = controller

        self.selected_row = 0
        self.selected_col = 0
        self.widget_list = []
        
        self.listbox = urwid.ListBox(urwid.SimpleFocusListWalker(self.widget_list))
        self.list_linebox = urwid.LineBox(self.listbox, title=title)

        super().__init__(self.list_linebox)

    def refresh_listbox(self, head=[], content=[]):
        # Ricostruisce intestazione e righe
        head_widgets = [urwid.Text(label, align=align) for label, align in head]
        self.header_widget = urwid.AttrMap(urwid.Columns(head_widgets), 'header')
        alignment = [a[1] for a in head]
        self.content_widgets = [RigaColonne(row, alignment, True) for row in content]

        # Aggiorna lista interna
        self.widget_list = [self.header_widget] + self.content_widgets

        # Aggiorna ListBox visiva
        self.listbox.body.clear()
        self.listbox.body.extend(self.widget_list)

        # Imposta selezione iniziale
        self.selected_row = 0
        self.selected_col = 0

        if self.selection_mode == "row":
            if self.content_widgets:
                self.listbox.set_focus(self.selected_row + 1)  # +1 per saltare intestazione
            else:
                self.listbox.set_focus(0)  # solo intestazione
        elif self.selection_mode == "col":
            self.listbox.set_focus(0)  # focus sull'intestazione

        # Applica evidenziazione
        self._aggiorna_evidenziazione()    

    def _aggiorna_evidenziazione(self):
        # funzione privata per selezionare riga per riga in caso di
        # selectionMode impostato a "row" e colonna per colonna in caso di 
        # selectionMode impostato a "col"
        for i, riga in enumerate(self.content_widgets):
            for j, attr in enumerate(riga.celle):
                if self.selection_mode == "row" and i == self.selected_row:
                    attr.set_attr_map({None: 'selected'})
                elif self.selection_mode == "col" and j == self.selected_col:
                    attr.set_attr_map({None: 'selected'})
                else:
                    attr.set_attr_map({None: 'normal'})

# Inizio gestione tasti
    def keypress(self, size, key):
        match key:
            case 'left' | 'right':
                self._gestisci_movimento_colonna(key)
            case 'up' | 'down':
                self._gestisci_movimento_riga(key)
            case 'enter':
                self._gestisci_enter()
            case _:
                return super().keypress(size, key)

    def _gestisci_movimento_colonna(self, key):
        step = 1 if key == 'right' else -1
        num_colonne = len(self.content_widgets[0].celle)
        self.selected_col = (self.selected_col + step) % num_colonne
        self._aggiorna_evidenziazione()

        if self.selection_mode == "row":
            self.app.main.cli_for_list.focus_position = 1 if key == 'right' else 0

    def _gestisci_movimento_riga(self, key):
        self._w.base_widget.set_focus(0)

        if self.selection_mode == "row":
            if key == 'up':
                if self.selected_row == 0:
                    self.app.main.view.focus_position = 1
                self.selected_row = max(0, self.selected_row - 1)
            elif key == 'down':
                max_row = len(self.content_widgets) - 1
                self.selected_row = min(max_row, self.selected_row + 1)

            self._w.base_widget.set_focus(self.selected_row + 1)
            self._aggiorna_evidenziazione()

        elif self.selection_mode == "col":
            self.app.main.view.focus_position = 0 if key == 'up' else 2

    def _gestisci_enter(self):
        if self._focus_su_scadenze():
            self._filtra_scadenze()
        else:
            self._mostra_popup_dettaglio()

# fine gestione tasti

    def _focus_su_scadenze(self):
        return self.app.main.view.focus_position == 1

    def _filtra_scadenze(self):
        mese = self.selected_col + 1
        #self.controller.emetti_evento("filtra_fatture", {"mese": mese})
        #self.controller.emetti_evento("listbox_enter", {"id": self.title, "mese": mese})
        evento = control.widget_control.Event(
            tipo="listbox_enter",
            sorgente=self.title,
            payload={"mese": mese}
        )
        self.controller.emetti_evento(evento)        

    def _mostra_popup_dettaglio(self):
        focus_pos = self.app.main.cli_for_list.focus_position
        row = self.selected_row
        evento = control.widget_control.Event(
            tipo="listbox_enter",
            sorgente=self.title,
            payload={"detail": focus_pos, "dati": row}
        )
        self.controller.emetti_evento(evento)        
        
    def render(self, size, focus=False):
        if focus:
            # Verifica che il focus sia valido
            try:
                current_focus = self.listbox.get_focus()[1]
            except IndexError:
                self.listbox.set_focus(0)

            evento = control.widget_control.Event(
                tipo="text-statusbar",
                sorgente=self,
                payload={"Messaggi": self}
            )
            self.controller.emetti_evento(evento)

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
        textInfo = urwid.LineBox(urwid.Text("Contabilizzare fatture XML presenti nei percorsi:", align='center'))
        textInfoPathF = urwid.Text(f"Fornitori: {self.start_path[1]}", align='center')
        textInfoPathC = urwid.Text(f"Clienti: {self.start_path[0]}", align='center')

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

        self.view = urwid.Filler(urwid.Pile([
            ('weight', 1, textInfo),
            (urwid.Divider()),
            (textInfoPathF),
            (urwid.Divider()),
            (textInfoPathC),
            (urwid.Divider()),
            ('pack', centered_ok_btn),
            ('pack', centered_cancel_btn)
        ]))
        
        super().__init__(self.view)
        
    def confirm(self, button):
        if self.on_close:
            self.makeCsv()
            self.on_close(True)
            self.alertExit()

    def cancel(self, button):
        self.on_close(True)

    def alertExit(self):
        pass

    def exitApp(self):
        raise urwid.ExitMainLoop()

    def makeCsv(self):
        scadenzclass = scadDati(self.start_path[0])
        scadenzclass.readXml()
        scadenzclass.xmlToCsv("datiFornitori.csv")
        scadenzclass.changeFile(self.start_path[1])
        scadenzclass.readXml()
        scadenzclass.xmlToCsv("datiClienti.csv")

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
            header = [["clienti", "fornitori"]]
            content = []
            content.append ([self.pathL, self.pathR])
            try:
                with open("path", mode="w", newline="", encoding="utf-8") as path:
                    writer = csv.writer(path, delimiter=";")
                    # Scrive le righe
                    writer.writerows(header)
                    writer.writerows(content)

            except Exception as e:
                print(f"Formato file errato: {e}")
                return

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

    def update_statusold(self, text1=None, text2=None):
        if text1:
            self.text.set_text(text1)
        elif text2:
            self.text.set_text(text2)
        else:
            self.text.set_text("")