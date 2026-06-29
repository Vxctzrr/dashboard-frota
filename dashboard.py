#Interface

import pandas as pd
import streamlit as st

from leitura import processar_aba
from detector import detectar_colunas
from analises import (
    preparar_dados,
    calcular_metricas,
    analisar_veiculos,
    ranking_gastos,
    volume_mensal_combustivel
)
from graficos import (
    grafico_gasto_veiculo,
    grafico_eficiencia,
    grafico_volume_combustivel
)
from banco import inicializar_banco, salvar_abastecimentos_df, carregar_abastecimentos

st.set_page_config(layout="wide")

inicializar_banco()

st.markdown("""
    <style>
    #MainMenu {visibility:hidden;}
    footer {visibility:hidden;}
    header {visibility:hidden;}
    </style>
""", unsafe_allow_html=True)

arquivos = st.file_uploader(
    "Envie Planilhas",
    type=["xlsx"],
    accept_multiple_files=True
)

modo_generico = st.toggle("Modo genérico (qualquer planilha)")

dfs = []

if arquivos:
    for arquivo in arquivos:
        excel = pd.ExcelFile(arquivo)
        abas = excel.sheet_names

        aba_escolhida = st.selectbox(
            f"Selecione a Aba - {arquivo.name}",
            abas,
            key=f"aba_{arquivo.name}"
        )

        df_temp = processar_aba(
            excel,
            aba_escolhida,
            arquivo.name,
            modo_generico
        )

        if df_temp is not None:
            dfs.append(df_temp)

if not dfs:
    st.error("Nenhum arquivo válido foi enviado.")
    st.stop()

df = pd.concat(dfs, ignore_index=True)
df.columns = df.columns.str.strip().str.lower()

cols = detectar_colunas(df)

col_produto = cols["produto"]
col_km = cols["km"]
col_litros = cols["litros"]
col_gasto = cols["gasto"]
col_placa = cols["placa"]
col_consumo = cols["consumo"]

if col_km is None or col_litros is None or col_gasto is None or col_placa is None:
    st.error("Não foi possível detectar todas as colunas obrigatórias.")
    st.write(df.columns.tolist())
    st.stop()

df = preparar_dados(
    df,
    col_km,
    col_litros,
    col_gasto,
    col_produto
)

st.title("Dashboard de Consumo da Frota")
st.caption("Análise de abastecimento, eficiência e custos por veículo")
st.divider()

st.header("Filtros")

col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    setor = st.selectbox("Setor", df["origem"].unique())

df_filtrado = df[df["origem"].astype(str).str.strip() == str(setor).strip()].copy()

with col_f2:
    veiculos = (
        df_filtrado[col_placa]
        .dropna()
        .astype(str)
        .unique()
    )

    opcoes = ["Todos"] + sorted(veiculos)
    veiculo_selecionado = st.selectbox("Veículo", opcoes)

if veiculo_selecionado != "Todos":
    df_filtrado = df_filtrado[
        df_filtrado[col_placa].astype(str) == str(veiculo_selecionado)
    ].copy()

intervalo_datas = None

with col_f3:
    if "data" in df_filtrado.columns and df_filtrado["data"].notna().any():
        data_min = df_filtrado["data"].min().date()
        data_max = df_filtrado["data"].max().date()

        intervalo_datas = st.date_input(
            "Período",
            value=(data_min, data_max),
            key="filtro_data"
        )
    else:
        st.info("Esta aba não possui coluna de data.")

if (
    intervalo_datas is not None
    and "data" in df_filtrado.columns
    and len(intervalo_datas) == 2
):
    data_inicio, data_fim = intervalo_datas

    data_inicio = pd.to_datetime(data_inicio)
    data_fim = pd.to_datetime(data_fim) + pd.Timedelta(days=1)

    df_filtrado = df_filtrado[
        (df_filtrado["data"] >= data_inicio) &
        (df_filtrado["data"] < data_fim)
    ].copy()

if df_filtrado.empty:
    st.warning("Nenhum registro encontrado para os filtros selecionados.")
    st.stop()

st.subheader("Banco de Dados")

if st.button("Salvar dados no banco"):
    salvos = salvar_abastecimentos_df(
        df_filtrado,
        col_placa,
        col_km,
        col_litros,
        col_gasto,
        col_produto
    )

    st.success(f"{salvos}novo(s) registro(s) salvo(s) no banco.")

if st.checkbox("Ver dados salvos no banco"):
    df_banco = carregar_abastecimentos()
    st.dataframe(df_banco, use_container_width=True)

mostrar_metricas(df_filtrado)

st.divider()

total_gasto, total_abastecimentos, media_km_l, custo_km = calcular_metricas(
    df_filtrado,
    col_km,
    col_litros,
    col_gasto
)

st.subheader("Resumo Geral")

c1, c2 = st.columns(2)
c1.metric("Gasto Total", f"R$ {total_gasto:.2f}")
c2.metric("Abastecimentos", total_abastecimentos)

c3, c4 = st.columns(2)
c3.metric("Média KM/L", f"{media_km_l:.2f}")
c4.metric("Custo por KM", f"R$ {custo_km:.2f}")

analise_veiculos = analisar_veiculos(
    df_filtrado,
    col_placa,
    col_km,
    col_litros,
    col_gasto
)

if analise_veiculos.empty:
    st.warning("Nenhum veículo encontrado para os filtros selecionados.")
    st.stop()

st.subheader("Análise por Veículo")
st.dataframe(analise_veiculos, use_container_width=True)

ranking = ranking_gastos(df_filtrado, col_placa, col_gasto)

st.subheader("Ranking de Gastos Por Veículo")
st.dataframe(ranking, use_container_width=True)

volume_mensal, tabela_volume = volume_mensal_combustivel(
    df_filtrado,
    col_litros
)

if volume_mensal is not None:
    st.subheader("Volume de Combustível por Mês")
    st.dataframe(tabela_volume.style.format("{:,.2f}"), use_container_width=True)

    fig_comb = grafico_volume_combustivel(volume_mensal, col_litros)
    st.plotly_chart(fig_comb, use_container_width=True)

st.subheader("Análises Visuais")

fig1 = grafico_gasto_veiculo(ranking, col_placa, col_gasto)
st.plotly_chart(fig1, use_container_width=True)

fig2 = grafico_eficiencia(analise_veiculos, col_gasto, col_placa)
st.plotly_chart(fig2, use_container_width=True)

st.subheader("Dados Detalhados")
st.dataframe(df_filtrado, use_container_width=True)