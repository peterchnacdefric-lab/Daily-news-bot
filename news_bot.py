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
# SOURCES MULTI (NEWS + FINANCE + ÉNERGIE)
# -----------------------------
feeds = [
    "https://news.google.com/rss?hl=fr&gl=FR&ceid=FR:fr",
    "https://www.lemonde.fr/rss/une.xml",
    "https://www.lemonde.fr/international/rss_full.xml",
    "https://www.lemonde.fr/economie/rss_full.xml",
    "https://feeds.leparisien.fr/leparisien/rss",
    "https://www.lavanguardia.com/rss/home.xml",
    "https://news.yahoo.com/rss/",
    "https://finance.yahoo.com/news/rssindex"
]

# -----------------------------
# COLLECTE (minimum volume garanti)
# -----------------------------
articles = []

for feed in feeds:
    try:
        r = requests.get(feed, timeout=10)
        root = ET.fromstring(r.content)

        for item in root.findall(".//item")[:15]:
            title = item.find("title").text
            if title and title not in articles:
                articles.append(title)
    except:
        continue

# garantie minimum
articles = articles[:50]

texte_brut = "\n".join(articles)

# -----------------------------
# PROMPT FINAL LONG FORMAT
# -----------------------------
prompt = f"""
Tu es un journaliste analyste économique et géopolitique expert simplifié.

DATE :
{date_complete}

MISSION :
Créer un rapport quotidien très détaillé basé sur l’actualité mondiale.

RÈGLES STRICTES :
- utiliser EXACTEMENT les titres fournis
- aucun Markdown
- minimum 10 articles distincts
- explications longues (10 à 20 lignes par article)
- style pédagogique et clair
- chaque article doit apprendre quelque chose de nouveau

------------------------------------
FORMAT POUR CHAQUE ARTICLE
------------------------------------

🧠 TITRE (identique à la source)

📌 Explication détaillée :
- 10 à 20 lignes minimum
- expliquer les faits en profondeur
- expliquer le contexte géopolitique ou économique
- expliquer les acteurs impliqués
- expliquer pourquoi cela arrive
- ajouter des détails utiles pour comprendre le monde réel

🧠 Apprentissage et contexte :
- intégrer des explications pédagogiques dans le texte
- expliquer les mécanismes (économie, politique, institutions, énergie, marchés)
- donner du sens global (comment ça fonctionne dans le monde réel)
- ajouter des exemples simples si nécessaire

🔎 Termes techniques :
- expliquer clairement les mots compliqués utilisés dans la news
- banques centrales, inflation, pétrole, taux, etc.

🔮 Projection :
- UN seul scénario possible
- expliquer ce qui est le plus probable dans le futur
- conséquences concrètes

------------------------------------
💰 INVESTISSEMENT FINAL
------------------------------------

- 1 seule entreprise cotée en bourse
- liée aux actualités du jour
- explication longue :
  pourquoi elle est impactée
  pourquoi elle est intéressante
  risques
- inclure prix de l’action actuel ou estimé

------------------------------------
₿ CRYPTO DU JOUR
------------------------------------

- Bitcoin
- Ethereum
- marché crypto global
- lien avec macro économie

------------------------------------
📊 SYNTHÈSE FINALE
------------------------------------

- résumé du monde aujourd’hui
- tendance globale
- 5 à 7 lignes

------------------------------------
IMPORTANT :
- très longue profondeur d’explication
- objectif : comprendre le monde, pas juste lire les news
- priorité à la pédagogie + clarté

NEWS :
{texte_brut}
"""

# -----------------------------
# IA CALL
# -----------------------------
client = Groq(api_key=GROQ_KEY)
completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=6000
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
