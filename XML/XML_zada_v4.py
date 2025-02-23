import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
import glob
import os
import re

def formatar_data(data):
    if pd.isna(data) or str(data).strip() == "":
        return ""  
    try:
        return pd.to_datetime(data, dayfirst=True).strftime('%d/%m/%Y')
    except Exception:
        return ""  

def tratar_valor(valor):
    if pd.isna(valor) or str(valor).strip() == "":
        return ""
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))  
    return str(valor)

def gerar_xml_siscoaf(arquivo_excel: str, nome_arquivo_xml: str):
    df = pd.read_excel(arquivo_excel)
    
    if len(df) < 2:
        print("Erro: O arquivo Excel precisa ter pelo menos duas linhas.")
        return
    
    lote = ET.Element("LOTE")
    ocorrencias = ET.SubElement(
        lote,
        "OCORRENCIAS",
        ID=f"SISCOAF{datetime.today().strftime('%d%m%Y')}"
    )
    
    envolvido_fixo = df.iloc[0]
    
    for _, linha in df.iterrows():
        ocorrencia = ET.SubElement(ocorrencias, "OCORRENCIA")

        ET.SubElement(ocorrencia, "CPFCNPJCom").text = tratar_valor(linha.get("CPFCNPJCom"))
        ET.SubElement(ocorrencia, "NumOcorrencia").text = tratar_valor(linha.get("NumOcorrencia"))
        ET.SubElement(ocorrencia, "DtInicio").text = formatar_data(linha.get("DtInicio"))
        ET.SubElement(ocorrencia, "DtFim").text = formatar_data(linha.get("DtFim"))
        ET.SubElement(ocorrencia, "AgNum").text = tratar_valor(linha.get("AgNum"))
        ET.SubElement(ocorrencia, "AgNome").text = tratar_valor(linha.get("AgNome"))
        ET.SubElement(ocorrencia, "AgMun").text = tratar_valor(linha.get("AgMun"))
        ET.SubElement(ocorrencia, "AgUF").text = tratar_valor(linha.get("AgUF"))
        ET.SubElement(ocorrencia, "VlCred").text = tratar_valor(linha.get("VlCred"))
        ET.SubElement(ocorrencia, "VlDeb").text = tratar_valor(linha.get("VlDeb"))
        ET.SubElement(ocorrencia, "VlProv").text = tratar_valor(linha.get("VlProv"))
        ET.SubElement(ocorrencia, "VlProp").text = tratar_valor(linha.get("VlProp"))
        ET.SubElement(ocorrencia, "Det").text = tratar_valor(linha.get("Det"))

        enquadramentos = ET.SubElement(ocorrencia, "ENQUADRAMENTOS")
        codigos_enquadramento = tratar_valor(linha.get("CodEnq", "1012")).split(',')
        for codigo in codigos_enquadramento:
            ET.SubElement(enquadramentos, "CodEnq").text = codigo.strip()

        envolvidos = ET.SubElement(ocorrencia, "ENVOLVIDOS")
        
        envolvido = ET.SubElement(envolvidos, "ENVOLVIDO")
        ET.SubElement(envolvido, "CPFCNPJEnv").text = tratar_valor(envolvido_fixo.get("CPFCNPJEnv")).zfill(11)
        ET.SubElement(envolvido, "NmEnv").text = tratar_valor(envolvido_fixo.get("NmEnv"))
        ET.SubElement(envolvido, "TpEnv").text = tratar_valor(envolvido_fixo.get("TpEnv"))
        ET.SubElement(envolvido, "AgNumEnv").text = str(tratar_valor(envolvido_fixo.get("AgNumEnv")))
        ET.SubElement(envolvido, "AgNomeEnv").text = str(tratar_valor(envolvido_fixo.get("AgNomeEnv")))
        ET.SubElement(envolvido, "NumConta").text = str(tratar_valor(envolvido_fixo.get("NumConta")))
        ET.SubElement(envolvido, "DtAbConta").text = formatar_data(envolvido_fixo.get("DtAbConta"))
        ET.SubElement(envolvido, "DtAtuaCad").text = formatar_data(envolvido_fixo.get("DtAtuaCad"))
        ET.SubElement(envolvido, "PObrigada").text = tratar_valor(envolvido_fixo.get("PObrigada"))
        ET.SubElement(envolvido, "PEP").text = tratar_valor(envolvido_fixo.get("PEP"))
        ET.SubElement(envolvido, "ServPub").text = tratar_valor(envolvido_fixo.get("ServPub"))
        
        envolvido = ET.SubElement(envolvidos, "ENVOLVIDO")
        ET.SubElement(envolvido, "CPFCNPJEnv").text = tratar_valor(linha.get("CPFCNPJEnv")).zfill(11)
        ET.SubElement(envolvido, "NmEnv").text = tratar_valor(linha.get("NmEnv"))
        ET.SubElement(envolvido, "TpEnv").text = tratar_valor(linha.get("TpEnv"))
        ET.SubElement(envolvido, "AgNumEnv").text = str(tratar_valor(linha.get("AgNumEnv")))
        ET.SubElement(envolvido, "AgNomeEnv").text = str(tratar_valor(linha.get("AgNomeEnv")))
        ET.SubElement(envolvido, "NumConta").text = str(tratar_valor(linha.get("NumConta")))
        ET.SubElement(envolvido, "DtAbConta").text = formatar_data(linha.get("DtAbConta"))
        ET.SubElement(envolvido, "DtAtuaCad").text = formatar_data(linha.get("DtAtuaCad"))
        ET.SubElement(envolvido, "PObrigada").text = tratar_valor(linha.get("PObrigada"))
        ET.SubElement(envolvido, "PEP").text = tratar_valor(linha.get("PEP"))
        ET.SubElement(envolvido, "ServPub").text = tratar_valor(linha.get("ServPub"))

    xml_bytes = ET.tostring(
        lote,
        encoding="iso-8859-1",
        xml_declaration=True,
        short_empty_elements=True 
    )

    xml_str = xml_bytes.decode("iso-8859-1")

    with open(nome_arquivo_xml, "w", encoding="iso-8859-1") as f:
        f.write(xml_str)

    print(f"Arquivo XML '{nome_arquivo_xml}' gerado com sucesso!")

if __name__ == "__main__":
    pasta_arquivos = r"pasta arquivo excel"
    arquivos_excel = glob.glob(os.path.join(pasta_arquivos, "*.xlsx"))

    for arquivo in arquivos_excel:
        nome_arquivo_xml = os.path.splitext(arquivo)[0] + ".xml"
        gerar_xml_siscoaf(arquivo, nome_arquivo_xml)
