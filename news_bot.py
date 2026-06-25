import os
import requests
import xml.etree.ElementTree as ET
from groq import Groq
from datetime import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
GROQ_KEY = os.environ["GROQ_KEY"]

headers = {"User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)"}

feeds = [
    ("Monde FR",   "https://news.google.com/rss/headlines/section/topic/WORLD?hl=fr&gl=FR&ceid=FR:fr"),
    ("Économie FR","https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=fr&gl=FR&ceid=FR:fr"),
    ("Tech FR",    "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=fr&gl=FR&ceid=FR:fr"),
    ("Une FR",     "https://news.google.com/rss?hl=fr&gl=FR&ceid=FR:fr"),
    ("Monde EN",   "https://news.google.com/rss/headlines/section/topic/WORLD?hl=en&gl=US&ceid=US:en"),
    ("Finance EN", "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en&gl=US&ceid=US:en"),
]

rapport = "🔍 DIAGNOSTIC DES SOURCES\n\n"

for nom, feed in feeds:
    try:
        r = requests.get(feed, timeout=15, headers=headers)
        rapport += f"✅ {nom} — statut HTTP {r.status_code} — {len(r.content)} octets\n"
        try:
            root = ET.fromstring(r.content)
            items = root.findall(".//item")
            rapport += f"   → {len(items)} articles trouvés\n"
            for item in items[:3]:
                t = item.find("title")
                if t is not None and t.text:
                    rapport += f"   • {t.text[:80]}\n"
        except Exception as e:
            rapport += f"   → Erreur parsing XML : {e}\n"
    except Exception as e:
        rapport += f"❌ {nom} — ERREUR : {e}\n"

requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    json={"chat_id": CHAT_ID, "text": rapport}
)
