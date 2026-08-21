import os, requests, xml.etree.ElementTree as ET, time, re
from groq import Groq
from datetime import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
GROQ_KEY = os.environ["GROQ_KEY"]

now = datetime.now()
date_complete = now.strftime("%A %d %B %Y")

H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def send(text):
    for i in range(0, len(text), 4000):
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": text[i:i+4000]
            }
        )
        time.sleep(0.5)


def sep(titre):
    return f"\n\n{'═'*35}\n{titre}\n{'═'*35}\n\n"


def groq_call(prompt, tokens=1000):
    last_error = None

    for attempt in range(3):
        try:
            time.sleep(3)

            c = Groq(api_key=GROQ_KEY)

            r = c.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=tokens,
                temperature=0.5
            )

            content = r.choices[0].message.content

            if content and content.strip():
                return content.strip()

        except Exception as e:
            last_error = e

        time.sleep(5)

    if last_error:
        raise last_error

    return ""


def analyse_article(titre, source, contexte):

    if len(contexte) > 80:

        prompt = f"""Tu es journaliste.

Date : {date_complete}

Titre : {titre}
Source : {source}

Contenu :
{contexte}

Réponds uniquement en français.

Fais une analyse courte en 3 paragraphes.

Premier paragraphe :
résume les faits importants en 4 à 5 lignes.

Deuxième paragraphe :
explique simplement pourquoi cette information est importante en 3 lignes.

Troisième paragraphe :
donne un fait intéressant et vérifiable lié au sujet en 2 lignes.

Maximum 150 mots.

N'utilise aucun titre.
N'utilise pas de Markdown."""

    else:

        prompt = f"""Tu es journaliste.

Date : {date_complete}

Titre : {titre}
Source : {source}

Le contenu détaillé n'est pas disponible.

Explique cette actualité en français.

Fais 3 courts paragraphes :

1. Ce que l'on sait et ce que le titre annonce.
2. Pourquoi cette actualité est importante.
3. Un fait intéressant lié au sujet.

Maximum 120 mots.

Ne pas inventer de chiffres ou de faits précis.
N'utilise aucun titre.
N'utilise pas de Markdown."""

    try:

        resultat = groq_call(
            prompt,
            tokens=400
        )

        if resultat and len(resultat.strip()) > 30:
            return resultat.strip()

    except:
        pass

    # FALLBACK
    try:

        fallback = groq_call(
            f"""Explique en français cette actualité en environ 100 mots.

Titre : {titre}
Source : {source}

Donne uniquement une explication claire et factuelle.""",
            tokens=250
        )

        if fallback and len(fallback.strip()) > 20:
            return fallback.strip()

    except:
        pass

    return (
        f"Cette actualité concerne : {titre}. "
        f"La source indiquée est {source}. "
        f"Le contenu détaillé n'a pas pu être analysé automatiquement."
    )


def get_crypto():

    try:

        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price"
            "?ids=bitcoin,ethereum,solana"
            "&vs_currencies=usd"
            "&include_24hr_change=true",
            timeout=10
        )

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

    for nom, symbole in symboles.items():

        try:

            r = requests.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{symbole}?interval=1d&range=2d",
                timeout=10,
                headers=H
            )

            data = r.json()["chart"]["result"][0]["meta"]

            prix = data["regularMarketPrice"]
            previous = data["previousClose"]

            res[nom] = {
                "prix": prix,
                "change": ((prix - previous) / previous) * 100
            }

        except:

            continue

    return res


feeds = [
    ("Le Monde", "https://www.lemonde.fr/rss/une.xml"),
    ("Le Figaro", "https://www.lefigaro.fr/rss/figaro_actualites.xml"),
    ("France Info", "https://www.francetvinfo.fr/titres.rss"),
    ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("RFI", "https://www.rfi.fr/fr/rss"),
    ("Les Echos", "https://feeds.lesechos.fr/lesechos-unes"),
    ("La Vanguardia", "https://www.lavanguardia.com/rss/home.xml"),
    ("The Guardian", "https://www.theguardian.com/world/rss"),
    ("Liberation", "https://www.liberation.fr/arc/outboundfeeds/rss/"),
    ("BBC Business", "https://feeds.bbci.co.uk/news/business/rss.xml")
]


articles = []


for nom, feed in feeds:

    try:

        r = requests.get(
            feed,
            timeout=15,
            headers=H
        )

        root = ET.fromstring(r.content)

        items = root.findall(".//item")

        for item in items[:3]:

            title = item.find("title")
            link = item.find("link")
            desc = item.find("description")

            content = item.find(
                "{http://purl.org/rss/1.0/modules/content/}encoded"
            )

            summary = item.find(
                "{http://www.w3.org/2005/Atom}summary"
            )

            if title is None or not title.text:
                continue

            titre = title.text.strip()

            if len(titre) < 20:
                continue

            lien = ""

            if link is not None and link.text:
                lien = link.text.strip()

            contexte = ""

            if content is not None and content.text:

                contexte = re.sub(
                    r"<[^>]+>",
                    " ",
                    content.text
                )

            elif summary is not None and summary.text:

                contexte = re.sub(
                    r"<[^>]+>",
                    " ",
                    summary.text
                )

            elif desc is not None and desc.text:

                contexte = re.sub(
                    r"<[^>]+>",
                    " ",
                    desc.text
                )

            contexte = re.sub(
                r"\s+",
                " ",
                contexte
            ).strip()

            contexte = contexte[:2000]

            articles.append({
                "titre": titre,
                "source": nom,
                "lien": lien,
                "contexte": contexte
            })

    except:

        continue


crypto = get_crypto()
marches = get_marches()


send(
    f"📅 Samuel — Daily News\n{date_complete}"
)


titres_pour_selection = "\n".join(
    [
        f"[{a['source']}] {a['titre']}"
        for a in articles
    ]
)


selection = groq_call(
    f"""Voici des titres d'actualité du {date_complete}.

Sélectionne exactement 6 titres importants et variés.

Essaie de couvrir :
- géopolitique
- économie
- technologie
- santé ou science
- société
- environnement

Un seul titre par thème si possible.

Réponds uniquement avec les 6 titres.
Un titre par ligne.
Copie les titres exactement.

TITRES :

{titres_pour_selection}""",
    tokens=400
)


lignes_selectionnees = [
    ligne.strip()
    for ligne in selection.split("\n")
    if len(ligne.strip()) > 20
][:6]


articles_selectionnes = []


for ligne in lignes_selectionnees:

    for article in articles:

        if (
            article["titre"] in ligne
            or ligne in article["titre"]
        ):

            if article not in articles_selectionnes:
                articles_selectionnes.append(article)

            break


if len(articles_selectionnes) < 6:

    for article in articles:

        if article not in articles_selectionnes:

            articles_selectionnes.append(article)

        if len(articles_selectionnes) >= 6:
            break


for i, article in enumerate(
    articles_selectionnes[:6],
    1
):

    titre = article["titre"]
    source = article["source"]
    lien = article["lien"]
    contexte = article["contexte"]

    analyse = analyse_article(
        titre,
        source,
        contexte
    )

    entete = (
        f"📰 {i}/6 — {titre.upper()}\n"
        f"📡 {source}"
    )

    bloc = sep(entete) + analyse

    if lien:

        bloc += f"\n\n🔗 {lien}"

    send(bloc)


# MARCHES

if marches:

    texte_marches = sep(
        "📈 MARCHES — DONNEES EN TEMPS REEL"
    )

    for nom, data in marches.items():

        emoji = (
            "🟢"
            if data["change"] > 0
            else "🔴"
        )

        texte_marches += (
            f"{emoji} {nom} : "
            f"{data['prix']:.2f} "
            f"({data['change']:+.2f}%)\n"
        )

    send(texte_marches)


# CRYPTO

if crypto:

    btc = crypto.get("bitcoin", {})
    eth = crypto.get("ethereum", {})
    sol = crypto.get("solana", {})

    btc_e = (
        "🟢"
        if btc.get("usd_24h_change", 0) > 0
        else "🔴"
    )

    eth_e = (
        "🟢"
        if eth.get("usd_24h_change", 0) > 0
        else "🔴"
    )

    sol_e = (
        "🟢"
        if sol.get("usd_24h_change", 0) > 0
        else "🔴"
    )

    donnees_crypto = (
        f"{btc_e} Bitcoin  : "
        f"${btc.get('usd', 0):,.0f} "
        f"({btc.get('usd_24h_change', 0):+.2f}%)\n"

        f"{eth_e} Ethereum : "
        f"${eth.get('usd', 0):,.0f} "
        f"({eth.get('usd_24h_change', 0):+.2f}%)\n"

        f"{sol_e} Solana   : "
        f"${sol.get('usd', 0):,.0f} "
        f"({sol.get('usd_24h_change', 0):+.2f}%)\n\n"

        "Source : CoinGecko"
    )

    send(
        sep(
            "₿ CRYPTO — DONNEES EN TEMPS REEL"
        )
        + donnees_crypto
    )


# INVESTISSEMENT

titres_analyses = [
    article["titre"]
    for article in articles_selectionnes[:6]
]


marches_texte = ""

if marches:

    for nom, data in marches.items():

        marches_texte += (
            f"{nom} : "
            f"{data['prix']:.2f} "
            f"({data['change']:+.2f}%)\n"
        )


crypto_texte = ""

if crypto:

    btc = crypto.get("bitcoin", {})
    eth = crypto.get("ethereum", {})

    crypto_texte = (
        f"Bitcoin : "
        f"${btc.get('usd', 0):,.0f} "
        f"({btc.get('usd_24h_change', 0):+.2f}%)\n"

        f"Ethereum : "
        f"${eth.get('usd', 0):,.0f} "
        f"({eth.get('usd_24h_change', 0):+.2f}%)"
    )


try:

    invest = groq_call(
        f"""Tu es un analyste financier.

Date : {date_complete}

Actualités :
{chr(10).join(titres_analyses)}

Marchés :
{marches_texte}

Crypto :
{crypto_texte}

Réponds en français.

Donne 5 courts paragraphes :

1. Tendance économique mondiale aujourd'hui.
2. Une action à surveiller avec son ticker.
3. Un secteur ou actif alternatif à surveiller.
4. Les principaux risques.
5. Un fun fact sur l'investissement.

Sois concret et précis.

Maximum 220 mots.

Termine par :
Analyse pédagogique uniquement, pas un conseil financier professionnel.""",
        tokens=600
    )

except:

    invest = (
        "L'analyse d'investissement n'a pas pu être générée "
        "aujourd'hui."
    )


send(
    sep("💼 INVESTISSEMENT DU JOUR")
    + invest
)


# SYNTHESE

try:

    synthese = groq_call(
        f"""Date : {date_complete}

Actualités principales :

{chr(10).join(titres_analyses)}

Fais une synthèse du monde aujourd'hui.

Maximum 5 lignes.

Français uniquement.
Sans Markdown.

Termine par une phrase forte.""",
        tokens=250
    )

except:

    synthese = (
        "La synthèse du jour n'a pas pu être générée."
    )


send(
    sep("📊 SYNTHESE DU JOUR")
    + synthese
    + f"\n\n{'═'*35}\n"
      f"🗞 Fin du rapport — {date_complete}"
)
