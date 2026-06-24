import os
import requests
import xml.etree.ElementTree as ET
from groq import Groq
from datetime import datetime

# Configuration
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
GROQ_KEY = os.environ["GROQ_KEY"]

# Date format fixe
now = datetime.now()
date_complete = now.strftime("%A %d %B %Y")

# Google News RSS
url = "https://news.google.com/rss?hl=fr&gl=FR&ceid=FR:fr"
response = requests.get(url)
root = ET.fromstring(response.content)

articles = []
for item in root.findall(".//item")[:25]:
    titre = item.find("title").text
    articles.append(titre)

texte_brut = "\n".join(articles)

# PROMPT
prompt = f"""
Tu es un journaliste analyste pédagogique spécialisé dans l’explication du monde moderne à travers les actualités.

OBJECTIF :
Créer un flux quotidien Telegram très lisible, varié, éducatif et structuré, permettant à l’utilisateur de comprendre ET apprendre progressivement le monde.

DATE OBLIGATOIRE EN PREMIÈRE LIGNE :
{date_complete}

RÈGLES IMPORTANTES :
- Aucun Markdown (interdiction stricte de *, #, code, soulignement)
- Style Telegram mobile fluide
- Beaucoup de variété dans les titres
- Chaque titre DOIT avoir un emoji différent et pertinent
- Mélange international, Europe, France, économie, tech, géopolitique
- Pas de répétition de structure mécanique

--------------------------------------------
STRUCTURE DES NEWS
--------------------------------------------

Chaque news doit être un bloc indépendant avec :

🎯 TITRE AVEC EMOJI (obligatoire, différent à chaque fois, adapté au sujet)

📌 Ce qui se passe :
5 à 8 lignes maximum
- explication claire
- vocabulaire simple mais pas simplifié à l’extrême
- contexte important inclus naturellement

🧠 COMPRENDRE LE CONTEXTE ET LES TERMES :
- explication intégrée dans le texte (pas de bloc séparé)
- expliquer les institutions, acteurs, concepts si présents
- ajouter du contexte géopolitique ou économique
- donner du sens global (pourquoi ça existe, comment ça fonctionne)
- style pédagogique naturel, comme un professeur dans une conversation

🔮 PROJECTION :
- ce qui peut se passer ensuite
- scénarios possibles
- tensions ou opportunités futures
- conséquences concrètes
2 à 4 phrases max

IMPORTANT :
- ne pas répéter les mêmes types de titres
- varier fortement les sujets et les angles
- chaque news doit être unique dans sa construction

--------------------------------------------
💰 INVESTISSEMENT DU JOUR (FIN DU RAPPORT)
--------------------------------------------

- 1 entreprise concrète uniquement
- liée directement à une ou plusieurs actualités du jour
- explication simple :
  pourquoi elle est impactée
  opportunité potentielle
  risques

Pas un conseil financier, analyse éducative.

--------------------------------------------
₿ CRYPTO DU JOUR
--------------------------------------------

- Bitcoin
- Ethereum
- marché crypto global

Inclure :
- tendances du jour
- raisons des mouvements
- événements importants (ETF, régulation, adoption, institutions, hacks)

--------------------------------------------
📊 SYNTHÈSE FINALE (MAX 5 LIGNES)
--------------------------------------------

- résumé global du jour
- tendances mondiales
- lecture simple de la situation

--------------------------------------------
STYLE GLOBAL :
- très visuel
- très varié
- pédagogique progressif
- compréhension + apprentissage intégré
- fluide pour Telegram mobile
- aucune structure répétitive visible
- chaque news doit sembler unique

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

# Telegram send
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
