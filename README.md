# POC véhicules intermédiaires : réparation, marché et emploi

Ce prototype croise trois sources de données ouvertes sur les véhicules intermédiaires (vélo cargo, catégories L1e à L7e) :

| Onglet | Ce qu'il montre | Source |
| --- | --- | --- |
| Réparation des vélos | Réparations aidées par le bonus réparation, par département, en 2024 et 2025 | ADEME, registre SYDEREP |
| Véhicules de catégorie L | Quadricycles légers (L6e) et autres véhicules L, dont les quadricycles lourds L7e, mis sur le marché ; liste des 92 producteurs de la filière véhicules | ADEME, registre SYDEREP |
| Emploi (BMO) | Projets de recrutement d'un métier (par exemple les mécaniciens de cycles), comparés aux réparations par département | France Travail, enquête BMO 2026 |

Les données de l'ADEME sont lues en direct. Si le site ne répond pas, l'application utilise la copie du dossier `data/` (relevée le 18/11/2026).

## Contenu du dossier

- `app.py` : l'application Streamlit.
- `POC_vehicules_intermediaires.ipynb` : la même analyse pas à pas, pour Google Colab.
- `requirements.txt` : la liste des bibliothèques dont Streamlit a besoin.
- `data/` : la copie de secours des données.

## Ouvrir le notebook dans Google Colab

1. Allez sur [colab.research.google.com](https://colab.research.google.com).
2. Menu *Fichier > Importer un notebook*, puis choisissez `POC_vehicules_intermediaires.ipynb`.
3. Menu *Exécution > Tout exécuter*.

## Publier l'application avec Streamlit Community Cloud

Aucun logiciel n'est à installer sur votre ordinateur : tout se fait dans le navigateur.

1. Sur GitHub, créez un nouveau dépôt (bouton *New*), par exemple `poc-velis`.
2. Dans le dépôt, cliquez sur *Add file > Upload files* et glissez **tout le contenu** du dossier, y compris le dossier `data`. Validez avec *Commit changes*.
3. Allez sur [share.streamlit.io](https://share.streamlit.io) et connectez-vous avec votre compte GitHub.
4. Cliquez sur *Create app*, choisissez le dépôt `poc-velis`, la branche `main` et le fichier `app.py`, puis *Deploy*.

L'application est en ligne au bout de deux ou trois minutes.

## Le fichier BMO (onglet Emploi)

L'application le télécharge seule avec le bouton « Télécharger l'enquête BMO 2026 ». Si le téléchargement échoue, déposez le fichier à la main :

- **Fichier** : `Base-open-data-BMO-2026.xlsx` (Excel, environ 3,8 Mo).
- **Lien direct** : [Base-open-data-BMO-2026.xlsx](https://www.francetravail.org/files/live/sites/peorg/files/documents/Statistiques-et-analyses/Open-data/BMO/Base-open-data-BMO-2026.xlsx)
- **Autres accès** : sur [statistiques.francetravail.org/bmo](https://statistiques.francetravail.org/bmo/), menu « Statistiques & analyses », puis « Open data » ; ou sur data.gouv.fr, jeu [Enquête Besoins en Main d'Oeuvre (BMO)](https://www.data.gouv.fr/datasets/enquete-besoins-en-main-doeuvre-bmo), ressource « Enquête BMO 2026 ».

Le fichier a deux feuilles : « Description_des_variables » et « BMO_2026_open_data » (53 786 lignes, une par métier et par bassin d'emploi). Colonnes utilisées : `Nom métier BMO`, `Dept`, `met` (projets de recrutement), `xmet` (projets jugés difficiles). Les petits effectifs sont masqués par « * ».

Le BMO n'a pas de métier « cycles ». Les mécaniciens cycles sont comptés dans **Ouvriers mécaniciens de véhicules (G0B41)**, le mot-clé par défaut. Autres métiers utiles : « Conducteurs et livreurs sur courte distance » (J3X42), « Ouvriers qualifiés en ajustement, montage et assemblage mécanique » (D2X31), « Techniciens et agents de maîtrise en maintenance de véhicules » (G1X71), « Carrossiers automobiles » (G0B40).

## Points à vérifier

- La catégorie 1 de la filière « articles de sport et loisirs » correspond très probablement aux cycles : à confirmer dans le référentiel de l'ADEME.
- La filière véhicules (VHCL) ne publie pour l'instant qu'une année de mises sur le marché (2025).
- Les noms de colonnes du fichier BMO peuvent changer d'une année à l'autre. L'application les détecte seule (vérifié sur le fichier 2026) ; sinon, ils se corrigent dans l'encadré « Colonnes utilisées ».

Données sous Licence Ouverte (Etalab).
