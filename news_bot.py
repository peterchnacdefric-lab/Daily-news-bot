import os, requests, xml.etree.ElementTree as ET, time, re
from groq import Groq
from datetime import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
GROQ_KEY = os.environ["GROQ_KEY"]

now = datetime.now()
date_complete = now.strftime("%A %d %B %Y")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def send(text):
    for i in range(0, len(text), 4000):
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text[i:i+4000]})
        time.sleep(0.5)

def sep(titre):
    return f"\n\n{'═'*35}\n{titre}\n{'═'*35}\n\n"

def groq_call(prompt, tokens=1000):
    time.sleep(3)
    c = Groq(api_key=GROQ_KEY)
    r = c.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=tokens,
        temperature=0.7)
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
    ("Le Monde",      "https://www.lemonde.fr/rss/une.xml"),
    ("Le Figaro",     "https://www.lefigaro.fr/rss/figaro_actualites.xml"),
    ("France Info",   "https://www.francetvinfo.fr/titres.rss"),
    ("BBC World",     "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("RFI",           "https://www.rfi.fr/fr/rss"),
    ("Les Echos",     "https://feeds.lesechos.fr/lesechos-unes"),
    ("La Vanguardia", "https://www.lavanguardia.com/rss/home.xml"),
    ("The Guardian",  "https://www.theguardian.com/world/rss"),
    ("Liberation",    "https://www.liberation.fr/arc/outboundfeeds/rss/"),
    ("BBC Business",  "https://feeds.bbci.co.uk/news/business/rss.xml"),
]

articles = []

for nom, feed in feeds:
    try:
        r = requests.get(feed, timeout=15, headers=H)
        root = ET.fromstring(r.content)
        items = root.findall(".//item")
        for item in items[:3]:
            title = item.find("title")
            link = item.find("link")
            desc = item.find("description")
            content = item.find("{http://purl.org/rss/1.0/modules/content/}encoded")
            summary = item.find("{http://www.w3.org/2005/Atom}summary")

            if title is None or not title.text or len(title.text.strip()) < 20:
                continue

            lien = ""
            if link is not None and link.text:
                lien = link.text.strip()

            contexte = ""
            if content is not None and content.text:
                contexte = re.sub(r'<[^>]+>', ' ', content.text).strip()[:2000]
            elif summary is not None and summary.text:
                contexte = re.sub(r'<[^>]+>', ' ', summary.text).strip()[:2000]
            elif desc is not None and desc.text:
                contexte = re.sub(r'<[^>]+>', ' ', desc.text).strip()[:2000]

            contexte = re.sub(r'\s+', ' ', contexte).strip()

            articles.append({
                "titre": title.text.strip(),
                "source": nom,
                "lien": lien,
                "contexte": contexte
            })
    except:
        continue

crypto = get_crypto()
marches = get_marches()

send(f"📅 Samuel — Daily News\n{date_complete}")

titres_pour_selection = "\n".join([f"[{a['source']}] {a['titre']}" for a in articles])

selection = groq_call(f"""Voici des titres d'actualite du {date_complete}, chacun avec sa source.

Selectionne exactement 6 titres les plus importants et varies : geopolitique, economie mondiale, tech, sante, science, societe. Un seul par theme.

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
    contexte = art["contexte"]

    if len(contexte) > 80:
        prompt = f"""Tu es un journaliste expert. Date : {date_complete}.

Titre : {titre}
Source : {source}
Contenu RSS :
{contexte}

Reponds TOUJOURS en FRANCAIS.

Ecris une analyse en 3 blocs séparés par UNE ligne vide. Sans titres. Sans Markdown.

BLOC 1 — RESUME (5 a 7 lignes)
Résume les faits concrets. Chiffres, noms, dates si disponibles. Ne reformule pas le titre.

BLOC 2 — EXPLICATION SIMPLE (3 a 4 lignes)
Explique comme pour un enfant de 10 ans. Pourquoi c'est important ?

BLOC 3 — LE SAVIEZ-VOUS (2 lignes)
Un seul fait surprenant et verifiable lié au sujet.

Maximum 180 mots."""
    else:
        prompt = f"""Tu es un journaliste expert. Date : {date_complete}.

Titre : {titre}
Source : {source}

Pas de contenu disponible. Reponds en FRANCAIS en 3 blocs séparés par UNE ligne vide. Sans titres. Sans Markdown.

BLOC 1 (4 lignes) : Ce que ce titre annonce, contexte général honnête.
BLOC 2 (3 lignes) : Explication simple pour un enfant de 10 ans.
BLOC 3 (2 lignes) : Un fait surprenant lié au sujet.

Maximum 150 mots. Ne pas inventer de chiffres précis."""

    analyse = groq_call(prompt, tokens=500)

    entete = f"📰 {i}/6 — {titre.upper()}\n📡 {source}"
    bloc = sep(entete) + analyse
    if lien:
        bloc += f"\n\n🔗 {lien}"
    send(bloc)

# MARCHES
if marches:
    texte_marches = sep("📈 MARCHES — DONNEES EN TEMPS REEL")
    for nom, d in marches.items():
        emoji = "🟢" if d["change"] > 0 else "🔴"
        texte_marches += f"{emoji} {nom} : {d['prix']:.2f} ({d['change']:+.2f}%)\n"
    send(texte_marches)

# CRYPTO
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
        f"Source : CoinGecko"
    )
    send(sep("₿ CRYPTO — DONNEES EN TEMPS REEL") + donnees_crypto)

# CONSEIL INVESTISSEMENT
titres_analyses = [a["titre"] for a in articles_selectionnes[:6]]
marches_texte = ""
if marches:
    for nom, d in marches.items():
        marches_texte += f"{nom} : {d['prix']:.2f} ({d['change']:+.2f}%)\n"

invest = groq_call(f"""Tu es un analyste financier mondial expert. Date : {date_complete}.

Actualites du jour :
{chr(10).join(titres_analyses)}

Marches en temps reel :
{marches_texte}

Ecris un conseil d'investissement en 4 blocs séparés par UNE ligne vide. Sans titres. Sans Markdown. En FRANCAIS.

BLOC 1 — LA NEWS ECONOMIQUE DU JOUR (4 lignes)
Quelle est la tendance economique mondiale la plus importante aujourd'hui ? Basee sur les actualites et les marches reels.

BLOC 2 — OU INVESTIR AUJOURD'HUI (4 lignes)
1 secteur ou actif precis a surveiller aujourd'hui et pourquoi. Lie directement aux actualites du jour. Sois concret.

BLOC 3 — CONTEXTE ET RISQUES (3 lignes)
Pourquoi ce choix ? Quels sont les risques reels ?

BLOC 4 — FUN FACT FINANCE (2 lignes)
Un fait surprenant sur les marches ou l'investissement que la plupart des gens ignorent.

Termine par : Ceci est une analyse pedagogique, pas un conseil financier professionnel.
Maximum 200 mots.""", tokens=600)

send(sep("💼 ECONOMIE & INVESTISSEMENT DU JOUR") + invest)

# SYNTHESE
synthese = groq_call(f"""Date : {date_complete}
Sujets du jour :
{chr(10).join(titres_analyses)}

Synthese de 5 lignes maximum. Lecture transversale du monde aujourd'hui.
Termine par une phrase forte. Sans Markdown. En FRANCAIS.""", tokens=200)

send(sep("📊 SYNTHESE DU JOUR") + synthese + f"\n\n{'═'*35}\n🗞 Fin du rapport — {date_complete}")
