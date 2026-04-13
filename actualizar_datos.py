"""
Actualiza el CSV de fondos OVDAS desde la base de datos local
y hace git push al repositorio de GitHub para actualizar el dashboard público.

Ejecutar después de cada scan:
    python actualizar_datos.py
    python actualizar_datos.py --solo-csv   # solo exporta, sin git push
"""
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

ROOT_SCANNER = Path(__file__).parent.parent / "scanner_fondos"
sys.path.insert(0, str(ROOT_SCANNER))

CSV_PATH = Path(__file__).parent / "data" / "fondos_ovdas.csv"


def exportar_csv():
    from database.models import get_fondos, init_db
    import pandas as pd

    init_db()
    fondos = get_fondos()
    df = pd.DataFrame(fondos)
    df["score_ovdas"] = pd.to_numeric(df.get("score_ovdas", 0), errors="coerce").fillna(0)
    ovdas = df[df["score_ovdas"] > 0].sort_values("score_ovdas", ascending=False).copy()

    for col in ["requisitos", "entidades_target", "raw_data"]:
        if col in ovdas.columns:
            ovdas[col] = ovdas[col].apply(
                lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (list, dict)) else str(x) if x else ""
            )

    ovdas = ovdas.drop(columns=["raw_data"], errors="ignore")
    CSV_PATH.parent.mkdir(exist_ok=True)
    ovdas.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
    print(f"OK: {len(ovdas)} fondos OVDAS exportados → {CSV_PATH}")
    return len(ovdas)


def git_push():
    repo_dir = Path(__file__).parent
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    cmds = [
        ["git", "add", "data/fondos_ovdas.csv"],
        ["git", "commit", "-m", f"datos: actualizar fondos OVDAS ({ts})"],
        ["git", "push"],
    ]
    for cmd in cmds:
        result = subprocess.run(cmd, cwd=repo_dir, capture_output=True, text=True)
        if result.returncode != 0:
            # "nothing to commit" no es un error real
            if "nothing to commit" in result.stdout + result.stderr:
                print("Sin cambios en los datos — no se hizo commit.")
                return
            print(f"Error en {' '.join(cmd)}: {result.stderr}")
            return
        print(f"✓ {' '.join(cmd)}")
    print("Dashboard público actualizado.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--solo-csv", action="store_true", help="Solo exporta CSV, sin git push")
    args = parser.parse_args()

    n = exportar_csv()
    if not args.solo_csv and n > 0:
        git_push()
