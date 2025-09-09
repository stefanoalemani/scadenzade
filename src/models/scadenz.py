#!/usr/bin/python3
# file name .......... scadenz.py
# scope .............. read and manage XML invoice deadline with write in
# .................... CSV, DBF and other format files
# language ........... Python 3.11.2
# author ............. Stefano Alemani
# date ............... 16-05-2025
# version ............ 0.6.0

import models.readwrite_csv_xml as rwxml
import glob
import os
from datetime import datetime
from tabulate import tabulate

class ScadDati:
    '''
    class for manage xml file of "fatture elettroniche (electronic invoice)
    agenzia delle entrate italiana" in detail refer to the management of a 
    payment schedule software. It basically extracts the deadline data and makes 
    it available to lists and dictionaries.
    '''

    def __init__(self, xml_file_pathname=""):
        '''
        xml_file_pathname può essere il percorso di un singolo file XML
        oppure una directory contenente più file XML.
        '''
        self.xml_filename = self._resolve_path(xml_file_pathname)
        self.scad_all = []

    def _resolve_path(self, path):
        if os.path.isfile(path):
            return path
        elif os.path.isdir(path):
            return os.path.join(path, '*.xml')
        else:
            raise ValueError(f"Percorso non valido: {path}")
    
    def change_file(self, xml_file_pathname):
        '''
        change reference file name or path of files. It can be useful when 
        selecting a vendor invoice path and in the same instance switching to
        customer invoices.
        '''
        self.xml_filename = self._resolve_path(xml_file_pathname)

    def read_xml(self, manual_scad=False, data_manual=None):
        '''
        return list of all invoice scadence. Every element of list is dictionary
        with this format: {'ModalitaPagamento1': 'MP12', 
        'DataScadenzaPagamento1': '2023-07-31', ... }
        If arg manual_scad is True and data_manual is set, in case of deadline 
        data not present, will be request manual insert, otherwise an alert will
        be generated and the invoice date will be considered deadline. See 
        add_scad.py for details.
        '''
        self.scad_all = []
        for file_path in glob.glob(self.xml_filename):
            scad_temp = rwxml.read_xml_scad(file_path, manual_scad, data_manual)
            self.scad_all.append(scad_temp)
        return self.scad_all

    def sniff_years(self):
        """
        Legge gli anni di scadenza dalle fatture e restituisce una lista ordinata
        di anni unici presenti.
        """
        dati = self.read_xml()
        anni = {
            int(valore[:4])
            for elemento in dati
            for sotto_dizionario in elemento
            if isinstance(sotto_dizionario, dict)
            for chiave, valore in sotto_dizionario.items()
            if chiave.startswith("DataScadenzaPagamento")
        }
        return sorted(anni)
    
    def write_years_csv(self, year_act, year_avl):
        rwxml.write_year ({"active": year_act, "available": year_avl})
    
    def sniff_years_old(self):
        """
        function for read years of deadlines in the invoices. Return a list with
        years present (grouped).
        """
        dati = self.read_xml()
        # Estrazione delle date di scadenza pagamento
        date_scadenza = []
        for elemento in dati:
            for sotto_dizionario in elemento:
                if isinstance(sotto_dizionario, dict):
                    for chiave, valore in sotto_dizionario.items():
                        if chiave.startswith("DataScadenzaPagamento"):
                            date_scadenza.append(valore)
        # Visualizza il risultato
        # Estrai gli anni e rimuovi i duplicati
        anni_unici = sorted({int(data[:4]) for data in date_scadenza})
        return (anni_unici)
   
    def xml_to_csv(self, filename):
        def format_date(date_str):
            return datetime.strptime(date_str, '%Y-%m-%d')

        header = [["Denominazione", "IdCodice", "TipoDocumento", "Numero", 
                   "Data", "ImportoTotaleDocumento", "DataScadenzaPagamento",
                   "ImportoPagamento", "ModalitaPagamento", "Cessionario",
                   "IdCodiceCess"]]
        
        content = []

        for scad in self.scad_all:
            num_scad = scad[0]
            for i in range(num_scad):
                invoice_dt = format_date(scad[3]["Data"])
                scad_dt = format_date(scad[1][f"DataScadenzaPagamento{i+1}"])
                importo_totale = float(scad[4]['ImponibileImporto']) + float(scad[4]['Imposta'])
                importo_pagamento = float(scad[1][f'ImportoPagamento{i+1}'])

                content.append([
                    scad[2]["Denominazione"],
                    scad[2]["IdCodice"],
                    scad[3]["TipoDocumento"],
                    scad[3]["Numero"],
                    invoice_dt,  # oggetto datetime
                    f"{importo_totale:.2f}",
                    scad_dt,      # oggetto datetime
                    f"{importo_pagamento:.2f}",
                    scad[1][f"ModalitaPagamento{i+1}"],
                    scad[5]["FDenominazione"],
                    scad[5]["FIdCodice"]
                ])

        # Ordina usando datetime, poi formatta le date
        content.sort(key=lambda x: (x[6], x[4]))  # x[6] = scad_dt, x[4] = invoice_dt

        # Converti le date in stringa dopo l'ordinamento
        for row in content:
            row[4] = row[4].strftime('%d-%m-%Y')  # invoice_dt
            row[6] = row[6].strftime('%d-%m-%Y')  # scad_dt

        rwxml.write_csv_clifor(filename, header, content)
        print(f"File CSV '{filename}' creato con successo e ordinato correttamente!")
            
    def xml_to_txt(self, output_file="dati.txt"):
        '''
        utility function to show all invoice expiration in text mode, without 
        the possibility of interacting. Function work after invoked readXml()
        '''
        rows = []
        for scad in self.scad_all:
            rows.append(f"Azienda: {scad[2]['Denominazione']} - P.IVA: {scad[2]['IdCodice']}")
            rows.append(f"Documento: {scad[3]['TipoDocumento']} n° {scad[3]['Numero']} del {scad[3]['Data']}")
            rows.append(f"Importo totale: € {scad[3]['ImportoTotaleDocumento']}")
            rows.append(f"Numero scadenze: {scad[0]}\n")
            for i in range(scad[0]):
                rows.append(f"  Scadenza {i+1}: {scad[1][f'DataScadenzaPagamento{i+1}']}")
                rows.append(f"  Importo: € {scad[1][f'ImportoPagamento{i+1}']}")
                rows.append(f"  Modalità: {scad[1][f'ModalitaPagamento{i+1}']}\n")
            rows.append("-" * 40)

        with open(output_file, "w") as file:
            file.write("\n".join(rows))
        print(f"File '{output_file}' generato con successo.")        

    def xml_to_dbf(self):
        pass  # da implementare

    def xml_to_xls(self):
        pass  # da implementare
        
class ViewScadGen:
    '''
    a class with a viewer function for managing invoices. It can display data in
    CSV files or other formats, and its methods perform some general calculation
    functions.
    '''
    
    def __init__(self, csv_filename=""):
        self.csv_file = csv_filename

    def change_file(self, csv_filename):
        '''
        change reference file name or path of files. It can be useful when 
        selecting a vendor invoice path and in the same instance switching to
        customer invoices.
        '''
        self.csv_file = csv_filename

    def scad_cli_for(self, year):
        '''
        read CSV file and group deadline, calc total invoice for month and 
        return list with 12 result, which are the monthly total amounts.
        Usable for customers and suppliers invoices.
        '''
        ########################################################################
        # adattabile anche per scadenze specifiche alla data indicata. Non usato
        # Filtrare le righe che hanno DataScadenzaPagamento nella data indicata 
        # (data_limite)
        # data_limite = datetime.strptime("2025-07-31", "%d-%m-%Y")
        # dati_filtrati = [riga for riga in dati if datetime.strptime(riga["Data
        # ScadenzaPagamento"], "%d-%m-%Y") == data_limite]
        ########################################################################

        # read file
        list_reader = rwxml.read_csv_raw(self.csv_file)
        total_month = []
        select_month = 1
        total_month = []
        for mese in range(1, 13):
            dati_filtrati = [
                riga for riga in list_reader
                if datetime.strptime(riga["DataScadenzaPagamento"], "%d-%m-%Y").month == mese
                and datetime.strptime(riga["DataScadenzaPagamento"], "%d-%m-%Y").year == year
            ]
            totale = sum(float(r["ImportoPagamento"]) for r in dati_filtrati)
            total_month.append(f"{totale:.2f}")

        return total_month
        
    def txt_view(self, data_supplier=[], data_customer=[]):
        # test function
        data_supplier.insert(0, "Fornitori")
        data_customer.insert(0, "Clienti")
        print(tabulate([data_supplier, data_customer], headers=[
            "Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago",
            "Set", "Ott", "Nov", "Dic"
        ], tablefmt="grid"))
        

# standalone usage example:
#if __name__ == "__main__" :
    #scadenzclass = ScadDati("../data_box/xml_clienti/IT01879020517A2025_a0bHJ.xml")
    #scadenzclass = ScadDati("../data_box/xml_clienti/")
    #print (scadenzclass.read_xml())
    #print ("OK")
    #scadenzclass = ScadDati("../data_box/xml_fornitori/IT04513160962_2kl7I.xml")
    #scadenzclass.read_xml(True, "2025-01-01")
    #scadenzclass.read_xml(False)
    #scadenzclass.xml_to_csv("dati_forni.csv")
#    scadenzclass.changeFile("xml-box/clienti/*")
#    scadenzclass.read_xml()
#    scadenzclass.xmlToCsv("datiClienti.csv")
#    scadenzario = viewScadGen("datiFornitori.csv")
#    totaliFornitori = scadenzario.scadCliFor(2025)
#    scadenzclass.xmlToTxt()
#    scadenzario.changeFile("datiClienti.csv")
#    totaliClienti = scadenzario.scadCliFor(2025)
#    scadenzario.txtView(totaliFornitori, totaliClienti)