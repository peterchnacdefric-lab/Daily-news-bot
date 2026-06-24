import os
import requests
import xml.etree.ElementTree as ET
from groq import Groq
from datetime import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
GROQ_KEY = os.environ["GROQ_KEY"]

# Date complète
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

# PROMPT SIMPLE ET ROBUSTE
prompt = f"""
Tu es un journaliste pédagogique et analyste du monde.

DATE :
{date_complete}

MISSION :
Transformer les news en un rapport clair, éducatif et structuré.

RÈGLES :
- Aucun Markdown
- Style Telegram lisible
- Explications simples mais informatives
- Mélange international + France + Europe

------------------------------------
FORMAT GLOBAL
------------------------------------

1) NEWS

Pour chaque news :

🧠 TITRE

📌 Explication :
Explique la news clairement (5 à 10 lignes)

🔎 Termes et contexte :
Explique ici les mots techniques ou le contexte (institutions, politique, économie, etc.)
Rendre simple et compréhensible

🔮 Projections :
Explique ce qui pourrait se passer ensuite
Donne 2 à 3 scénarios possibles

------------------------------------
2) INVESTISSEMENT FINAL

💰 Donne UNE seule entreprise à surveiller ou investir

Inclure :
- nom de l’entreprise
- pourquoi elle est liée aux news
- analyse simple
- prix actuel de l’action (estimation si nécessaire ou récent connu)

IMPORTANT : ce n’est pas un conseil financier

------------------------------------

3) SYNTHÈSE FINALE

Résumé très court de la journée (max 5 lignes)

------------------------------------

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
