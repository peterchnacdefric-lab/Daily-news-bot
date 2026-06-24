import os
import requests
import xml.etree.ElementTree as ET
from groq import Groq
from datetime import datetime

# Configuration
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
GROQ_KEY = os.environ["GROQ_KEY"]

# Date du jour
aujourd_hui = datetime.now().strftime("%d/%m/%Y")

# Récupère les news Google
url = "https://news.google.com/rss?hl=fr&gl=FR&ceid=FR:fr"
response = requests.get(url)
root = ET.fromstring(response.content)

articles = []
for item in root.findall(".//item")[:20]:
    titre = item.find("title").text
    articles.append(titre)

texte_brut = "\n".join(articles)

# PROMPT
prompt = f"""
Tu es un analyste de presse et vulgarisateur.

Tu transformes les informations de Google News du jour en un briefing quotidien clair, visuel et facile à lire, comme si tu expliquais à une personne de 10 ans mais avec une analyse intelligente d’adulte.

Le résultat doit ressembler à un fil d’actualités simple et fluide.

RÈGLES IMPORTANTES :
- Utilise des gros titres clairs pour chaque news
- Mélange actualités internationales, France, Espagne et Europe selon l’importance
- Pas de sections fixes obligatoires
- Pas de structure rigide
- Juste des titres + explications
- Emojis autorisés mais légers et uniquement pour améliorer la lecture
- Style adapté Telegram (lecture rapide, mobile)
- Pas de symboles techniques visibles (pas d’astérisques, pas de hashtags, pas de Markdown)

FORMAT POUR CHAQUE ACTUALITÉ :

GROS TITRE (court et clair avec éventuellement un emoji)
Explication simple en 2 à 4 phrases maximum
Pourquoi c’est important en 1 phrase

Puis si un mot complexe apparaît :

TU DOIS COMPRENDRE :
Explique simplement les mots importants comme OTAN ONU BCE Fed inflation taux d’intérêt PIB récession etc
Chaque explication doit être très courte 1 à 3 lignes maximum comme pour un enfant de 10 ans

Ensuite, dans tout le flux des news :

IDÉE D’INVESTISSEMENT DU JOUR :
Propose une seule idée basée uniquement sur les actualités du jour
Cela peut être une entreprise un secteur ou une tendance économique
Explique :
- pourquoi c’est lié aux news
- pourquoi c’est intéressant
- quels sont les risques
Précise que ce n’est PAS un conseil financier mais une analyse éducative

CRYPTO DU JOUR :
Résume Bitcoin Ethereum et les principales cryptos
Explique :
- tendance générale du marché
- événements importants (ETF régulation adoption institutions hacks)
- causes des mouvements

SYNTHÈSE FINALE :
5 lignes maximum
Résumé de la journée
Tendance globale du monde
Conclusion simple et claire

STYLE GLOBAL :
- Très clair
- Phrases courtes
- Accessible
- Pédagogique
- Fluide comme un journal moderne
- Optimisé pour lecture Telegram sur mobile

Voici les actualités du jour :
{texte_brut}
"""

# Résumé via Groq
client = Groq(api_key=GROQ_KEY)
completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ],
    max_tokens=4000
)

resume = completion.choices[0].message.content

# Envoi Telegram (sans Markdown pour éviter bugs)
def envoyer_message(texte):
    for i in range(0, len(texte), 4000):
        morceau = texte[i:i+4000]
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": morceau
            }
        )

envoyer_message(f"🗞 Actualités du {aujourd_hui}\n\n{resume}")
