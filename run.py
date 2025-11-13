from app import create_app
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Crear app Flask
app = create_app()

if __name__ == "__main__":
    # Tomar el puerto que Railway asigna dinámicamente
    port = int(os.getenv("PORT", 5000))
    print(f"🚀 Iniciando Flask en el puerto {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)

