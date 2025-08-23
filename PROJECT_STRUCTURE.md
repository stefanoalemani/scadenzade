# Project Structure

Questo file descrive la struttura del progetto Python "scadenzade"
per la gestione delle scadenze delle fatture elettroniche italiane (ADE).

## invoice_utils/
- `__init__.py` → Inizializzazione del pacchetto
- `reader.py` → Funzioni per leggere file CSV e XML
- `xml_editor.py` → Funzioni per modificare XML (es. aggiunta scadenza)

## models/
- `invoice_model.py` → Struttura dati della fattura
- `payment_model.py` → Struttura dati del pagamento

## view/

## utils/
- `file_utils.py` → Funzioni generiche per file
- `xml_utils.py` → Funzioni generiche per XML

## cli/
- `interface.py` → Interfaccia da terminale

## config/
- `settings.py` → Configurazioni globali

## tests/
- `test_read_csv_xml.py` → Test per lettura CSV/XML
- `test_invoice_model.py` → Test per modello fattura