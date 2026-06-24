import os
import requests
import xml.etree.ElementTree as ET
from groq import Groq
from datetime import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
GROQ_KEY = os.environ["GROQ_KEY"]

now = datetime.now()
date_complete = now.strftime("%A %d %B %Y")

# 🔁 REMPLACEMENT GOOGLE NEWS → LE MONDE
rss_feeds = [
    "https://www.lemonde.fr/rss/une.xml",
    "https://www.lemonde.fr/international/rss_full.xml",
    "https://www.lemonde.fr/politique/rss_full.xml",
    "https://www.lemonde.fr/economie/rss_full.xml"
]

articles = []

for feed in rss_feeds:
    response = requests.get(feed)
    root = ET.fromstring(response.content)
    for item in root.findall(".//item")[:5]:
        titre = item.find("title").text
        articles.append(titre)

texte_brut = "\n".join(articles)

prompt = f"""
Tu es un journaliste analyste pédagogique expert.

DATE :
{date_complete}

MISSION :
Transformer les articles du Monde en un rapport quotidien détaillé, éducatif et structuré.

RÈGLES :
- utiliser EXACTEMENT les titres fournis
- aucun Markdown
- style Telegram lisible
- explications longues et pédagogiques
- apprentissage intégré

FORMAT :

🧠 TITRE

📌 Explication :
8 à 12 lignes minimum
contexte + causes + acteurs + enjeux

🧠 Apprentissage :
explication pédagogique intégrée

🔎 Contexte technique :
institutions, politique, économie

🔮 Projections :
scénarios futurs détaillés

------------------------------------

💰 INVESTISSEMENT :
1 entreprise liée aux news

₿ CRYPTO :
analyse du marché

📊 SYNTHÈSE :
5 à 7 lignes

NEWS :
{texte_brut}
"""

client = Groq(api_key=GROQ_KEY)
completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=4000
)

resume = completion.choices[0].message.content

def send(text):
    for i in range(0, len(text), 4000):
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text[i:i+4000]}
        )

send(resume)
