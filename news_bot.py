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

url = "https://news.google.com/rss?hl=fr&gl=FR&ceid=FR:fr"
response = requests.get(url)
root = ET.fromstring(response.content)

articles = []
for item in root.findall(".//item")[:40]:
    titre = item.find("title").text
    articles.append(titre)

texte_brut = "\n".join(articles)

prompt = f"""
Tu es un journaliste pédagogique.

DATE :
{date_complete}

MISSION :
Créer EXACTEMENT 10 news (pas plus, pas moins).

RÈGLES STRICTES :
- 10 news obligatoires
- chaque news a un emoji différent
- aucun Markdown
- format Telegram simple
- news internationales + France + Europe

FORMAT POUR CHAQUE NEWS :

🎯 TITRE (emoji obligatoire unique)

📌 Explication :
5 à 8 lignes max, simple mais informatif

🔮 Projection :
2 à 4 lignes sur le futur possible

---

IMPORTANT :
Tu dois produire 10 blocs complets.

------------------------------------

🧠 APPRENDRE LE MONDE (long)

- minimum 12 lignes
- paragraphes séparés
- expliquer politique, économie, relations internationales
- expliquer le fonctionnement du monde à partir des news
- très pédagogique

------------------------------------

💰 INVESTISSEMENT :
1 entreprise liée aux news

------------------------------------

₿ CRYPTO :
marché crypto actuel

------------------------------------

📊 SYNTHÈSE :
max 5 lignes

------------------------------------

NEWS INPUT :
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
