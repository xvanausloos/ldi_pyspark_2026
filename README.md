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

**Différence 8080 vs 4040** :
- `http://localhost:8080` → UI du **Spark Master** (vue cluster) : liste des workers, ressources, applications.
- `http://localhost:4040` → UI de **l'application Spark** qui tourne dans `spark-client` (vue job) : jobs, stages, tasks, DAG, durées de tâches (c'est ici que l'on observe le skew).

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

### Générer le jeu de données `/data/sales`

Le script [`spark-apps/generate_data.py`](spark-apps/generate_data.py) génère un jeu de données de ventes volumineux et le stocke au format Parquet dans le répertoire partagé `/data/sales` (côté hôte : dossier `data/sales/`).

Depuis le conteneur `spark-client` :

```bash
docker compose exec -it spark-client bash

cd /opt/spark-apps
spark-submit \
  --master spark://spark-master:7077 \
  generate_data.py
```

Une fois l'exécution terminée, vous devriez voir les fichiers générés dans le dossier `data/sales/` sur votre machine.

Le but de ce dataset est d'expérimenté le Data Skew et comment régler le problème.

### Exécuter `skew_groupby.py` et interpréter les résultats

Le script [`spark-apps/skew_groupby.py`](spark-apps/skew_groupby.py) lit le dataset `/data/sales` puis calcule, pour chaque pays, le total des montants de vente (groupBy + sum).

Depuis le conteneur `spark-client` :

```bash
docker compose exec -it spark-client bash

cd /opt/spark-apps
spark-submit \
  --master spark://spark-master:7077 \
  skew_groupby.py
```

Dans la console, vous verrez un tableau de la forme :

```text
+-------+----------+
|country|     total|
+-------+----------+
|    FR |  ...     |
|    US |  ...     |
|    UK |  ...     |
+-------+----------+
```

L'intérêt de ce script est de montrer le **skew** : la majorité des lignes du dataset appartiennent au pays `FR`, ce qui crée un fort déséquilibre de charge entre partitions lors du groupBy et prépare les exercices suivants (salting, broadcast, AQE, etc.).

Allez observer la durée des stages par executors http://localhost:4040/stages/stage/?id=1&attempt=0

Il y a une preuve évidente de déséquilibre des données (data skew) dans le job Spark. 

Deux tâches ont traité 10,5 MiB / 10 000 000 d'enregistrements chacune.
Une tâche n'a traité que 18,4 KiB / 0 enregistrement.

Il s'agit d'un déséquilibre massif : deux tâches ont effectué la quasi-totalité du travail, tandis que la troisième n'a presque rien fait.

```
Index,Taille d'entrée / Enregistrements,Durée,Shuffle Write
0,"10,5 MiB / 10 000 000",1 s,109 B / 3
1,"10,5 MiB / 10 000 000","0,9 s",109 B / 3
2,"18,4 KiB / 0","0,6 s",0 B / 0
```

Les tâches 0 et 1 ont géré l'intégralité des données (10 millions d'enregistrements chacune).

La tâche 2 est restée pratiquement inactive (0 enregistrement).
Pourquoi est-ce un "Skew" ?

    Distribution inégale des données : Les données n'ont pas été partitionnées de manière uniforme. Deux partitions contenaient toutes les données, tandis qu'une était vide.

    Impact sur la performance : Les deux tâches occupées ont pris plus de temps, tandis que le troisième exécuteur était sous-utilisé.

    Gaspillage de ressources : Un exécuteur (ou cœur) était inactif alors que les autres étaient à pleine charge.

### Démonstration skew sur join
`spark-apps/skew_join.py` 

Depuis le conteneur `spark-client` :

```bash
`docker compose exec -it spark-client bash`

cd /opt/spark-apps
spark-submit \
  --master spark://spark-master:7077 \
  skew_join.py
```
On voit dans l'interface Spark Application `http://localhost:4040/stages/stage/?id=2&attempt=0` qu'un des executor n'a rien traité:

Executor ID,Logs (stdout),Logs (stderr),Address,Task Time,Total Tasks,Failed Tasks,Killed Tasks,Succeeded Tasks,Excluded,Input Size / Records,Shuffle Write Size / Records
2,[stdout](#),[stderr](#),172.21.0.6:40557,0.9 s,1,0,0,1,false,38.6 MiB / 10,000,000,59 B / 1
1,[stdout](#),[stderr](#),172.21.0.5:39433,1.0 s,1,0,0,1,false,38.6 MiB / 10,000,000,59 B / 1
0,[stdout](#),[stderr](#),172.21.0.3:42319,0.3 s,1,0,0,1,false,—,56 B / 1

## Correction avec Salting
`spark-apps/salted_join.py`

```bash
spark-submit \
  --master spark://spark-master:7077 \
  salted_join.py
```

## Correction du skew avec le broadcast join
`spark-apps/broadcast_join.py`


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

### Exécuter `generate_data.py` en local (optionnel)

Il est possible d'exécuter `generate_data.py` directement depuis votre environnement Python local géré par `uv`, mais pour le lab il est recommandé d'utiliser le cluster Docker (section précédente) afin de rester cohérent avec le reste des exercices.

Prérequis :
- environnement virtuel créé et synchronisé (`uv venv` puis `uv sync`) ;
- Java compatible avec Spark (par exemple un JDK 17 configuré via `JAVA_HOME`).

Depuis la racine du projet :

```bash
uv run python spark-apps/generate_data.py
```

Les données seront également écrites dans le répertoire `data/sales/`.

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
