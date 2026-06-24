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

# -----------------------------
# SOURCES RSS
# -----------------------------
feeds = [
    # Google News global
    "https://news.google.com/rss?hl=fr&gl=FR&ceid=FR:fr",

    # Le Monde
    "https://www.lemonde.fr/rss/une.xml",
    "https://www.lemonde.fr/international/rss_full.xml",
    "https://www.lemonde.fr/politique/rss_full.xml",

    # Le Parisien
    "https://feeds.leparisien.fr/leparisien/rss",

    # La Vanguardia (Espagne)
    "https://www.lavanguardia.com/rss/home.xml",

    # Le Dauphiné Libéré
    "https://www.ledauphine.com/actualite/rss"
]

# -----------------------------
# EXTRACTION
# -----------------------------
articles = []

for feed in feeds:
    try:
        response = requests.get(feed, timeout=10)
        root = ET.fromstring(response.content)

        for item in root.findall(".//item")[:10]:
            title = item.find("title").text

            if title and title not in articles:
                articles.append(title)

    except:
        continue

# limite sécurité
articles = articles[:30]

texte_brut = "\n".join(articles)

# -----------------------------
# PROMPT IA
# -----------------------------
prompt = f"""
Tu es un journaliste analyste pédagogique expert.

DATE :
{date_complete}

MISSION :
Créer un rapport quotidien à partir de plusieurs sources internationales (France, Espagne, Europe, Google News).

RÈGLES :
- utiliser EXACTEMENT les titres fournis
- aucun Markdown
- style Telegram lisible
- explications longues et pédagogiques
- apprentissage intégré dans chaque news

FORMAT :

🧠 TITRE

📌 Explication :
8 à 12 lignes minimum
(contexte + faits + acteurs + enjeux + explication simple)

🧠 Apprentissage :
explication progressive pour comprendre le monde (institutions, économie, géopolitique)

🔎 Contexte technique :
définitions des termes importants

🔮 Projection :
3 scénarios possibles (stable / tension / crise)

------------------------------------

💰 INVESTISSEMENT :
1 entreprise liée aux news du jour

₿ CRYPTO :
analyse marché crypto

📊 SYNTHÈSE :
5 à 7 lignes

NEWS :
{texte_brut}
"""

# -----------------------------
# IA
# -----------------------------
client = Groq(api_key=GROQ_KEY)
completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=4000
)

resume = completion.choices[0].message.content

# -----------------------------
# TELEGRAM
# -----------------------------
def send(text):
    for i in range(0, len(text), 4000):
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text[i:i+4000]}
        )

send(resume)
