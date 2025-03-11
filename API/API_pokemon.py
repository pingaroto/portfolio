import requests
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

class CustomFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        super().__init__("%(asctime)s - %(name)s -- [%(levelname)s] >> %(message)s", "%Y-%m-%d %H:%M:%S", *args, **kwargs)

LOGGER = logging.getLogger("Pokédex")
handler = logging.StreamHandler()
handler.setFormatter(CustomFormatter())
LOGGER.addHandler(handler)
LOGGER.setLevel(logging.INFO)

slack_token = ''
app_token = ''
channel_id = ''

app = App(token=slack_token)
client = WebClient(token=slack_token)

def get_type_symbol(tipo):
    type_symbols = {
        "Normal": "⚪",
        "Fire": "🔥",
        "Water": "💧",
        "Electric": "⚡",
        "Grass": "🌿",
        "Ice": "❄️",
        "Fighting": "🥊",
        "Poison": "☠️",
        "Ground": "🌍",
        "Flying": "🦅",
        "Psychic": "🔮",
        "Bug": "🐛",
        "Rock": "🪨",
        "Ghost": "👻",
        "Dragon": "🐉",
        "Dark": "🌑",
        "Steel": "🛠️",
        "Fairy": "🧚"
    }
    return type_symbols.get(tipo, "❓")

def post_to_slack(name, id_,image_normal, image_shiny, hp, atk, deff, satk, sdef, spd, tipos):

    tipos_formatados = " ".join([f"{get_type_symbol(t)} {t}" for t in tipos])

    try:
        response = client.chat_postMessage(
            channel=channel_id,
            text=f"Pokédex:\n*{name}* - Número: {id_}",
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"🔍 *Pokédex:* \n Número: `{id_}` - *Nome:* `{name}`"
                    }
                },
                {
                    "type": "image",
                    "image_url": image_normal,
                    "alt_text": f"Imagem normal de {name}"
                },
                {
                    "type": "image",
                    "image_url": image_shiny,
                    "alt_text": f"Imagem shiny de {name}"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*📊 Status:*"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"❤️ *HP:* `{hp}`"},
                        {"type": "mrkdwn", "text": f"⚔️ *Ataque:* `{atk}`"},
                        {"type": "mrkdwn", "text": f"🛡️ *Defesa:* `{deff}`"},
                        {"type": "mrkdwn", "text": f"⚔️✨ *Ataque Especial:* `{satk}`"},
                        {"type": "mrkdwn", "text": f"🛡️✨ *Defesa Especial:* `{sdef}`"},
                        {"type": "mrkdwn", "text": f"🪽 *Velocidade:* `{spd}`"}
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"🔹 *Tipo(s):* `{tipos_formatados}`"
                    }
                }
            ]
        )
    except SlackApiError as e:
        print(f"Error posting to Slack: {e.response['error']}")


def get_info_pkm():
    try:
        pokemon = input("Qual pokémon você quer os detalhes? ").lower()
        url = f'https://pokeapi.co/api/v2/pokemon/{pokemon}'
        
        response = requests.get(url)

        if response.status_code == 200:
            info = response.json()
            forms_url = info["forms"][0]["url"]
            dale = requests.get(forms_url)
            kek = dale.json()
            name = kek["name"].capitalize()
            id_= kek["id"]
            image_normal = kek["sprites"]["front_default"]
            image_shiny = kek["sprites"]["front_shiny"]
            hp = info["stats"][0]['base_stat']
            atk = info["stats"][1]['base_stat']
            deff = info["stats"][2]['base_stat']
            satk = info["stats"][3]['base_stat']
            sdef = info["stats"][4]['base_stat']
            spd = info["stats"][5]['base_stat']
            tipos = [t["type"]["name"].capitalize() for t in info["types"]]

            LOGGER.info(name)
            LOGGER.info("Busca finalizada!")
            
            return name, id_,image_normal, image_shiny, hp, atk, deff, satk, sdef, spd, tipos
        
        else:
            LOGGER.error(f"Erro na request: {response.status_code} - Pokémon não encontrado")

    except requests.exceptions.RequestException as e:
        LOGGER.error(f"Erro ao acessar a API: {e}")
    except KeyError:
        LOGGER.error("Erro ao acessar os dados do Pokémon. Estrutura inesperada da API.")

name, id_,image_normal, image_shiny, hp, atk, deff, satk, sdef, spd, tipos = get_info_pkm()
post_to_slack(name, id_,image_normal, image_shiny, hp, atk, deff, satk, sdef, spd, tipos)
