import pandas as pd
import os
import glob
import warnings
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime, timedelta
import time
import shutil


lastDate = (datetime.today() - timedelta(days=1)).replace(hour=0, minute=0, second=0).strftime('%Y-%m-%d')

warnings.simplefilter(action='ignore', category=pd.errors.DtypeWarning)
warnings.simplefilter(action='ignore', category=FutureWarning)


class CustomFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        super().__init__("%(asctime)s - %(name)s -- [%(levelname)s] >> %(message)s", "%Y-%m-%d %H:%M:%S", *args, **kwargs)

LOGGER = logging.getLogger("Conciliador")
handler = logging.StreamHandler()
handler.setFormatter(CustomFormatter())
LOGGER.addHandler(handler)
LOGGER.setLevel(logging.INFO)

slack_token = 'xoxb-token do seu bot/app do slack'
channel_id = 'id do canal que bot/app irá mandar a msg'
client = WebClient(token=slack_token)
user_id = 'user a ser mencionado na msg'
user_id2 = 'user2 a ser mencionado na msg'

diretorios = {
    'sistema': "local que contem os csv",
    'banco': "local que contem os csv"
    #Pode ter mais de um diretorio, basta adicionar na concatencaçao a abaixo
}

LOGGER.info("Iniciando processamento...")

def carregar_e_processar(diretorio, origem, sep=',', encoding='utf-8'):
    dfs = []
    for caminho in glob.glob(os.path.join(diretorio, '*.csv')):
        nome_arquivo = os.path.basename(caminho)
        LOGGER.info(f"Processando arquivo: {nome_arquivo}")
        df = pd.read_csv(caminho, sep=sep, encoding=encoding, dtype={'DADOS1': str, 'DADOS2': str, 'DADOS3': str, 'DADOS4': str, 'DADOS4': str})
        df['Origem'] = origem 
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

def formatar_data(df, coluna):
    df[coluna] = pd.to_datetime(df[coluna]).dt.strftime('%d/%m/%Y %H:%M:%S')
    return df

df_sistema = carregar_e_processar(diretorios['sistema'], 'sistema', sep=';', encoding='latin1')
df_banco = carregar_e_processar(diretorios['banco'], 'banco', sep=';', encoding='latin1')

LOGGER.info("Arquivos processados")

df_sistema = df_sistema.rename(columns={'de':'para',
                                        'ajustar':'nome de colunas'})
df_sistema = df_sistema[~df_sistema['coluna1'].isin(['filtro1'])]

df_banco = df_banco.rename(columns={'de':'para',
                                    'ajustar':'nome de colunas'
})
df_banco = df_banco[~df_banco['coluna2'].isin([('filtro2')])]

LOGGER.info("Dataframes padronizados...")

colunas_selecionadas = ['lista para seleçao de colunas desejadas para menor consumo de memoria']
origens = ['banco']

dfs_sistemas = []
for df, origem in zip([df_banco], origens):
    df['Origem'] = origem
    for coluna in colunas_selecionadas:
        if coluna not in df.columns:
            df[coluna] = pd.NA
    dfs_sistemas.append(df[colunas_selecionadas])

df_bancos = pd.concat(dfs_sistemas, ignore_index=True)
dfs_sistemas = pd.concat([df_sistema], ignore_index=True)

#conversao de valores formato string para float (1.000,00~1000.00)
dfs_sistemas['Valor_'] = dfs_sistemas['Valor_'].str.replace('.', '').str.replace(',', '.').astype(float)
df_bancos['Valor'] = df_bancos['Valor'].str.replace('.', '').str.replace(',', '.').astype(float)

LOGGER.info('DFs concatenados')

LOGGER.info("Conciliando...")

conciliados = pd.merge(dfs_sistemas, df_bancos, on='EndToEnd ID', how='inner')
divergentes_sistema = pd.merge(dfs_sistemas, df_bancos, on='EndToEnd ID', how='outer', indicator=True).loc[lambda x: x['_merge'] == 'left_only']
divergentes_sistema = pd.merge(dfs_sistemas, df_bancos, on='EndToEnd ID', how='outer', indicator=True).loc[lambda x: x['_merge'] == 'right_only']

LOGGER.info("Tratando dados...")

#conversao para padrao BR para arquivos exportados
def formatar_valor(valor):
    if pd.notna(valor):
        return f"{valor:.2f}".replace('.', ',')
    return valor

LOGGER.info("Salvando relatórios...")

divergentes_sistema.drop(columns=['_merge'])[[ 
     'colunas desejadas'
]].to_csv(f'\\caminhos1\\pendencias_sistema_{lastDate}.csv', index=False, sep=';', decimal=',')

divergentes_sistema.drop(columns=['_merge'])[[ 
    'colunas desejadas'
]].to_csv(f'.\\caminhos2\\pendencias_banco_{lastDate}.csv', index=False, sep=';', decimal=',')

conciliados[['colunas desejadas']].to_csv(f'\\caminhos3\\conciliados_{lastDate}.csv', index=False, sep=';', decimal=',')


# resumo a ser mandado no canal do slack para report
total_divergentes_sistema = divergentes_sistema['Valor_'].sum()
total_divergentes_sistema = divergentes_sistema['Valor'].sum()

count_conciliados = conciliados.shape[0]
count_divergentes_sistema = divergentes_sistema.shape[0]
count_divergentes_sistema = divergentes_sistema.shape[0]

def enviar_arquivo_slack(caminho_arquivo):
    try:
        response = client.files_upload_v2(
            channel=channel_id,
            file=caminho_arquivo,
            title=os.path.basename(caminho_arquivo)
        )
        LOGGER.info(f"Arquivo enviado ao Slack com sucesso!")
    except SlackApiError as e:
        LOGGER.error(f"Erro ao enviar arquivo ao Slack: {e.response['error']}")

def post_to_slack():
    message = (
        f"Total de transações conciliadas: {count_conciliados}\n"
        f"Transações presentes no sistema e não no banco: {count_divergentes_sistema}        Total de R$: {formatar_valor(total_divergentes_sistema)}\n"
        f"Transações presentes no banco e não no sistema: {count_divergentes_sistema}       Total de R$: {formatar_valor(total_divergentes_sistema)}"
    )
    try:
        response = client.chat_postMessage(channel=channel_id, text=message)
        LOGGER.info("Mensagem enviada ao Slack com sucesso")
    except SlackApiError as e:
        LOGGER.error(f"Erro ao enviar mensagem ao Slack: {e.response['error']}")

def bank_report():
    message = (f"<@{user_id}> msg1\n"
               f"<@{user_id2}> msg2." )
    try:
        response = client.chat_postMessage(channel=channel_id, text=message)
        LOGGER.info("msg3")
    except SlackApiError as e:
        LOGGER.error(f"Erro ao enviar mensagem ao Slack: {e.response['error']}")  

kek1 = f'.\\caminhos1\\pendencias_banco_{lastDate}.csv'
kek2 = f'.\\caminhos2\\pendencias_sistema_{lastDate}.csv'


post_to_slack()
enviar_arquivo_slack(kek1)
enviar_arquivo_slack(kek2)

bank_report()

LOGGER.info("Processo finalizado!")
