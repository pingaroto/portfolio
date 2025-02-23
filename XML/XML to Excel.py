import xml.etree.ElementTree as ET
import os
import pandas as pd

def buscar_arquivos_xml(diretorio):
    arquivos_xml = []
    for arquivo in os.listdir(diretorio):
        if arquivo.endswith(".xml"):
            arquivos_xml.append(os.path.join(diretorio, arquivo))
    return arquivos_xml

def parse_nfe(xml_file):

    tree = ET.parse(xml_file)
    root = tree.getroot()

    namespaces = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

    def buscar_valor(caminho, ns):
        elemento = root.find(caminho, ns)
        return elemento.text if elemento is not None else ''

    numero_nfe = buscar_valor('.//nfe:ide/nfe:nNF', namespaces)
    cnpj_emitente = buscar_valor('.//nfe:emit/nfe:CNPJ', namespaces)
    nome_emitente = buscar_valor('.//nfe:emit/nfe:xNome', namespaces)
    nome_fantasia_emitente = buscar_valor('.//nfe:emit/nfe:xFant', namespaces)
    uf_emitente = buscar_valor('.//nfe:emit/nfe:enderEmit/nfe:UF', namespaces)
    data_nf = buscar_valor('.//nfe:ide/nfe:dhEmi', namespaces)

    nfe_data = []

    for item in root.findall('.//nfe:det', namespaces):
        n_item = item.get('nItem')
        if n_item:
            item_data = {
                'Numero_NF': numero_nfe,
                'Data': data_nf, 
                'CNPJ_Emitente': cnpj_emitente,
                'Nome_Emitente': nome_emitente,
                'Nome_Fantasia_Emitente': nome_fantasia_emitente,
                'UF_Emitente': uf_emitente,
                'Codigo_Produto': buscar_valor(f'.//nfe:det[@nItem="{n_item}"]/nfe:prod/nfe:cProd', namespaces),
                'Descricao_Produto': buscar_valor(f'.//nfe:det[@nItem="{n_item}"]/nfe:prod/nfe:xProd', namespaces),
                'NCM': buscar_valor(f'.//nfe:det[@nItem="{n_item}"]/nfe:prod/nfe:NCM', namespaces),
                'CFOP': buscar_valor(f'.//nfe:det[@nItem="{n_item}"]/nfe:prod/nfe:CFOP', namespaces),
                'Quantidade_Produto': buscar_valor(f'.//nfe:det[@nItem="{n_item}"]/nfe:prod/nfe:qCom', namespaces),
                'Valor_Unidade_Produto': buscar_valor(f'.//nfe:det[@nItem="{n_item}"]/nfe:prod/nfe:vUnCom', namespaces),
                'Valor_Total_Produto': buscar_valor(f'.//nfe:det[@nItem="{n_item}"]/nfe:prod/nfe:vProd', namespaces),
                'ICMS_Valor': buscar_valor(f'.//nfe:det[@nItem="{n_item}"]/nfe:imposto/nfe:ICMS/nfe:ICMS00/nfe:vICMS', namespaces),
                'ICMS': buscar_valor(f'.//nfe:det[@nItem="{n_item}"]/nfe:imposto/nfe:ICMS/nfe:ICMS00/nfe:pICMS', namespaces),
                'Frete': buscar_valor('.//nfe:total/nfe:ICMSTot/nfe:vFrete', namespaces),
                'IPI': buscar_valor('.//nfe:total/nfe:ICMSTot/nfe:vIPI', namespaces),
                'Valor_NF': buscar_valor('.//nfe:total/nfe:ICMSTot/nfe:vNF', namespaces)
            }
            nfe_data.append(item_data)
    return nfe_data

def exportar_para_csv(dados, caminho_arquivo_csv):

    df = pd.DataFrame(dados)

    for coluna in ['Valor_Unidade_Produto', 'Valor_Total_Produto', 'ICMS_Valor', 'ICMS', 'Frete', 'IPI', 'Valor_NF', 'Quantidade_Produto']:
        df[coluna] = df[coluna].apply(lambda x: str(x).replace('.', ','))

    df.to_csv(caminho_arquivo_csv, index=False, sep=';', decimal=',', encoding='utf-8')
    print(f"Dados exportados para {caminho_arquivo_csv}")

def processar_arquivos_xml(pasta_entrada, pasta_saida):
    arquivos_xml = buscar_arquivos_xml(pasta_entrada)

    todas_as_nfes = []

    for arquivo in arquivos_xml:

        dados_nfe = parse_nfe(arquivo)
        todas_as_nfes.extend(dados_nfe)

    caminho_arquivo_csv = os.path.join(pasta_saida, "nfe_data.csv")

    exportar_para_csv(todas_as_nfes, caminho_arquivo_csv)
    print(f"Dados exportados para {caminho_arquivo_csv}")

pasta_entrada = r'pasta entrada'
pasta_saida = r"pasta saida"

processar_arquivos_xml(pasta_entrada, pasta_saida)
