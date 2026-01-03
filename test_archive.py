import sys
sys.path.insert(0, '.')
from log_archiver import compress_text_log, archive_simulation_logs
import os

# Test compression texte
test_log = 'logs/test_archive.log'
with open(test_log, 'w') as f:
    f.write('Test log line\n' * 10)
print(f"Créé {test_log}")
compressed = compress_text_log(test_log, keep_original=False)
print(f"Compressé en {compressed}")

# Test archivage simulation
archive = archive_simulation_logs(simulation_id='DQN_0', log_dir='logs')
if archive:
    print(f"Archive créée: {archive}")
    # Vérifier que l'archive existe
    if os.path.exists(archive):
        print("Archive valide")
    else:
        print("Archive manquante")
else:
    print("Échec archivage")

print("Test terminé.")