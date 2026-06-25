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
    return f"\n\n{'═'*35}\n{titre}\n{'═'*35}\n\n"

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

send(f"🗞 RAPPORT QUOTIDIEN\n📅 {date_complete}\n📰 {len(tous_les_titres)} titres collectes\n{'═'*35}")

selection = groq_call(f"""Voici des titres d'actualite du {date_complete}.
Selectionne exactement 10 titres les plus importants et varies : geopolitique, economie, tech, sante, science, societe, environnement, culture. Maximum 1 titre par theme.
Reponds UNIQUEMENT avec les 10 titres, un par ligne, sans numero ni commentaire.
TITRES :
{chr(10).join(tous_les_titres[:80])}""", tokens=600)

titres = [t.strip() for t in selection.strip().split("\n") if len(t.strip()) > 20][:10]

for i, titre in enumerate(titres, 1):
    analyse = groq_call(f"""Tu es un journaliste expert. Date : {date_complete}.

Sujet : {titre}

Redige une analyse en 3 blocs EXACTEMENT, separes par une ligne vide entre chaque bloc. Sans Markdown, sans titres de section.

BLOC 1 — L'ESSENTIEL (entre 10 et 15 lignes)
Explique clairement ce qui se passe. Qui sont les acteurs ? Quels sont les enjeux concrets ? Pourquoi c'est important aujourd'hui ? Donne des chiffres et des faits precis. Ecris de facon fluide et journalistique, pas en liste.

[ligne vide]

BLOC 2 — LES TERMES A CONNAITRE (5 a 8 lignes)
Explique simplement les 2 ou 3 termes techniques ou concepts importants lies a ce sujet. Style dictionnaire simple, accessible a tous.

[ligne vide]

BLOC 3 — CE QUE TU NE SAVAIS PAS (5 a 8 lignes)
Un ou deux faits surprenants, peu connus ou contre-intuitifs sur ce sujet. Quelque chose qui etonne, qui fait reflechir, ou qui donne une nouvelle perspective. Style curieux et vivant.

Sans Markdown. Sans titres de section. Juste les 3 blocs separes par une ligne vide.""", tokens=2000)

    send(sep(f"📰 {i}/10 — {titre.upper()}") + analyse)

# MARCHES
if marches:
    texte_marches = sep("📈 MARCHES FINANCIERS — EN TEMPS REEL")
    for nom, d in marches.items():
        emoji = "🟢" if d["change"] > 0 else "🔴"
        texte_marches += f"{emoji} {nom} : {d['prix']:.2f} ({d['change']:+.2f}%)\n"
    send(texte_marches)

# CRYPTO
if crypto:
    btc = crypto.get("bitcoin", {})
    eth = crypto.get("ethereum", {})
    sol = crypto.get("solana", {})

    donnees_crypto = (
        f"₿  Bitcoin  : ${btc.get('usd', 0):,.0f}  ({btc.get('usd_24h_change', 0):+.2f}%)\n"
        f"Ξ  Ethereum : ${eth.get('usd', 0):,.0f}  ({eth.get('usd_24h_change', 0):+.2f}%)\n"
        f"◎  Solana   : ${sol.get('usd', 0):,.0f}  ({sol.get('usd_24h_change', 0):+.2f}%)"
    )

    analyse_crypto = groq_call(f"""Date : {date_complete}
Prix crypto reels :
{donnees_crypto}
Actualites du jour : {', '.join(titres[:4])}

Ecris une analyse courte en 2 blocs separes par une ligne vide :

BLOC 1 (8 lignes) : Que signifie cette tendance ? Quel evenement macro l'explique ?

BLOC 2 (5 lignes) : Une curiosite peu connue sur Bitcoin ou la blockchain.

Sans Markdown. Sans titres.""", tokens=500)

    send(sep("₿ CRYPTO DU JOUR — EN TEMPS REEL") + donnees_crypto + "\n\n" + analyse_crypto)

# INVESTISSEMENT
invest = groq_call(f"""Date : {date_complete}
Sujets du jour : {', '.join(titres)}

Identifie UNE entreprise cotee en bourse liee a ces actualites.
Ecris en 2 blocs separes par une ligne vide :

BLOC 1 (8 lignes) : Nom, secteur, lien avec l'actualite du jour, ce qui peut faire bouger le titre.

BLOC 2 (5 lignes) : Risques concrets + un fait peu connu sur cette entreprise.

Termine par : Analyse pedagogique uniquement, pas un conseil financier.
Sans Markdown. Sans titres.""", tokens=600)

send(sep("💼 INVESTISSEMENT DU JOUR") + invest)

# SYNTHESE
synthese = groq_call(f"""Date : {date_complete}
Sujets analyses : {', '.join(titres)}

Ecris une synthese de 10 lignes maximum. Pas un resume article par article.
Une lecture transversale : quelle tendance profonde relie ces evenements ?
Qu'est-ce que ca dit du monde aujourd'hui ? Termine par une phrase forte et marquante.
Sans Markdown.""", tokens=400)

send(sep("📊 SYNTHESE DU JOUR") + synthese + f"\n\n{'═'*35}\n🗞 Fin du rapport — {date_complete}")
