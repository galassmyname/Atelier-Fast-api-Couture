"""Tests des paiements, livraisons et statistiques (RG16 à RG20)."""

from datetime import date, timedelta

from tests.conftest import API, avancer_jusqua_terminee


def test_paiement_regles(client, accueil, commande):
    """RG16."""
    url = f"{API}/commandes/{commande['id']}/paiements"
    assert (
        client.post(
            url, headers=accueil, json={"montant": 999999, "mode": "wave"}
        ).status_code
        == 409
    )
    demain = (date.today() + timedelta(days=1)).isoformat()
    assert (
        client.post(
            url,
            headers=accueil,
            json={"montant": 1000, "mode": "wave", "date_paiement": demain},
        ).status_code
        == 422
    )
    assert (
        client.post(
            url, headers=accueil, json={"montant": 0, "mode": "wave"}
        ).status_code
        == 422
    )


def test_annuler_paiement_recalcule(client, admin, accueil, commande):
    """RG17."""
    p = client.post(
        f"{API}/commandes/{commande['id']}/paiements",
        headers=accueil,
        json={"montant": 20000, "mode": "orange_money"},
    ).json()
    assert client.delete(f"{API}/paiements/{p['id']}", headers=admin).status_code == 204
    c = client.get(f"{API}/commandes/{commande['id']}", headers=admin).json()
    assert c["montant_paye"] == 0 and c["solde"] == 75000


def test_domicile_exige_adresse(client, accueil, commande):
    """RG18."""
    r = client.put(
        f"{API}/commandes/{commande['id']}/livraison",
        headers=accueil,
        json={"mode": "domicile", "date_prevue": date.today().isoformat()},
    )
    assert r.status_code == 422


def test_replanifier_ne_cree_pas_de_doublon(client, accueil, commande):
    url = f"{API}/commandes/{commande['id']}/livraison"
    j1 = (date.today() + timedelta(days=3)).isoformat()
    j2 = (date.today() + timedelta(days=5)).isoformat()
    l1 = client.put(
        url, headers=accueil, json={"mode": "retrait_atelier", "date_prevue": j1}
    ).json()
    l2 = client.put(
        url, headers=accueil, json={"mode": "retrait_atelier", "date_prevue": j2}
    ).json()
    assert l1["id"] == l2["id"]
    c = client.get(f"{API}/commandes/{commande['id']}", headers=accueil).json()
    assert c["date_livraison_prevue"] == j2


def test_confirmation_exige_terminee_et_soldee(client, accueil, tailleur, commande):
    """RG19 et RG20 : scénario de la démo (étapes 6 à 8)."""
    url = f"{API}/commandes/{commande['id']}"
    # Pas encore terminée
    assert client.post(f"{url}/livraison/confirmer", headers=accueil).status_code == 409
    avancer_jusqua_terminee(client, tailleur, commande["id"])
    # Terminée mais pas soldée : 409 avec le montant
    client.post(
        f"{url}/paiements", headers=accueil, json={"montant": 30000, "mode": "wave"}
    )
    r = client.post(f"{url}/livraison/confirmer", headers=accueil)
    assert r.status_code == 409 and "45000" in r.json()["detail"]
    # Solde puis confirmation : retrait atelier créé automatiquement
    client.post(
        f"{url}/paiements", headers=accueil, json={"montant": 45000, "mode": "especes"}
    )
    r = client.post(f"{url}/livraison/confirmer", headers=accueil)
    assert r.status_code == 200
    c = r.json()
    assert c["statut"] == "livree" and c["solde"] == 0
    assert c["livraison"]["mode"] == "retrait_atelier"
    # RG12 : plus modifiable
    assert client.patch(url, headers=accueil, json={"notes": "x"}).status_code == 409


def test_livraison_avec_solde_impaye_autorisee(client, accueil, tailleur, commande):
    avancer_jusqua_terminee(client, tailleur, commande["id"])
    r = client.post(
        f"{API}/commandes/{commande['id']}/livraison/confirmer",
        headers=accueil,
        json={"autoriser_solde_impaye": True},
    )
    assert r.status_code == 200 and r.json()["solde"] == 75000


def test_tableau_de_bord(client, admin, commande):
    r = client.get(f"{API}/statistiques/tableau-de-bord", headers=admin)
    assert r.status_code == 200
    d = r.json()
    assert d["chiffre_affaires_mois"] == 75000
    assert d["commandes_par_statut"]["livree"] == 0  # tous les statuts présents


def test_chiffre_affaires_dates_invalides(client, admin):
    r = client.get(
        f"{API}/statistiques/chiffre-affaires",
        headers=admin,
        params={"date_debut": "2026-12-01", "date_fin": "2026-01-01"},
    )
    assert r.status_code == 422


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
