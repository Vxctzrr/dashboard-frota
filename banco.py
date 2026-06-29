import sqlite3
import pandas as pd
import hashlib
from datetime import datetime

DB_NAME = "frota.db"


def conectar():
    return sqlite3.connect(DB_NAME)


def inicializar_banco():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS abastecimentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        origem TEXT,
        placa TEXT,
        data TEXT,
        km REAL,
        litros REAL,
        gasto REAL,
        combustivel TEXT,
        row_hash TEXT UNIQUE,
        criado_em TEXT
    )
    """)

    conn.commit()
    conn.close()


def gerar_hash(valores):
    texto = "|".join(str(x) for x in valores)
    return hashlib.md5(texto.encode("utf-8")).hexdigest()


def salvar_abastecimentos_df(
    df,
    col_placa,
    col_km,
    col_litros,
    col_gasto,
    col_produto=None
):
    conn = conectar()
    cursor = conn.cursor()

    salvos = 0

    for _, row in df.iterrows():
        origem = row.get("origem", "")
        placa = row.get(col_placa, "")
        data = row.get("data", "")
        km = row.get(col_km, 0)
        litros = row.get(col_litros, 0)
        gasto = row.get(col_gasto, 0)

        combustivel = ""
        if col_produto and col_produto in df.columns:
            combustivel = row.get(col_produto, "")

        row_hash = gerar_hash([
            origem,
            placa,
            data,
            km,
            litros,
            gasto,
            combustivel
        ])

        try:
            cursor.execute("""
            INSERT INTO abastecimentos (
                origem,
                placa,
                data,
                km,
                litros,
                gasto,
                combustivel,
                row_hash,
                criado_em
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(origem),
                str(placa),
                str(data),
                float(km) if pd.notna(km) else 0,
                float(litros) if pd.notna(litros) else 0,
                float(gasto) if pd.notna(gasto) else 0,
                str(combustivel),
                row_hash,
                datetime.now().isoformat()
            ))

            salvos += 1

        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()

    return salvos


def carregar_abastecimentos():
    conn = conectar()

    df = pd.read_sql_query(
        "SELECT * FROM abastecimentos",
        conn
    )

    conn.close()

    return df

def limpar_banco():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM abastecimentos")
    cursor.execute("DELETe FROM sqlite_sequence WHERE name='abastecimentos'")

    conn.commit()
    conn.close()

    