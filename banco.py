import sqlite3
import pandas as pd
import hashlib
import random
from datetime import datetime

from config import DB_NAME, USUARIO_ADMIN, SENHA_ADMIN


def conectar():
    return sqlite3.connect(DB_NAME)

#inicializa o banco de dados...
def inicializar_banco():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE,
        cpf TEXT UNIQUE,
        senha_hash TEXT,
        criado_em TEXT
    )
    """)

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

#Login
def gerar_hash(valores):
    texto = "|".join(str(x) for x in valores)
    return hashlib.md5(texto.encode("utf-8")).hexdigest()


#criar a senha
def gerar_hash_senha(senha):
    return hashlib.sha256(str(senha).encode("utf-8")).hexdigest()


#cria usuario
def gerar_usuario():
    conn = conectar()
    cursor = conn.cursor()

    while True:
        usuario = str(random.randint(1000, 9999))

        cursor.execute(
            "SELECT 1 FROM usuarios WHERE usuario = ?",
            (usuario,)
        )

        if cursor.fetchone() is None:
            conn.close()
            return usuario


#criar usuário...
def criar_usuario(cpf, senha):
    cpf = str(cpf).replace(".", "").replace("-", "").strip()

    conn = conectar()
    cursor = conn.cursor()

    senha_hash = gerar_hash_senha(senha)
    usuario = gerar_usuario()

    try:
        cursor.execute("""
        INSERT INTO usuarios (usuario, cpf, senha_hash, criado_em)
        VALUES (?, ?, ?, ?)
        """, (
            usuario,
            cpf,
            senha_hash,
            datetime.now().isoformat()
        ))

        conn.commit()
        return usuario

    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()


#verificar login...
def verificar_login(usuario, senha):
    usuario = str(usuario).strip().replace(".", "").replace("-", "")

    if usuario == USUARIO_ADMIN and senha == SENHA_ADMIN:
        return True

    conn = conectar()
    cursor = conn.cursor()

    senha_hash = gerar_hash_senha(senha)

    cursor.execute("""
    SELECT * FROM usuarios
    WHERE usuario = ? AND senha_hash = ?
    """, (usuario, senha_hash))

    resultado = cursor.fetchone()

    conn.close()

    return resultado is not None


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


#carregar abastecimentos...
def carregar_abastecimentos():
    conn = conectar()

    df = pd.read_sql_query(
        "SELECT * FROM abastecimentos",
        conn
    )

    conn.close()

    return df


#limpar banco de dados...
def limpar_banco():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM abastecimentos")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='abastecimentos'")

    conn.commit()
    conn.close()

#mostrar usuarios cadastrados
def listar_usuarios():
    conn = conectar()

    df = pd.read_sql_query(
        "SELECT id, usuario, cpf, criado_em FROM usuarios ORDER BY criado_em DESC",
        conn
    )

    conn.close()
    return df


#excluir usuario
def excluir_usuario(usuario):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM usuarios WHERE usuario = ?",
        (str(usuario),)
    )

    conn.commit()
    conn.close()

#registrar log
def registrar_log(usuario, acao):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT,
        acao TEXT,
        criado_em TEXT
    )
    """)

    cursor.execute("""
    INSERT INTO logs (usuario, acao, criado_em)
    VALUES(?, ?, ?)    
    """, (
        str(usuario),
        str(acao),
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

#carregar logs
def carregar_logs():
    conn = conectar()


    df = pd.read_sql_query(
        "SELECT * FROM logs ORDER BY criado_em DESC",
        conn
    )

    conn.close()
    return df