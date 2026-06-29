#calculos e agrupamento

import pandas as pd
from utils import converter_numero_seguro, classificar_combustivel

def preparar_dados(df, col_km, col_litros, col_gasto, col_produto=None):
    df = df.copy()

    df[col_gasto] = df[col_gasto].apply(converter_numero_seguro)
    df[col_litros] = df[col_litros].apply(converter_numero_seguro)
    df[col_km] = df[col_km].apply(converter_numero_seguro)

    if "data" in df.columns:
        df["data"] = pd.to_datetime(
            df["data"],
            errors="coerce",
            format="mixed",
            dayfirst=True
        )
        df["mes"] = df["data"].dt.to_period("M").astype(str)

    if col_produto and col_produto in df.columns:
        df["tipo_combustivel"] = df[col_produto].apply(classificar_combustivel)

    return df


def calcular_metricas(df, col_km, col_litros, col_gasto):
    total_gasto = df[col_gasto].sum()
    total_abastecimentos = len(df)
    total_km = df[col_km].sum()
    total_litros = df[col_litros].sum()

    media_km_l = total_km / total_litros if total_litros > 0 else 0
    custo_km = total_gasto / total_km if total_km > 0 else 0

    return total_gasto, total_abastecimentos, media_km_l, custo_km


def analisar_veiculos(df, col_placa, col_km, col_litros, col_gasto):
    analise = (
        df.groupby(col_placa)
        .agg({
            col_km: "sum",
            col_litros: "sum",
            col_gasto: "sum"
        })
        .reset_index()
    )

    analise["km_l"] = analise[col_km] / analise[col_litros]
    analise["custo_km"] = analise[col_gasto] / analise[col_km]

    analise.replace([float("inf"), -float("inf")], 0, inplace=True)
    analise.fillna(0, inplace=True)

    analise = analise[
        (analise[col_km] > 0) &
        (analise[col_litros] > 0)
    ].copy()

    analise["km_l"] = analise["km_l"].round(2)
    analise["custo_km"] = analise["custo_km"].round(2)

    def definir_status(row):
        if row["km_l"] < 2 or row["custo_km"] > 5:
            return "🔴 Crítico"
        elif row["km_l"] < 3 or row["custo_km"] > 4:
            return "🟡 Atenção"
        else:
            return "🟢 Normal"

    analise["status"] = analise.apply(definir_status, axis=1)

    return analise


def ranking_gastos(df, col_placa, col_gasto):
    return (
        df.groupby(col_placa)[col_gasto]
        .sum()
        .sort_values(ascending=True)
        .reset_index()
    )


def volume_mensal_combustivel(df, col_litros):
    if (
        "mes" not in df.columns
        or "tipo_combustivel" not in df.columns
    ):
        return None, None

    volume = (
        df.groupby(["mes", "tipo_combustivel"])[col_litros]
        .sum()
        .reset_index()
    )

    tabela = (
        volume.pivot(
            index="mes",
            columns="tipo_combustivel",
            values=col_litros
        )
        .fillna(0)
        .round(2)
    )

    return volume, tabela