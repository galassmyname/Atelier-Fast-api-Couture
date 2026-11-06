# API Atelier de couture

API REST de gestion d'un atelier de couture : clients, mesures, commandes, paiements,
livraisons et statistiques. Projet final du module FastAPI / PostgreSQL – Sonatel Academy.

**Stack :** FastAPI · SQLAlchemy 2 · PostgreSQL · Alembic · Pydantic · JWT (Argon2) · pytest · Docker

---

## Architecture

```
app/
├── main.py          # application FastAPI, routeurs, gestion des erreurs, /health
├── config.py        # lecture des variables d'environnement (.env)
├── database.py      # moteur SQLAlchemy et session
├── security.py      # hachage Argon2 et jetons JWT
├── deps.py          # utilisateur connecté et contrôle des rôles
├── exceptions.py    # erreur métier convertie en réponse HTTP
├── seed.py          # création de l'admin et du catalogue
├── models/          # modèles SQLAlchemy
├── schemas/         # schémas Pydantic (création / modification / lecture)
├── services/        # logique métier (règles RG1 à RG24)
└── routers/         # routes, un fichier par domaine
alembic/             # migrations
tests/               # tests pytest
```

Les routeurs vérifient les droits, appellent un service puis valident la transaction.
Toute la logique métier est dans `services/`.

---

## Installation et lancement avec Docker (recommandé)

```bash
git clone <url-du-depot>
cd atelier-couture
cp .env.example .env        # puis modifier les valeurs (SECRET_KEY, mots de passe)
docker compose up --build
```

Au démarrage, le conteneur applique les migrations (`alembic upgrade head`),
crée l'administrateur et le catalogue (`python -m app.seed`), puis lance l'API.

- Documentation Swagger : http://localhost:8000/docs
- Santé : http://localhost:8000/health

Arrêter : `docker compose down` · Réinitialiser la base : `docker compose down -v`

---

## Installation sans Docker

Prérequis : Python 3.11 et PostgreSQL.

```bash
python -m venv venv
source venv/bin/activate          # Windows : venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # renseigner DATABASE_URL vers votre base PostgreSQL
alembic upgrade head              # création du schéma
python -m app.seed                # administrateur + catalogue
uvicorn app.main:app --reload
```

Générer une clé secrète :
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Lancer les tests

Les tests utilisent une base SQLite en mémoire : aucune base ni Docker n'est nécessaire.

```bash
pytest -v
```

37 tests : au moins un par règle de gestion importante, et des tests des droits par rôle.

---

## Comptes de test

| Rôle | Identifiant | Mot de passe |
|---|---|---|
| admin | valeur de `ADMIN_EMAIL` dans `.env` | valeur de `ADMIN_PASSWORD` |

Les comptes **accueil** et **tailleur** se créent avec l'admin, via `POST /api/v1/utilisateurs` :

```json
{ "email": "accueil@atelier.sn", "nom_complet": "Aïda Accueil", "mot_de_passe": "accueil123", "role": "accueil" }
{ "email": "tailleur@atelier.sn", "nom_complet": "Moussa Tailleur", "mot_de_passe": "tailleur123", "role": "tailleur" }
```

Connexion dans Swagger : bouton **Authorize** (username = e-mail).

---

## Routes réalisées (44/44)

Préfixe `/api/v1` (sauf `/health`).

| Domaine | Routes |
|---|---|
| Authentification | `POST /auth/login` · `GET /auth/me` |
| Utilisateurs (admin) | `POST /utilisateurs` · `GET /utilisateurs` · `GET /utilisateurs/{id}` · `PATCH /utilisateurs/{id}` |
| Clients | `POST /clients` · `GET /clients` · `GET /clients/{id}` · `PATCH /clients/{id}` · `DELETE /clients/{id}` · `GET /clients/{id}/commandes` · `GET /clients/{id}/resume` |
| Catalogue | `POST /catalogue` · `GET /catalogue` · `GET /catalogue/{id}` · `PATCH /catalogue/{id}` |
| Mesures | `POST /clients/{id}/mesures` · `GET /clients/{id}/mesures` · `GET /clients/{id}/mesures/derniere` · `GET /mesures/{id}` · `PATCH /mesures/{id}` · `DELETE /mesures/{id}` |
| Commandes | `POST /commandes` · `GET /commandes` · `GET /commandes/{id}` · `PATCH /commandes/{id}` · `POST /commandes/{id}/statut` · `GET /commandes/{id}/historique` · `POST /commandes/{id}/lignes` · `DELETE /commandes/{id}/lignes/{ligne_id}` |
| Paiements | `POST /commandes/{id}/paiements` · `GET /commandes/{id}/paiements` · `DELETE /paiements/{id}` |
| Livraisons | `PUT /commandes/{id}/livraison` · `GET /commandes/{id}/livraison` · `POST /commandes/{id}/livraison/confirmer` · `GET /livraisons` |
| Statistiques (admin) | `GET /statistiques/tableau-de-bord` · `GET /statistiques/chiffre-affaires` · `GET /statistiques/types-vetement` · `GET /statistiques/top-clients` · `GET /statistiques/impayes` |
| Santé | `GET /health` |

---

## Conventions

- Erreurs : `{"detail": "message en français"}` ; codes 401, 403, 404, 409, 422.
- Listes paginées : `{"items", "total", "limit", "offset"}` (limit 20 par défaut, 100 max).
- Montants en FCFA (entiers), mesures en centimètres.