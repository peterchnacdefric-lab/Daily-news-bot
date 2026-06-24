import os
import requests
import xml.etree.ElementTree as ET
from groq import Groq
from datetime import datetime

# Configuration
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
GROQ_KEY = os.environ["GROQ_KEY"]

# Date format fixe en français
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
Tu es un journaliste analyste et pédagogue spécialisé dans la compréhension du monde réel.

OBJECTIF :
Transformer Google News en un rapport quotidien structuré, fluide et pédagogique adapté à Telegram.

DATE OBLIGATOIRE EN PREMIÈRE LIGNE :
{date_complete}

RÈGLES GÉNÉRALES :
- Aucun Markdown (interdiction totale de *, #, soulignements ou code)
- Format Telegram lisible (mobile)
- Texte fluide, structuré avec titres
- Emojis légers uniquement pour structurer les sections
- Mélange international + France + Europe selon pertinence
- Pas de listes rigides répétitives

--------------------------------------------
STRUCTURE OBLIGATOIRE
--------------------------------------------

Chaque sujet doit être présenté sous forme de TITRE PRINCIPAL (gros titre clair).

Sous chaque titre :

1) EXPLICATION DES FAITS (5 à 10 lignes maximum)
- Explication claire et naturelle
- Style journal simple mais informatif
- Pas de séparation artificielle

2) 🧠 COMPRENDRE LES TERMES IMPORTANTs
- uniquement si des termes techniques apparaissent dans cette news
- expliquer dans le flux directement
- politique, économie, géopolitique, institutions
- explication simple intégrée dans le texte (pas de bloc séparé)
- style pédagogique très simple

3) 🔮 PROJECTION
- ce qui pourrait arriver ensuite
- conséquences possibles
- risques ou évolution probable
- 2 à 4 phrases max

--------------------------------------------
SECTION INVESTISSEMENT (EN FIN DE RAPPORT)
--------------------------------------------

💰 INVESTISSEMENT DU JOUR

- une seule entreprise concrète
- liée directement aux actualités du jour
- explication simple :
  pourquoi cette entreprise est intéressante aujourd’hui
  quelles opportunités
  quels risques

Important :
- ce n’est pas un conseil financier
- analyse éducative

--------------------------------------------
₿ CRYPTO DU JOUR
--------------------------------------------

- Bitcoin
- Ethereum
- marché crypto global

Inclure :
- tendances actuelles
- raisons des mouvements
- événements importants (ETF, régulation, adoption, institutions)

--------------------------------------------
📊 SYNTHÈSE FINALE (MAX 5 LIGNES)
--------------------------------------------

- résumé global du jour
- tendance mondiale
- lecture simple de la situation

--------------------------------------------
STYLE GLOBAL :
- très fluide
- très lisible Telegram
- pédagogique progressif
- pas de répétition
- compréhension + apprentissage intégré dans le flux
- emojis uniquement pour titres et sections (pas dans le texte explicatif)

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
