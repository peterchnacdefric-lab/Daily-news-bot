import os, requests, xml.etree.ElementTree as ET, time
from groq import Groq
from datetime import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
GROQ_KEY = os.environ["GROQ_KEY"]

now = datetime.now()
date_complete = now.strftime("%A %d %B %Y")
H = {"User-Agent": "Mozilla/5.0"}

def send(text):
    for i in range(0, len(text), 4000):
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text[i:i+4000]})
        time.sleep(0.5)

def sep(titre):
    return f"\n\n{'─'*35}\n◆ {titre}\n{'─'*35}\n\n"

def groq_call(prompt, tokens=2000):
    time.sleep(3)
    c = Groq(api_key=GROQ_KEY)
    r = c.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=tokens,
        temperature=0.85)
    return r.choices[0].message.content

def get_crypto():
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd&include_24hr_change=true",
            timeout=10)
        return r.json()
    except:
        return None

def get_marches():
    res = {}
    symboles = {
        "CAC 40": "%5EFCHI",
        "S&P 500": "%5EGSPC",
        "Petrole Brent": "BZ%3DF",
        "Or": "GC%3DF",
        "EUR/USD": "EURUSD%3DX"
    }
    for nom, s in symboles.items():
        try:
            r = requests.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{s}?interval=1d&range=2d",
                timeout=10, headers=H)
            d = r.json()["chart"]["result"][0]["meta"]
            prix = d["regularMarketPrice"]
            prev = d["previousClose"]
            res[nom] = {"prix": prix, "change": ((prix - prev) / prev) * 100}
        except:
            continue
    return res

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
        r = requests.get(feed, timeout=15, headers=H)
        root = ET.fromstring(r.content)
        for item in root.findall(".//item")[:12]:
            title = item.find("title")
            if title is not None and title.text:
                texte = title.text.strip()
                if texte not in tous_les_titres and len(texte) > 20:
                    tous_les_titres.append(texte)
    except:
        continue

crypto = get_crypto()
marches = get_marches()

send(f"🗞 RAPPORT QUOTIDIEN\n📅 {date_complete}\n📰 {len(tous_les_titres)} titres collectes\n{'─'*35}")

selection = groq_call(f"""Voici des titres d'actualite du {date_complete}.
Selectionne exactement 6 titres les plus importants et varies : geopolitique, economie, tech, sante, science, societe. Un seul par theme.
Reponds UNIQUEMENT avec les 6 titres, un par ligne, sans numero ni commentaire.
TITRES :
{chr(10).join(tous_les_titres[:60])}""", tokens=400)

titres = [t.strip() for t in selection.strip().split("\n") if len(t.strip()) > 20][:6]

for i, titre in enumerate(titres, 1):
    analyse = groq_call(f"""Tu es un journaliste analyste expert. Date : {date_complete}.
Sujet : {titre}

Redige une analyse complete et longue. Structure OBLIGATOIRE (sans Markdown) :

LES FAITS
Que se passe-t-il exactement ? Acteurs, chiffres, enjeux concrets. Minimum 80 mots.

LE CONTEXTE HISTORIQUE
Pourquoi maintenant ? Histoire et evenements passes. Dates et faits precis. Minimum 80 mots.

LE MECANISME
Comment ca fonctionne vraiment ? Rouages economiques ou politiques. Definis chaque terme technique. Minimum 80 mots.

LA CURIOSITE
Un fait surprenant, peu connu ou contre-intuitif. Ce que 95% des gens ignorent sur ce sujet. Minimum 40 mots.

LES CONSEQUENCES REELLES
Impact concret sur la vie des gens ordinaires. Exemples tres precis. Minimum 60 mots.

LA PROJECTION
Ce qui va probablement se passer dans les 4 prochaines semaines. Realiste et argumente. Minimum 50 mots.

Total minimum : 400 mots. Style dense, curieux, intelligent. Sans Markdown.""", tokens=2000)

    send(sep(f"SUJET {i}/6 — {titre.upper()}") + analyse)

if marches:
    texte_marches = sep("MARCHES FINANCIERS — DONNEES EN TEMPS REEL")
    for nom, d in marches.items():
        emoji = "🟢" if d["change"] > 0 else "🔴"
        texte_marches += f"{emoji} {nom} : {d['prix']:.2f} ({d['change']:+.2f}%)\n"
    send(texte_marches)

if crypto:
    btc = crypto.get("bitcoin", {})
    eth = crypto.get("ethereum", {})
    sol = crypto.get("solana", {})

    donnees_crypto = f"""Bitcoin : ${btc.get('usd', 0):,.0f} ({btc.get('usd_24h_change', 0):+.2f}% sur 24h)
Ethereum : ${eth.get('usd', 0):,.0f} ({eth.get('usd_24h_change', 0):+.2f}% sur 24h)
Solana : ${sol.get('usd', 0):,.0f} ({sol.get('usd_24h_change', 0):+.2f}% sur 24h)"""

    analyse_crypto = groq_call(f"""Date : {date_complete}
Voici les prix crypto reels :
{donnees_crypto}
Actualites du jour : {', '.join(titres[:3])}

Analyse en 200 mots :
- Que signifie cette tendance aujourd'hui ?
- Quel evenement macro explique ce mouvement ?
- Une curiosite peu connue sur Bitcoin ou la blockchain
- Projection a 2 semaines
Sans Markdown. Ne pas inventer de chiffres.""", tokens=600)

    send(sep("CRYPTO DU JOUR — DONNEES EN TEMPS REEL") + donnees_crypto + "\n\n" + analyse_crypto)

invest = groq_call(f"""Date : {date_complete}
Sujets du jour : {', '.join(titres)}

Identifie UNE entreprise cotee en bourse liee a ces actualites.
Analyse en 200 mots :
- Nom complet et secteur
- Lien direct avec l'actualite du jour
- Ce qui peut faire bouger le titre aujourd'hui
- Risques concrets
- Un fait peu connu sur cette entreprise
Ne donne aucun prix precis car tu n'as pas acces aux donnees temps reel.
Termine par : Analyse pedagogique uniquement, pas un conseil financier.
Sans Markdown.""", tokens=800)

send(sep("INVESTISSEMENT DU JOUR") + invest)

synthese = groq_call(f"""Date : {date_complete}
Sujets analyses : {', '.join(titres)}

Ecris une synthese de 150 mots. Pas un resume — une lecture transversale.
Quelle tendance profonde relie ces evenements ? Qu'est-ce que ca dit du monde aujourd'hui ?
Sans Markdown.""", tokens=500)

send(sep("SYNTHESE FINALE") + synthese + f"\n\n{'─'*35}\nFin du rapport — {date_complete} 🗞")
