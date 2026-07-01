"""TriageBot application package."""

# Carga el `.env` al importar el paquete, antes que cualquier submódulo
# (`db.py` crea el engine y `classifier.py` lee la API key al importarse).
# `override=False` (por defecto) no pisa variables ya definidas en el entorno,
# así no interfiere con los tests (`monkeypatch.setenv`) ni con la CI.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv está en requirements; guard defensivo.
    pass
