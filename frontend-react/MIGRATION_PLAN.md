# Migration Frontend vers React (zero regression visuelle)

## Objectif
Migrer le frontend HTML/CSS/JS vers React sans casser le design ni les parcours utilisateur.

## Strategie
1. Garder le frontend legacy intact (`frontend/`) pendant la migration.
2. Migrer page par page vers `frontend-react/src/pages`.
3. Conserver les classes CSS existantes a chaque etape.
4. Remplacer progressivement les scripts DOM par des hooks React.
5. Valider visuellement avant/apres sur desktop et mobile.

## Ordre recommande
1. Landing (`index.html`) - deja commencee
2. Login / Signup
3. Dashboard
4. Payment
5. Admin / Super Admin

## Regles de non-regression
1. Meme HTML visuel (structure + classes) pendant la premiere passe.
2. Aucune nouvelle librairie UI tant que la parite n'est pas validee.
3. Captures avant/apres obligatoires pour chaque page.
4. Validation responsive sur au moins 360px, 768px, 1280px.

## Lancement local
```bash
cd frontend-react
npm install
npm run dev
```

## Commandes Docker utiles
Demarrer les services backend/microservices pendant la migration frontend:

```bash
docker compose up -d
```

Si vous utilisez la stack microservices dediee:

```bash
docker compose -f docker-compose.microservices.yml up -d
```

Arreter les services:

```bash
docker compose down
docker compose -f docker-compose.microservices.yml down
```
