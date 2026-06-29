#funções pequenas de limpeza
import pandas as pd
import re

def converter_numero_seguro(valor):
    if pd.isna(valor):
        return 0.0

    if isinstance(valor, (int, float)):
        return float(valor)

    v = str(valor).strip()

    if v == "":
        return 0.0

    v = re.sub(r"[^\d,.\-]", "", v)

    if v == "":
        return 0.0

    if "," in v and "." in v:
        if v.rfind(",") > v.rfind("."):
            v = v.replace(".", "").replace(",", ".")
        else:
            v = v.replace(",", "")

    elif "," in v:
        v = v.replace(",", ".")

    try:
        return float(v)
    except:
        return 0.0


def limpar_valor_monetario(valor):
    return converter_numero_seguro(valor)


def classificar_combustivel(x):
    x = str(x).upper()

    if "DIESEL" in x:
        return "Diesel"
    elif "ETANOL" in x:
        return "Etanol"
    elif "GASOLINA" in x:
        return "Gasolina"
    else:
        return "Outros"