# LAB SPARK LDI Training Mars 2026

Voici un lab Spark complet (5 nœuds) pour expérimenter :

data skew

shuffle massif

broadcast join

salting

Adaptive Query Execution

avec Apache Spark dans un cluster local Docker.

Ce type de lab est très proche de ce qu’on utilise pour enseigner le tuning Spark.

Architecture du cluster

Cluster :

Spark Lab Cluster

        +----------------+
        |  Spark Driver  |
        +--------+-------+
                 |
                 v
           +------------+
           |  Master    |
           +-----+------+
                 |
   +-------------+-------------+
   |             |             |
+-------+     +-------+     +-------+
|Worker1|     |Worker2|     |Worker3|
+-------+     +-------+     +-------+

Total :

## Démarrer l'infrastructure Docker

Ce projet fournit un script pour installer et démarrer l'infrastructure Spark (cluster Docker) à partir du `docker-compose.yaml`.

Depuis la racine du projet :

```bash
chmod +x setup_install_infra.sh
./setup_install_infra.sh
```

Ce script :
- démarre Docker Desktop si nécessaire ;
- effectue un `docker compose pull` pour récupérer les images ;
- lance le cluster Spark en arrière-plan (`docker compose up -d`).

### Interfaces web fournies par le cluster

Une fois le cluster démarré, les interfaces suivantes sont disponibles :

- **Spark Master UI** : `http://localhost:8080`
- **Spark Worker 1 UI** : `http://localhost:8081`
- **Spark Worker 2 UI** : `http://localhost:8082`
- **Spark Worker 3 UI** : `http://localhost:8083`
- **Spark Application UI** (lorsqu'un job tourne dans le client) : `http://localhost:4040`

Ces ports sont mappés à partir des services définis dans `docker-compose.yaml` :
- `spark-master` (7077, 8080)
- `spark-worker-1` (8081)
- `spark-worker-2` (8082)
- `spark-worker-3` (8083)
- `spark-client` (4040)

### Utiliser le conteneur client Spark

Le service `spark-client` est prévu pour lancer des commandes interactives ou des jobs Spark contre le master.

Se connecter en shell dans le conteneur client :

```bash
docker compose exec -it spark-client bash
```

Depuis ce shell, les scripts du dossier `spark-apps` du projet sont montés dans `/opt/spark-apps` et les données dans `/data`.  
Exemples :

```bash
# Shell interactif Scala
spark-shell --master spark://spark-master:7077

# Shell SQL
spark-sql --master spark://spark-master:7077

# Lancer un script Python fourni par le lab
spark-submit \
  --master spark://spark-master:7077 \
  generate_data.py
```

### Arrêter le cluster

Pour arrêter les conteneurs sans supprimer les données :

```bash
docker compose down
```

Pour tout supprimer (y compris les volumes anonymes) :

```bash
docker compose down -v
```

## Environnement Python avec `uv`

Ce projet utilise `uv` pour gérer l'environnement virtuel Python et les dépendances.

### Installation de `uv` (une seule fois)

Sur macOS :

```bash
brew install uv
```

ou via le script officiel :

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Créer et utiliser l'environnement virtuel

Depuis la racine du projet :

```bash
# Créer un environnement virtuel local (.venv)
uv venv

# Activer l'environnement
source .venv/bin/activate
```

### Gérer les dépendances

**Ajouter un nouveau package** (par exemple `pyspark`) :

```bash
uv add pyspark
```

**Ajouter un package avec une version précise** :

```bash
uv add pyspark==3.5.5
```

Cela met automatiquement à jour le fichier `pyproject.toml` et, si besoin, le `uv.lock`.

**Installer toutes les dépendances définies dans le projet** (utile après un `git clone`) :

```bash
uv sync
```

**Installer uniquement les dépendances de dev** (section `dev` dans `pyproject.toml`) :

```bash
uv sync --group dev
```

**Exécuter un script Python dans l'environnement** :

```bash
uv run python votre_script.py
```

## Structure du projet 
```
ldi_pyspark_2026
│
├── docker-compose.yml
│
├── spark-apps
│   ├── generate_data.py
│   ├── skew_groupby.py
│   ├── skew_join.py
│   ├── salted_join.py
│   └── broadcast_join.py
│
└── data
````
