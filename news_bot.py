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

# Récupération Google News
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
Tu es un analyste de presse moderne spécialisé dans les formats Telegram.

Tu transformes les Google News du jour en un flux d’actualités VISUEL, VARIÉ et FACILE À LIRE.

OBJECTIF :
Créer un fil d’info comme une application news moderne sur mobile.

RÈGLES ABSOLUES :
- INTERDICTION de Markdown (aucun *, aucun #, aucun __, aucun code)
- INTERDICTION de longs paragraphes
- INTERDICTION de style article classique monotone
- Texte directement lisible sur Telegram
- Emojis OBLIGATOIRES mais légers et variés (pas répétitifs)

FORMAT OBLIGATOIRE :
Chaque news doit être un BLOC INDÉPENDANT.

STRUCTURE DE CHAQUE BLOC :

🧠 TITRE COURT (impactant, 6 à 12 mots max)

Ensuite 3 mini lignes maximum :

1) Ce qui se passe :
Explication simple mais pas trop courte (2-3 phrases max)

2) Détail intéressant :
Ajoute un élément concret ou contextuel :
- chiffre
- acteur impliqué
- enjeu caché
- conséquence directe
(1 à 2 phrases max)

3) Pourquoi c’est important :
1 phrase simple

VARIATION OBLIGATOIRE :
- Certaines news peuvent être économiques
- D’autres politiques
- D’autres géopolitiques
- D’autres tech
- Mélange naturel, pas de structure fixe visible

SECTION TERMINALE DANS LE FLUX (PAS À PART) :

💡 IDÉE D’INVESTISSEMENT DU JOUR

Une seule idée basée sur les news du jour.
Peut être entreprise secteur ou tendance.

Tu dois inclure :
- lien direct avec l’actualité
- explication simple
- opportunité
- risques

Pas de conseil financier.

₿ CRYPTO DU JOUR

- Bitcoin
- Ethereum
- tendances globales crypto

Explique simplement :
- pourquoi ça bouge
- événements (ETF régulation institutions hacks adoption)

FIN :

📊 SYNTHÈSE FINALE (MAX 5 LIGNES)

Résumé global du jour
Tendance du monde (incertitude croissance tension etc)

STYLE OBLIGATOIRE :
- très visuel
- très fluide
- varié
- naturel
- comme un feed news moderne
- accessible comme si on expliquait à un jeune de 10 ans + analyse adulte légère

Voici les actualités du jour :
{texte_brut}
"""

# Appel IA
client = Groq(api_key=GROQ_KEY)
completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=4000
)

resume = completion.choices[0].message.content

# Envoi Telegram (SANS Markdown pour éviter les astérisques)
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
