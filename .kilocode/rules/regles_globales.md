# regles_globales.md

Règles générales applicables à toutes les tâches exécutées par Kilo Code.

## Lignes directrices

- Utiliser uniquement des caractères ASCII dans les messages `print`, les logs, les commandes exécutées, et les noms de fichiers temporaires.
- Vérifier les attributs des objets avant de les utiliser (avec `hasattr` ou documentation).
- Valider les paramètres de configuration avant de les passer à une fonction.
- Mettre à jour systématiquement la liste des tâches après chaque étape.
- Créer des fichiers temporaires dans un contexte `tempfile` et les supprimer immédiatement après usage.
- Éviter les caractères Unicode dans les commandes exécutées via `execute_command`.
- Commenter les modifications importantes dans le code et inclure des docstrings.
- Attraper les exceptions dans les scripts de test et afficher un message clair.
- Apprendre de ses erreurs : après chaque erreur identifiée, mettre à jour les fichiers de règles (`regles_globales.md` et `regles_environnement_travail.md`) pour inclure une nouvelle ligne directrice ou clarifier une existante.
- Lors de la lecture de fichiers compressés (gzip) avec Python, si la sortie `print` n'apparaît pas, utiliser `sys.stdout.buffer.write(data)` pour écrire les bytes bruts directement.
- Préférer les commandes Python aux commandes shell spécifiques (PowerShell, cmd) pour les opérations de système sous Windows, car elles sont plus portables et évitent les problèmes de shell.
- Vérifier la syntaxe des commandes Python à une ligne avant exécution ; utiliser des blocs multilignes si nécessaire.
- En cas d'absence de sortie après une commande `execute_command`, vérifier si le fichier est vide, puis essayer d'écrire directement les bytes ou changer d'encodage.
- Éviter les commandes Unix incompatibles avec Windows (head, grep, tail, etc.) dans `execute_command`. Utiliser des commandes PowerShell natives ou des alternatives Python.
- Préférer les chemins relatifs aux chemins absolus. Utiliser `os.path.join` pour la portabilité.
- Les noms de fichiers et de répertoires doivent être en minuscules, sans espaces, avec des underscores pour la séparation.
- Les scripts Python doivent être exécutables avec `python -m` depuis la racine du projet.
- Les dépendances externes doivent être documentées dans `requirements.txt` ou `pyproject.toml`.
- Les tests doivent être écrits avec `pytest` et placés dans le répertoire `tests/`.
- Les logs doivent être structurés et inclure des timestamps. Utiliser le module `logging` avec des handlers appropriés.
- Les fonctions doivent avoir des signatures typées (type hints) lorsque possible.
- Les docstrings doivent suivre le format Google ou NumPy, en français pour les projets francophones.
- Les commits Git doivent être descriptifs et suivre la convention de messages (ex: `feat: ajout de X`).
- Les branches doivent être nommées selon le modèle `feature/nom`, `bugfix/nom`, `hotfix/nom`.
- Les configurations sensibles (clés API, mots de passe) ne doivent jamais être commitées. Utiliser des variables d'environnement.
- Les performances doivent être considérées : éviter les boucles imbriquées inutiles, utiliser des structures de données appropriées.
- La sécurité : valider les entrées utilisateur, éviter les injections (SQL, commandes).
- La lisibilité du code est prioritaire sur l'optimisation prématurée.
- Utiliser des outils de linting (`flake8`, `black`, `isort`) pour maintenir un style cohérent.
- Documenter les décisions architecturales dans un fichier `ARCHITECTURE.md` ou `DECISIONS.md`.
- Les images et ressources binaires doivent être placées dans un répertoire `assets/` ou `resources/`.
- Les fichiers de configuration doivent être au format YAML ou JSON, avec des valeurs par défaut claires.
- Les scripts shell (`.sh`, `.bat`) doivent être testés sur la plateforme cible avant déploiement.
- Les erreurs doivent être remontées avec des codes d'erreur significatifs et des messages en anglais.
- Les interfaces utilisateur doivent être responsives et accessibles (contrastes, tailles de police).
- Les API REST doivent suivre les conventions HTTP (codes de statut, méthodes appropriées).
- Les bases de données doivent être versionnées avec des migrations (Alembic, Django migrations).
- Les environnements virtuels doivent être utilisés pour isoler les dépendances.
- Les conteneurs Docker doivent être légers et suivre les meilleures pratiques (multi-stage builds).
- Les pipelines CI/CD doivent être automatisés et exécuter les tests à chaque commit.
- Les métriques et monitoring doivent être intégrés pour les applications de production.
- La documentation doit être à jour et inclure des exemples d'utilisation.
- Les revues de code doivent être effectuées avant la fusion des pull requests.
- Les sauvegardes de données critiques doivent être régulières et testées.
- Les licences des dépendances doivent être vérifiées pour la conformité.
- Les mises à jour de sécurité doivent être appliquées rapidement.
