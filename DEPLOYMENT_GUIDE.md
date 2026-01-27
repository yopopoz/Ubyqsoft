# Guide de Déploiement sur KVM Hostinger

Suivez ces étapes pour déployer votre application sur votre serveur VPS.

## 1. Prérequis sur le serveur (SSH)
Connectez-vous à votre VPS :
```bash
ssh root@votre_ip_serveur
```

Installez Docker et Docker Compose :
```bash
# Mettre à jour les paquets
apt update && apt upgrade -y

# Installer Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Vérifier l'installation
docker compose version
```

## 2. Organisation et Transfert (Multi-App Ready)
Pour héberger plusieurs applications proprement, nous allons utiliser le dossier `/opt/` qui est le standard pour les logiciels tiers.

Structure recommandée sur le serveur :
```
/opt/
  ├── bbox-l/          <-- Votre application actuelle
  ├── autre-app/       <-- Vos futures applications
  └── proxy/           <-- (Optionnel) Un proxy global pour gérer les domaines
```

### Méthode 1 : Git (Recommandé pour les mises à jour faciles)
**Avantage** : Plus rapide pour les mises à jour suivantes (juste `git pull`).
**Pré-requis** : Avoir un compte GitHub ou GitLab.

1.  **Sur votre PC Local** (si ce n'est pas déjà fait) :
    ```powershell
    # Initialiser git
    git init
    git add .
    git commit -m "Déploiement initial"
    
    # Lier à votre dépôt distant (exemple GitHub)
    git branch -M main
    git remote add origin https://github.com/VOTRE_USER/VOTRE_PROJET.git
    git push -u origin main
    ```

2.  **Sur le Serveur** :
    ```bash
    # Créer le dossier et cloner (une seule fois au début)
    # Note : Il faudra peut-être générer une clé SSH sur le serveur pour GitHub/GitLab
    git clone https://github.com/VOTRE_USER/VOTRE_PROJET.git /opt/bbox-l
    ```

3.  **Pour mettre à jour plus tard** :
    ```bash
    cd /opt/bbox-l
    git pull
    docker compose -f docker-compose.prod.yml up -d --build
    ```

### Méthode 2 : SCP (Copie directe sans Git)
Utilisez cette méthode si vous ne voulez pas mettre votre code sur GitHub/GitLab.


```powershell
# 1. Créer le dossier sur le serveur
ssh root@82.112.253.118 "mkdir -p /opt/bbox-l"

# 2. Transférer les fichiers
# (Il vous demandera votre mot de passe à chaque fois sauf si vous avez une clé SSH)

scp -r "c:\Users\pc\Desktop\BBOX L\frontend" root@82.112.253.118:/opt/bbox-l/
scp -r "c:\Users\pc\Desktop\BBOX L\backend" root@82.112.253.118:/opt/bbox-l/
scp -r "c:\Users\pc\Desktop\BBOX L\nginx" root@82.112.253.118:/opt/bbox-l/
scp "c:\Users\pc\Desktop\BBOX L\docker-compose.prod.yml" root@82.112.253.118:/opt/bbox-l/
```

## 3. Lancer l'application
Sur le serveur :

```bash
cd /opt/bbox-l

# Créer un dossier pour nginx si non existant (si transfert incomplet)
mkdir -p nginx && nano nginx/nginx.conf
# (Collez le contenu de nginx.conf si nécessaire)

# Lancer la production
docker compose -f docker-compose.prod.yml up -d --build
```

## 4. Configuration (Optionnel mais recommandé)
Pour changer les mots de passe ou secrets, créez un fichier `.env` sur le serveur dans `/opt/bbox-l` :

```env
POSTGRES_USER=admin
POSTGRES_PASSWORD=votre_mot_de_passe_secret
POSTGRES_DB=logistics_prod
JWT_SECRET=super_secret_jwt_key
FRONTEND_URL=http://votre_domaine.com
```

Puis relancez :
```bash
docker compose -f docker-compose.prod.yml up -d
```

## 5. Accès
L'application devrait être accessible sur `http://votre_ip_serveur`.
- Frontend : `http://votre_ip_serveur`
- API : `http://votre_ip_serveur/api/health`

## Notes
- Si vous utilisez un domaine, pointez les enregistrements DNS A vers l'IP du VPS.
- Pour le HTTPS, la méthode la plus simple est d'utiliser un reverse proxy comme Traefik ou de configurer Certbot/Let's Encrypt sur le serveur hôte ou dans le conteneur Nginx.

## 6. Initialisation de la Base de Données (Premier lancement)
Lors de la première installation, la base de données est vide. Vous devez exécuter une commande pour créer l'utilisateur administrateur par défaut.

Sur le serveur, dans le dossier `/opt/bbox-l` :

```bash
# Initialiser les données (crée admin@example.com / admin)
docker compose -f docker-compose.prod.yml exec backend python -m app.seed_data
```

**Identifiants par défaut :**
- Email : `admin@example.com`
- Mot de passe : `admin`

