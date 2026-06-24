import os
import requests
import xml.etree.ElementTree as ET
from groq import Groq
from datetime import datetime
from collections import OrderedDict

# =========================
# CONFIG
# =========================

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
GROQ_KEY = os.environ["GROQ_KEY"]

client = Groq(api_key=GROQ_KEY)

now = datetime.now()
date_complete = now.strftime("%A %d %B %Y")

# =========================
# RSS SOURCES
# =========================

feeds = [
    "https://news.google.com/rss?hl=fr&gl=FR&ceid=FR:fr",
    "https://www.lemonde.fr/rss/une.xml",
    "https://www.lemonde.fr/international/rss_full.xml",
    "https://www.lemonde.fr/politique/rss_full.xml",
    "https://feeds.leparisien.fr/leparisien/rss",
    "https://www.lavanguardia.com/rss/home.xml",
    "https://www.ledauphine.com/actualite/rss"
]

# =========================
# EXTRACTION ROBUSTE
# =========================

articles = OrderedDict()

def extract_items(xml_content, feed_name):
    """Support RSS + XML cassé + erreurs silencieuses"""
    try:
        root = ET.fromstring(xml_content)

        # RSS classique
        items = root.findall(".//item")

        # fallback Atom
        if not items:
            items = root.findall(".//entry")

        return items

    except Exception as e:
        print(f"❌ XML error sur {feed_name}: {e}")
        return []

for feed in feeds:
    try:
        response = requests.get(
            feed,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        if response.status_code != 200:
            print(f"⚠️ HTTP error {response.status_code} sur {feed}")
            continue

        items = extract_items(response.content, feed)

        print(f"✅ {feed} → {len(items)} items")

        for item in items[:20]:
            title = item.find("title")

            if title is not None:
                title_text = title.text

                if title_text and title_text not in articles:
                    articles[title_text] = True

    except Exception as e:
        print(f"❌ Feed error {feed}: {e}")
        continue

# =========================
# LIMITATION INTELLIGENTE
# =========================

articles_list = list(articles.keys())

print(f"🧾 Total articles collectés: {len(articles_list)}")

articles_list = articles_list[:80]  # augmentation de capacité

texte_brut = "\n".join(articles_list)

# =========================
# PROMPT IA
# =========================

prompt = f"""
Tu es un journaliste analyste expert.

DATE :
{date_complete}

MISSION :
Créer un briefing mondial clair et pédagogique à partir de titres d'actualité.

RÈGLES :
- utiliser uniquement les titres fournis
- ne pas inventer de faits
- style clair, pédagogique, structuré
- explications simples mais riches
- pas de Markdown

FORMAT :

🧠 TITRE

📌 Explication :
(8-12 lignes minimum)

🧠 Apprentissage :
(comprendre le contexte mondial)

🔎 Contexte technique :
(définitions simples)

🔮 Projection :
(stable / tension / crise)

------------------------------------

💰 INVESTISSEMENT :
1 entreprise liée à l’actualité

₿ CRYPTO :
analyse générale du marché

📊 SYNTHÈSE :
5-7 lignes

NEWS :
{texte_brut}
"""

# =========================
# IA CALL
# =========================

completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=4000
)

resume = completion.choices[0].message.content

# =========================
# TELEGRAM SENDER ROBUSTE
# =========================

def send_message(text):
    chunks = [text[i:i+3500] for i in range(0, len(text), 3500)]

    for chunk in chunks:
        try:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": CHAT_ID,
                    "text": chunk
                },
                timeout=10
            )
        except Exception as e:
            print("❌ Telegram error:", e)

send_message(resume)
