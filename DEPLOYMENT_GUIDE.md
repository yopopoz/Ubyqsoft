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

### Méthode Automatisée (Recommandée)

Nous avons créé des scripts pour automatiser tout le processus.

1.  **Préparation du Git** :
    Assurez-vous que tout votre code est commité et "pushé" sur votre dépôt GitHub/GitLab.
    ```bash
    git push origin main
    ```

2.  **Configuration Initiale du Serveur** (À faire une seule fois) :
    Ce script installe Docker, Git, et prépare les dossiers.
    ```powershell
    # Depuis votre PC local (dans le dossier du projet)
    ./scripts/setup_server.sh <IP_DU_SERVEUR>
    # Exemple : ./scripts/setup_server.sh 82.112.253.118
    ```

3.  **Déploiement / Mise à jour** :
    Ce script télécharge la dernière version du code et redémarre les conteneurs.
    ```powershell
    # Usage : ./scripts/deploy.sh <IP_DU_SERVEUR> <URL_DU_REPO_GIT>
    ./scripts/deploy.sh 82.112.253.118 https://github.com/VOTRE_USER/VOTRE_PROJET.git
    ```

### Méthode Manuelle (Alternative)

Si vous préférez tout faire manuellement ou si les scripts ne fonctionnent pas pour une raison spécifique.

#### 1. Transfert du code
**Via Git** :
```bash
ssh root@<IP_DU_SERVEUR>
cd /opt/bbox-l
git pull
```

**Via SCP** (Copie directe) :
```powershell
scp -r "c:\Users\pc\Desktop\BBOX L\frontend" root@<IP_DU_SERVEUR>:/opt/bbox-l/
scp -r "c:\Users\pc\Desktop\BBOX L\backend" root@<IP_DU_SERVEUR>:/opt/bbox-l/
scp "docker-compose.prod.yml" root@<IP_DU_SERVEUR>:/opt/bbox-l/
```

#### 2. Lancement
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

## 4. Configuration HTTPS et Domaine

Une fois l'application lancée, configurez votre domaine pour pointer vers l'IP du serveur.
Pour le HTTPS, vous pouvez utiliser un reverse proxy comme Nginx Proxy Manager ou Traefik, ou configurer Certbot sur le Nginx hôte.

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

