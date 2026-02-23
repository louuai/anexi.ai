# 🎨 Anexi.ai Frontend - Premium UI

Interface élégante et professionnelle pour Anexi.ai avec animations fluides et design moderne.

## 📦 Structure

```
frontend/
├── index.html          # Page d'accueil
├── login.html          # Page de connexion
├── signup.html         # Page d'inscription (multi-step)
├── css/
│   └── style.css       # Styles complets avec animations
└── js/
    ├── auth.js         # Logique d'authentification
    └── animations.js   # Animations homepage
```

## ✨ Features

### 🎯 Pages Incluses

1. **Homepage (index.html)**
   - Hero section animée avec businessman travaillant sur laptop
   - Statistiques avec compteurs animés
   - Features grid
   - Navigation responsive

2. **Login (login.html)**
   - Split screen design
   - Animation de businessman productif (gauche)
   - Formulaire élégant (droite)
   - Toggle password visibility
   - Google OAuth button
   - Remember me & Forgot password

3. **Signup (signup.html)**
   - Multi-step form (3 étapes)
   - Progress indicator animé
   - Business type selection avec radio cards
   - Password strength meter
   - Success animation avec confetti
   - Auto-login après inscription

### 🎨 Design Features

- **Animations fluides** : Floating, typing, growing charts
- **Gradient backgrounds** animés
- **Glass morphism** effects
- **Professional color scheme** (Indigo/Purple)
- **Responsive** : Mobile, tablet, desktop
- **Dark/Light elements** bien contrastés

### 🔐 Authentication Features

- JWT token storage
- Auto-redirect si déjà connecté
- Toast notifications
- Form validation
- Password strength checker
- Multi-step signup avec validation

## 🚀 Installation

### Prérequis
- API Gateway Anexi.ai en cours d'exécution sur `http://localhost:8000`

### Étapes

1. **Ouvrir directement dans le navigateur**
```bash
# Simplement double-cliquer sur index.html
# OU utiliser un serveur local
```

2. **Avec Live Server (Recommandé)**
```bash
# VS Code extension: Live Server
# Clic droit sur index.html > Open with Live Server
```

3. **Avec Python SimpleHTTPServer**
```bash
cd frontend
python -m http.server 8080
# Ouvrir http://localhost:8080
```

## 🎯 Utilisation

### Test du Flow Complet

1. **Homepage**
   - Ouvrir `index.html`
   - Voir les animations (businessman qui tape, graphiques)
   - Cliquer sur "Get Started"

2. **Signup**
   - Étape 1: Remplir nom, email, password
   - Voir le password strength meter
   - Étape 2: Choisir business type (FB Ads / Shopify / WhatsApp / Mix)
   - Étape 3: Accepter les terms
   - Soumettre → Auto-login → Redirect vers dashboard

3. **Login**
   - Email + Password
   - Remember me
   - Submit → Get JWT token → Redirect

### Configuration API

Dans `js/auth.js`, modifier l'URL de l'API si besoin:

```javascript
const API_URL = '/api';  // Requêtes proxifiées par Nginx vers api-gateway
```

## 🎨 Personnalisation

### Couleurs

Dans `css/style.css`:

```css
:root {
    --primary: #6366F1;        /* Indigo principal */
    --primary-dark: #4F46E5;   /* Indigo foncé */
    --secondary: #10B981;      /* Vert success */
    /* ... */
}
```

### Animations

Modifier les keyframes dans `style.css`:
- `@keyframes float` - Animation flottante
- `@keyframes typing` - Animation typing
- `@keyframes growBar` - Croissance des barres
- etc.

### Illustrations

Les illustrations sont **entièrement CSS/HTML** (pas d'images):
- Businessman scene
- Office chair
- Laptop avec dashboard
- Floating icons
- Success animations

Pour modifier, éditer les classes `.businessman`, `.laptop`, etc. dans `style.css`.

## 📱 Responsive Design

Breakpoints:
- **Desktop**: > 1024px (full features)
- **Tablet**: 768px - 1024px (layout adapté)
- **Mobile**: < 768px (single column, simplifié)

## 🔧 Troubleshooting

### Backend Connection Issues

Si l'authentification ne fonctionne pas:

1. Vérifier que le backend tourne:
```bash
curl http://localhost:8000/health
```

2. Vérifier CORS dans le backend (`main.py`):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # OK pour dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

3. Ouvrir la console du navigateur (F12) pour voir les erreurs

### Animations ne se chargent pas

1. Vérifier que tous les fichiers CSS/JS sont chargés
2. Ouvrir F12 > Network pour voir les 404s
3. Vérifier les chemins relatifs des fichiers

## 📊 Performance

- **CSS**: ~50KB (minifié)
- **JS**: ~10KB (minifié)
- **Total page load**: < 100KB (sans images)
- **Animation FPS**: 60fps smooth

## 🎯 Next Steps

1. **Dashboard** - Créer `dashboard.html` avec analytics
2. **Orders Page** - Liste des commandes avec filtres
3. **Settings** - Profile management
4. **Dark Mode** - Toggle dark/light theme

## 🤝 Intégration avec Backend

L'interface utilise les endpoints:
- `POST /auth/signup` - Création de compte
- `POST /auth/login` - Connexion
- `POST /auth/profile` - Choix du profil business
- `GET /auth/me` - Info utilisateur

Token JWT stocké dans `localStorage`:
```javascript
localStorage.getItem('access_token')
localStorage.getItem('user_id')
```

## 📝 Notes

- **Google OAuth**: Bouton présent mais non fonctionnel (à implémenter backend)
- **Forgot Password**: Lien présent mais non fonctionnel (à implémenter)
- **Dashboard redirect**: Pointe vers `dashboard.html` (à créer)

## 🎨 Design Inspirations

Le design s'inspire de:
- **Stripe** - Clean, professional
- **Vercel** - Animations fluides
- **Linear** - Minimalisme élégant
- **Notion** - Multi-step forms

## 🚀 Production Ready

Pour la production:
1. Minifier CSS/JS
2. Optimiser les animations (reduce-motion)
3. Ajouter loading states
4. Implémenter error boundaries
5. SEO optimization
6. Analytics tracking

---

**Made with 💜 for Anexi.ai**
