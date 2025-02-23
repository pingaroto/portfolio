import pandas as pd
import xml.etree.ElementTree as ET
import os
from datetime import datetime

def criar_xml_lote_cancelamento(df, pasta_saida, id_lote=f"SISCOAFCancelamento{datetime.today().strftime('%d%m%Y')}"):

    root = ET.Element("LOTECANCELAMENTO")
    ocorrencias = ET.SubElement(root, "OCORRENCIAS", ID=id_lote)

    for _, row in df.iterrows():
        ocorrencia = ET.SubElement(ocorrencias, "OCORRENCIA")
        ET.SubElement(ocorrencia, "NUMEROORIGEM").text = str(row["NUMEROORIGEM"])
        ET.SubElement(ocorrencia, "NUMEROCOAF").text = str(row["NUMEROCOAF"])
        ET.SubElement(ocorrencia, "AUTENTICACAO").text = row["AUTENTICACAO"]
        ET.SubElement(ocorrencia, "MOTIVO").text = row["MOTIVO"]

    tree = ET.ElementTree(root)
    nome_arquivo = os.path.join(pasta_saida, "lote_cancelamento.xml")

    with open(nome_arquivo, "wb") as f:
        tree.write(f, encoding="ISO-8859-1", xml_declaration=True)

    print(f"Arquivo XML '{nome_arquivo}' gerado com sucesso.")
    return nome_arquivo

def processar_planilha(caminho_planilha, pasta_saida):

    df = pd.read_excel(caminho_planilha, dtype={"NUMEROORIGEM": str, "NUMEROCOAF": str, "AUTENTICACAO": str})
    
    if not {"NUMEROORIGEM", "NUMEROCOAF", "AUTENTICACAO", "MOTIVO"}.issubset(df.columns):
        raise ValueError("A planilha deve conter as colunas: NUMEROORIGEM, NUMEROCOAF, AUTENTICACAO, MOTIVO")

    os.makedirs(pasta_saida, exist_ok=True)

    criar_xml_lote_cancelamento(df, pasta_saida)


caminho_excel = r"caminho planilha excel"
pasta_saida = r"pasta para saido de XML" 

processar_planilha(caminho_excel, pasta_saida)
