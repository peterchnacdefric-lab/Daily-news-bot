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

def groq_call(prompt, tokens=1200):
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
    ("Le Monde",       "https://www.lemonde.fr/rss/une.xml"),
    ("Le Figaro",      "https://www.lefigaro.fr/rss/figaro_actualites.xml"),
    ("France Info",    "https://www.francetvinfo.fr/titres.rss"),
    ("BBC Monde",      "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("Reuters",        "https://feeds.reuters.com/reuters/topNews"),
    ("Yahoo Finance",  "https://finance.yahoo.com/news/rssindex"),
    ("Google Monde",   "https://news.google.com/rss/headlines/section/topic/WORLD?hl=fr&gl=FR&ceid=FR:fr"),
    ("Google Eco",     "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=fr&gl=FR&ceid=FR:fr"),
    ("Google Tech",    "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=fr&gl=FR&ceid=FR:fr"),
    ("Google Sante",   "https://news.google.com/rss/headlines/section/topic/HEALTH?hl=fr&gl=FR&ceid=FR:fr"),
    ("Google Science", "https://news.google.com/rss/headlines/section/topic/SCIENCE?hl=fr&gl=FR&ceid=FR:fr"),
]

tous_les_titres = []
sources_map = {}

for nom, feed in feeds:
    try:
        r = requests.get(feed, timeout=15, headers=H)
        root = ET.fromstring(r.content)
        for item in root.findall(".//item")[:12]:
            title = item.find("title")
            source = item.find("source")
            if title is not None and title.text:
                texte = title.text.strip()
                if texte not in tous_les_titres and len(texte) > 20:
                    tous_les_titres.append(texte)
                    if source is not None and source.text:
                        sources_map[texte] = source.text.strip()
                    else:
                        sources_map[texte] = nom
    except:
        continue

crypto = get_crypto()
marches = get_marches()

# Premier message : juste la date
send(f"📅 Samuel — Daily News\n{date_complete}")

selection = groq_call(f"""Voici des titres d'actualite du {date_complete}.
Selectionne exactement 6 titres les plus importants et varies : geopolitique, economie, tech, sante, science, societe. Un seul par theme.
Reponds UNIQUEMENT avec les 6 titres, un par ligne, sans numero ni commentaire.
TITRES :
{chr(10).join(tous_les_titres[:80])}""", tokens=400)

titres = [t.strip() for t in selection.strip().split("\n") if len(t.strip()) > 20][:6]

for i, titre in enumerate(titres, 1):
    source_affichee = sources_map.get(titre, "Presse internationale")

    analyse = groq_call(f"""Tu es un journaliste expert. Date : {date_complete}.

Sujet : {titre}
Source : {source_affichee}

Ecris une analyse courte et percutante en 3 blocs. Entre chaque bloc, laisse UNE ligne vide. Sans titres de section. Sans Markdown.

BLOC 1 — RESUME (6 a 8 lignes maximum)
Explique clairement ce qui se passe. Qui, quoi, pourquoi maintenant. Chiffres concrets si disponibles. Direct et factuel.

BLOC 2 — MOTS CLES (3 a 5 lignes)
Explique simplement 2 termes techniques ou concepts importants lies a ce sujet. Style simple et accessible.

BLOC 3 — LE SAVIEZ-VOUS (3 a 4 lignes)
Un seul fait surprenant, peu connu ou contre-intuitif sur ce sujet. Quelque chose qui etonne vraiment.

Maximum 200 mots au total. Concis, precis, interessant.""", tokens=600)

    entete = f"📰 {i}/6 — {titre.upper()}\n📡 {source_affichee}"
    send(sep(entete) + analyse)

# MARCHES
if marches:
    texte_marches = sep("📈 MARCHES — EN TEMPS REEL")
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

    analyse_crypto = groq_call(f"""Prix crypto reels :
{donnees_crypto}

Ecris 2 blocs separes par une ligne vide. Sans titres. Sans Markdown. Maximum 100 mots.

BLOC 1 (4 lignes) : Que signifie cette tendance ? Quel evenement explique ce mouvement ?
BLOC 2 (3 lignes) : Une curiosite peu connue sur Bitcoin ou la blockchain.""", tokens=300)

    send(sep("₿ CRYPTO — EN TEMPS REEL") + donnees_crypto + "\n\n" + analyse_crypto)

# INVESTISSEMENT
invest = groq_call(f"""Sujets du jour : {', '.join(titres)}

Identifie UNE entreprise cotee liee a ces actualites.
2 blocs separes par une ligne vide. Sans titres. Sans Markdown. Maximum 120 mots.

BLOC 1 (5 lignes) : Nom, secteur, lien avec l'actualite, ce qui peut faire bouger le titre.
BLOC 2 (3 lignes) : Risques + un fait peu connu sur cette entreprise.

Termine par : Analyse pedagogique uniquement, pas un conseil financier.""", tokens=350)

send(sep("💼 INVESTISSEMENT DU JOUR") + invest)

# SYNTHESE
synthese = groq_call(f"""Sujets analyses : {', '.join(titres)}

Synthese de 6 lignes maximum. Pas un resume — une lecture transversale du monde aujourd'hui.
Termine par une phrase forte et marquante. Sans Markdown.""", tokens=250)

send(sep("📊 SYNTHESE DU JOUR") + synthese + f"\n\n{'═'*35}\n🗞 Fin du rapport — {date_complete}")
