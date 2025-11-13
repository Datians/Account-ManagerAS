from app import create_app
from dotenv import load_dotenv

load_dotenv()  # <- carga variables del .env al entorno
app = create_app()

if __name__ == "__main__":
    from os import environ
    port = int(environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
