#!/usr/bin/env python3
"""
ntj_convert.py - App ntJobsApp per conversione formati file
Supporta: PDF->MD/XLS/DOC, DFC tra formati strutturati
"""

import os
import sys
import shutil
import zipfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acJobsApp import acJobsApp, NormalizePath, DictExist, StringBool, ErrorProc
import aiSys

# =============================================================================
# VARIABILI GLOBALI
# =============================================================================
jData = None
nCounter = 0
sTimestamp = ""
sTimestampStart = ""
sTimestampEnd = ""
nElapsedSeconds = 0
xData = None

# =============================================================================
# HELPER: format_timedelta
# =============================================================================
def format_timedelta(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

# =============================================================================
# FUNZIONE: app_start
# =============================================================================
def app_start():
    global jData, nCounter, sTimestamp, sTimestampStart, sTimestampEnd, nElapsedSeconds
    sProc = "app_start"
    sResult = ""

    print(f"{aiSys.Timestamp()} - Esecuzione {sProc}")

    jData = acJobsApp()
    sTimestampStart = aiSys.Timestamp()

    sResult = jData.Start()
    if sResult:
        print(f"Errore Start: {sResult}")
        jData.End(sResult)
        return sResult

    sResult = jData.Run(cbCommand)

    sTimestampEnd = aiSys.Timestamp()
    nElapsedSeconds = aiSys.TimestampDiff(sTimestampStart, sTimestampEnd, "s") or 0
    print(f"Durata esecuzione: {format_timedelta(nElapsedSeconds)}")

    jData.End(sResult)
    return sResult

# =============================================================================
# FUNZIONE: cbCommand
# =============================================================================
def cbCommand(dictJob):
    global jData
    sProc = "cbCommand"
    sResult = ""

    print(f"{aiSys.Timestamp()} - Esecuzione {sProc}")

    jData.dictJob = dictJob.copy()
    jData.sCommand = DictExist(dictJob, "COMMAND", "")

    if jData.sCommand == "CONVERT":
        sResult = cmd_convert()
    else:
        sResult = f"Comando non supportato: {jData.sCommand}"

    return ErrorProc(sResult, sProc)

# =============================================================================
# FUNZIONE: cmd_convert
# =============================================================================
def cmd_convert():
    global jData, nCounter, sTimestamp, xData
    sProc = "cmd_convert"
    sResult = ""

    print(f"{aiSys.Timestamp()} - Esecuzione {sProc}")

    sEngine = DictExist(jData.dictJob, "ENGINE", "").lower()
    sType = DictExist(jData.dictJob, "TYPE", "").upper()
    bZip = StringBool(DictExist(jData.dictJob, "ZIP", "FALSE"))
    sFmt_in = DictExist(jData.dictJob, "FORMAT.IN", "").lower()
    sFmt_out = DictExist(jData.dictJob, "FORMAT.OUT", "").lower()

    print(f"DFC: Inizio conversione")

    file_in_keys = [k for k in jData.dictJob.keys() if k.startswith("FILE.IN.")]
    file_in_keys.sort(key=lambda x: int(x.split(".")[-1]) if x.split(".")[-1].isdigit() else 0)
    if "FILE.IN" in jData.dictJob and "FILE.IN" not in file_in_keys:
        file_in_keys.insert(0, "FILE.IN")

    nCounter = 0
    for key in file_in_keys:
        sFile_in = jData.dictJob[key]
        sFile_out = DictExist(jData.dictJob, "FILE.OUT", "")
        if not sFile_out:
            base, _ = os.path.splitext(sFile_in)
            ext_map = {
                "md": ".md", "markdown": ".md", "pdf": ".pdf", "docx": ".docx",
                "xlsx": ".xlsx", "xls": ".xls", "yaml": ".yaml", "yml": ".yml",
                "json": ".json", "xml": ".xml", "ini": ".ini", "csv": ".csv",
                "txt": ".txt", "html": ".html", "htm": ".htm"
            }
            sFile_out = base + ext_map.get(sFmt_out, f".{sFmt_out}")

        sFile_in = NormalizePath(sFile_in)
        sFile_out = NormalizePath(sFile_out)

        sResult = app_argverify(sFile_in, sFile_out, sFmt_in, sFmt_out, sEngine, sType)
        if sResult:
            break

        if sEngine == "dfc":
            sResult = app_dfc(sFile_in, sFile_out, sFmt_in, sFmt_out)
        elif sEngine == "pandoc":
            sResult = app_pandoc(sFile_in, sFile_out, sFmt_in, sFmt_out)
        elif sEngine == "fast":
            sResult = app_fast(sFile_in, sFile_out, sFmt_in, sFmt_out, sType)
        else:
            sResult = f"Engine non supportato: {sEngine}"

        if sResult == "" and bZip:
            sResult = app_zip(sFile_out)

        if sResult:
            break

        nCounter += 1

    if sResult == "":
        print(f"Conclusione esportazione: {nCounter} file processati")
    else:
        print(f"Errore conversione: {sResult}")

    return ErrorProc(sResult, sProc)

# =============================================================================
# FUNZIONE: app_argverify
# =============================================================================
def app_argverify(sFile_in, sFile_out, sFmt_in, sFmt_out, sEngine, sType):
    global jData
    sProc = "app_argverify"
    sResult = ""

    print(f"{aiSys.Timestamp()} - Esecuzione {sProc}")

    ext_map = {
        ".ini": "ini", ".xls": "xls", ".xlsx": "xls", ".xml": "xml",
        ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".csv": "csv",
        ".txt": "txt", ".html": "html", ".htm": "html",
        ".md": "markdown", ".markdown": "markdown", ".pdf": "pdf",
        ".docx": "docx"
    }
    _, sFile_in_ext = os.path.splitext(sFile_in.lower())
    expected_fmt = ext_map.get(sFile_in_ext, "")

    if not os.path.isfile(sFile_in):
        sResult = f"Errore file input non trovato: {sFile_in}"
    elif expected_fmt and expected_fmt != sFmt_in:
        sResult = f"Formato input non corrispondente al file: {sFmt_in} (estensione: {sFile_in_ext})"
    elif sEngine == "dfc" and sFmt_in not in ["ini", "xls", "xml", "json", "yaml", "csv", "txt"]:
        sResult = f"Formato input non valido per DFC: {sFmt_in}"
    elif sEngine == "pandoc" and not sFmt_in:
        sResult = "FORMAT.IN obbligatorio per PANDOC"
    elif sEngine == "fast" and sType not in ["PDF2XLS", "PDF2DOC"]:
        sResult = f"TYPE non valido per FAST: {sType}"

    return ErrorProc(sResult, sProc)

# =============================================================================
# FUNZIONE: app_dfc
# =============================================================================
def app_dfc(sFile_in, sFile_out, sFmt_in, sFmt_out):
    global xData
    sProc = "app_dfc"
    sResult = ""

    print(f"{aiSys.Timestamp()} - Esecuzione {sProc}")

    sResult = app_dfc_read(sFile_in, sFmt_in)
    if sResult:
        return ErrorProc(sResult, sProc)

    sResult = app_dfc_write(sFile_out, sFmt_out)
    if sResult:
        return ErrorProc(sResult, sProc)

    return ""

# =============================================================================
# FUNZIONE: app_dfc_read
# =============================================================================
def app_dfc_read(sFile_in, sFmt_in):
    global xData, sTimestamp
    sProc = "app_dfc_read"
    sResult = ""

    print(f"{aiSys.Timestamp()} - Esecuzione {sProc}")
    sTimestamp = aiSys.Timestamp()

    try:
        sFmt_in = sFmt_in.lower()
        if sFmt_in == "ini":
            import configparser
            config = configparser.ConfigParser(interpolation=None)
            config.optionxform = str
            config.read(sFile_in, encoding='utf-8')
            xData = {section: dict(config[section]) for section in config.sections()}

        elif sFmt_in in ["xls", "xlsx"]:
            import openpyxl
            wb = openpyxl.load_workbook(sFile_in, data_only=True)
            ws = wb["sheet"] if "sheet" in wb.sheetnames else wb.active
            rows = list(ws.iter_rows(values_only=True))
            if rows:
                headers = [str(h) for h in rows[0]]
                xData = []
                for row in rows[1:]:
                    xData.append(dict(zip(headers, row)))

        elif sFmt_in == "xml":
            import xml.etree.ElementTree as ET
            tree = ET.parse(sFile_in)
            root = tree.getroot()
            def xml_to_dict(elem):
                result = {}
                for child in elem:
                    if len(child) > 0:
                        result[child.tag] = xml_to_dict(child)
                    else:
                        result[child.tag] = child.text
                return result
            xData = xml_to_dict(root)

        elif sFmt_in == "json":
            import json
            with open(sFile_in, 'r', encoding='utf-8') as f:
                xData = json.load(f)

        elif sFmt_in == "yaml":
            import yaml
            with open(sFile_in, 'r', encoding='utf-8') as f:
                xData = yaml.safe_load(f)

        elif sFmt_in == "csv":
            import csv
            with open(sFile_in, 'r', encoding='utf-8') as f:
                first_line = f.readline()
                sDelim = ';' if ';' in first_line else ','
                f.seek(0)
                reader = csv.DictReader(f, delimiter=sDelim)
                asHeader = reader.fieldnames
                xData = list(reader)
                nRows_in = len(xData)
                print(f"Letto csv di {nRows_in}, Delimitatore: {sDelim}")

        elif sFmt_in == "txt":
            with open(sFile_in, 'r', encoding='utf-8') as f:
                xData = f.read()

        else:
            sResult = f"Formato input DFC non supportato: {sFmt_in}"

    except Exception as e:
        sResult = f"Errore lettura {sFmt_in}: {str(e)}"

    return ErrorProc(sResult, sProc)

# =============================================================================
# FUNZIONE: app_dfc_write
# =============================================================================
def app_dfc_write(sFile_out, sFmt_out):
    global xData
    sProc = "app_dfc_write"
    sResult = ""

    print(f"{aiSys.Timestamp()} - Esecuzione {sProc}")
    sTimestamp = aiSys.Timestamp()

    try:
        os.makedirs(os.path.dirname(sFile_out), exist_ok=True)
        sFmt_out = sFmt_out.lower()

        if sFmt_out == "ini":
            import configparser
            config = configparser.ConfigParser(interpolation=None)
            config.optionxform = str
            for section, items in xData.items():
                config.add_section(section)
                for k, v in items.items():
                    config.set(section, k, str(v))
            with open(sFile_out, 'w', encoding='utf-8') as f:
                config.write(f)

        elif sFmt_out in ["xls", "xlsx"]:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "sheet"
            if xData and isinstance(xData, list) and len(xData) > 0:
                headers = list(xData[0].keys())
                ws.append(headers)
                nRows_out = 0
                for row in xData:
                    ws.append([row.get(h, "") for h in headers])
                    nRows_out += 1
                print(f"Scritto xlsx: {nRows_out} righe")
            wb.save(sFile_out)

        elif sFmt_out == "xml":
            import xml.etree.ElementTree as ET
            import xml.dom.minidom as minidom
            def dict_to_xml(tag, d):
                elem = ET.Element(tag)
                for key, val in d.items():
                    child = ET.SubElement(elem, key)
                    if isinstance(val, dict):
                        child.append(dict_to_xml(key, val))
                    else:
                        child.text = str(val) if val is not None else ""
                return elem
            root = dict_to_xml("root", xData)
            rough = ET.tostring(root, encoding='utf-8')
            reparsed = minidom.parseString(rough)
            with open(sFile_out, 'w', encoding='utf-8') as f:
                f.write(reparsed.toprettyxml(indent="  "))

        elif sFmt_out == "json":
            import json
            with open(sFile_out, 'w', encoding='utf-8') as f:
                json.dump(xData, f, indent=2, ensure_ascii=False)

        elif sFmt_out == "yaml":
            import yaml
            with open(sFile_out, 'w', encoding='utf-8') as f:
                yaml.dump(xData, f, default_flow_style=False, allow_unicode=True)

        elif sFmt_out == "csv":
            import csv
            if xData and isinstance(xData, list) and len(xData) > 0:
                fieldnames = list(xData[0].keys())
                with open(sFile_out, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
                    writer.writeheader()
                    writer.writerows(xData)
                print(f"Scritto csv: {len(xData)} righe")

        elif sFmt_out == "txt":
            with open(sFile_out, 'w', encoding='utf-8') as f:
                f.write(str(xData))

        else:
            sResult = f"Formato output DFC non supportato: {sFmt_out}"

    except Exception as e:
        sResult = f"Errore scrittura {sFmt_out}: {str(e)}"

    return ErrorProc(sResult, sProc)

# =============================================================================
# FUNZIONE: app_pandoc
# =============================================================================
def app_pandoc(sFile_in, sFile_out, sFmt_in, sFmt_out):
    sProc = "app_pandoc"
    sResult = ""

    print(f"{aiSys.Timestamp()} - Esecuzione {sProc}")
    sTimestamp = aiSys.Timestamp()

    try:
        import pypandoc
        os.makedirs(os.path.dirname(sFile_out), exist_ok=True)
        output = pypandoc.convert_file(
            sFile_in,
            sFmt_out,
            format=sFmt_in if sFmt_in else None,
            outputfile=sFile_out
        )
        if output:
            sResult = f"Pandoc warning: {output}"

    except ImportError:
        sResult = "pypandoc non installato. Esegui: pip install pypandoc"
    except Exception as e:
        sResult = f"Errore pandoc: {str(e)}"

    return ErrorProc(sResult, sProc)

# =============================================================================
# FUNZIONE: app_fast
# =============================================================================
def app_fast(sFile_in, sFile_out, sFmt_in, sFmt_out, sType):
    sProc = "app_fast"
    sResult = ""

    print(f"{aiSys.Timestamp()} - Esecuzione {sProc}")
    sTimestamp = aiSys.Timestamp()

    try:
        os.makedirs(os.path.dirname(sFile_out), exist_ok=True)

        if sType == "PDF2XLS":
            import fitz
            import pandas as pd
            doc = fitz.open(sFile_in)
            all_tables = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                tabs = page.find_tables()
                for table in tabs:
                    df = table.to_pandas()
                    all_tables.append(df)
            doc.close()
            if all_tables:
                combined = pd.concat(all_tables, ignore_index=True)
                combined.to_excel(sFile_out, index=False, engine='openpyxl')
            else:
                sResult = "Nessuna tabella trovata nel PDF"

        elif sType == "PDF2DOC":
            engine = DictExist(jData.dictJob, "ENGINE", "").lower()
            if engine == "fast":
                import pdf2docx
                pdf2docx.convert(sFile_in, sFile_out)
            elif engine == "normal":
                import fitz
                from docx import Document
                doc = fitz.open(sFile_in)
                docx_doc = Document()
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    text = page.get_text()
                    if text.strip():
                        docx_doc.add_paragraph(text)
                    if page_num < len(doc) - 1:
                        docx_doc.add_page_break()
                doc.close()
                docx_doc.save(sFile_out)
            else:
                sResult = "ENGINE per PDF2DOC deve essere FAST o NORMAL"

        else:
            sResult = f"TYPE non supportato per FAST: {sType}"

    except ImportError as e:
        sResult = f"Libreria mancante per FAST: {str(e)}"
    except Exception as e:
        sResult = f"Errore FAST: {str(e)}"

    return ErrorProc(sResult, sProc)

# =============================================================================
# FUNZIONE: app_zip
# =============================================================================
def app_zip(sFile_out):
    sProc = "app_zip"
    sResult = ""

    print(f"{aiSys.Timestamp()} - Esecuzione {sProc}")
    sTimestamp = aiSys.Timestamp()

    if not sFile_out:
        return ErrorProc("Errore percorso output non definito", sProc)

    try:
        base, ext = os.path.splitext(sFile_out)
        zip_path = base + ".zip"
        resources_dir = base + "_resources"

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            if os.path.isfile(sFile_out):
                zf.write(sFile_out, os.path.basename(sFile_out))
            if os.path.isdir(resources_dir):
                for root, dirs, files in os.walk(resources_dir):
                    for file in files:
                        full_path = os.path.join(root, file)
                        arc_name = os.path.relpath(full_path, os.path.dirname(resources_dir))
                        zf.write(full_path, arc_name)

        print(f"Creato archivio: {zip_path}")

    except Exception as e:
        sResult = f"Errore creazione zip: {str(e)}"

    return ErrorProc(sResult, sProc)

# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    sResult = app_start()
    if sResult:
        print(f"ERRORE: {sResult}")
        sys.exit(1)
    sys.exit(0)