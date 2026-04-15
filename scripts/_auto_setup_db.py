import pymysql, sys

configs = [
    {"password": ""},
    {"password": "root"},
    {"password": "1234"},
]

host, port, user, db_name = "localhost", 3306, "root", "gaming_python"

conn = None
working_password = None

for cfg in configs:
    try:
        conn = pymysql.connect(host=host, port=port, user=user, password=cfg["password"])
        working_password = cfg["password"]
        print(f"[OK] Connexion reussie avec password='{cfg['password']}'")
        break
    except pymysql.OperationalError:
        pass

if conn is None:
    print("[ERREUR] Impossible de se connecter avec les mots de passe courants.")
    print("Lancez manuellement : venv\\Scripts\\python scripts\\setup_mysql.py")
    sys.exit(1)

cur = conn.cursor()
cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
conn.commit()
conn.close()
print(f"[OK] Base '{db_name}' creee.")

from pathlib import Path
env_path = Path(".env")
content = env_path.read_text(encoding="utf-8")
new_url = f"DATABASE_URL=mysql+pymysql://{user}:{working_password}@{host}:{port}/{db_name}"
lines = [new_url if l.startswith("DATABASE_URL=") else l for l in content.splitlines()]
env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"[OK] .env mis a jour : {new_url}")
