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

# -----------------------------
# SOURCES FIABLES ET ACCESSIBLES
# -----------------------------
feeds = [
    ("Google News FR", "https://news.google.com/rss?hl=fr&gl=FR&ceid=FR:fr"),
    ("Google News Monde", "https://news.google.com/rss/headlines/section/topic/WORLD?hl=fr&gl=FR&ceid=FR:fr"),
    ("Google News Économie", "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=fr&gl=FR&ceid=FR:fr"),
    ("Google News Tech", "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=fr&gl=FR&ceid=FR:fr"),
    ("Google News Science", "https://news.google.com/rss/headlines/section/topic/SCIENCE?hl=fr&gl=FR&ceid=FR:fr"),
    ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
    ("Yahoo News", "https://news.yahoo.com/rss/"),
    ("Reuters", "https://feeds.reuters.com/reuters/topNews"),
    ("BBC Monde", "http://feeds.bbci.co.uk/news/world/rss.xml"),
    ("RFI", "https://www.rfi.fr/fr/rss"),
]

headers = {
    "User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)"
}

# -----------------------------
# COLLECTE ROBUSTE
# -----------------------------
articles = []
sources_ok = []
sources_ko = []

for nom, feed in feeds:
    try:
        r = requests.get(feed, timeout=15, headers=headers)
        root = ET.fromstring(r.content)
        count = 0
        for item in root.findall(".//item")[:12]:
            title = item.find("title")
            if title is not None and title.text:
                texte = title.text.strip()
                if texte not in articles and len(texte) > 15:
                    articles.append(texte)
                    count += 1
        sources_ok.append(f"{nom} ({count} articles)")
    except Exception as e:
        sources_ko.append(nom)
        continue

articles = articles[:60]
texte_brut = "\n".join([f"- {a}" for a in articles])

# -----------------------------
# PROMPT
# -----------------------------
prompt = f"""
Tu es un journaliste analyste économique et géopolitique expert.

DATE : {date_complete}

Tu as accès à {len(articles)} titres d'actualité provenant de sources internationales.

MISSION : Créer un rapport quotidien approfondi basé sur ces actualités.

RÈGLES STRICTES :
- Minimum 10 articles distincts traités
- Explications longues et détaillées (15 à 25 lignes par article)
- Style pédagogique, clair, sans jargon non expliqué
- Aucun Markdown (pas de **, pas de #)
- Chaque article doit vraiment apprendre quelque chose

------------------------------------
FORMAT POUR CHAQUE ARTICLE
------------------------------------

🧠 TITRE (reprendre le titre source)

📌 Explication détaillée :
- Expliquer les faits en profondeur
- Expliquer le contexte géopolitique ou économique
- Qui sont les acteurs, leurs intérêts, leurs relations
- Pourquoi cela se passe maintenant
- Conséquences concrètes pour les citoyens ordinaires

🎓 Pédagogie :
- Expliquer les mécanismes en jeu
- Définir les termes techniques clairement
- Donner un exemple concret du monde réel si utile

🔮 Ce qui va probablement se passer :
- 1 scénario probable et réaliste
- Conséquences concrètes à court terme

------------------------------------
💰 INVESTISSEMENT DU JOUR
------------------------------------
IMPORTANT : Ne traiter cette section QUE si Yahoo Finance ou Reuters fournit des données financières claires dans les titres. Si aucune donnée financière pertinente n'est disponible, écrire simplement : "Pas assez de données financières aujourd'hui pour une analyse fiable."

Si données disponibles :
- 1 entreprise cotée en bourse liée aux actualités
- Pourquoi elle est impactée aujourd'hui
- Risques réels
- Avertissement : ceci est pédagogique, pas un conseil financier

------------------------------------
₿ CRYPTO DU JOUR
------------------------------------
- Bitcoin et Ethereum : tendance actuelle
- Lien avec la macroéconomie mondiale
- Ce qui influence les prix en ce moment

------------------------------------
📊 SYNTHÈSE FINALE
------------------------------------
- Résumé du monde aujourd'hui en 6 à 8 lignes
- Tendance globale
- Ce qu'il faut retenir

------------------------------------
TITRES DU JOUR :
{texte_brut}
"""

# -----------------------------
# IA CALL
# -----------------------------
client = Groq(api_key=GROQ_KEY)
completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=7000
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

header = f"🗞 RAPPORT QUOTIDIEN — {date_complete}\n"
header += f"✅ Sources actives : {', '.join(sources_ok)}\n"
if sources_ko:
    header += f"❌ Sources inaccessibles : {', '.join(sources_ko)}\n"
header += f"📰 {len(articles)} titres analysés\n\n"

send(header + resume)
