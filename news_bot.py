# =========================
# LIMITATION INTELLIGENTE (15 ARTICLES)
# =========================

articles_list = list(articles.keys())

print(f"🧾 Articles collectés avant trim: {len(articles_list)}")

# 👉 ON FORCE 15 ARTICLES MAX
articles_list = articles_list[:15]

print(f"🧾 Articles utilisés: {len(articles_list)}")

texte_brut = "\n".join(articles_list)

# =========================
# PROMPT OPTIMISÉ (moins de tokens)
# =========================

prompt = f"""
Tu es un journaliste analyste pédagogique.

DATE :
{date_complete}

MISSION :
Créer un briefing quotidien clair basé uniquement sur les titres.

RÈGLES :
- utiliser uniquement les titres fournis
- ne pas inventer de faits
- rester synthétique mais pédagogique
- éviter les répétitions

FORMAT :

🧠 TITRE

📌 Explication (5-8 lignes)

🧠 Apprentissage (simple)

🔎 Contexte (court)

🔮 Projection (3 scénarios courts)

💰 INVESTISSEMENT (1 idée liée)

₿ CRYPTO (analyse courte)

📊 SYNTHÈSE (5 lignes max)

NEWS :
{texte_brut}
"""

# =========================
# IA CALL OPTIMISÉ (ANTI 429)
# =========================

completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=1500  # 🔥 IMPORTANT : réduit coût tokens
)

resume = completion.choices[0].message.content
