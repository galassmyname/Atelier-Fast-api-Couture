"""Tests de l'authentification (RG21 à RG24) et des droits par rôle."""

from tests.conftest import API, MOT_DE_PASSE


def test_login_et_profil_sans_hash(client, admin):
    r = client.get(f"{API}/auth/me", headers=admin)
    assert r.status_code == 200
    assert "mot_de_passe_hash" not in r.json()  # RG21


def test_login_meme_message_si_echec(client):
    """RG23 : même message que l'e-mail soit inconnu ou le mot de passe faux."""
    r1 = client.post(
        f"{API}/auth/login",
        data={"username": "inconnu@test.sn", "password": MOT_DE_PASSE},
    )
    r2 = client.post(
        f"{API}/auth/login", data={"username": "admin@test.sn", "password": "mauvais"}
    )
    assert r1.status_code == r2.status_code == 401
    assert r1.json()["detail"] == r2.json()["detail"]


def test_sans_jeton_401(client):
    assert client.get(f"{API}/clients").status_code == 401


def test_compte_desactive_refuse_immediatement(client, admin, accueil):
    """RG22 : un compte désactivé est refusé même avec un jeton encore valide."""
    client.patch(f"{API}/utilisateurs/2", headers=admin, json={"actif": False})
    assert client.get(f"{API}/auth/me", headers=accueil).status_code == 401


def test_admin_ne_peut_pas_se_desactiver(client, admin):
    """RG24."""
    r = client.patch(f"{API}/utilisateurs/1", headers=admin, json={"actif": False})
    assert r.status_code == 409
    r = client.patch(f"{API}/utilisateurs/1", headers=admin, json={"role": "accueil"})
    assert r.status_code == 409


def test_mot_de_passe_trop_court(client, admin):
    r = client.post(
        f"{API}/utilisateurs",
        headers=admin,
        json={
            "email": "x@test.sn",
            "nom_complet": "X",
            "mot_de_passe": "court",
            "role": "accueil",
        },
    )
    assert r.status_code == 422


def test_droits_par_role(client, accueil, tailleur, fatou):
    """403 quand le rôle est insuffisant."""
    # L'accueil ne peut pas prendre de mesures
    r = client.post(
        f"{API}/clients/{fatou['id']}/mesures", headers=accueil, json={"tour_cou": 38}
    )
    assert r.status_code == 403
    # Le tailleur ne peut pas créer de commande
    r = client.post(
        f"{API}/commandes",
        headers=tailleur,
        json={"client_id": fatou["id"], "lignes": [{"type_vetement_id": 1}]},
    )
    assert r.status_code == 403
    # Seul l'admin voit les statistiques et supprime des clients
    assert (
        client.get(f"{API}/statistiques/tableau-de-bord", headers=accueil).status_code
        == 403
    )
    assert (
        client.delete(f"{API}/clients/{fatou['id']}", headers=accueil).status_code
        == 403
    )
    assert client.get(f"{API}/utilisateurs", headers=tailleur).status_code == 403
