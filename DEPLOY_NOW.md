# 🚀 DÉPLOIEMENT AZALSCORE EN UN CLIC

## Option 1: Déploiement Render.com (RECOMMANDÉ - Gratuit)

### Cliquez sur ce lien:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/MASITH-developpement/Azalscore)

**C'est tout!** Le système fait le reste automatiquement.

---

## Ce qui se passe automatiquement:

1. ✅ Création de la base de données PostgreSQL
2. ✅ Déploiement de l'API FastAPI
3. ✅ Déploiement du Frontend React
4. ✅ Configuration HTTPS automatique
5. ✅ Génération des secrets
6. ✅ Connexion entre les services

---

## Après le déploiement (3-5 minutes):

**URLs générées automatiquement:**
- Frontend: `https://azalscore-frontend.onrender.com`
- API: `https://azalscore-api.onrender.com`
- Documentation: `https://azalscore-api.onrender.com/docs`

**Identifiants par défaut:**
- Email: `admin@azalscore.local`
- Password: (affiché dans les logs de déploiement)

---

## Option 2: Déploiement Local Docker

Si Docker est installé sur votre machine:

```bash
cd /home/user/Azalscore
./installer/install.sh --auto
```

---

## Option 3: Déploiement Manuel

Si aucune des options ci-dessus ne fonctionne:

1. Créez un compte sur https://render.com (gratuit)
2. Cliquez "New" → "Blueprint"
3. Connectez votre repo GitHub
4. Sélectionnez ce repo
5. Cliquez "Apply"

---

## Support

En cas de problème:
- Issues: https://github.com/MASITH-developpement/Azalscore/issues
- Documentation: /docs/DEPLOYMENT.md
