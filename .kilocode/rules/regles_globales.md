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
