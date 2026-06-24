import os
import requests
import xml.etree.ElementTree as ET
from groq import Groq

# Configuration
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
GROQ_KEY = os.environ["GROQ_KEY"]

# Récupère les news Google
url = "https://news.google.com/rss?hl=fr&gl=FR&ceid=FR:fr"
response = requests.get(url)
root = ET.fromstring(response.content)

articles = []
for item in root.findall(".//item")[:10]:
    titre = item.find("title").text
    articles.append(titre)

texte_brut = "\n".join(articles)

# Résumé via Groq
client = Groq(api_key=GROQ_KEY)
completion = client.chat.completions.create(
    model=model="llama-3.3-70b-versatile",
,
    messages=[
        {
            "role": "user",
            "content": f"Résume ces actualités du jour en français de façon claire et concise, avec des emojis :\n\n{texte_brut}"
        }
    ]
)

resume = completion.choices[0].message.content

# Envoie sur Telegram
message = f"🗞 *Actualités du jour*\n\n{resume}"
requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    json={
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
)
