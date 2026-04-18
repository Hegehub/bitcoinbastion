# 🏰 Bitcoin Bastion

> **Couche d’intelligence souveraine pour Bitcoin**

---

## 🚀 Vue d’ensemble

**Bitcoin Bastion** est une plateforme d’intelligence et d’opérations native Bitcoin, conçue pour fonctionner **au-dessus du protocole Bitcoin**.

Elle transforme l’état brut du réseau en :

- signaux exploitables
- évaluations des risques
- décisions opérationnelles
- insights de souveraineté

---

> La plupart des systèmes *consomment les données Bitcoin*.  
> Bitcoin Bastion **interprète la réalité Bitcoin**.

---

## 🎯 Problème

Les utilisateurs Bitcoin, les trésoreries et les opérateurs font face à un environnement fragmenté :

- les données on-chain sont bruitées et difficiles à interpréter  
- les risques liés à la structure des portefeuilles sont invisibles  
- les opérations de trésorerie sont manuelles et sujettes aux erreurs  
- l’exposition à la vie privée est mal comprise  
- la préparation à la récupération est rarement vérifiée  
- aucun système unifié n’existe pour l’**assurance de souveraineté**

---

## 💡 Solution

Bitcoin Bastion fournit un système unifié qui :

### 1. Comprend l’état de Bitcoin
- activité on-chain  
- actualités et narratifs  
- comportement des entités  

### 2. L’interprète
- génération de signaux explicables  
- scoring des risques  
- recommandations contextuelles  

### 3. Permet l’action
- workflows de trésorerie  
- application des politiques  
- visibilité opérationnelle  

### 4. Garantit la survivabilité (Citadel)
- préparation à la récupération  
- cartographie des dépendances  
- simulation de catastrophes  
- planification des réparations  

---

## 🧠 Architecture du système

```text
Réseau Bitcoin (couche protocolaire)
        ↓
Ingestion des données
  - On-chain
  - Actualités
  - Entités
        ↓
Couche d’interprétation
  - Moteur de signaux
  - Graphe d’explicabilité
        ↓
Couche opérationnelle
  - Intelligence des portefeuilles
  - Moteur de trésorerie
  - Moteur de politiques
  - Analyse de confidentialité
        ↓
Couche Citadel (souveraineté)
  - Récupération
  - Dépendances
  - Simulations
  - Plans de réparation
        ↓
Couche de livraison
  - API
  - Telegram
  - Outils opérateur
```

---

## 🏰 Citadel — Couche de souveraineté

Citadel est la couche déterminante du système.

Elle répond à des questions critiques :

* Vos bitcoins peuvent-ils être récupérés ?
* Quelles dépendances peuvent casser votre système ?
* Que se passe-t-il en conditions de défaillance ?
* Que faut-il corriger immédiatement ?

---

> Bastion vous dit ce qui se passe.
> Citadel vous dit si vous y survivrez.

---

## ⚙️ Capacités principales

### Intelligence

* Ingestion des actualités et suivi de la réputation
* Génération de signaux explicables
* Suivi des entités et listes de surveillance

### Surveillance on-chain

* Activité transactionnelle
* Détection des transferts importants
* Signaux basés sur les événements

### Portefeuille & trésorerie

* Évaluation de la santé des portefeuilles
* Workflows de demandes de trésorerie
* Approbations basées sur des politiques

### Politiques & confidentialité

* Simulation et application des politiques
* Scoring des risques de confidentialité

### Observabilité

* Métriques et sondes de santé
* Suivi des tâches et journaux d’audit

### Souveraineté (Citadel)

* Scoring d’évaluation
* Graphe de dépendances
* Préparation à la récupération
* Simulations de catastrophes
* Vérification de l’héritage
* Plans de réparation

---

## 🧰 Technologie

* **Backend** : FastAPI
* **Langage** : Python 3.12
* **Base de données** : PostgreSQL
* **ORM** : SQLAlchemy 2.x
* **File de tâches** : Celery + Redis
* **Migrations** : Alembic
* **Authentification** : JWT + Argon2
* **Métriques** : Prometheus
* **Telegram** : aiogram

---

## 📊 Feuille de route & état d’exécution

> ✔ = Implémenté
> ❌ = Pas encore terminé

---

### 🧱 Fondations

* ✔ Backend FastAPI modulaire
* ✔ Modèles de base de données & repositories
* ✔ Système d’authentification (JWT)
* ✔ Middleware / journalisation / métriques
* ✔ Infrastructure Docker
* ❌ Application complète de la cohérence des migrations
* ❌ Validation du schéma au niveau CI

---

### 📰 Couche d’intelligence

* ✔ Ingestion des actualités
* ✔ Moteur de signaux (baseline)
* ✔ Modèles d’explicabilité
* ❌ Maturité complète du pipeline de signaux
* ❌ Profondeur du graphe de preuves

---

### ⛓ Couche on-chain

* ✔ Baseline d’ingestion on-chain
* ✔ Abstraction des fournisseurs
* ❌ Intégration réelle d’un nœud Bitcoin
* ❌ Conscience de l’état de la chaîne
* ❌ Modélisation des réorganisations/finalité

---

### 👛 Portefeuille & trésorerie

* ✔ Évaluation de la santé des portefeuilles
* ✔ Workflows de trésorerie
* ✔ Moteur de politiques
* ✔ Scoring de confidentialité
* ❌ Intelligence UTXO
* ❌ Conscience des descripteurs
* ❌ Simulation de dépense

---

### 🏰 Citadel (souveraineté)

* ✔ Surface API Citadel
* ✔ Baseline d’évaluation
* ✔ Endpoints de récupération & simulation
* ❌ Modèles persistants de souveraineté
* ❌ Moteur de preuve de récupération
* ❌ Simulations déterministes
* ❌ Graphe complet des dépendances
* ❌ Véritable système de scoring

---

### ⚡ Profondeur native Bitcoin

* ❌ Moteur UTXO
* ❌ Moteur mempool
* ❌ Modélisation du marché des frais
* ❌ Conscience du système de scripts
* ❌ Système de descripteurs
* ❌ Moteur d’état de chaîne

---

### 📡 Livraison & opérations

* ✔ Endpoints d’administration
* ✔ Suivi des tâches
* ✔ Snapshot d’observabilité
* ❌ Runtime Telegram complet
* ❌ Orchestration de livraison
* ❌ Outils opérateur

---

## 🧠 Principes de conception

### Natif Bitcoin

Le système est construit sur :

* le modèle UTXO
* la structure des transactions
* la dynamique du marché des frais
* le système de scripts

---

### Explicabilité d’abord

Tous les résultats doivent :

* inclure un raisonnement
* montrer les preuves
* fournir un niveau de confiance

---

### Souveraineté d’abord

Le système suppose :

* aucune garde des fonds
* aucune confiance requise
* aucune hypothèse sur la configuration utilisateur

---

### Évolution modulaire

Chaque couche peut évoluer indépendamment :

* ingestion
* signaux
* politiques
* Citadel

---

## 🔐 Modèle de sécurité

* Aucune clé privée stockée
* Aucune manipulation de seed phrase
* Accès API authentifié
* Contrôle d’accès basé sur les rôles (baseline)

---

## 🧪 Développement

```bash
docker compose up --build
```

Documentation :

```
http://localhost:8000/docs
```

Métriques :

```
http://localhost:8000/metrics
```

---

## 🚧 Statut

Bitcoin Bastion est actuellement :

* une **plateforme backend solide**
* un **système d’intelligence fonctionnel**
* un **moteur de souveraineté à un stade précoce**

Il n’est pas encore :

* pleinement conscient du protocole Bitcoin
* pleinement déterministe
* pleinement durci pour la production

---

## 🧭 Vision

Bitcoin Bastion évolue vers :

> Un système qui comprend Bitcoin
>
> et garantit que vous y survivrez.

---

## 
