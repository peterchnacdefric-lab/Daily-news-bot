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

headers = {"User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)"}

# Google News par thème — toujours accessible
feeds = [
    ("Monde",      "https://news.google.com/rss/headlines/section/topic/WORLD?hl=fr&gl=FR&ceid=FR:fr"),
    ("France",     "https://news.google.com/rss/headlines/section/topic/NATION?hl=fr&gl=FR&ceid=FR:fr"),
    ("Économie",   "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=fr&gl=FR&ceid=FR:fr"),
    ("Tech",       "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=fr&gl=FR&ceid=FR:fr"),
    ("Science",    "https://news.google.com/rss/headlines/section/topic/SCIENCE?hl=fr&gl=FR&ceid=FR:fr"),
    ("Santé",      "https://news.google.com/rss/headlines/section/topic/HEALTH?hl=fr&gl=FR&ceid=FR:fr"),
    ("Sports",     "https://news.google.com/rss/headlines/section/topic/SPORTS?hl=fr&gl=FR&ceid=FR:fr"),
    ("Une",        "https://news.google.com/rss?hl=fr&gl=FR&ceid=FR:fr"),
    ("Finance EN", "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en&gl=US&ceid=US:en"),
    ("Monde EN",   "https://news.google.com/rss/headlines/section/topic/WORLD?hl=en&gl=US&ceid=US:en"),
]

articles_par_theme = {}
tous_les_titres = []

for nom, feed in feeds:
    try:
        r = requests.get(feed, timeout=15, headers=headers)
        root = ET.fromstring(r.content)
        titres = []
        for item in root.findall(".//item")[:10]:
            title = item.find("title")
            if title is not None and title.text:
                texte = title.text.strip()
                if texte not in tous_les_titres and len(texte) > 20:
                    titres.append(texte)
                    tous_les_titres.append(texte)
        if titres:
            articles_par_theme[nom] = titres
    except:
        continue

# Formate par thème
texte_brut = ""
for theme, titres in articles_par_theme.items():
    texte_brut += f"\n=== {theme.upper()} ===\n"
    for t in titres:
        texte_brut += f"- {t}\n"

prompt = f"""
Tu es un journaliste analyste économique et géopolitique expert.

DATE : {date_complete}
NOMBRE DE TITRES COLLECTÉS : {len(tous_les_titres)}

MISSION : Créer un rapport quotidien approfondi et varié.

RÈGLES STRICTES :
- Traiter EXACTEMENT 10 articles différents, issus de THÈMES VARIÉS
- Ne pas se concentrer uniquement sur un seul sujet
- Explications longues (15 à 25 lignes par article)
- Style pédagogique et clair
- Aucun Markdown (pas de **, pas de #)
- Varier : géopolitique, économie, tech, santé, science, société

------------------------------------
FORMAT POUR CHAQUE ARTICLE (répéter 10 fois)
------------------------------------

🧠 [NUMÉRO]. TITRE

📌 Explication détaillée :
Minimum 15 lignes. Expliquer les faits, le contexte géopolitique ou économique, les acteurs impliqués, leurs intérêts, pourquoi cela se passe maintenant, et les conséquences concrètes pour les gens ordinaires.

🎓 Pédagogie :
Expliquer les mécanismes en jeu. Définir les termes techniques. Donner un exemple concret si utile.

🔮 Projection probable :
Un scénario réaliste et concret à court terme.

------------------------------------
💰 INVESTISSEMENT DU JOUR
------------------------------------
1 entreprise cotée en bourse liée aux actualités du jour.
- Nom et secteur
- Pourquoi elle est impactée aujourd'hui
- Opportunité potentielle
- Risques réels
Note : analyse pédagogique uniquement, pas un conseil financier.

------------------------------------
₿ CRYPTO DU JOUR
------------------------------------
- Bitcoin : tendance et niveau actuel
- Ethereum : tendance
- Lien avec la macroéconomie mondiale
- Ce qui influence les prix en ce moment

------------------------------------
📊 SYNTHÈSE FINALE
------------------------------------
Résumé du monde aujourd'hui en 8 lignes. Tendance globale. Ce qu'il faut retenir.

------------------------------------
ACTUALITÉS PAR THÈME :
{texte_brut}
"""

client = Groq(api_key=GROQ_KEY)
completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=7000
)

resume = completion.choices[0].message.content

def send(text):
    for i in range(0, len(text), 4000):
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text[i:i+4000]}
        )

header = f"🗞 RAPPORT QUOTIDIEN — {date_complete}\n"
header += f"📰 {len(tous_les_titres)} titres collectés sur {len(articles_par_theme)} thèmes\n\n"

send(header + resume)
