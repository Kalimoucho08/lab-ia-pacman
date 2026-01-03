import gzip
import sys
path = 'logs/test_log_compression_20260103_001546.log.gz'
try:
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        content = f.read()
        print("Contenu du fichier compressé (premières 500 caractères):")
        print(content[:500])
        print("\nTaille du fichier compressé:", len(content), "caractères")
except Exception as e:
    print("Erreur:", e)
    sys.exit(1)