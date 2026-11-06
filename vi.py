"""Importe chaque module séparément et affiche toutes les erreurs d'un coup."""
import importlib
import os
import traceback
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite://"          # base factice, aucune connexion
os.environ.setdefault("SECRET_KEY", "verification")

erreurs = 0
for fichier in sorted(Path("app").rglob("*.py")):
    module = ".".join(fichier.with_suffix("").parts)
    try:
        importlib.import_module(module)
    except Exception as e:
        erreurs += 1
        derniere = traceback.extract_tb(e.__traceback__)[-1]
        print(f"❌ {module}\n   {type(e).__name__}: {e}\n   -> {derniere.filename}:{derniere.lineno}\n")

print("Tout s'importe correctement ✅" if erreurs == 0 else f"{erreurs} module(s) en erreur")