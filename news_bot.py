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

# -----------------------------
# DONNEES CRYPTO REELLES (CoinGecko - 100% gratuit)
# -----------------------------
def get_crypto():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd&include_24hr_change=true"
        r = requests.get(url, timeout=10)
        data = r.json()
        btc = data["bitcoin"]
        eth = data["ethereum"]
        sol = data["solana"]
        return {
            "btc_prix": btc["usd"],
            "btc_change": btc["usd_24h_change"],
            "eth_prix": eth["usd"],
            "eth_change": eth["usd_24h_change"],
            "sol_prix": sol["usd"],
            "sol_change": sol["usd_24h_change"],
        }
    except:
        return None

# -----------------------------
# DONNEES MARCHES REELLES (Yahoo Finance - gratuit)
# -----------------------------
def get_marches():
    symboles = {
        "CAC 40": "%5EFCHI",
        "S&P 500": "%5EGSPC",
        "Pétrole Brent": "BZ%3DF",
        "Or": "GC%3DF",
        "EUR/USD": "EURUSD%3DX"
    }
    resultats = {}
    for nom, symbole in symboles.items():
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbole}?interval=1d&range=2d"
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            data = r.json()
            prix = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
            prev = data["chart"]["result"][0]["meta"]["previousClose"]
            change = ((prix - prev) / prev) * 100
            resultats[nom] = {"prix": prix, "change": change}
        except:
            continue
    return resultats

# -----------------------------
# COLLECTE NEWS
# -----------------------------
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

# -----------------------------
# RECUPERATION DONNEES
# -----------------------------
crypto = get_crypto()
marches = get_marches()

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

# -----------------------------
# SELECTION DES 6 MEILLEURS TITRES
# -----------------------------
selection_prompt = f"""Voici des titres d'actualite du {date_complete}.

Selectionne exactement 6 titres les plus importants et varies (geopolitique, economie, tech, sante, science, societe). Un seul titre par theme.

Reponds UNIQUEMENT avec les 6 titres, un par ligne, sans numero ni commentaire.

TITRES :
{chr(10).join(tous_les_titres[:60])}"""

selection_brute = groq_call(selection_prompt, tokens=500)
titres_selectionnes = [t.strip() for t in selection_brute.strip().split("\n") if len(t.strip()) > 20][:6]

# -----------------------------
# ENVOI HEADER
# -----------------------------
send(f"🗞 RAPPORT QUOTIDIEN\n📅 {date_complete}\n📰 {len(tous_les_titres)} titres collectes\n{'='*30}")

# -----------------------------
# ANALYSE DE CHAQUE ARTICLE
# -----------------------------
for i, titre in enumerate(titres_selectionnes, 1):
    prompt_article = f"""Tu es un journaliste analyste expert. Date : {date_complete}.

Sujet unique a analyser : {titre}

Redige une analyse complete. Tu n'as PAS acces a internet donc base-toi sur tes connaissances generales pour contextualiser ce titre.

Structure obligatoire (sans Markdown) :

LES FAITS
Que se passe-t-il ? Qui sont les acteurs ? Quels enjeux concrets ?

LE CONTEXTE HISTORIQUE
Pourquoi ca arrive maintenant ? Histoire et evenements passes qui expliquent la situation. Donne des dates et des faits precis.

LE MECANISME
Comment ca fonctionne vraiment ? Explique les rouages economiques, politiques ou scientifiques. Definis chaque terme technique simplement.

LA CURIOSITE
Un fait surprenant, peu connu ou contre-intuitif lie a ce sujet. Quelque chose que 95% des gens ignorent.

LES CONSEQUENCES REELLES
Impact concret sur la vie quotidienne des gens ordinaires. Exemples tres precis.

LA PROJECTION
Ce qui va probablement se passer dans les 4 prochaines semaines. Realiste et argumente.

Minimum 350 mots. Style dense et intelligent."""

    analyse = groq_call(prompt_article, tokens=2000)
    bloc = f"\n{'='*30}\n📰 {i}/6 — {titre.upper()}\n{'='*30}\n\n{analyse}"
    send(bloc)

# -----------------------------
# MARCHES FINANCIERS (donnees reelles)
# -----------------------------
marches_text = f"\n{'='*30}\n📈 MARCHES DU JOUR — DONNEES EN TEMPS REEL\n{'='*30}\n"
if marches:
    for nom, data in marches.items():
        emoji = "🟢" if data["change"] > 0 else "🔴"
        marches_text += f"{emoji} {nom} : {data['prix']:.2f} ({data['change']:+.2f}%)\n"
else:
    marches_text += "Donnees de marche indisponibles aujourd'hui.\n"
send(marches_text)

# -----------------------------
# CRYPTO (donnees reelles)
# -----------------------------
if crypto:
    btc_emoji = "🟢" if crypto["btc_change"] > 0 else "🔴"
    eth_emoji = "🟢" if crypto["eth_change"] > 0 else "🔴"
    sol_emoji = "🟢" if crypto["sol_change"] > 0 else "🔴"

    crypto_text = f"\n{'='*30}\n₿ CRYPTO DU JOUR — DONNEES EN TEMPS REEL\n{'='*30}\n\n"
    crypto_text += f"{btc_emoji} Bitcoin : ${crypto['btc_prix']:,.0f} ({crypto['btc_change']:+.2f}% sur 24h)\n"
    crypto_text += f"{eth_emoji} Ethereum : ${crypto['eth_prix']:,.0f} ({crypto['eth_change']:+.2f}% sur 24h)\n"
    crypto_text += f"{sol_emoji} Solana : ${crypto['sol_prix']:,.0f} ({crypto['sol_change']:+.2f}% sur 24h)\n"

    prompt_crypto = f"""Date : {date_complete}

Voici les prix crypto reels d'aujourd'hui :
Bitcoin : ${crypto['btc_prix']:,.0f} ({crypto['btc_change']:+.2f}% sur 24h)
Ethereum : ${crypto['eth_prix']:,.0f} ({crypto['eth_change']:+.2f}% sur 24h)
Solana : ${crypto['sol_prix']:,.0f} ({crypto['sol_change']:+.2f}% sur 24h)

Actualites du jour : {', '.join(titres_selectionnes[:3])}

Analyse en 200 mots :
- Que signifie cette tendance aujourd'hui ?
- Quel evenement macro explique ce mouvement ?
- Une curiosite peu connue sur Bitcoin ou la blockchain
- Projection a 2 semaines

Sans Markdown. Pas d'invention de chiffres."""

    crypto_analyse = groq_call(prompt_crypto, tokens=600)
    crypto_text += f"\n{crypto_analyse}"
    send(crypto_text)
else:
    send(f"\n{'='*30}\n₿ CRYPTO\n{'='*30}\nDonnees indisponibles aujourd'hui.")

# -----------------------------
# INVESTISSEMENT
# -----------------------------
prompt_invest = f"""Date : {date_complete}
Sujets du jour : {', '.join(titres_selectionnes)}

Identifie UNE entreprise cotee en bourse liee a ces actualites.

Analyse en 200 mots :
- Nom et secteur
- Lien direct avec l'actualite du jour
- Ce qui peut faire bouger le titre
- Risques concrets
- Un fait peu connu sur cette entreprise

Ne donne AUCUN prix precis car tu n'as pas acces aux donnees en temps reel.
Termine par : "Analyse pedagogique uniquement, pas un conseil financier."
Sans Markdown."""

invest = groq_call(prompt_invest, tokens=800)
send(f"\n{'='*30}\n💰 INVESTISSEMENT DU JOUR\n{'='*30}\n\n{invest}")

# -----------------------------
# SYNTHESE
# -----------------------------
prompt_synthese = f"""Date : {date_complete}
Sujets analyses : {', '.join(titres_selectionnes)}

Ecris une synthese de 150 mots. Pas un resume — une lecture transversale. Quelle tendance profonde relie ces evenements ? Qu'est-ce que ca dit du monde aujourd'hui ?

Sans Markdown."""

synthese = groq_call(prompt_synthese, tokens=500)
send(f"\n{'='*30}\n📊 SYNTHESE FINALE\n{'='*30}\n\n{synthese}\n{'='*30}\nFin du rapport — {date_complete} 🗞")
