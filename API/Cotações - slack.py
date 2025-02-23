import requests
import schedule
import time
import matplotlib.pyplot as plt
from io import BytesIO
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import locale
import numpy as np
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

slack_token = 'xoxb-'
app_token = 'xapp-'
channel_id = ''

app = App(token=slack_token)

class CustomFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        super().__init__("%(asctime)s - %(name)s -- [%(levelname)s] >> %(message)s", "%Y-%m-%d %H:%M:%S", *args, **kwargs)

LOGGER = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(CustomFormatter())
LOGGER.addHandler(handler)
LOGGER.setLevel(logging.INFO)

client = WebClient(token=slack_token)

btc_prices = []
usd_prices = []
eur_prices = []
CHF_prices = []

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

def get_exchange_rates():
    try:
        url = 'https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL,BTC-BRL,CHF-BRL'
        response = requests.get(url)
        data = response.json()

        if 'BTCBRL' in data and 'USDBRL' in data and 'EURBRL' in data:
            btc_to_brl = float(data['BTCBRL']['bid'])
            usd_to_brl = float(data['USDBRL']['bid'])
            eur_to_brl = float(data['EURBRL']['bid'])
            CHF_to_brl = float(data['CHFBRL']['bid'])
        else:
            print("Erro: 'BTCBRL', 'USDBRL' ou 'EURBRL' ou 'CHFBRL' não encontrados na resposta da API.")
            btc_to_brl = None
            usd_to_brl = None
            eur_to_brl = None
            CHF_to_brl = None

        return btc_to_brl, usd_to_brl, eur_to_brl, CHF_to_brl

    except requests.RequestException as e:
        print(f"Erro ao fazer a solicitação da API: {e}")
        return None, None, None

def post_to_slack():

    if len(btc_prices) > 0:
        formatted_btc_to_brl = locale.currency(btc_prices[-1], grouping=True)
        formatted_usd_to_brl = locale.currency(usd_prices[-1], grouping=True)
        formatted_eur_to_brl = locale.currency(eur_prices[-1], grouping=True)
        formatted_CHF_to_brl = locale.currency(CHF_prices[-1], grouping=True)
        message = (
            f"Cotação atual:\n"
            f"Bitcoin para Real: {formatted_btc_to_brl}\n"
            f"Dólar para Real: {formatted_usd_to_brl}\n"
            f"Euro para Real: {formatted_eur_to_brl}\n"
            f"CHF para Real: {formatted_CHF_to_brl}"
        )
    else:
        message = "Não foi possível obter as cotações no momento."

    try:
        response = client.chat_postMessage(
            channel=channel_id,
            text=message
        )
    except SlackApiError as e:
        print(f"Error posting to Slack: {e.response['error']}")

def annotate_min_max(ax, data, label_color):
    min_index = np.argmin(data)
    max_index = np.argmax(data)
    min_val = locale.currency(data[min_index], grouping=True)
    max_val = locale.currency(data[max_index], grouping=True)
    ax.annotate(f'Mín: {min_val}', xy=(min_index, data[min_index]), xytext=(min_index, data[min_index] - 10),
                arrowprops=dict(facecolor=label_color, shrink=0.05), fontsize=8, color=label_color)
    ax.annotate(f'Máx: {max_val}', xy=(max_index, data[max_index]), xytext=(max_index, data[max_index] + 10),
                arrowprops=dict(facecolor=label_color, shrink=0.05), fontsize=8, color=label_color)

def generate_and_post_graph():

    if len(btc_prices) > 0:

        fig, ax1 = plt.subplots(figsize=(10, 5))
        ax1.plot(btc_prices, label='Bitcoin (BRL)', color='tab:blue')
        ax1.set_xlabel('Tempo (minutos)')
        ax1.set_ylabel('Bitcoin (BRL)', color='tab:blue')
        ax1.tick_params(axis='y', labelcolor='tab:blue')
        annotate_min_max(ax1, btc_prices, 'tab:blue')

        fig.tight_layout() 
        plt.title('Gráfico BitCoin')

        buf = BytesIO()
        plt.grid(True, linestyle =':', linewidth=0.5)
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()

        try:

            response = client.files_upload_v2(
                channel=channel_id,
                file=buf,
                filename='currency_variation.png',
                title='Variação do preço das moedas na última hora'
            )

            post_to_slack()
        except SlackApiError as e:
            print(f"Error posting graph to Slack: {e.response['error']}")

def collect_and_post_data():

    btc_to_brl, usd_to_brl, eur_to_brl, CHF_to_brl = get_exchange_rates()
    if btc_to_brl is not None and usd_to_brl is not None and eur_to_brl is not None and CHF_to_brl is not None:
        btc_prices.append(btc_to_brl)
        usd_prices.append(usd_to_brl)
        eur_prices.append(eur_to_brl)
        CHF_prices.append(CHF_to_brl)

        LOGGER.info(f"BTC: {btc_to_brl:.2f} BRL, USD: {usd_to_brl:.2f} BRL, EUR: {eur_to_brl:.2f} BRL, CHF: {CHF_to_brl:.2f}")

schedule.every(1).minutes.do(collect_and_post_data)

@app.event("app_mention")
def handle_app_mention_events(body, say, logger):
    event = body.get("event", {})
    text = event.get("text", "").lower()

    if "dale" in text:
        print("Mensagem 'dale' recebida!")
        say("Dale! Enviando o gráfico da última hora.")
        generate_and_post_graph()

if __name__ == "__main__":
    handler = SocketModeHandler(app, app_token)
    
    import threading
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()
    
    handler.start()
