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

# Google News RSS
url = "https://news.google.com/rss?hl=fr&gl=FR&ceid=FR:fr"
response = requests.get(url)
root = ET.fromstring(response.content)

articles = []
for item in root.findall(".//item")[:25]:
    titre = item.find("title").text
    articles.append(titre)

texte_brut = "\n".join(articles)

# PROMPT
prompt = f"""
Tu es un journaliste analyste pédagogique expert.

DATE :
{date_complete}

MISSION :
Transformer les actualités en un rapport quotidien très détaillé, clair et éducatif.

RÈGLES IMPORTANTES :
- utiliser EXACTEMENT les titres fournis
- aucun Markdown
- style Telegram lisible
- explications riches, pédagogiques et approfondies
- chaque réponse doit faire apprendre quelque chose de nouveau

------------------------------------
FORMAT OBLIGATOIRE
------------------------------------

Pour chaque news :

🧠 TITRE (identique à la source)

📌 Explication :
- 8 à 12 lignes minimum
- expliquer en détail le contexte de la news
- expliquer les causes de l’événement
- expliquer les acteurs impliqués
- ajouter du contexte historique ou structurel quand utile
- rendre compréhensible même pour quelqu’un qui découvre le sujet

🧠 Apprentissage du jour (intégré dans l’explication) :
- ajouter une notion éducative liée à la news
- expliquer comment fonctionne une institution, un mécanisme économique, ou un concept politique
- donner un exemple concret pour mieux comprendre
- rendre la personne plus intelligente sur le sujet, pas juste informée

🔎 Contexte technique :
- expliquer les termes complexes présents dans la news
- institutions, politiques, économie, géopolitique
- 3 à 6 lignes supplémentaires si nécessaire

🔮 Projections :
- 3 à 5 lignes minimum
- expliquer plusieurs scénarios possibles
- scénario stable
- scénario tendu
- scénario extrême si pertinent
- expliquer les conséquences concrètes pour le monde réel

------------------------------------
💰 INVESTISSEMENT FINAL
------------------------------------

- 1 seule entreprise liée aux news du jour
- explication longue :
  pourquoi cette entreprise est directement impactée
  pourquoi elle est intéressante aujourd’hui
  opportunités à court et moyen terme
  risques importants
- inclure prix de l’action (récent ou estimation si nécessaire)

------------------------------------
₿ CRYPTO DU JOUR
------------------------------------

- Bitcoin
- Ethereum
- marché crypto global

Inclure :
- analyse des mouvements récents
- causes détaillées
- événements majeurs (ETF, régulation, institutions, hacks, adoption)

------------------------------------
📊 SYNTHÈSE FINALE
------------------------------------

- résumé global du jour
- analyse de la tendance mondiale
- 5 à 7 lignes

------------------------------------
IMPORTANT :
- profondeur maximale dans les explications
- priorité à la compréhension réelle
- style pédagogique mais sérieux
- aucun résumé superficiel

NEWS :
{texte_brut}
"""

# IA
client = Groq(api_key=GROQ_KEY)
completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=4000
)

resume = completion.choices[0].message.content

# Telegram
def send(text):
    for i in range(0, len(text), 4000):
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text[i:i+4000]}
        )

send(resume)
