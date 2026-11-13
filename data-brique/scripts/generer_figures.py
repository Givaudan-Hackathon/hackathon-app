"""Figures du livrable Data G15, calculees a partir des sorties de validation (aucun chiffre saisi).

Usage (depuis data-brique/) : .venv/Scripts/python scripts/generer_figures.py

Sorties : docs/figures/validation_avant_apres.png, docs/figures/comparaison_versions.png
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

RACINE = Path(__file__).resolve().parents[1]
SORTIES = RACINE / "benchmark" / "sorties"
FIGURES = RACINE / "docs" / "figures"

# memes criteres et memes libelles que docs/validation_30_cas.md
CRITERES = [("type_ok", "Type de produit"), ("aromes_ok", "Arôme(s), tous trouvés"),
            ("arome_principal_ok", "Arôme principal"), ("contraintes_ok", "Contraintes"),
            ("comportement_ok", "Comportement"), ("sans_marque", "Aucune marque citée"),
            ("sans_chiffre_invente", "Aucun chiffre inventé"), ("sans_prix", "Aucun prix inventé"),
            ("cas_reussi", "Cas entièrement réussi")]


def lire(nom: str) -> pd.DataFrame:
    return pd.read_csv(SORTIES / nom, encoding="utf-8")


def compte(colonne: pd.Series) -> tuple[int, int]:
    """(reussis, mesures) ; une case vide = critere non applicable a ce cas."""
    valeurs = colonne.dropna().astype(str)
    return int((valeurs == "True").sum()), len(valeurs)


def etiqueter(ax, barres, comptes):
    for barre, (ok, n) in zip(barres, comptes):
        ax.annotate(f"{ok}/{n}", (barre.get_x() + barre.get_width() / 2, barre.get_height()),
                    ha="center", va="bottom", fontsize=8, xytext=(0, 2), textcoords="offset points")


def figure_avant_apres() -> Path:
    avant, apres = lire("validation_30_cas_avant.csv"), lire("validation_30_cas.csv")
    fig, ax = plt.subplots(figsize=(11, 5))
    largeur = 0.38
    x = range(len(CRITERES))
    for decalage, df, nom, couleur in [(-largeur / 2, avant, "Avant (v2.2.2-references)", "#b0b7c3"),
                                       (largeur / 2, apres, "Après (v2.3.0-affiner)", "#2f6db5")]:
        comptes = [compte(df[col]) for col, _ in CRITERES]
        barres = ax.bar([i + decalage for i in x], [100 * ok / n for ok, n in comptes], largeur,
                        label=nom, color=couleur)
        etiqueter(ax, barres, comptes)
    ax.set_xticks(list(x), [libelle for _, libelle in CRITERES], rotation=25, ha="right")
    ax.set_ylabel("% des 30 cas")
    ax.set_ylim(0, 125)
    ax.set_yticks(range(0, 101, 20))
    ax.set_title("Validation sur les 30 cas de référence, avant / après les corrections par mécanismes")
    ax.legend(loc="upper center", ncol=2, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.01, "Source : benchmark/sorties/validation_30_cas_avant.csv et validation_30_cas.csv",
             fontsize=7, color="#555")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    chemin = FIGURES / "validation_avant_apres.png"
    fig.savefig(chemin, dpi=150)
    plt.close(fig)
    return chemin


def figure_versions() -> Path:
    # (libelle, colonne V1, colonne V2.1, colonne V2.2) ; None = critere non mesurable pour la version
    criteres = [("Division", "v1_division_ok", "v21_division_ok", "division_ok"),
                ("Arôme principal", None, "v21_arome_principal_ok", "arome_principal_ok"),
                ("Pistes ou relance", None, "v21_comportement_ok", "v22_comparable_ok")]
    jeux = [("30 cas de référence (guident les corrections)", "validation_30_cas.csv", "V2.2 : v2.3.0-affiner"),
            ("10 cas jamais vus (indépendants)", "validation_cas_finaux.csv", "V2.2 : v2.2.3-mecanismes")]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
    largeur = 0.26
    for ax, (titre, fichier, nom_v22) in zip(axes, jeux):
        df = lire(fichier)
        for k, (version, couleur) in enumerate([("V1", "#d9d9d9"), ("V2.1", "#9bbbe0"), (nom_v22, "#2f6db5")]):
            positions, hauteurs, comptes = [], [], []
            for i, critere in enumerate(criteres):
                colonne = critere[1 + k]
                if colonne is None:
                    continue
                ok, n = compte(df[colonne])
                positions.append(i + (k - 1) * largeur)
                hauteurs.append(100 * ok / n)
                comptes.append((ok, n))
            barres = ax.bar(positions, hauteurs, largeur, label=version, color=couleur)
            etiqueter(ax, barres, comptes)
        ax.set_xticks(range(len(criteres)), [c[0] for c in criteres])
        ax.set_title(titre, fontsize=10)
        ax.set_ylim(0, 125)
        ax.set_yticks(range(0, 101, 20))
        ax.legend(loc="upper center", ncol=3, fontsize=8, frameon=False)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("% des cas mesurés")
    fig.suptitle("Comparaison V1 / V2.1 / V2.2 sur les critères comparables")
    fig.text(0.01, 0.01, "Source : benchmark/sorties/validation_30_cas.csv et validation_cas_finaux.csv. "
             "V1 ne produit pas d'arôme ni de pistes : barres absentes.", fontsize=7, color="#555")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    chemin = FIGURES / "comparaison_versions.png"
    fig.savefig(chemin, dpi=150)
    plt.close(fig)
    return chemin


if __name__ == "__main__":
    FIGURES.mkdir(parents=True, exist_ok=True)
    for chemin in (figure_avant_apres(), figure_versions()):
        print(chemin.relative_to(RACINE))
