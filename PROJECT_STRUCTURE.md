# Struttura del Progetto — *scadenzade*

Questo file descrive la struttura del progetto Python **scadenzade**, pensato per la gestione delle scadenze delle fatture elettroniche italiane (ADE).

---

#src/

## /config/
Contiene file di configurazione e costanti.

- `__init__.py` → Inizializza il pacchetto
- `constants.py` → Elenco di costanti organizzate per nome
- `path.csv` → Percorsi dei file XML delle fatture (clienti e fornitori)
- `year.csv` → Annualità dei dati fatture disponibili
- `year_loader.py` → Legge l'anno da year.csv

---

## /control/
Gestione dell’architettura MVC.

- `widget_control.py` → Controller principale. Gestisce eventi e interazioni tra i widget

---

## /data_box/
Contiene i dati elaborati e i file sorgente.

- `dati_clienti.csv` → Dati utili per le fatture clienti (generato dopo contabilizzazione)
- `dati_fornitori.csv` → Dati utili per le fatture fornitori (generato dopo contabilizzazione)

### /data_box/xml_clienti/
- `fattureclienti.xml` → Multipli file XML con fatture clienti, da scaricare dal proprio gestore fatture xml o dall'ade. Percorso modificabile

### /data_box/xml_fornitori/
- `fatturefornitori.xml` →  Multipli file XML con fatture fornitori, da scaricare dal proprio gestore fatture xml o dall'ade. Percorso modificabile

---

## /models/
Moduli logici e di elaborazione dati.

- `add_scad.py` → Gestisce l'aggiunta manuale/automatica della data di scadenza nel file XML
- `data_provider.py` → Classe ad alto livello per lettura/scrittura e distribuzione dati. Usa `readwrite_csv_xml.py`
- `readwrite_csv_xml.py` → Funzioni per leggere/scrivere file CSV e XML (usati in `config/` e `data_box/`)
- `scadenz.py` → Gestisce le scadenze delle fatture XML. Può esportare in CSV, DBF, TXT. Utilizzabile anche come script standalone

---

## /view/
Interfaccia grafica e componenti UI.

- `main_view.py` → Modulo principale dell’interfaccia. Importa i widget da `widget_class.py` e gestisce la logica minima
- `popup.py` → Gestione delle finestre popup
- `widget_class.py` → Classi per ogni widget. Costruisce i widget base usando `urwid`. Funziona come libreria ad alto livello

---

## Note Finali

- Tutti i moduli sono pensati per essere modulari e facilmente estendibili
- La struttura segue il pattern MVC per separare logica, dati e interfaccia
- I file CSV e XML sono trattati come fonti dati primarie, con possibilità di esportazione in altri formati