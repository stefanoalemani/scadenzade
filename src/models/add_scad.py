#!/usr/bin/python3
# file name .......... add_scad.py
# scope .............. utility add manuals deadlines in XML file
# language ........... Python 3.11.2
# author ............. Stefano Alemani
# date ............... 14-08-2025
# version ............ 0.6.0

def add_scad(dett_doc, dett_ana, manual_scad=False, data_manual=None):
    """
    Gestisce l'aggiunta manuale della data di scadenza nel file XML.
    Da tracciato "DataScadenzaPagamento" non è obbligatorio, quindi se non presente
    andrebbe ricercato il tipo di pagamento usato e interpretato per calcolare la scadenza, 
    strada percorribile se disponibile il file anagrafica clienti, ma non certa perchè
    per ogni singola fattura potrebbe esserci una scadenza particolare. Di conseguenza 
    si opta per dare la possibilità di inserimento manuale della data di scadenza da interfaccia,
    data che si andrà a scrivere nell'xml. Di default senza impostare manualScad = True in addScad
    si considera la data di scadenza uguale alla data della fattura, in considerazione che 
    normalmente in caso di pagamenti non uguali alla data della fattura quasi tutti i sw di fatturazione
    scrivono 'DataScadenzaPagamento' nell'xml

    Restituisce la data di scadenza da inserire nel file XML della fattura.

    Parametri:
    - dett_doc (dict): Dati della fattura. Deve contenere almeno 'Numero' e 'Data'.
    - dett_ana (dict): Dati anagrafici del cliente. Deve contenere 'Denominazione'.
    - manual_scad (bool): Se True, si usa la data passata in `data_manual`.
    - data_manual (str): Data di scadenza manuale già validata (formato 'yyyy-mm-dd').

    Ritorna:
    - str: Data di scadenza da scrivere nel tracciato XML.
    """
    warning_base = (
             f"\nnon essendo un dato obbligatorio succede che a volte il tracciato \n"
             f"xml della fattura non presenti la data di scadenza. In questo caso \n"
             f"per la fattura {dett_doc.get('Numero')} del {dett_doc.get('Data')} di: \n"
             f"{dett_ana.get('Denominazione')} \n"
             f"non è presente. \n"
    )

    if manual_scad and data_manual:
        warning_text = (
            f"\nATTENZIONE: La fattura {dett_doc.get('Numero')} del {dett_doc.get('Data')} "
            f"di {dett_ana.get('Denominazione')} non contiene la data di scadenza.\n"
            f"È stata inserita manualmente la scadenza {data_manual} e sarà salvata nel tracciato XML.\n"
        )
        data = data_manual
    elif manual_scad:
        warning_text = (
            f"\nATTENZIONE: La fattura {dett_doc.get('Numero')} del {dett_doc.get('Data')} "
            f"di {dett_ana.get('Denominazione')} non contiene la data di scadenza e non è stata "
            "impostata manualmente.\n"
        )
        print(warning_base + warning_text)
        return None
    elif manual_scad == False:
        warning_text = (
            f"\nATTENZIONE: La fattura {dett_doc.get('Numero')} del {dett_doc.get('Data')} "
            f"di {dett_ana.get('Denominazione')} non contiene la data di scadenza.\n"
            f"Sarà considerata come scadenza la data della fattura."
        )
        data = dett_doc.get('Data', '1970-01-01')
    print(warning_base + warning_text)
    return data