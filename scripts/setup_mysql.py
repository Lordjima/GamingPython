"""
Script de configuration MySQL — Gaming Python
Lance avec : venv\Scripts\python scripts\setup_mysql.py
"""
import sys

try:
    import pymysql
except ImportError:
    print("[ERREUR] PyMySQL non installé. Lance : pip install PyMySQL")
    sys.exit(1)


def main():
    print()
    print("=" * 55)
    print("  Gaming Python — Configuration MySQL (WampServer)")
    print("=" * 55)
    print()
    print("  Informations de connexion WampServer :")
    print()

    host     = input("  Host     [localhost] : ").strip() or "localhost"
    port_str = input("  Port     [3306]      : ").strip() or "3306"
    port     = int(port_str)
    user     = input("  User     [root]      : ").strip() or "root"
    password = input("  Password []          : ").strip()
    db_name  = input("  Database [gaming_python] : ").strip() or "gaming_python"

    print()
    print(f"  Connexion à {user}@{host}:{port}...")

    try:
        conn = pymysql.connect(
            host=host, port=port, user=user, password=password
        )
        cur = conn.cursor()
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        conn.commit()
        conn.close()
        print(f"  [OK] Base '{db_name}' créée (ou déjà existante).")
    except pymysql.OperationalError as e:
        print(f"  [ERREUR] Impossible de se connecter : {e}")
        print("  Vérifiez que WampServer est démarré (icône verte).")
        sys.exit(1)

    # Met à jour le .env automatiquement
    from pathlib import Path
    env_path = Path(__file__).parent.parent / ".env"

    if env_path.exists():
        content = env_path.read_text(encoding="utf-8")
        new_url = f"DATABASE_URL=mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"

        lines = content.splitlines()
        new_lines = []
        replaced = False
        for line in lines:
            if line.startswith("DATABASE_URL="):
                new_lines.append(new_url)
                replaced = True
            else:
                new_lines.append(line)

        if not replaced:
            new_lines.append(new_url)

        env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        print(f"  [OK] .env mis à jour avec : {new_url}")

    print()
    print("  Maintenant lancez :")
    print("  > uvicorn server.main:app --reload")
    print()


if __name__ == "__main__":
    main()
