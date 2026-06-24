import os
import requests
import xml.etree.ElementTree as ET
from groq import Groq
from datetime import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
GROQ_KEY = os.environ["GROQ_KEY"]

# Date
now = datetime.now()
date_complete = now.strftime("%A %d %B %Y")

# Google News RSS (titre + contenu)
url = "https://news.google.com/rss?hl=fr&gl=FR&ceid=FR:fr"
response = requests.get(url)
root = ET.fromstring(response.content)

articles = []
for item in root.findall(".//item")[:25]:
    titre = item.find("title").text
    articles.append(titre)

texte_brut = "\n".join(articles)

# PROMPT FINAL
prompt = f"""
Tu es un journaliste pédagogique et analyste du monde réel.

DATE :
{date_complete}

MISSION :
Transformer les actualités en un rapport clair, éducatif et structuré.

RÈGLES IMPORTANTES :
- INTERDICTION de créer des titres
- Tu DOIS utiliser EXACTEMENT les titres fournis dans les news
- Aucun Markdown
- Style Telegram lisible
- Explications simples mais enrichissantes
- Ajoute de la connaissance nouvelle dans chaque explication (apprentissage progressif)

------------------------------------
FORMAT OBLIGATOIRE
------------------------------------

Pour chaque news :

🧠 TITRE (copié exactement depuis la source, sans modification)

📌 Explication :
- expliquer la news clairement (5 à 10 lignes)
- ajouter du contexte réel pour comprendre l’événement
- AJOUTER UN APPRENTISSAGE : chaque jour, inclure un élément éducatif lié (ex : comment fonctionne une institution, pourquoi une décision existe, comment un mécanisme économique marche)
- rendre l’utilisateur plus intelligent sur le sujet, pas juste informé

🔎 Contexte technique :
- expliquer les termes compliqués présents dans la news
- institutions, politiques, économie, géopolitique
- expliquer simplement mais précisément

🔮 Projections :
- 2 à 3 scénarios possibles
- conséquences futures
- risques ou opportunités

------------------------------------
💰 INVESTISSEMENT FINAL
------------------------------------

- 1 seule entreprise liée aux news du jour
- explication simple :
  pourquoi elle est impactée
  opportunité
  risques
- inclure prix de l’action (si connu ou estimation récente)

------------------------------------
📊 SYNTHÈSE FINALE
------------------------------------

- résumé du jour
- tendance globale
- max 5 lignes

------------------------------------
IMPORTANT :
- les titres doivent être identiques à ceux fournis
- chaque explication doit apporter un apprentissage nouveau
- pas de répétition
- style pédagogique progressif

NEWS :
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
def send(text):
    for i in range(0, len(text), 4000):
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text[i:i+4000]}
        )

send(resume)
