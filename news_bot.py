import os
import requests
import xml.etree.ElementTree as ET
from groq import Groq
from datetime import datetime

# Configuration
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
GROQ_KEY = os.environ["GROQ_KEY"]

# Date formatée lisible
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
Tu es un journaliste pédagogique spécialisé dans l’apprentissage du monde à travers les actualités.

OBJECTIF :
Transformer les Google News du jour en un flux d’actualités simple, clair et compréhensible, puis enseigner les concepts importants en bas pour permettre à l’utilisateur d’apprendre progressivement la politique, la géopolitique et l’économie.

DATE :
{date_complete}

RÈGLES IMPORTANTES :
- Aucun Markdown (interdiction totale de *, #, soulignements, code)
- Style Telegram lisible (mobile)
- News simples avec vocabulaire normal
- Explications détaillées uniquement en bas
- Emojis légers uniquement pour guider la lecture
- Focus international + un peu France

--------------------------------------------
FORMAT DES NEWS (PARTIE 1)
--------------------------------------------

Chaque news doit être un bloc :

🧠 TITRE (court et clair, 6 à 12 mots)

📌 Ce qui se passe :
Explication simple, 2 à 3 phrases max, vocabulaire normal

🔎 Détail intéressant :
Un élément concret :
- chiffre
- acteur
- décision politique
- conséquence réelle
1 à 2 phrases max

🌍 Pourquoi c’est important :
1 phrase simple

--------------------------------------------
SECTION FINALE OBLIGATOIRE
--------------------------------------------

🧭 APPRENDRE LE MONDE (EXPLICATION SIMPLE)

Ici tu expliques TOUT ce qui est nécessaire pour comprendre les news du jour.

IMPORTANT :
- expliquer comme à un débutant total
- langage très simple
- 1 à 4 lignes max par concept

Tu dois inclure uniquement les concepts présents dans les news du jour.

STRUCTURE :

🏛 POLITIQUE (EXPLICATION DE BASE)

- Parlement :
explique simplement ce que c’est et ce qu’il fait (vote des lois, contrôle du gouvernement)

- Gouvernement :
explique qu’il exécute les décisions et dirige le pays

- Président :
explique son rôle (chef de l’État, représentation, décisions importantes selon pays)

- Premier ministre :
explique qu’il dirige l’action du gouvernement

- Démocratie :
explique que le peuple vote pour choisir ses dirigeants

🌍 ORGANISATIONS INTERNATIONALES

- ONU :
ce que c’est et son rôle dans le monde

- OTAN :
ce que c’est et son rôle militaire

- Union européenne :
ce que c’est et pourquoi les pays travaillent ensemble

💰 ÉCONOMIE (SI PRÉSENT DANS LES NEWS)

- inflation :
augmentation générale des prix

- taux d’intérêt :
coût de l’argent

- PIB :
richesse d’un pays

--------------------------------------------
💡 IDÉE D’INVESTISSEMENT DU JOUR
--------------------------------------------

Une seule idée basée sur les news du jour.

Doit inclure :
- lien avec actualité
- opportunité
- risques
- explication simple

Pas un conseil financier.

--------------------------------------------
₿ CRYPTO DU JOUR
--------------------------------------------

- Bitcoin
- Ethereum
- tendances crypto

Explique :
- mouvements récents
- raisons
- événements importants (ETF, régulation, institutions)

--------------------------------------------
📊 SYNTHÈSE FINALE (MAX 5 LIGNES)
--------------------------------------------

Résumé global du jour
Tendance du monde
Situation générale simple

STYLE GLOBAL :
- très pédagogique
- fluide
- simple
- visuel
- progression d’apprentissage
- parfait pour Telegram mobile

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

# Envoi Telegram
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
