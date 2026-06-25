import os
import requests
import xml.etree.ElementTree as ET
from groq import Groq
from datetime import datetime
import time

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
GROQ_KEY = os.environ["GROQ_KEY"]

now = datetime.now()
date_complete = now.strftime("%A %d %B %Y")
headers = {"User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)"}

feeds = [
    ("Monde FR",    "https://news.google.com/rss/headlines/section/topic/WORLD?hl=fr&gl=FR&ceid=FR:fr"),
    ("France",      "https://news.google.com/rss/headlines/section/topic/NATION?hl=fr&gl=FR&ceid=FR:fr"),
    ("Economie FR", "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=fr&gl=FR&ceid=FR:fr"),
    ("Tech FR",     "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=fr&gl=FR&ceid=FR:fr"),
    ("Sante",       "https://news.google.com/rss/headlines/section/topic/HEALTH?hl=fr&gl=FR&ceid=FR:fr"),
    ("Science",     "https://news.google.com/rss/headlines/section/topic/SCIENCE?hl=fr&gl=FR&ceid=FR:fr"),
    ("Une FR",      "https://news.google.com/rss?hl=fr&gl=FR&ceid=FR:fr"),
    ("Monde EN",    "https://news.google.com/rss/headlines/section/topic/WORLD?hl=en&gl=US&ceid=US:en"),
    ("Finance EN",  "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en&gl=US&ceid=US:en"),
    ("Tech EN",     "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en&gl=US&ceid=US:en"),
]

tous_les_titres = []
for nom, feed in feeds:
    try:
        r = requests.get(feed, timeout=15, headers=headers)
        root = ET.fromstring(r.content)
        for item in root.findall(".//item")[:12]:
            title = item.find("title")
            if title is not None and title.text:
                texte = title.text.strip()
                if texte not in tous_les_titres and len(texte) > 20:
                    tous_les_titres.append(texte)
    except:
        continue

client = Groq(api_key=GROQ_KEY)

def groq_call(prompt, tokens=2000):
    time.sleep(2)
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=tokens,
        temperature=0.8
    )
    return completion.choices[0].message.content

def send(text):
    for i in range(0, len(text), 4000):
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text[i:i+4000]}
        )
        time.sleep(0.5)

# Etape 1 : choisir les 6 meilleurs titres
selection_prompt = f"""Voici {len(tous_les_titres)} titres d'actualite du {date_complete}.

Selectionne exactement 6 titres, les plus importants et varies possible (geopolitique, economie, tech, sante, societe, science). Pas deux fois le meme theme.

Reponds UNIQUEMENT avec les 6 titres selectionnes, un par ligne, sans numero ni commentaire.

TITRES :
{chr(10).join(tous_les_titres[:60])}"""

selection_brute = groq_call(selection_prompt, tokens=500)
titres_selectionnes = [t.strip() for t in selection_brute.strip().split("\n") if len(t.strip()) > 20][:6]

# Etape 2 : analyser chaque titre separement
send(f"🗞 RAPPORT QUOTIDIEN\n📅 {date_complete}\n📰 {len(tous_les_titres)} titres collectes\n\n{'='*30}")

for i, titre in enumerate(titres_selectionnes, 1):
    prompt_article = f"""Tu es un journaliste analyste expert. Aujourd'hui : {date_complete}.

Sujet : {titre}

Ecris une analyse COMPLETE et LONGUE sur ce sujet. Tu dois absolument inclure :

1. LES FAITS : Que se passe-t-il exactement ? Qui sont les acteurs ? Quels chiffres concrets ?

2. LE CONTEXTE HISTORIQUE : Pourquoi ca arrive maintenant ? Quelle est l'histoire derriere ce sujet ? Donne des dates, des evenements passes qui expliquent la situation actuelle.

3. LES MECANISMES : Comment ca fonctionne vraiment ? Si c'est economique, explique les flux d'argent, les institutions, les marches. Si c'est geopolitique, explique les alliances, les interets, les rapports de force. Sois precis et technique, mais explique chaque terme.

4. LA CURIOSITE DU JOUR : Un fait surprenant, peu connu, contre-intuitif ou fascinant lie a ce sujet. Quelque chose que la plupart des gens ne savent pas.

5. LES CONSEQUENCES CONCRETES : Comment ca affecte la vie des gens ordinaires ? Donne des exemples tres concrets et tangibles.

6. PROJECTION : Ce qui va probablement se passer dans les 4 prochaines semaines. Sois realiste et precis.

Longueur minimum : 400 mots. Style : dense, intelligent, curieux. Aucun Markdown."""

    analyse = groq_call(prompt_article, tokens=2000)

    bloc = f"\n\n{'='*30}\n"
    bloc += f"📰 SUJET {i}/{len(titres_selectionnes)}\n"
    bloc += f"{'='*30}\n\n"
    bloc += f"🧠 {titre.upper()}\n\n"
    bloc += analyse
    send(bloc)

# Etape 3 : investissement
prompt_invest = f"""Date : {date_complete}
Sujets du jour : {', '.join(titres_selectionnes)}

Identifie UNE seule entreprise cotee en bourse directement liee a l'un de ces sujets.

Ecris une analyse de 200 mots minimum :
- Nom complet et secteur
- Pourquoi elle est impactee AUJOURD'HUI specifiquement
- Chiffres concrets (prix action approximatif, capitalisation)
- Ce qui pourrait faire monter ou baisser le titre
- Risques reels et concrets
- Un fait peu connu sur cette entreprise

Termine par : "Ceci est une analyse pedagogique uniquement, pas un conseil financier."

Aucun Markdown."""

invest = groq_call(prompt_invest, tokens=1000)
send(f"\n\n{'='*30}\n💰 INVESTISSEMENT DU JOUR\n{'='*30}\n\n{invest}")

# Etape 4 : crypto
prompt_crypto = f"""Date : {date_complete}

Analyse le marche crypto aujourd'hui en lien avec l'actualite mondiale.

Inclus :
- Bitcoin : niveau approximatif et tendance
- Ethereum : tendance
- Quel evenement macro influence le marche aujourd'hui
- Ce que font les grands investisseurs institutionnels
- Une curiosite sur la blockchain peu connue du grand public
- Projection a 2 semaines

Minimum 150 mots. Aucun Markdown."""

crypto = groq_call(prompt_crypto, tokens=800)
send(f"\n\n{'='*30}\n₿ CRYPTO DU JOUR\n{'='*30}\n\n{crypto}")

# Etape 5 : synthese
prompt_synthese = f"""Date : {date_complete}
Sujets analyses aujourd'hui : {', '.join(titres_selectionnes)}

Ecris une synthese globale de 150 mots. Pas un resume des sujets — une lecture transversale du monde aujourd'hui. Quelle est la tendance profonde qui relie ces evenements ? Qu'est-ce que ca dit de l'etat du monde en ce moment ? Qu'est-ce qu'il faut absolument retenir ?

Aucun Markdown."""

synthese = groq_call(prompt_synthese, tokens=600)
send(f"\n\n{'='*30}\n📊 SYNTHESE FINALE\n{'='*30}\n\n{synthese}\n\n{'='*30}\nFin du rapport — {date_complete}")
