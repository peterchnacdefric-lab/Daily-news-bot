import os
import requests
import xml.etree.ElementTree as ET
from groq import Groq
from datetime import datetime

# CONFIG
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
GROQ_KEY = os.environ["GROQ_KEY"]

# DATE
now = datetime.now()
date_complete = now.strftime("%A %d %B %Y")

# GOOGLE NEWS
url = "https://news.google.com/rss?hl=fr&gl=FR&ceid=FR:fr"
response = requests.get(url)
root = ET.fromstring(response.content)

articles = []
for item in root.findall(".//item")[:30]:
    titre = item.find("title").text
    articles.append(titre)

texte_brut = "\n".join(articles)

# PROMPT
prompt = f"""
Tu es un journaliste analyste pédagogique expert en vulgarisation du monde moderne.

OBJECTIF :
Créer un briefing quotidien Telegram structuré, éducatif et visuel permettant de comprendre l’actualité ET d’apprendre le contexte du monde.

DATE OBLIGATOIRE EN PREMIÈRE LIGNE :
{date_complete}

RÈGLES IMPORTANTES :
- Aucun Markdown (interdiction stricte de *, #, code)
- Style Telegram lisible
- EXACTEMENT environ 10 NEWS distinctes
- Chaque news doit avoir un emoji différent dans le titre
- News variées : géopolitique, économie, tech, société, international
- Aucun format répétitif

--------------------------------------------
FORMAT DES NEWS (x10 environ)
--------------------------------------------

Pour chaque news :

🎯 TITRE AVEC EMOJI (unique et adapté)

📌 Ce qui se passe :
5 à 8 lignes max
- explication claire
- contexte nécessaire
- vocabulaire simple mais sérieux
- style journal moderne

🔮 Projection :
- évolution possible
- risques ou opportunités
- scénario futur probable
2 à 4 phrases max

IMPORTANT :
- chaque news doit être différente dans son angle et style
- éviter répétition des sujets similaires
- varier fortement les thématiques

--------------------------------------------
🧠 APPRENDRE LE MONDE (SECTION ÉTENDUE)
--------------------------------------------

Cette section doit expliquer en profondeur le contexte global des news du jour.

RÈGLES :
- minimum 10 lignes
- utiliser des paragraphes séparés (sauts de ligne obligatoires)
- explication progressive et pédagogique
- langage simple mais riche en compréhension
- uniquement les concepts présents dans les news du jour

CONTENU OBLIGATOIRE :

Tu dois expliquer :

- Comment fonctionne un gouvernement dans les pays mentionnés
- Pourquoi les décisions politiques influencent les marchés et les conflits
- Comment les organisations internationales influencent les décisions (ONU, OTAN, UE etc)
- Comment l’économie mondiale réagit aux tensions ou décisions politiques
- Pourquoi les médias suivent certains événements plutôt que d’autres
- Comment les conflits géopolitiques se forment et évoluent
- Pourquoi les marchés financiers réagissent aux actualités
- Comment les relations entre pays influencent la stabilité mondiale

FORMAT :
- texte fluide
- plusieurs paragraphes séparés par des lignes vides
- style professeur qui explique calmement
- compréhension progressive
- très pédagogique

--------------------------------------------
💰 INVESTISSEMENT DU JOUR
--------------------------------------------

- 1 entreprise concrète uniquement
- liée directement aux news du jour
- explication simple :
  pourquoi elle est impactée
  opportunité
  risques

Pas de conseil financier.

--------------------------------------------
₿ CRYPTO DU JOUR
--------------------------------------------

- Bitcoin
- Ethereum
- tendances globales

Inclure :
- mouvements récents
- raisons
- événements (ETF, régulation, institutions, adoption)

--------------------------------------------
📊 SYNTHÈSE FINALE (MAX 5 LIGNES)
--------------------------------------------

- résumé global du jour
- tendance mondiale
- lecture simple de la situation

--------------------------------------------
STYLE GLOBAL :
- très visuel
- très pédagogique
- très structuré mais naturel
- compréhension + apprentissage profond
- adapté Telegram mobile
- chaque news doit être unique

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

# TELEGRAM
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
