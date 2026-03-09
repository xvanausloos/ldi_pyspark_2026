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