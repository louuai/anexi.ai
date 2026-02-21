# 🔧 Quick Fix - Email Validator

## Problème Rencontré

Erreur lors du démarrage:
```
ImportError: email-validator is not installed
```

## ✅ Solution

Il manquait la dépendance `email-validator` pour valider les emails avec Pydantic.

### Fix Rapide

```bash
pip install pydantic[email]
```

OU installer directement:

```bash
pip install email-validator
```

### Requirements.txt Mis à Jour

Le fichier `requirements.txt` a été mis à jour pour inclure `pydantic[email]`:

```txt
fastapi
uvicorn
SQLAlchemy>=1.4
psycopg2-binary
pydantic
pydantic[email]          # ← AJOUTÉ
alembic
python-jose[cryptography]
passlib[bcrypt]
python-multipart
```

## 🚀 Pour Redémarrer

```bash
# Réinstaller les dépendances
pip install -r requirements.txt

# Lancer le serveur
uvicorn app.main:app --reload
```

L'API devrait démarrer sans problème maintenant!

## ✅ Vérification

Après le fix, vous devriez voir:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

Accédez à: http://127.0.0.1:8000/docs pour voir la documentation Swagger!
