try:
    import tensorflow as tf
    print('TensorFlow version:', tf.__version__)
except ImportError:
    print('TensorFlow non installé')