#!/usr/bin/env python3
# file name .......... readwrite_csv_xml.py
# scope .............. utility for reading CSV and deadlines from XML (ADE) file
# language............ Python 3.11.2
# author ............. Stefano Alemani
# version ............ 0.6.0

import csv
from typing import List, Dict, Tuple
from models.add_scad import add_scad
import lxml.etree as ET
from config.constants import CONFIG_DIR, DATA_DIR

def read_csv_path() -> Dict[str, List[str]]:
    start_path = {"fornitori": [], "clienti": []}
    try:
        with open(CONFIG_DIR / "path.csv", "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                start_path["fornitori"].append(row.get("fornitori", ""))
                start_path["clienti"].append(row.get("clienti", ""))

    except Exception as e:
        print(f"Errore nella lettura del file path: {e}")
    
    return start_path

def write_csv_path(path_cli_for: Dict[str, List[str]]) -> None:
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        fornitori = path_cli_for.get("fornitori", [])
        clienti = path_cli_for.get("clienti", [])

        if not clienti or not fornitori:
            raise ValueError("Percorsi mancanti: servono almeno un percorso per fornitori e clienti")

        with (CONFIG_DIR / "path.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["fornitori", "clienti"], delimiter=";")
            writer.writeheader()
            writer.writerow({
                "fornitori": fornitori[0],
                "clienti": clienti[0]
            })            
    except Exception as e:
        print(f"Errore nella scrittura del file path.csv: {e}")

def ensure_csv_path_exists() -> None:
    try:
        with (CONFIG_DIR / "path.csv").open("x", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["fornitori", "clienti"], delimiter=";")
            writer.writeheader()
    except FileExistsError:
        pass  # Il file esiste già
        
def make_csv_default_clifor() -> None:
    fieldnames = [
        'Denominazione', 'ImportoPagamento', 'DataScadenzaPagamento',
        'Numero', 'IdCodice', 'Data', 'ImportoTotaleDocumento',
        'ModalitaPagamento', 'Cessionario', 'IdCodiceCess'
    ]
    for filename in ["dati_fornitori.csv", "dati_clienti.csv"]:
        try:
            with (DATA_DIR / filename).open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
                writer.writeheader()
        except Exception as e:
            print(f"Errore nella creazione del file {filename}: {e}")

def read_csv_raw(csv_filename: str) -> List[Dict[str, str]]:
    try:
        with open(csv_filename, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            return list(reader)
    except Exception as e:
        print(f"Errore nella lettura del file CSV: {e}")
        return []

def read_csv_clifor(csv_filename: str) -> List[Tuple[str, ...]]:
    raw_data = read_csv_raw(csv_filename)
    return [
        (row.get('Denominazione', ''), row.get('ImportoPagamento', ''),
         row.get('DataScadenzaPagamento', ''), row.get('Numero', ''),
         row.get('IdCodice', ''), row.get('Data', ''), 
         row.get('ImportoTotaleDocumento', ''), row.get('ModalitaPagamento', ''), 
         row.get('Cessionario', ''), row.get('IdCodiceCess', '')
        )
        for row in raw_data
    ]

def write_csv_clifor(csv_filename: str, header: List[str], content: List[List[str]]) -> None:
    try:
        with open(csv_filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";", quoting=csv.QUOTE_MINIMAL)
            for row in header:
                writer.writerow(row)
            for row in content:
                writer.writerow(row)
    except Exception as e:
        print(f"Errore nella scrittura del file {csv_filename}: {e}")
   
def flatten_xml(element) -> Dict[str, str]:
    """Flattens XML elements into a flat dictionary, warning on duplicate keys."""
    result = {}
    for child in element:
        if len(child):  # has children
            result.update(flatten_xml(child))
        else:
            if child.tag in result:
                # print(f"Attenzione: chiave duplicata '{child.tag}' rilevata. Sovrascrittura in corso.")
                pass
            result[child.tag] = child.text or ""
    return result

def read_xml_scad(xml_filename: str, manual_scad: bool = False, data_manual: str = None) -> Tuple[int, Dict[str, str], Dict[str, str], Dict[str, str], Dict[str, str], Dict[str, str]]:
    try:
        tree = ET.parse(xml_filename)
        root = tree.getroot()

        ret_pag, ret_ana, ret_doc, ret_imp, ret_ana_cess = {}, {}, {}, {}, {}

        # Cedente/Prestatore
        cedente = root.find('FatturaElettronicaHeader/CedentePrestatore/DatiAnagrafici')
        if cedente is not None:
            ret_ana.update(flatten_xml(cedente))
        ret_ana.setdefault("Denominazione", ret_ana.get("Cognome", "Sconosciuto"))

        # Documento
        doc = root.find('FatturaElettronicaBody/DatiGenerali/DatiGeneraliDocumento')
        if doc is not None:
            ret_doc.update(flatten_xml(doc))

        # Pagamenti
        pagamenti = root.findall('FatturaElettronicaBody/DatiPagamento/DettaglioPagamento')
        modificato = False

        for i, pagamento in enumerate(pagamenti, start=1):
            for elem in pagamento:
                ret_pag[f"{elem.tag}{i}"] = elem.text or ""

            if f"DataScadenzaPagamento{i}" not in ret_pag:
                scadenza = add_scad(ret_doc, ret_ana, manual_scad, data_manual)
                if scadenza is None:
                    return None
                ET.SubElement(pagamento, "DataScadenzaPagamento").text = scadenza
                modificato = True

            for elem in pagamento:
                ret_pag[f"{elem.tag}{i}"] = elem.text or ""

        if modificato:
            tree.write(xml_filename, encoding="utf-8", xml_declaration=True)

        # Importi
        importi = root.findall('FatturaElettronicaBody/DatiBeniServizi/DatiRiepilogo')
        for imp in importi:
            ret_imp.update(flatten_xml(imp))

        # Cessionario/Committente
        cessionario = root.find('FatturaElettronicaHeader/CessionarioCommittente/DatiAnagrafici')
        if cessionario is not None:
            temp = flatten_xml(cessionario)
            ret_ana_cess.update({f"F{k}": v for k, v in temp.items()})

        return len(pagamenti), ret_pag, ret_ana, ret_doc, ret_imp, ret_ana_cess

    except Exception as e:
        print(f"Errore nella lettura del file XML: {e}")
        return 0, {}, {}, {}, {}, {}

def read_year() -> Dict[str, List[int] | str]:
    year = {"active": "", "available": []}
    try:
        with (CONFIG_DIR / "year.csv").open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                if not year["active"]:
                    year["active"] = row.get("active", "")
                available_str = row.get("available", "")
                # Rimuove le parentesi quadre e divide la stringa
                available_list = [
                    int(item.strip()) for item in available_str.strip("[]").split(",")
                    if item.strip().isdigit()
                ]
                year["available"] = available_list
    except Exception as e:
        print(f"Errore nella lettura del file year.csv: {e}")
    return year

def read_yearOLD() -> Dict[str, List[str] | str]:
    year = {"active": "", "available": []}
    try:
        with (CONFIG_DIR / "year.csv").open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                if not year["active"]:
                    year["active"] = row.get("active", "")
                year["available"].append(row.get("available", ""))
    except Exception as e:
        print(f"Errore nella lettura del file year.csv: {e}")
    return year

def write_year(year: Dict[str, List[str] | str]) -> Dict[str, str]:
    existing = read_year()
    updated = {
        "active": year.get("active", existing["active"]),
        "available": year.get("available", existing["available"])[0] if isinstance(existing["available"], list) and existing["available"] else ""
    }
    try:
        with (CONFIG_DIR / "year.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["active", "available"], delimiter=";")
            writer.writeheader()
            writer.writerow(updated)
    except Exception as e:
        print(f"Errore nella scrittura del file year.csv: {e}")
    return updated