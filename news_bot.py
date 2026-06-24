import os
import requests
import xml.etree.ElementTree as ET
from groq import Groq
from datetime import datetime

# Configuration
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
GROQ_KEY = os.environ["GROQ_KEY"]

# Date stable et identique tous les jours
now = datetime.now()
date_complete = now.strftime("%A %d %B %Y")

# Google News RSS
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
Tu es un journaliste pédagogique et analyste géopolitique.

OBJECTIF :
Transformer les Google News du jour en un flux d’actualités clair, visuel et éducatif, avec analyse et projection future.

DATE (OBLIGATOIRE EN PREMIÈRE LIGNE DU RÉSULTAT) :
Journal du jour — {date_complete}

RÈGLES IMPORTANTES :
- Aucun Markdown (interdiction totale de *, #, soulignements, code)
- Style Telegram lisible
- Vocabulaire simple dans les news
- Analyse plus profonde uniquement dans les sections finales
- Emojis légers uniquement pour structurer
- Focus international + un peu France

--------------------------------------------
FORMAT DES NEWS
--------------------------------------------

Chaque news doit être un bloc :

🧠 TITRE (court, clair, 6 à 12 mots)

📌 Ce qui se passe :
Explication simple, 2 à 3 phrases max

🔎 Détail intéressant :
Un élément concret :
- chiffre
- acteur
- décision
- contexte important
1 à 2 phrases max

🌍 Pourquoi c’est important :
1 phrase simple

🔮 Projection / futur possible :
Explique ce qui pourrait arriver ensuite :
- scénario probable si ça continue
- conséquences possibles
- risques ou tensions futures
2 à 4 phrases max

--------------------------------------------
SECTION APPRENTISSAGE
--------------------------------------------

🧭 APPRENDRE LE MONDE (EXPLICATION SIMPLE)

Tu expliques les notions présentes dans les news.

RÈGLES :
- très simple (niveau débutant)
- 1 à 4 lignes max par concept
- uniquement ce qui apparaît dans les news

STRUCTURE :

🏛 POLITIQUE :
Parlement :
ce que c’est et son rôle

Gouvernement :
ce que c’est et son rôle

Président :
rôle selon les pays

Premier ministre :
fonction principale

Démocratie :
définition simple

🌍 ORGANISATIONS :
ONU :
rôle international

OTAN :
rôle militaire

Union européenne :
coopération des pays

💰 ÉCONOMIE :
Inflation :
explication simple

Taux d’intérêt :
explication simple

PIB :
explication simple

--------------------------------------------
💡 IDÉE D’INVESTISSEMENT DU JOUR
--------------------------------------------

Une seule idée basée sur les news du jour.

Inclure :
- lien avec l’actualité
- opportunité
- risques
- explication simple

Pas un conseil financier.

--------------------------------------------
₿ CRYPTO DU JOUR
--------------------------------------------

- Bitcoin
- Ethereum
- tendances générales

Inclure :
- mouvements récents
- raisons
- événements (ETF régulation institutions adoption hacks)

--------------------------------------------
📊 SYNTHÈSE FINALE (MAX 5 LIGNES)
--------------------------------------------

Résumé global du jour
Tendance mondiale
Lecture simple de la situation

STYLE GLOBAL :
- pédagogique
- fluide
- visuel
- progression d’apprentissage
- clair pour Telegram
- cohérent tous les jours

Voici les actualités du jour :
{texte_brut}
"""

# IA
client = Groq(api_key=GROQ_KEY)
completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=4000
)

resume = completion.choices[0].message.content

# Telegram
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

envoyer_message(resume)
