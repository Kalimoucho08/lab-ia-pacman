import gzip
path = 'logs/test_log_compression_20260103_001820.log.gz'
try:
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        content = f.read()
        print("Succès ! Contenu (premiers 500 caractères):")
        print(content[:500])
except Exception as e:
    print("Erreur:", e)
    import traceback
    traceback.print_exc()