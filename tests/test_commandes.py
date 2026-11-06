"""Tests des commandes et du workflow (RG5 à RG15)."""

import re
from datetime import date, timedelta

from tests.conftest import API, avancer_jusqua_terminee


def test_numero_et_montants(commande):
    """RG5 et RG7."""
    assert re.fullmatch(r"CMD-\d{4}-\d{5}", commande["numero"])
    assert commande["montant_total"] == 75000
    assert commande["solde"] == 75000
    assert commande["statut"] == "en_attente"


def test_date_prevue_par_defaut(commande):
    """RG8 : date de commande + le plus long délai (Boubou : 10 jours)."""
    attendu = date.today() + timedelta(days=10)
    assert commande["date_livraison_prevue"] == attendu.isoformat()


def test_remise_trop_grande(client, accueil, fatou):
    r = client.post(
        f"{API}/commandes",
        headers=accueil,
        json={
            "client_id": fatou["id"],
            "lignes": [{"type_vetement_id": 2}],
            "remise": 99999,
        },
    )
    assert r.status_code == 422


def test_prestation_inactive_refusee(client, accueil, fatou):
    """RG6."""
    r = client.post(
        f"{API}/commandes",
        headers=accueil,
        json={"client_id": fatou["id"], "lignes": [{"type_vetement_id": 3}]},
    )
    assert r.status_code == 422


def test_mesures_automatiques_et_appartenance(client, accueil, tailleur, fatou):
    """RG9."""
    m = client.post(
        f"{API}/clients/{fatou['id']}/mesures", headers=tailleur, json={"tour_cou": 38}
    ).json()
    c = client.post(
        f"{API}/commandes",
        headers=accueil,
        json={"client_id": fatou["id"], "lignes": [{"type_vetement_id": 1}]},
    ).json()
    assert c["mesure_id"] == m["id"]
    # Mesures d'un autre client : refusées
    autre = client.post(
        f"{API}/clients",
        headers=accueil,
        json={"nom": "Ba", "prenom": "Awa", "telephone": "780000000"},
    ).json()
    r = client.post(
        f"{API}/commandes",
        headers=accueil,
        json={
            "client_id": autre["id"],
            "mesure_id": m["id"],
            "lignes": [{"type_vetement_id": 1}],
        },
    )
    assert r.status_code == 422


def test_transition_interdite_avec_message(client, accueil, commande):
    """Workflow : le message indique les statuts possibles."""
    r = client.post(
        f"{API}/commandes/{commande['id']}/statut",
        headers=accueil,
        json={"statut": "terminee"},
    )
    assert r.status_code == 409
    assert "Statuts possibles : annulee, en_coupe" in r.json()["detail"]


def test_meme_statut_et_livree_refuses(client, accueil, commande):
    """RG13."""
    url = f"{API}/commandes/{commande['id']}/statut"
    assert (
        client.post(url, headers=accueil, json={"statut": "en_attente"}).status_code
        == 409
    )
    assert (
        client.post(url, headers=accueil, json={"statut": "livree"}).status_code == 409
    )


def test_tailleur_ne_peut_pas_annuler(client, tailleur, commande):
    """RG14."""
    r = client.post(
        f"{API}/commandes/{commande['id']}/statut",
        headers=tailleur,
        json={"statut": "annulee"},
    )
    assert r.status_code == 403


def test_annulation_avec_acompte_exige_commentaire(client, accueil, commande):
    """RG14."""
    client.post(
        f"{API}/commandes/{commande['id']}/paiements",
        headers=accueil,
        json={"montant": 10000, "mode": "wave"},
    )
    url = f"{API}/commandes/{commande['id']}/statut"
    assert (
        client.post(url, headers=accueil, json={"statut": "annulee"}).status_code == 422
    )
    r = client.post(
        url,
        headers=accueil,
        json={"statut": "annulee", "commentaire": "Remboursé en espèces"},
    )
    assert r.status_code == 200


def test_historique(client, tailleur, commande):
    """RG15 : création + changements tracés, avec aller-retour essayage/retouches."""
    url = f"{API}/commandes/{commande['id']}"
    for s in [
        "en_coupe",
        "en_couture",
        "essayage",
        "retouches",
        "essayage",
        "terminee",
    ]:
        assert (
            client.post(
                f"{url}/statut", headers=tailleur, json={"statut": s}
            ).status_code
            == 200
        )
    histo = client.get(f"{url}/historique", headers=tailleur).json()
    assert histo[0]["ancien_statut"] is None
    assert len(histo) == 7


def test_lignes_modifiables_seulement_en_attente(client, accueil, tailleur, commande):
    """RG10."""
    url = f"{API}/commandes/{commande['id']}"
    r = client.post(f"{url}/lignes", headers=accueil, json={"type_vetement_id": 2})
    assert r.status_code == 201
    assert r.json()["montant_total"] == 87000
    client.post(f"{url}/statut", headers=tailleur, json={"statut": "en_coupe"})
    r = client.post(f"{url}/lignes", headers=accueil, json={"type_vetement_id": 2})
    assert r.status_code == 409


def test_derniere_ligne_non_supprimable(client, accueil, fatou):
    c = client.post(
        f"{API}/commandes",
        headers=accueil,
        json={"client_id": fatou["id"], "lignes": [{"type_vetement_id": 1}]},
    ).json()
    ligne_id = c["lignes"][0]["id"]
    r = client.delete(f"{API}/commandes/{c['id']}/lignes/{ligne_id}", headers=accueil)
    assert r.status_code == 409


def test_total_jamais_sous_le_paye(client, accueil, commande):
    """RG7 : une remise qui ramènerait le total sous le payé est refusée."""
    client.post(
        f"{API}/commandes/{commande['id']}/paiements",
        headers=accueil,
        json={"montant": 70000, "mode": "especes"},
    )
    r = client.patch(
        f"{API}/commandes/{commande['id']}", headers=accueil, json={"remise": 20000}
    )
    assert r.status_code == 409
