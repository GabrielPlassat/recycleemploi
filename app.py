"""POC Véhicules intermédiaires : réparation, mises sur le marché et emploi.

Application Streamlit. Elle lit les données ouvertes de l'ADEME en direct
et, si le site ne répond pas, utilise la copie enregistrée dans le dossier data/.
"""

from io import BytesIO
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

DATA_DIR = Path(__file__).parent / "data"
ADEME_API = "https://data.ademe.fr/data-fair/api/v1/datasets/{id}/lines"
ID_REPARATION = "kzuew6wsvf2efs9xo-hf-pkl"
ID_MISES_SUR_MARCHE = "wowibc83bqmkehe2w8krhzdo"
ID_PRODUCTEURS = "rep-producteurs-idu"
BMO_URL = (
    "https://www.francetravail.org/files/live/sites/peorg/files/documents/"
    "Statistiques-et-analyses/Open-data/BMO/Base-open-data-BMO-2026.xlsx"
)

st.set_page_config(page_title="POC véhicules intermédiaires", layout="wide")


# ---------------------------------------------------------------- chargement


def lire_ademe(dataset_id: str, params: dict) -> pd.DataFrame:
    """Lit toutes les lignes d'un jeu de données ADEME (API Data Fair)."""
    reponse = requests.get(
        ADEME_API.format(id=dataset_id), params={**params, "size": 10000}, timeout=20
    )
    reponse.raise_for_status()
    return pd.DataFrame(reponse.json()["results"])


@st.cache_data(ttl=24 * 3600, show_spinner="Chargement des réparations…")
def charger_reparations() -> tuple[pd.DataFrame, str]:
    try:
        brut = lire_ademe(
            ID_REPARATION,
            {
                "filiere_eq": "ASL",
                "categorie_eq": "CAT_1",
                "select": "annee,dep_reparation,nombre_reparations",
            },
        )
        df = (
            brut.rename(columns={"dep_reparation": "departement"})
            .groupby(["annee", "departement"], as_index=False)["nombre_reparations"]
            .sum()
        )
        source = "en direct (ADEME)"
    except Exception:
        df = pd.read_csv(DATA_DIR / "reparations_velos_departement.csv", dtype={"departement": str})
        source = "copie locale du 18/11/2026"
    noms = pd.read_csv(DATA_DIR / "departements.csv", dtype=str)
    df["departement"] = df["departement"].astype(str).str.zfill(2)
    df = df.merge(noms, on="departement", how="left")
    df["nom_departement"] = df["nom_departement"].fillna(df["departement"])
    return df, source


@st.cache_data(ttl=24 * 3600, show_spinner="Chargement des mises sur le marché…")
def charger_mises_sur_marche() -> tuple[pd.DataFrame, str]:
    try:
        brut = lire_ademe(
            ID_MISES_SUR_MARCHE,
            {"filiere_in": "VHCL,ASL", "select": "annee,filiere,specif1,quantite,tonnage"},
        )
        df = (
            brut.rename(columns={"specif1": "categorie"})
            .groupby(["annee", "filiere", "categorie"], as_index=False)[["quantite", "tonnage"]]
            .sum(min_count=1)
        )
        source = "en direct (ADEME)"
    except Exception:
        df = pd.read_csv(DATA_DIR / "mises_sur_marche_vehicules.csv")
        source = "copie locale du 18/11/2026"
    return df, source


@st.cache_data(ttl=24 * 3600, show_spinner="Chargement des producteurs…")
def charger_producteurs() -> tuple[pd.DataFrame, str]:
    segments = pd.read_csv(DATA_DIR / "producteurs_vhcl.csv")
    try:
        brut = lire_ademe(
            ID_PRODUCTEURS, {"Filiere_eq": "VHCL", "select": "Raison_Sociale,Pays"}
        )
        df = brut.rename(columns={"Raison_Sociale": "raison_sociale", "Pays": "pays"})
        df = df.merge(segments, on="raison_sociale", how="left")
        df["segment"] = df["segment"].fillna("Nouveau : à classer")
        source = "en direct (ADEME)"
    except Exception:
        df = segments
        source = "copie locale du 18/11/2026"
    return df.sort_values("raison_sociale"), source


@st.cache_data(ttl=24 * 3600, show_spinner="Téléchargement de l'enquête BMO…")
def telecharger_bmo() -> bytes:
    reponse = requests.get(BMO_URL, timeout=60)
    reponse.raise_for_status()
    return reponse.content


def lire_bmo(contenu: bytes) -> pd.DataFrame:
    """Lit le fichier BMO en repérant la ligne d'en-tête automatiquement."""
    apercu = pd.read_excel(BytesIO(contenu), header=None, nrows=15)
    ligne_entete = 0
    for i, ligne in apercu.iterrows():
        textes = [str(v).strip().lower() for v in ligne.tolist()]
        if "met" in textes or any("métier" in t or "metier" in t for t in textes):
            ligne_entete = i
            break
    return pd.read_excel(BytesIO(contenu), header=ligne_entete)


def nombre(n: float) -> str:
    """Nombre arrondi avec espace pour les milliers : 12 345."""
    return f"{n:,.0f}".replace(",", "\u202f")


def deviner(colonnes: list[str], indices: list[str]) -> int:
    """Position de la première colonne dont le nom contient un des indices."""
    noms = [str(c).strip().lower() for c in colonnes]
    for indice in indices:  # d'abord les noms exacts
        if indice in noms:
            return noms.index(indice)
    for indice in indices:  # puis les noms qui contiennent l'indice
        for i, nom in enumerate(noms):
            if len(indice) > 3 and indice in nom:
                return i
    return 0


# ---------------------------------------------------------------- page

st.title("Véhicules intermédiaires : réparation, marché et emploi")
st.caption(
    "POC à partir des données ouvertes de l'ADEME (registre SYDEREP) et de France Travail. "
    "Licence Ouverte Etalab."
)

reparations, source_rep = charger_reparations()
marche, source_marche = charger_mises_sur_marche()
producteurs, source_prod = charger_producteurs()

onglet_rep, onglet_vehicules, onglet_emploi = st.tabs(
    ["Réparation des vélos", "Véhicules de catégorie L", "Emploi (BMO)"]
)

# ---- Onglet 1 : réparations
with onglet_rep:
    st.subheader("Réparations de vélos aidées par le bonus réparation")
    st.caption(
        f"Source : ADEME, « REP - Réparation des produits usagés », filière ASL, "
        f"catégorie 1 (cycles, à confirmer). Données {source_rep}."
    )
    annees = sorted(reparations["annee"].unique())
    totaux = reparations.groupby("annee")["nombre_reparations"].sum()
    colonnes = st.columns(len(annees) + 1)
    for col, annee in zip(colonnes, annees):
        col.metric(f"Réparations {annee}", nombre(totaux[annee]))
    if len(annees) >= 2:
        a0, a1 = annees[-2], annees[-1]
        colonnes[-1].metric(f"Évolution {a0} → {a1}", f"× {totaux[a1] / totaux[a0]:.1f}")

    annee_choisie = st.selectbox("Année", annees, index=len(annees) - 1)
    nb = st.slider("Nombre de départements affichés", 5, 40, 15)
    vue = (
        reparations[reparations["annee"] == annee_choisie]
        .sort_values("nombre_reparations", ascending=False)
        .head(nb)
    )
    vue["libelle"] = vue["departement"] + " " + vue["nom_departement"]
    st.bar_chart(
        vue,
        x="libelle",
        y="nombre_reparations",
        horizontal=True,
        sort="-nombre_reparations",
        x_label="",
        y_label="Nombre de réparations",
        height=30 * nb + 60,
    )

    tableau = reparations.pivot_table(
        index=["departement", "nom_departement"],
        columns="annee",
        values="nombre_reparations",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()
    tableau.columns = [str(c) for c in tableau.columns]
    st.markdown("**Tous les départements**")
    st.dataframe(tableau, hide_index=True, width="stretch")
    st.download_button(
        "Télécharger le tableau (CSV)",
        tableau.to_csv(index=False).encode("utf-8"),
        "reparations_velos_departement.csv",
        "text/csv",
    )

# ---- Onglet 2 : véhicules L
with onglet_vehicules:
    st.subheader("Mises sur le marché déclarées dans SYDEREP")
    st.caption(f"Source : ADEME, « REP - Tonnages des mises sur le marché ». Données {source_marche}.")
    vhcl = marche[marche["filiere"] == "VHCL"]
    if not vhcl.empty:
        derniere = vhcl["annee"].max()
        vhcl = vhcl[vhcl["annee"] == derniere]
        c1, c2 = st.columns(2)
        for col, cat, titre in (
            (c1, "L6e", "Quadricycles légers (L6e)"),
            (c2, "L", "Autres véhicules L, dont quadricycles lourds L7e"),
        ):
            ligne = vhcl[vhcl["categorie"] == cat]
            if not ligne.empty:
                q, t = float(ligne["quantite"].iloc[0]), float(ligne["tonnage"].iloc[0])
                col.metric(f"{titre}, {derniere}", f"{nombre(q)} véhicules")
                col.caption(f"{nombre(t)} t, soit environ {nombre(t * 1000 / q)} kg par véhicule")

    cycles = marche[(marche["filiere"] == "ASL") & (marche["categorie"] == "CAT_1")]
    if not cycles.empty:
        st.markdown("**Cycles mis sur le marché (tonnes, catégorie ASL 1)**")
        st.line_chart(cycles.assign(annee=cycles["annee"].astype(str)).set_index("annee")["tonnage"], x_label="Année", y_label="Tonnes")

    st.subheader("Producteurs inscrits dans la filière véhicules (VHCL)")
    st.caption(f"Source : ADEME, « Producteurs enregistrés dans SYDEREP ». Données {source_prod}.")
    choix = st.multiselect(
        "Segments",
        sorted(producteurs["segment"].unique()),
        default=[s for s in producteurs["segment"].unique() if not s.startswith("Autres")],
    )
    st.dataframe(
        producteurs[producteurs["segment"].isin(choix)],
        hide_index=True,
        width="stretch",
    )

# ---- Onglet 3 : emploi
with onglet_emploi:
    st.subheader("Projets de recrutement (enquête BMO 2026)")
    st.write(
        "L'enquête Besoins en main-d'œuvre de France Travail donne, par métier et par "
        "département, le nombre de projets de recrutement et la part jugée difficile. "
        "Choisissez un mot-clé de métier pour comparer ces besoins aux réparations de vélos."
    )
    contenu = None
    if st.button("Télécharger l'enquête BMO 2026 depuis France Travail"):
        try:
            contenu = telecharger_bmo()
            st.session_state["bmo"] = contenu
        except Exception as erreur:
            st.error(f"Téléchargement impossible ({erreur}). Utilisez le dépôt de fichier ci-dessous.")
    fichier = st.file_uploader("Ou déposez le fichier BMO (.xlsx)", type="xlsx")
    if fichier is not None:
        st.session_state["bmo"] = fichier.getvalue()
    contenu = st.session_state.get("bmo")

    if contenu:
        bmo = lire_bmo(contenu)
        cols = [str(c) for c in bmo.columns]
        bmo.columns = cols
        with st.expander("Colonnes utilisées (détectées automatiquement, modifiables)"):
            col_metier = st.selectbox("Nom du métier", cols, index=deviner(cols, ["nom métier bmo", "nom_metier", "métier", "metier"]))
            col_dep = st.selectbox("Code département", cols, index=deviner(cols, ["dept", "departement", "département"]))
            col_projets = st.selectbox("Projets de recrutement", cols, index=deviner(cols, ["met"]))
            col_difficiles = st.selectbox("Projets difficiles", cols, index=deviner(cols, ["xmet"]))

        mot_cle = st.text_input("Mot-clé du métier", "cycles")
        filtre = bmo[col_metier].astype(str).str.contains(mot_cle, case=False, na=False)
        metiers = sorted(bmo.loc[filtre, col_metier].astype(str).unique())
        if not metiers:
            st.warning("Aucun métier ne contient ce mot-clé. Essayez par exemple « véhicules » ou « mécanicien ».")
        else:
            choisis = st.multiselect("Métiers retenus", metiers, default=metiers)
            sel = bmo[bmo[col_metier].astype(str).isin(choisis)].copy()
            for c in (col_projets, col_difficiles):
                sel[c] = pd.to_numeric(sel[c].astype(str).str.replace("*", "", regex=False), errors="coerce")
            sel["departement"] = sel[col_dep].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(2)
            emploi = sel.groupby("departement", as_index=False)[[col_projets, col_difficiles]].sum()
            emploi = emploi.rename(columns={col_projets: "projets_recrutement", col_difficiles: "projets_difficiles"})

            derniere_annee = reparations["annee"].max()
            croise = emploi.merge(
                reparations[reparations["annee"] == derniere_annee][["departement", "nom_departement", "nombre_reparations"]],
                on="departement",
                how="outer",
            ).fillna({"projets_recrutement": 0, "projets_difficiles": 0, "nombre_reparations": 0})
            croise["part_difficile_%"] = (
                100 * croise["projets_difficiles"] / croise["projets_recrutement"].where(croise["projets_recrutement"] > 0)
            ).round(0)

            c1, c2 = st.columns(2)
            c1.metric("Projets de recrutement", nombre(croise["projets_recrutement"].sum()))
            c2.metric("Dont difficiles", nombre(croise["projets_difficiles"].sum()))
            st.markdown(f"**Comparaison par département (réparations {derniere_annee})**")
            st.scatter_chart(
                croise,
                x="nombre_reparations",
                y="projets_recrutement",
                x_label=f"Réparations de vélos {derniere_annee}",
                y_label="Projets de recrutement",
            )
            colonnes_ordre = ["departement", "nom_departement", "projets_recrutement",
                              "projets_difficiles", "part_difficile_%", "nombre_reparations"]
            st.dataframe(
                croise[colonnes_ordre].sort_values("projets_recrutement", ascending=False),
                hide_index=True,
                width="stretch",
            )
    else:
        st.info("Aucune donnée BMO chargée pour l'instant.")
