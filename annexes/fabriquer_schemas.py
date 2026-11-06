# -*- coding: utf-8 -*-
"""Dessine les deux schémas de la partie 3 (client.html) à partir du fichier des réponses, et les place dans la page.

Principe : chaque schéma est un dessin SVG écrit par une fonction Python. Les chiffres ne sont jamais tapés à la main :
ils sont recalculés ici à partir de donnees/reponses-questionnaire.csv, le fichier des 108 réponses publié sur le site.
Dans la page, chaque schéma occupe la place entre deux balises :
    <!-- schema:choix -->  ...  <!-- /schema:choix -->
Le script remplace ce qu'il y a entre les deux ; le texte autour, écrit par le groupe, ne bouge pas.
Le script ajoute aussi, sous le graphique du TD 2 (proposition.html, écrit à la main), un bandeau qui en montre le code.

Lancer, depuis le dossier du site, avec un Python qui a pandas et statsmodels :
    python annexes/fabriquer_schemas.py
"""
import re
from html import escape
from pathlib import Path

import pandas as pd
from statsmodels.stats.proportion import proportion_confint

SITE = Path(__file__).resolve().parents[1]

# ---- les couleurs : celles du site ; A et B validées (contraste, daltonisme) ---------------------------------
A_, B_ = "#A86B00", "#27509B"            # version A (ocre), version B (bleu Michelin)
ENCRE, GRIS, TRAIT = "#10203F", "#566179", "#D5DDEC"
# échelle d'accord de 1 à 7 : divergente, violet (pas d'accord) / gris (neutre) / sarcelle (d'accord)
ACCORD = ["#5E3C99", "#8C6BB1", "#BFAEDB", "#C9CED8", "#9FD3C7", "#3FA392", "#157A6E"]


# ---- les nombres à la française ------------------------------------------------------------------------------
def fr(x, d=2):
    return f"{x:,.{d}f}".replace(",", " ").replace(".", ",").replace("-", "−")


def pc(x, d=0):
    return f"{fr(100 * x, d)} %"


# =================================================================================================================
# 1. Les calculs, sur le fichier des réponses
# =================================================================================================================
d = pd.read_csv(SITE / "donnees" / "reponses-questionnaire.csv")
A, B = d[d.version == "A"], d[d.version == "B"]
nA, nB = len(A), len(B)
kA, kB = int((A.choix_pneu == "michelin").sum()), int((B.choix_pneu == "michelin").sum())
pA, pB = kA / nA, kB / nB
icA, icB = proportion_confint(kA, nA, method="wilson"), proportion_confint(kB, nB, method="wilson")


# =================================================================================================================
# 2. Les briques du dessin
# =================================================================================================================
def T(x, y, s, taille=12, couleur=ENCRE, ancre="start", gras=False):
    g = ' font-weight="700"' if gras else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{taille}" fill="{couleur}" text-anchor="{ancre}"{g}>{escape(s)}</text>'


def L(x1, y1, x2, y2, couleur=TRAIT, ep=1, tirets=False):
    t = ' stroke-dasharray="5 4"' if tirets else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{couleur}" stroke-width="{ep}"{t}/>'


def barre_v(x, y_base, hauteur, largeur, couleur, info):
    """Une colonne posée sur la ligne de base, bout arrondi de 4 px en haut, carré en bas."""
    r = min(4, hauteur / 2, largeur / 2)
    y = y_base - hauteur
    chemin = (f"M{x:.1f},{y_base:.1f} V{y + r:.1f} Q{x:.1f},{y:.1f} {x + r:.1f},{y:.1f} H{x + largeur - r:.1f} "
              f"Q{x + largeur:.1f},{y:.1f} {x + largeur:.1f},{y + r:.1f} V{y_base:.1f} Z")
    return f'<path d="{chemin}" fill="{couleur}" tabindex="0"><title>{escape(info)}</title></path>'


def svg(nom, largeur, hauteur, titre, description, corps):
    return (f'<svg viewBox="0 0 {largeur} {hauteur}" role="img" aria-labelledby="{nom}-t {nom}-d">'
            f'<title id="{nom}-t">{escape(titre)}</title><desc id="{nom}-d">{escape(description)}</desc>{corps}</svg>')


def legende(entrees):
    return '<div class="leg">' + "".join(f'<span style="--c:{c}">{escape(l)}</span>' for l, c in entrees) + "</div>"


def tableau(entetes, lignes):
    th = "".join(f"<th>{escape(x)}</th>" for x in entetes)
    tr = "".join("<tr>" + "".join(f"<td>{escape(str(x))}</td>" for x in l) + "</tr>" for l in lignes)
    return (f'<details class="chiffres-fig"><summary>Voir les chiffres du schéma</summary>'
            f'<div class="tableau"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div></details>')


def figure(titre, contenu, leg=None, table=None, large=False):
    c = " large" if large else ""
    return (f'<figure class="fig{c}"><figcaption><b>Schéma 1</b> · {escape(titre)}</figcaption>'
            f'{legende(leg) if leg else ""}{contenu}{table or ""}</figure>')


def bandeau(intro, code):
    return (f'<details class="code-fig"><summary>Voir le code de ce graphique</summary><p class="note">{intro}</p>'
            f'<pre class="code"><code>{escape(code)}</code></pre></details>')


def aligne(code):
    """Aligne les commentaires de fin de ligne en une seule colonne, pour que le code se lise d'un coup d'œil."""
    lignes = code.split("\n")
    coupe = [(l.split("  #", 1) if "  #" in l and not l.lstrip().startswith("#") else [l]) for l in lignes]
    large = max((len(c[0].rstrip()) for c in coupe if len(c) == 2), default=0)
    return "\n".join(c[0] if len(c) == 1 else c[0].rstrip().ljust(large) + "   #" + c[1] for c in coupe)


INTRO_COURT = ("Le principe, en version courte : d'abord les chiffres, calculés sur le fichier des réponses, puis le dessin "
               "(les valeurs en commentaire sont celles du graphique). Le code complet est dans "
               "<a href=\"annexes/fabriquer_schemas.py\">annexes/fabriquer_schemas.py</a>.")


# =================================================================================================================
# 3. Les deux schémas de la partie 3
# =================================================================================================================
SCHEMAS = {}


# ---- La question de contrôle : barres divergentes de 1 à 7 -------------------------------------------------------
def divergentes(nom):
    larg, centre, ech = 560, 300, 2.4     # 2,4 px par point de %
    c = []
    rang = [("Version A · 40 000 km", A), ("Version B · 50 000 km", B)]
    for g in (-60, -40, -20, 0, 20, 40, 60, 80):
        x = centre + g * ech
        c.append(L(x, 22, x, 150, TRAIT if g else GRIS, 1))
        c.append(T(x, 168, f"{abs(g)} %", 10.5, GRIS, "middle"))
    c.append(T(centre - 8, 16, "← pas d'accord", 11, GRIS, "end"))
    c.append(T(centre + 8, 16, "d'accord →", 11, GRIS, "start"))
    for i, (lib, g) in enumerate(rang):
        y = 40 + i * 58
        parts = [(g.manip_km == k).mean() * 100 for k in range(1, 8)]
        gauche = -(parts[0] + parts[1] + parts[2] + parts[3] / 2)
        x = centre + gauche * ech
        for k, v in enumerate(parts):
            l_ = v * ech
            if l_ > 0:
                c.append(f'<rect x="{x + 1:.1f}" y="{y}" width="{max(l_ - 2, 0.5):.1f}" height="30" fill="{ACCORD[k]}" tabindex="0">'
                         f'<title>{escape(lib)} · réponse {k + 1} : {fr(v, 1)} %</title></rect>')
            x += l_
        dacc, pasacc = sum(parts[4:]), sum(parts[:3])
        c.append(T(centre + gauche * ech - 6, y + 20, f"{fr(pasacc, 0)} %", 12, ENCRE, "end", gras=True))
        c.append(T(x + 6, y + 20, f"{fr(dacc, 0)} %", 12, ENCRE, "start", gras=True))
        c.append(T(8, y + 13, lib.split(" · ")[0], 12, ENCRE, gras=True))
        c.append(T(8, y + 28, f"moyenne {fr(g.manip_km.mean())} sur 7", 11, GRIS))
    return svg(nom, larg, 178, "Réponses à la question de contrôle, de 1 à 7",
               "Barres divergentes centrées sur la réponse neutre 4 : à gauche les réponses 1 à 3, à droite 5 à 7, pour chaque version.", "".join(c))


SCHEMAS["controle"] = figure(
    "« Le Michelin m'a semblé durer plus longtemps que le Hankook » : la répartition des réponses",
    divergentes("man"),
    leg=[("1 pas du tout d'accord", ACCORD[0]), ("2", ACCORD[1]), ("3", ACCORD[2]), ("4 neutre", ACCORD[3]), ("5", ACCORD[4]), ("6", ACCORD[5]),
         ("7 tout à fait d'accord", ACCORD[6])],
    table=tableau(["Version", "1", "2", "3", "4", "5", "6", "7", "Moyenne"],
                  [(f"Version {v}", *[pc((g.manip_km == k).mean(), 1) for k in range(1, 8)], fr(g.manip_km.mean()))
                   for v, g in [("A", A), ("B", B)]]), large=True)
SCHEMAS["controle"] = SCHEMAS["controle"][:-len("</figure>")] + bandeau(INTRO_COURT, aligne(f"""# 1. Les chiffres : la part de chaque réponse, de 1 à 7, dans chaque version
reponses = pd.read_csv("donnees/reponses-questionnaire.csv")
parts = reponses.groupby("version").manip_km.value_counts(normalize=True)
# moyenne : {fr(A.manip_km.mean())} sur 7 en A, {fr(B.manip_km.mean())} en B

# 2. Le dessin : une barre par version, en 7 morceaux, centrée sur la réponse neutre (4)
for version in ["A", "B"]:
    p = parts[version]
    x = centre - (p[1] + p[2] + p[3] + p[4] / 2) * 240     # « pas d'accord » part vers la gauche
    for reponse in range(1, 8):
        rectangle(x, largeur=p[reponse] * 240, couleur=couleurs[reponse])
        x += p[reponse] * 240                               # le morceau suivant commence où finit celui-ci""")) + "</figure>"


# ---- Le choix, avec intervalles de confiance ---------------------------------------------------------------------
def colonnes_ic(nom):
    larg, haut, gauche, droite, base, plot = 480, 300, 52, 470, 250, 210
    y = lambda v: base - plot * v
    c = []
    for g in (0, 0.25, 0.5, 0.75, 1):
        c.append(L(gauche, y(g), droite, y(g)))
        c.append(T(gauche - 6, y(g) + 4, f"{int(g * 100)} %", 10.5, GRIS, "end"))
    c.append(L(gauche, y(0.5), droite, y(0.5), GRIS, 1.2, tirets=True))
    c.append(T(droite, y(0.5) - 6, "50 % : pas de préférence", 10.5, GRIS, "end"))
    for i, (lib, k, n, p, ic, col) in enumerate([("Version A · 40 000 km", kA, nA, pA, icA, A_), ("Version B · 50 000 km", kB, nB, pB, icB, B_)]):
        cx = 150 + i * 160
        c.append(barre_v(cx - 14, base, plot * p, 28, col, f"{lib} : {pc(p)} ({k} sur {n}), IC 95 % de {pc(ic[0])} à {pc(ic[1])}"))
        c.append(L(cx, y(ic[0]), cx, y(ic[1]), ENCRE, 1.5))
        c.append(L(cx - 7, y(ic[0]), cx + 7, y(ic[0]), ENCRE, 1.5))
        c.append(L(cx - 7, y(ic[1]), cx + 7, y(ic[1]), ENCRE, 1.5))
        c.append(T(cx + 22, y(p) + 5, pc(p), 15, ENCRE, "start", gras=True))
        c.append(T(cx, base + 18, lib, 12, ENCRE, "middle", gras=True))
        c.append(T(cx, base + 34, f"{k} sur {n} · IC de {pc(ic[0])} à {pc(ic[1])}", 10.5, GRIS, "middle"))
    c.append(L(gauche, base, droite, base, GRIS))
    return svg(nom, larg, haut, "Part qui choisit le Michelin, par version",
               f"Version A : {pc(pA)}, version B : {pc(pB)} ; les traits verticaux sont les intervalles de confiance à 95 % (Wilson).", "".join(c))


SCHEMAS["choix"] = figure(
    "la part qui choisit le Michelin à 97,90 € plutôt que le Hankook à 81,99 €", colonnes_ic("cho"),
    leg=[("Version A · 40 000 km", A_), ("Version B · 50 000 km", B_)],
    table=tableau(["Version", "Choisissent Michelin", "Répondants", "Part", "IC 95 % (Wilson)"],
                  [("A · 40 000 km", kA, nA, pc(pA, 1), f"{pc(icA[0], 1)} à {pc(icA[1], 1)}"),
                   ("B · 50 000 km", kB, nB, pc(pB, 1), f"{pc(icB[0], 1)} à {pc(icB[1], 1)}")]))
SCHEMAS["choix"] = SCHEMAS["choix"][:-len("</figure>")] + bandeau(INTRO_COURT, aligne(f"""# 1. Les chiffres
pA, pB = {kA} / {nA}, {kB} / {nB}                                  # {pc(pA)} et {pc(pB)} choisissent Michelin
icA = proportion_confint({kA}, {nA}, method="wilson")              # de {pc(icA[0])} à {pc(icA[1])}
icB = proportion_confint({kB}, {nB}, method="wilson")              # de {pc(icB[0])} à {pc(icB[1])}

# 2. Le dessin : 0 % en bas (y = 250), 100 % en haut (y = 40)
y = lambda part: 250 - part * 210
colonne(x=150, haut=y(pA), couleur=OCRE)  ;  trait(x=150, de_=y(icA[0]), a=y(icA[1]))
colonne(x=310, haut=y(pB), couleur=BLEU)  ;  trait(x=310, de_=y(icB[0]), a=y(icB[1]))
ligne_pointillee(y(0.5))                                   # 50 % : pas de préférence""")) + "</figure>"


# =================================================================================================================
# 4. Le bandeau du graphique du TD 2, écrit à la main dans proposition.html
# =================================================================================================================
INTRO_TD2 = ("Dessin SVG écrit directement dans la page : chaque segment est un rectangle &lt;rect&gt; dont la hauteur vaut 2,8 pixels "
             "par euro (0 € en y = 340) ; les deux lignes horizontales sont le prix actuel et le plafond des concurrents.")


def resume_td2(bloc):
    noms = ["coût de revient", "autres coûts", "coût de revient", "autres coûts", "variation (la campagne)"]
    rects = [re.sub(r"\s*class=\"seg\"|\s*stroke=\"#fff\" stroke-width=\"2\"|<title>.*", "", r) + "/>"
             for r in re.findall(r'<rect class="seg"[^>]*>(?:<title>[^<]*</title>)?', bloc)]
    lignes = "\n".join(f"{r}   <!-- {n} -->" for r, n in zip(rects, noms))
    return ("<!-- 2,8 pixels par euro, 0 € en bas (y = 340) : un segment de 70,32 € fait 196,9 pixels de haut -->\n" + lignes
            + '\n<line y1="71.5" y2="71.5" stroke="#C2410C" stroke-dasharray="6 4"/>   <!-- le plafond de Continental, 95,90 € -->'
            + '\n<line y1="65.9" y2="65.9" stroke="#0F2A5C"/>   <!-- le prix actuel, 97,90 € -->')


def blocs(html, classe):
    """Les <div class="classe"> ... </div> de la page, avec leurs div imbriquées."""
    out, i, ouvre = [], 0, f'<div class="{classe}">'
    while (a := html.find(ouvre, i)) >= 0:
        prof = 0
        for m in re.finditer(r"<div\b|</div>", html[a:]):
            prof += 1 if m.group().startswith("<div") else -1
            if prof == 0:
                fin = a + m.end()
                break
        out.append((a, fin))
        i = fin
    return out


# =================================================================================================================
# 5. Placer les schémas et les bandeaux dans les pages
# =================================================================================================================
for chemin in sorted(SITE.glob("*.html")):
    html = chemin.read_text(encoding="utf-8")
    avant = html
    noms = re.findall(r"<!-- schema:([\w-]+) -->", html)
    for n in noms:
        motif = re.compile(rf"(<!-- schema:{re.escape(n)} -->)(.*?)(<!-- /schema:{re.escape(n)} -->)", re.S)
        html = motif.sub(lambda m: m.group(1) + "\n" + SCHEMAS[n] + "\n" + m.group(3), html)
    numero = iter(range(1, 100))      # les schémas d'une page sont numérotés dans l'ordre où ils apparaissent
    html = re.sub(r"<figcaption><b>Schéma \d+</b>", lambda m: f"<figcaption><b>Schéma {next(numero)}</b>", html)
    html = re.sub(r"<!-- code:auto -->.*?<!-- /code:auto -->\n?", "", html, flags=re.S)
    for a, b in sorted(blocs(html, "td2"), reverse=True):
        html = html[:b] + "\n<!-- code:auto -->" + bandeau(INTRO_TD2, resume_td2(html[a:b])) + "<!-- /code:auto -->" + html[b:]
    if html != avant:
        chemin.write_text(html, encoding="utf-8")
        print(f"{chemin.name} : {len(noms)} schéma(s) placé(s)")
print(f"Choix du Michelin : {pc(pA)} en version A ({kA} sur {nA}), {pc(pB)} en version B ({kB} sur {nB})")
