"""Tests des clients et des mesures (RG1 à RG4)."""

from tests.conftest import API


def test_telephone_normalise_et_unique(client, accueil, fatou):
    """RG1 : "77 123 45 67" et "771234567" désignent le même client."""
    assert fatou["telephone"] == "771234567"
    r = client.post(
        f"{API}/clients",
        headers=accueil,
        json={"nom": "Ba", "prenom": "Awa", "telephone": "771234567"},
    )
    assert r.status_code == 409


def test_telephone_invalide(client, accueil):
    r = client.post(
        f"{API}/clients",
        headers=accueil,
        json={"nom": "Ba", "prenom": "Awa", "telephone": "12ab"},
    )
    assert r.status_code == 422


def test_garder_son_numero_nest_pas_un_doublon(client, accueil, fatou):
    r = client.patch(
        f"{API}/clients/{fatou['id']}",
        headers=accueil,
        json={"telephone": "77.123.45.67"},
    )
    assert r.status_code == 200


def test_nom_ne_peut_pas_etre_vide(client, accueil, fatou):
    r = client.patch(f"{API}/clients/{fatou['id']}", headers=accueil, json={"nom": ""})
    assert r.status_code == 422


def test_mesures_au_moins_une_et_bornees(client, tailleur, fatou):
    """RG2."""
    url = f"{API}/clients/{fatou['id']}/mesures"
    assert client.post(url, headers=tailleur, json={}).status_code == 422
    assert client.post(url, headers=tailleur, json={"tour_cou": 0}).status_code == 422
    assert client.post(url, headers=tailleur, json={"tour_cou": 301}).status_code == 422
    assert client.post(url, headers=tailleur, json={"tour_cou": 38}).status_code == 201


def test_dernieres_mesures(client, tailleur, fatou):
    """RG3 : la prise de date la plus récente."""
    url = f"{API}/clients/{fatou['id']}/mesures"
    client.post(
        url, headers=tailleur, json={"tour_cou": 37, "date_prise": "2026-01-01"}
    )
    client.post(
        url, headers=tailleur, json={"tour_cou": 39, "date_prise": "2026-06-01"}
    )
    r = client.get(f"{url}/derniere", headers=tailleur)
    assert r.json()["tour_cou"] == 39


def test_correction_ne_peut_pas_tout_vider(client, tailleur, fatou):
    m = client.post(
        f"{API}/clients/{fatou['id']}/mesures", headers=tailleur, json={"tour_cou": 38}
    ).json()
    r = client.patch(
        f"{API}/mesures/{m['id']}", headers=tailleur, json={"tour_cou": None}
    )
    assert r.status_code == 422


def test_suppressions_bloquees_si_utilisees(client, admin, tailleur, accueil, fatou):
    """RG4 : client avec commandes et mesures utilisées ne se suppriment pas."""
    m = client.post(
        f"{API}/clients/{fatou['id']}/mesures", headers=tailleur, json={"tour_cou": 38}
    ).json()
    client.post(
        f"{API}/commandes",
        headers=accueil,
        json={"client_id": fatou["id"], "lignes": [{"type_vetement_id": 1}]},
    )
    assert (
        client.delete(f"{API}/mesures/{m['id']}", headers=tailleur).status_code == 409
    )
    assert (
        client.delete(f"{API}/clients/{fatou['id']}", headers=admin).status_code == 409
    )
