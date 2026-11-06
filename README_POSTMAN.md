# Tester l'API avec Postman

Ce guide explique comment tester l'API Atelier de couture avec Postman et rejouer le scénario de démonstration (annexe A de l'énoncé).

## 1. Prérequis

- L'API tourne : `docker compose up --build` (ou `uvicorn app.main:app --reload`)
- Adresse de base : `http://localhost:8000`
- Postman installé (application ou version web)
- Le script `python -m app.seed` a été exécuté (admin + catalogue créés)

## 2. Créer l'environnement Postman

Dans Postman : **Environments → New**, nom : `Atelier local`. Ajoute ces variables :

| Variable | Valeur initiale |
|---|---|
| `base_url` | `http://localhost:8000/api/v1` |
| `admin_email` | valeur de `ADMIN_EMAIL` du `.env` |
| `admin_password` | valeur de `ADMIN_PASSWORD` du `.env` |
| `accueil_email` | `accueil@atelier.sn` |
| `accueil_password` | `accueil123` |
| `tailleur_email` | `tailleur@atelier.sn` |
| `tailleur_password` | `tailleur123` |
| `token` | (vide, rempli automatiquement) |
| `client_id`, `commande_id` | (vides, remplis automatiquement) |

Sélectionne l'environnement `Atelier local` en haut à droite.

## 3. Créer une collection

**Collections → New → `Atelier couture`**.

Dans l'onglet **Authorization** de la collection :
- Type : `Bearer Token`
- Token : `{{token}}`

Toutes les requêtes héritent ainsi du jeton (laisse « Inherit auth from parent » dans chaque requête).

## 4. Connexion (une requête par rôle)

Crée 3 requêtes `POST {{base_url}}/auth/login` : **Login admin**, **Login accueil**, **Login tailleur**.

- Onglet **Body** → `x-www-form-urlencoded` (et **pas** raw JSON)
- Clés : `username` = `{{admin_email}}` et `password` = `{{admin_password}}` (adapte pour accueil et tailleur)
- Onglet **Authorization** de cette requête : `No Auth`
- Onglet **Scripts → Post-response** (ou **Tests** dans les anciennes versions), pour enregistrer le jeton automatiquement :

```javascript
pm.test("Connexion réussie", function () {
    pm.response.to.have.status(200);
});
pm.environment.set("token", pm.response.json().access_token);
```

**Pour changer de rôle : lance simplement le login du rôle voulu.** Le jeton est remplacé.

## 5. Préparation : créer les comptes accueil et tailleur

1. Lance **Login admin**
2. `POST {{base_url}}/utilisateurs` (Body → raw → JSON) :

```json
{"email": "accueil@atelier.sn", "nom_complet": "Aïda Accueil", "mot_de_passe": "accueil123", "role": "accueil"}
```
```json
{"email": "tailleur@atelier.sn", "nom_complet": "Moussa Tailleur", "mot_de_passe": "tailleur123", "role": "tailleur"}
```

Attendu : **201**. Rejouer la même requête : **409** (e-mail déjà utilisé).

## 6. Scénario de démonstration

Pour chaque requête : Body → **raw → JSON**. Remplace `1` par l'id réel si besoin.

| # | Rôle | Requête | Corps | Attendu |
|---|---|---|---|---|
| 1 | accueil | `POST /clients` | `{"nom":"Diop","prenom":"Fatou","telephone":"77 123 45 67"}` | **201** |
| 1b | accueil | `POST /clients` | `{"nom":"Ba","prenom":"Awa","telephone":"771234567"}` | **409** (doublon, RG1) |
| 2 | tailleur | `POST /clients/1/mesures` | `{"tour_poitrine":92,"tour_taille":75,"longueur_robe":140}` | **201** |
| 2b | accueil | `POST /clients/1/mesures` | même corps | **403** |
| 3 | accueil | `POST /commandes` | voir ci-dessous | **201**, total 75 000 |
| 4 | accueil | `POST /commandes/1/statut` | `{"statut":"terminee"}` | **409** + statuts possibles |
| 5 | tailleur | `POST /commandes/1/statut` | `en_coupe`, `en_couture`, `essayage`, `retouches`, `essayage`, `terminee` (un par un) | **200** à chaque fois |
| 5b | tailleur | `GET /commandes/1/historique` | - | **200**, 7 lignes |
| 6 | accueil | `POST /commandes/1/paiements` | `{"montant":30000,"mode":"wave","reference":"WV-123"}` | **201** |
| 6b | accueil | `POST /commandes/1/paiements` | `{"montant":999999,"mode":"wave"}` | **409** |
| 7 | accueil | `POST /commandes/1/livraison/confirmer` | (vide) | **409** (45000 FCFA impayés) |
| 8 | accueil | `POST /commandes/1/paiements` | `{"montant":45000,"mode":"especes"}` | **201** |
| 8b | accueil | `POST /commandes/1/livraison/confirmer` | (vide) | **200**, statut `livree`, solde 0 |
| 9 | admin | `GET /statistiques/tableau-de-bord` | - | **200**, CA du mois inclut 75 000 |
| 9b | accueil | `GET /statistiques/tableau-de-bord` | - | **403** |
| 10 | admin | `GET /statistiques/impayes` | - | **200** |
| 10b | admin | `GET /commandes?en_retard=true` | - | **200** |

Corps de l'étape 3 (vérifie les id avec `GET /catalogue` : Boubou = 1, Pantalon = 6) :

```json
{
  "client_id": 1,
  "lignes": [
    {"type_vetement_id": 1, "quantite": 2},
    {"type_vetement_id": 6, "quantite": 1, "prix_unitaire": 10000}
  ],
  "remise": 5000
}
```

À vérifier dans la réponse : numéro `CMD-2026-0000X`, `montant_total` = 75000, `date_livraison_prevue` = aujourd'hui + 10 jours, `mesure_id` rempli automatiquement.

## 7. Tests automatiques dans Postman (optionnel)

Dans l'onglet **Scripts → Post-response** d'une requête, tu peux vérifier le résultat et sauvegarder des id.

Création de client (étape 1) :

```javascript
pm.test("Client créé", () => pm.response.to.have.status(201));
pm.environment.set("client_id", pm.response.json().id);
```

Création de commande (étape 3) :

```javascript
pm.test("Commande créée", () => pm.response.to.have.status(201));
const c = pm.response.json();
pm.environment.set("commande_id", c.id);
pm.test("Numéro au bon format", () => pm.expect(c.numero).to.match(/^CMD-\d{4}-\d{5}$/));
pm.test("Total correct", () => pm.expect(c.montant_total).to.eql(75000));
```

Tu peux ensuite écrire `{{client_id}}` et `{{commande_id}}` dans les URL au lieu de `1`.

Test d'un refus attendu (ex. étape 4) :

```javascript
pm.test("Transition refusée", () => pm.response.to.have.status(409));
pm.test("Statuts possibles indiqués", () =>
    pm.expect(pm.response.json().detail).to.include("Statuts possibles"));
```

## 8. Lancer toute la collection d'un coup

Clic droit sur la collection → **Run collection**. L'ordre des requêtes doit suivre le scénario (login du bon rôle avant chaque groupe d'étapes). Si tu relances la collection, repars d'une base vide : `docker compose down -v` puis `docker compose up --build`.

## 9. Problèmes fréquents

| Symptôme | Cause probable |
|---|---|
| **401** partout | jeton absent ou expiré : relance le login du rôle |
| **403** inattendu | mauvais rôle connecté : relance le bon login |
| **422** sur le login | corps envoyé en JSON : utilise `x-www-form-urlencoded` |
| `Could not get response` | API arrêtée ou mauvais port : vérifie `http://localhost:8000/health` |
| **404** sur une commande | id inexistant (base réinitialisée) : vérifie `commande_id` |
