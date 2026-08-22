import os
import requests
import xml.etree.ElementTree as ET
import time
import re
from groq import Groq
from datetime import datetime


# ============================================================
# CONFIGURATION
# ============================================================

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
GROQ_KEY = os.environ["GROQ_KEY"]

now = datetime.now()
date_complete = now.strftime("%A %d %B %Y")

H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0 Safari/537.36"
}


# ============================================================
# TELEGRAM
# ============================================================

def send(text):
    if not text:
        return

    for i in range(0, len(text), 4000):
        try:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": CHAT_ID,
                    "text": text[i:i + 4000]
                },
                timeout=15
            )
        except Exception:
            pass

        time.sleep(0.5)


def sep(titre):
    return f"\n\n{'═' * 35}\n{titre}\n{'═' * 35}\n\n"


# ============================================================
# GROQ
# ============================================================
#
# openai/gpt-oss-20b es un modelo "reasoning": antes de escribir la
# respuesta final, gasta tokens "pensando" internamente. Esos tokens
# de razonamiento cuentan dentro del mismo presupuesto que le pasamos
# como límite de tokens de salida. Si el límite es demasiado bajo, el
# modelo se queda sin tokens en pleno razonamiento y la respuesta
# final sale vacía o cortada a la mitad.
#
# Para evitarlo:
#  - reasoning_effort="low" reduce al mínimo ese "pensamiento" interno
#  - max_completion_tokens (en vez del antiguo max_tokens) con margen
#    generoso, para que siempre quede espacio de sobra para la
#    respuesta final.

def groq_call(prompt, tokens=700, retries=3):

    last_error = None

    for attempt in range(retries):

        try:
            time.sleep(2)

            client = Groq(api_key=GROQ_KEY)

            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_completion_tokens=tokens,
                reasoning_effort="low",
                temperature=0.4
            )

            result = response.choices[0].message.content

            if result and result.strip():
                return result.strip()

        except Exception as e:
            last_error = e

        time.sleep(4)

    if last_error:
        raise last_error

    return ""


# ============================================================
# ARTICLE ANALYSIS
# ============================================================

def analyse_article(titre, source, contexte):

    contexte = contexte.strip()

    if len(contexte) > 100:

        prompt = f"""
Tu es un journaliste professionnel.

DATE : {date_complete}

SOURCE : {source}

TITRE :
{titre}

CONTENU RSS :
{contexte}

Analyse uniquement les informations présentes dans le titre et le contenu RSS.

IMPORTANT :
- Ne pas inventer de chiffres.
- Ne pas inventer de déclarations.
- Ne pas ajouter de faits qui ne sont pas dans le contenu.
- Si une information n'est pas disponible, ne la présente pas comme certaine.
- Réponds uniquement en français.
- Aucun Markdown.
- Aucun titre de section.

Structure exactement en 3 paragraphes séparés par une ligne vide :

PARAGRAPHE 1 :
Résumé factuel de l'actualité en 4 à 5 lignes.

PARAGRAPHE 2 :
Explique simplement pourquoi cette actualité est importante, en 3 lignes.

PARAGRAPHE 3 :
Donne un fait intéressant lié au sujet uniquement s'il peut être déduit de manière fiable du contenu fourni. Sinon explique brièvement pourquoi le contexte est important.

Maximum 140 mots.
"""

    else:

        prompt = f"""
Tu es un journaliste professionnel.

DATE : {date_complete}

SOURCE : {source}

TITRE :
{titre}

Le flux RSS ne fournit pas suffisamment de contenu.

Explique cette actualité uniquement à partir du titre.

IMPORTANT :
- Ne pas inventer de chiffres.
- Ne pas inventer de personnes, déclarations ou événements.
- Ne pas présenter des suppositions comme des faits.
- Réponds uniquement en français.
- Aucun Markdown.
- Aucun titre de section.

Fais 3 courts paragraphes :

1. Ce que le titre indique.
2. Pourquoi le sujet peut être important.
3. Ce qui devrait être vérifié ou approfondi.

Maximum 100 mots.
"""

    try:

        result = groq_call(
            prompt,
            tokens=900,
            retries=3
        )

        if result and len(result) > 40:
            return result

    except Exception:
        pass

    # FALLBACK
    try:

        fallback = groq_call(
            f"""
Explique cette actualité en français en 80 mots maximum.

Titre : {titre}
Source : {source}

Utilise uniquement les informations disponibles.
Ne rien inventer.
Aucun Markdown.
""",
            tokens=500,
            retries=2
        )

        if fallback and len(fallback) > 20:
            return fallback

    except Exception:
        pass

    return (
        "L'analyse détaillée de cette actualité n'a pas pu être "
        "générée automatiquement."
    )


# ============================================================
# CRYPTO
# ============================================================

def get_crypto():

    try:

        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price"
            "?ids=bitcoin,ethereum,solana"
            "&vs_currencies=usd"
            "&include_24hr_change=true",
            timeout=10
        )

        return response.json()

    except Exception:

        return None


# ============================================================
# MARKETS
# ============================================================

def get_marches():

    result = {}

    symbols = {
        "CAC 40": "%5EFCHI",
        "S&P 500": "%5EGSPC",
        "Petrole Brent": "BZ%3DF",
        "Or": "GC%3DF",
        "EUR/USD": "EURUSD%3DX"
    }

    for name, symbol in symbols.items():

        try:

            response = requests.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/"
                f"{symbol}?interval=1d&range=2d",
                timeout=10,
                headers=H
            )

            data = response.json()["chart"]["result"][0]["meta"]

            price = data["regularMarketPrice"]
            previous = data["previousClose"]

            change = ((price - previous) / previous) * 100

            result[name] = {
                "prix": price,
                "change": change
            }

        except Exception:

            continue

    return result


# ============================================================
# RSS SOURCES
# ============================================================

feeds = [

    (
        "Le Monde",
        "https://www.lemonde.fr/rss/une.xml"
    ),

    (
        "Le Figaro",
        "https://www.lefigaro.fr/rss/figaro_actualites.xml"
    ),

    (
        "France Info",
        "https://www.francetvinfo.fr/titres.rss"
    ),

    (
        "BBC World",
        "https://feeds.bbci.co.uk/news/world/rss.xml"
    ),

    (
        "RFI",
        "https://www.rfi.fr/fr/rss"
    ),

    (
        "Les Echos",
        "https://feeds.lesechos.fr/lesechos-unes"
    ),

    (
        "La Vanguardia",
        "https://www.lavanguardia.com/rss/home.xml"
    ),

    (
        "The Guardian",
        "https://www.theguardian.com/world/rss"
    ),

    (
        "Liberation",
        "https://www.liberation.fr/arc/outboundfeeds/rss/"
    ),

    (
        "BBC Business",
        "https://feeds.bbci.co.uk/news/business/rss.xml"
    )
]


# ============================================================
# COLLECT ARTICLES
# ============================================================

articles = []


for source, feed in feeds:

    try:

        response = requests.get(
            feed,
            timeout=15,
            headers=H
        )

        root = ET.fromstring(response.content)

        items = root.findall(".//item")

        for item in items[:4]:

            title = item.find("title")
            link = item.find("link")
            description = item.find("description")

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

            elif description is not None and description.text:

                contexte = re.sub(
                    r"<[^>]+>",
                    " ",
                    description.text
                )

            contexte = re.sub(
                r"\s+",
                " ",
                contexte
            ).strip()

            contexte = contexte[:2500]

            articles.append({
                "titre": titre,
                "source": source,
                "lien": lien,
                "contexte": contexte
            })

    except Exception:
        continue


# ============================================================
# REAL-TIME DATA
# ============================================================

crypto = get_crypto()
marches = get_marches()


# ============================================================
# HEADER
# ============================================================

send(
    f"📅 Samuel — Daily News\n"
    f"{date_complete}"
)


# ============================================================
# SELECT THE 6 BEST NEWS
# ============================================================

titles_for_selection = "\n".join(
    [
        f"[{a['source']}] {a['titre']}"
        for a in articles
    ]
)


selection_prompt = f"""
Tu es le rédacteur en chef d'un journal international.

Date : {date_complete}

Voici une liste de titres provenant de plusieurs médias.

Sélectionne exactement les 6 actualités les PLUS IMPORTANTES de la journée.

PRIORITÉ ABSOLUE :

1. Géopolitique internationale
2. Guerres et conflits
3. Économie mondiale
4. Marchés et finance
5. Technologie et IA
6. Science, santé et climat
7. Grandes décisions politiques internationales

ÉVITE absolument :

- tourisme local
- immobilier local
- faits divers locaux
- petites polémiques politiques françaises
- interviews sans conséquence majeure
- lifestyle
- célébrités
- articles uniquement régionaux
- classement de villes
- événements touristiques
- sujets anecdotiques

Une actualité française peut être sélectionnée si elle a une importance nationale ou internationale majeure.

Cherche surtout une sélection INTERNATIONALE et VARIÉE.

Ne sélectionne pas plusieurs articles traitant exactement du même événement.

Réponds UNIQUEMENT avec les 6 titres sélectionnés.

Un titre par ligne.

Copie exactement les titres fournis.

TITRES :

{titles_for_selection}
"""


try:

    selection = groq_call(
        selection_prompt,
        tokens=700,
        retries=3
    )

except Exception:

    selection = ""


selected_lines = [
    line.strip()
    for line in selection.split("\n")
    if len(line.strip()) > 20
][:6]


selected_articles = []


# ============================================================
# MATCH AI SELECTION WITH RSS ARTICLES
# ============================================================

for selected_line in selected_lines:

    for article in articles:

        if (
            article["titre"] in selected_line
            or selected_line in article["titre"]
        ):

            if article not in selected_articles:
                selected_articles.append(article)

            break


# ============================================================
# FALLBACK IF AI SELECTION FAILS
# ============================================================

if len(selected_articles) < 6:

    keywords_priority = [
        "guerre",
        "ukraine",
        "iran",
        "israel",
        "russie",
        "chine",
        "etats-unis",
        "trump",
        "europe",
        "otan",
        "economie",
        "inflation",
        "banque centrale",
        "taux",
        "bourse",
        "pétrole",
        "energie",
        "technologie",
        "ia",
        "intelligence artificielle",
        "climat",
        "science",
        "santé"
    ]

    priority_articles = []

    for article in articles:

        text = (
            article["titre"] + " " +
            article["contexte"]
        ).lower()

        score = 0

        for keyword in keywords_priority:

            if keyword in text:
                score += 1

        priority_articles.append(
            (score, article)
        )

    priority_articles.sort(
        key=lambda x: x[0],
        reverse=True
    )

    for score, article in priority_articles:

        if article not in selected_articles:

            selected_articles.append(article)

        if len(selected_articles) >= 6:
            break


# ============================================================
# LAST FALLBACK
# ============================================================

if len(selected_articles) < 6:

    for article in articles:

        if article not in selected_articles:
            selected_articles.append(article)

        if len(selected_articles) >= 6:
            break


# ============================================================
# SEND 6 NEWS
# ============================================================

for i, article in enumerate(
    selected_articles[:6],
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

    header = (
        f"📰 {i}/6 — {titre.upper()}\n"
        f"📡 {source}"
    )

    message = sep(header) + analyse

    if lien:
        message += f"\n\n🔗 {lien}"

    send(message)


# ============================================================
# MARKETS
# ============================================================

if marches:

    market_message = sep(
        "📈 MARCHES — DONNEES EN TEMPS REEL"
    )

    for name, data in marches.items():

        emoji = (
            "🟢"
            if data["change"] >= 0
            else "🔴"
        )

        market_message += (
            f"{emoji} {name} : "
            f"{data['prix']:.2f} "
            f"({data['change']:+.2f}%)\n"
        )

    send(market_message)


# ============================================================
# CRYPTO
# ============================================================

if crypto:

    btc = crypto.get("bitcoin", {})
    eth = crypto.get("ethereum", {})
    sol = crypto.get("solana", {})

    btc_emoji = (
        "🟢"
        if btc.get("usd_24h_change", 0) >= 0
        else "🔴"
    )

    eth_emoji = (
        "🟢"
        if eth.get("usd_24h_change", 0) >= 0
        else "🔴"
    )

    sol_emoji = (
        "🟢"
        if sol.get("usd_24h_change", 0) >= 0
        else "🔴"
    )

    crypto_message = (

        f"{btc_emoji} Bitcoin  : "
        f"${btc.get('usd', 0):,.0f} "
        f"({btc.get('usd_24h_change', 0):+.2f}%)\n"

        f"{eth_emoji} Ethereum : "
        f"${eth.get('usd', 0):,.0f} "
        f"({eth.get('usd_24h_change', 0):+.2f}%)\n"

        f"{sol_emoji} Solana   : "
        f"${sol.get('usd', 0):,.0f} "
        f"({sol.get('usd_24h_change', 0):+.2f}%)\n\n"

        "Source : CoinGecko"
    )

    send(
        sep("₿ CRYPTO — DONNEES EN TEMPS REEL")
        + crypto_message
    )


# ============================================================
# INVESTMENT
# ============================================================

titles_analysed = [
    article["titre"]
    for article in selected_articles[:6]
]


markets_text = ""

if marches:

    for name, data in marches.items():

        markets_text += (
            f"{name} : "
            f"{data['prix']:.2f} "
            f"({data['change']:+.2f}%)\n"
        )


crypto_text = ""

if crypto:

    btc = crypto.get("bitcoin", {})
    eth = crypto.get("ethereum", {})

    crypto_text = (
        f"Bitcoin : "
        f"${btc.get('usd', 0):,.0f} "
        f"({btc.get('usd_24h_change', 0):+.2f}%)\n"

        f"Ethereum : "
        f"${eth.get('usd', 0):,.0f} "
        f"({eth.get('usd_24h_change', 0):+.2f}%)"
    )


investment_prompt = f"""
Tu es un analyste financier.

Date : {date_complete}

ACTUALITÉS :
{chr(10).join(titles_analysed)}

MARCHÉS RÉELS :
{markets_text}

CRYPTO RÉELLE :
{crypto_text}

Fais une analyse pédagogique en français.

IMPORTANT :

- Utilise uniquement les données fournies ci-dessus.
- Ne prétends pas avoir accès à d'autres données en temps réel.
- NE DONNE PAS de prix d'action actuel si celui-ci n'est pas fourni.
- NE DONNE PAS de bénéfices ou chiffres financiers précis non fournis.
- Ne fabrique aucune information.
- Si tu cites une entreprise, utilise une entreprise réelle.
- Les tickers doivent être corrects.
- Pas de Markdown.
- Réponse courte et complète.

Structure exactement en 5 paragraphes séparés par une ligne vide :

1. TENDANCE MONDIALE
Explique la tendance économique dominante aujourd'hui en 3 lignes.

2. ACTION À SURVEILLER
Cite UNE entreprise et son ticker.
Explique pourquoi elle pourrait être intéressante compte tenu des actualités.
Ne donne aucun prix non fourni.

3. ACTIF OU SECTEUR ALTERNATIF
Cite un secteur, ETF, matière première, obligation ou crypto pertinent.

4. RISQUES
Donne 2 ou 3 risques concrets.

5. FUN FACT FINANCE
Donne un fait financier intéressant et fiable. Si tu n'es pas certain, ne l'invente pas.

Maximum 180 mots.

Termine exactement par :

Analyse pédagogique uniquement, pas un conseil financier professionnel.
"""


try:

    investment = groq_call(
        investment_prompt,
        tokens=1200,
        retries=3
    )

except Exception:

    investment = (
        "L'analyse d'investissement n'a pas pu être "
        "générée aujourd'hui."
    )


# ============================================================
# INVESTMENT FALLBACK
# ============================================================

if not investment or len(investment) < 80:

    try:

        investment = groq_call(
            f"""
Donne une analyse financière très courte en français.

Actualités :
{chr(10).join(titles_analysed)}

Marchés :
{markets_text}

Crypto :
{crypto_text}

Donne seulement :
1. tendance mondiale
2. une action à surveiller
3. un risque principal

Maximum 100 mots.

Ne donne aucun chiffre non fourni.
""",
            tokens=500,
            retries=2
        )

    except Exception:

        investment = (
            "Analyse d'investissement indisponible aujourd'hui."
        )


send(
    sep("💼 INVESTISSEMENT DU JOUR")
    + investment
)


# ============================================================
# DAILY SUMMARY
# ============================================================

summary_prompt = f"""
Date : {date_complete}

Actualités sélectionnées :

{chr(10).join(titles_analysed)}

Fais une synthèse transversale de la journée.

IMPORTANT :
- français uniquement
- maximum 5 lignes
- ne répète pas simplement les titres
- explique ce que ces événements disent du monde aujourd'hui
- termine par une phrase forte
- aucun Markdown
"""


try:

    summary = groq_call(
        summary_prompt,
        tokens=600,
        retries=3
    )

except Exception:

    summary = (
        "La synthèse du jour n'a pas pu être générée."
    )


if not summary or len(summary) < 30:

    summary = (
        "Les principales actualités du jour montrent "
        "un environnement international marqué par "
        "des tensions géopolitiques, économiques et "
        "climatiques."
    )


send(
    sep("📊 SYNTHESE DU JOUR")
    + summary
    + f"\n\n{'═' * 35}\n"
      f"🗞 Fin du rapport — {date_complete}"
)
