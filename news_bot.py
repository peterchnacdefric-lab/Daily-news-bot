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

feeds = [
    ("Monde FR",    "https://news.google.com/rss/headlines/section/topic/WORLD?hl=fr&gl=FR&ceid=FR:fr"),
    ("France",      "https://news.google.com/rss/headlines/section/topic/NATION?hl=fr&gl=FR&ceid=FR:fr"),
    ("Économie FR", "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=fr&gl=FR&ceid=FR:fr"),
    ("Tech FR",     "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=fr&gl=FR&ceid=FR:fr"),
    ("Santé",       "https://news.google.com/rss/headlines/section/topic/HEALTH?hl=fr&gl=FR&ceid=FR:fr"),
    ("Science",     "https://news.google.com/rss/headlines/section/topic/SCIENCE?hl=fr&gl=FR&ceid=FR:fr"),
    ("Une FR",      "https://news.google.com/rss?hl=fr&gl=FR&ceid=FR:fr"),
    ("Monde EN",    "https://news.google.com/rss/headlines/section/topic/WORLD?hl=en&gl=US&ceid=US:en"),
    ("Finance EN",  "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en&gl=US&ceid=US:en"),
    ("Tech EN",     "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en&gl=US&ceid=US:en"),
]

articles_par_theme = {}
tous_les_titres = []

for nom, feed in feeds:
    try:
        r = requests.get(feed, timeout=15, headers=headers)
        root = ET.fromstring(r.content)
        titres = []
        for item in root.findall(".//item")[:12]:
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

texte_brut = ""
for theme, titres in articles_par_theme.items():
    texte_brut += f"\n=== {theme.upper()} ===\n"
    for t in titres:
        texte_brut += f"- {t}\n"

# On envoie d'abord les titres bruts pour vérifier la collecte
diagnostic = f"📥 Titres collectés : {len(tous_les_titres)}\nThèmes : {', '.join(articles_par_theme.keys())}\n\nPremiers titres :\n"
for t in tous_les_titres[:10]:
    diagnostic += f"• {t}\n"

requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    json={"chat_id": CHAT_ID, "text": diagnostic}
)

# Prompt en deux parties pour forcer la longueur
prompt_partie1 = f"""Tu es un analyste géopolitique et économique expert. Tu dois produire un rapport TRÈS LONG et TRÈS DÉTAILLÉ.

DATE : {date_complete}

CONSIGNE ABSOLUE : Chaque sujet doit faire MINIMUM 300 mots. Si tu écris moins, tu as échoué ta mission.

Traite les 4 premiers sujets les plus importants parmi ces titres :

{texte_brut}

FORMAT OBLIGATOIRE POUR CHAQUE SUJET :

📰 SUJET [numéro] : [titre exact de la source]

📌 ANALYSE (minimum 150 mots) :
Explique les faits en détail. Qui sont les acteurs ? Quels sont leurs intérêts réels ? Pourquoi maintenant ? Quelles sont les causes profondes ? Quelles conséquences concrètes pour les citoyens ordinaires ? Donne des chiffres, des noms, des exemples précis.

🎓 CONTEXTE ET MÉCANISMES (minimum 100 mots) :
Explique comment ça fonctionne. Les institutions impliquées. Les mécanismes économiques ou politiques. Définis les termes complexes simplement avec des exemples du quotidien.

🔮 PROJECTION RÉALISTE (minimum 50 mots) :
Ce qui va probablement se passer dans les 2 à 4 prochaines semaines. Basé sur les faits, pas sur des espoirs.

---

Commence maintenant avec le Sujet 1. Sois LONG, DENSE, et PRÉCIS."""

prompt_partie2 = f"""Continue le rapport du {date_complete}.

Traite maintenant les 4 sujets suivants les plus importants parmi ces titres :

{texte_brut}

Même format obligatoire (minimum 300 mots par sujet) :

📰 SUJET [numéro] : [titre]
📌 ANALYSE (minimum 150 mots)
🎓 CONTEXTE ET MÉCANISMES (minimum 100 mots)
🔮 PROJECTION RÉALISTE (minimum 50 mots)

Après les 4 sujets, ajoute :

💰 INVESTISSEMENT DU JOUR :
Entreprise directement liée aux actualités. Nom, secteur, pourquoi aujourd'hui, opportunité, risques. Minimum 100 mots. Note : analyse pédagogique uniquement.

₿ CRYPTO DU JOUR :
Bitcoin et Ethereum. Tendance actuelle. Lien avec la macro. Ce que font les institutionnels. Minimum 80 mots.

📊 SYNTHÈSE FINALE :
Le monde aujourd'hui en 8 lignes. Ce qu'il faut absolument retenir."""

client = Groq(api_key=GROQ_KEY)

def appeler_groq(prompt):
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=7000,
        temperature=0.7
    )
    return completion.choices[0].message.content

def send(text):
    for i in range(0, len(text), 4000):
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text[i:i+4000]}
        )

header = f"🗞 RAPPORT QUOTIDIEN — {date_complete}\n📰 {len(tous_les_titres)} titres analysés\n\n"

partie1 = appeler_groq(prompt_partie1)
partie2 = appeler_groq(prompt_partie2)

send(header + partie1 + "\n\n---\n\n" + partie2)
