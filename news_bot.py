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
    ("BBC World",      "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("Reuters",        "https://feeds.reuters.com/reuters/topNews"),
    ("Yahoo Finance",  "https://finance.yahoo.com/news/rssindex"),
    ("RFI",            "https://www.rfi.fr/fr/rss"),
    ("Liberation",     "https://www.liberation.fr/arc/outboundfeeds/rss/"),
    ("Les Echos",      "https://feeds.lesechos.fr/lesechos-unes"),
    ("Der Spiegel EN", "https://www.spiegel.de/international/index.rss"),
    ("El Pais EN",     "https://feeds.elpais.com/mrss-s/pages/ep/site/english.elpais.com/portada"),
    ("The Guardian",   "https://www.theguardian.com/world/rss"),
]

articles = []

for nom, feed in feeds:
    try:
        r = requests.get(feed, timeout=15, headers=H)
        root = ET.fromstring(r.content)
        items = root.findall(".//item")
        if items:
            item = items[0]
            title = item.find("title")
            link = item.find("link")
            if title is not None and title.text and len(title.text.strip()) > 20:
                lien = ""
                if link is not None and link.text:
                    lien = link.text.strip()
                else:
                    lien = item.find("{http://www.w3.org/2005/Atom}link")
                    if lien is not None:
                        lien = lien.get("href", "")
                    else:
                        lien = ""
                articles.append({
                    "titre": title.text.strip(),
                    "source": nom,
                    "lien": lien
                })
    except:
        continue

crypto = get_crypto()
marches = get_marches()

send(f"📅 Samuel — Daily News\n{date_complete}")

titres_pour_selection = "\n".join([f"[{a['source']}] {a['titre']}" for a in articles])

selection = groq_call(f"""Voici des titres d'actualite du {date_complete}, chacun avec sa source.

Selectionne exactement 6 titres les plus importants et varies : geopolitique, economie, tech, sante, science, societe. Un seul par theme.

Reponds UNIQUEMENT avec les 6 titres selectionnes, un par ligne, exactement comme ils sont ecrits, sans numero ni commentaire.

TITRES :
{titres_pour_selection}""", tokens=500)

lignes_selectionnees = [l.strip() for l in selection.strip().split("\n") if len(l.strip()) > 20][:6]

articles_selectionnes = []
for ligne in lignes_selectionnees:
    for a in articles:
        if a["titre"] in ligne or ligne in a["titre"]:
            if a not in articles_selectionnes:
                articles_selectionnes.append(a)
                break

if len(articles_selectionnes) < 6:
    for a in articles:
        if a not in articles_selectionnes:
            articles_selectionnes.append(a)
        if len(articles_selectionnes) >= 6:
            break

for i, art in enumerate(articles_selectionnes[:6], 1):
    titre = art["titre"]
    source = art["source"]
    lien = art["lien"]

    analyse = groq_call(f"""Tu es un journaliste expert. Date : {date_complete}.

Titre exact : {titre}
Source : {source}

IMPORTANT : Base-toi uniquement sur ce titre. Ne complete pas avec des informations incertaines.

Ecris une analyse en 3 blocs. Entre chaque bloc, laisse UNE ligne vide. Sans titres. Sans Markdown.

BLOC 1 — RESUME (5 a 7 lignes)
Explique ce que ce titre annonce. Reste factuel et prudent si tu manques de details.

BLOC 2 — MOTS CLES (3 a 4 lignes)
Explique 2 termes techniques ou concepts importants. Simple et accessible.

BLOC 3 — LE SAVIEZ-VOUS (2 a 3 lignes)
Un fait verifiable et surprenant lie au contexte de ce sujet.

Maximum 180 mots au total.""", tokens=500)

    entete = f"📰 {i}/6 — {titre.upper()}\n📡 {source}"
    bloc = sep(entete) + analyse
    if lien:
        bloc += f"\n\n🔗 Lire l'article : {lien}"
    send(bloc)

if marches:
    texte_marches = sep("📈 MARCHES — DONNEES EN TEMPS REEL")
    for nom, d in marches.items():
        emoji = "🟢" if d["change"] > 0 else "🔴"
        texte_marches += f"{emoji} {nom} : {d['prix']:.2f} ({d['change']:+.2f}%)\n"
    send(texte_marches)

if crypto:
    btc = crypto.get("bitcoin", {})
    eth = crypto.get("ethereum", {})
    sol = crypto.get("solana", {})

    btc_e = "🟢" if btc.get("usd_24h_change", 0) > 0 else "🔴"
    eth_e = "🟢" if eth.get("usd_24h_change", 0) > 0 else "🔴"
    sol_e = "🟢" if sol.get("usd_24h_change", 0) > 0 else "🔴"

    donnees_crypto = (
        f"{btc_e} Bitcoin  : ${btc.get('usd', 0):,.0f}  ({btc.get('usd_24h_change', 0):+.2f}%)\n"
        f"{eth_e} Ethereum : ${eth.get('usd', 0):,.0f}  ({eth.get('usd_24h_change', 0):+.2f}%)\n"
        f"{sol_e} Solana   : ${sol.get('usd', 0):,.0f}  ({sol.get('usd_24h_change', 0):+.2f}%)\n\n"
        f"Source : CoinGecko (temps reel)"
    )

    send(sep("₿ CRYPTO — DONNEES EN TEMPS REEL") + donnees_crypto)

titres_analyses = [a["titre"] for a in articles_selectionnes[:6]]
synthese = groq_call(f"""Date : {date_complete}
Sujets du jour :
{chr(10).join(titres_analyses)}

Synthese de 5 lignes maximum. Lecture transversale du monde aujourd'hui.
Termine par une phrase forte. Sans Markdown.""", tokens=200)

send(sep("📊 SYNTHESE DU JOUR") + synthese + f"\n\n{'═'*35}\n🗞 Fin du rapport — {date_complete}")
