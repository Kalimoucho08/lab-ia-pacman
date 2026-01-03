import gzip
import sys
path = 'logs/test_log_compression_20260103_001546.log.gz'
try:
    with gzip.GzipFile(path, 'rb') as f:
        content = f.read()
        print("Contenu brut (premiers 500 octets):", content[:500])
        print("\nDécodé en UTF-8:")
        print(content.decode('utf-8', errors='replace')[:500])
except Exception as e:
    print("Erreur:", e)
    import traceback
    traceback.print_exc()