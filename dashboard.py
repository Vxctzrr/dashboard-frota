#Interface
import pandas as pd
import streamlit as st

from autenticacao import(
    tela_login,
    botao_sair,
    usuario_admin
)
from leitura import processar_aba
from detector import detectar_colunas
from analises import (
    preparar_dados,
    calcular_metricas,
    analisar_veiculos,
    ranking_gastos,
    volume_mensal_combustivel
)
from graficos import(
    grafico_gasto_veiculo,
    grafico_eficiencia,
    grafico_volume_combustivel
)
from banco import(
    inicializar_banco,
    salvar_abastecimentos_df,
    carregar_abastecimentos,
    limpar_banco,
    listar_usuarios,
    excluir_usuario,
    carregar_logs,
    registrar_log
)
from config import NOME_SISTEMA

st.set_page_config(layout="wide")
#st.logo("logo.png", size="large") #(quando tiver logo)

inicializar_banco()
tela_login()
botao_sair()

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

    if arquivos:
        assinatura_upload = "|".join(
            sorted([f"{arquivo.name}-{arquivo.size}" for arquivo in arquivos])
        )

        if st.session_state.get("ultimo_upload_logado") != assinatura_upload:
            registrar_log(
                st.session_state.get("usuario"),
                f"Carregou {len(arquivos)} arquivos(s): {', '.join([a.name for a in arquivos])}"
            )

            st.session_state["ultimo_upload_logado"] = assinatura_upload

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

st.title(NOME_SISTEMA)
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

#Área admin
if usuario_admin():
    st.subheader("Painel Administrativo")

    aba_usuarios, aba_logs, aba_config = st.tabos(
        ["Usuários", "Logs", "Configurações"]
    )

    with aba_usuarios:
        st.write ("### Usuários cadastrados")

        df_usuarios = listar_usuarios()
        st.dataframe(df_usuarios, use_container_width=True)

        usuario_excluir = st.text_input(
            "Digite o código do usuário para excluir",
            key="usuario_excluir"
        )

        if st.button("Excluir usuário", key="btn_excluir_usuario"):
            if usuario_excluir == "0":
                st.error("Você não pode excluir o administrador.")
        elif usuario_excluir.strip() == "":
            st.warning("Digite um usuário")
        else:
            excluir_usuario(usuario_excluir)
            registrar_log(
                st.session_state.get("usuario"),
                f"Excluiu usuário {usuario_excluir}"
            )
            st.success("Usuário excluido com sucesso.")

            registrar_log(
                st.session_state.get("usuario"),
                f"Excluiu usuário {usuário_excluir}"
            )
            st.rerun()

    with aba_logs:
        st.write("### Logs do sistema")

        df_logs = carregar_logs()
        st.dataframe(df_logs, use_container_width=True)

    with aba_config:
        st.write("### Configurações")
        st.info("Área reservada para futuras configurações do sistema.")

#salvar dados no banco de dados
if usuario_admin():
    
    st.subheader("Banco de dados")

    if st.button("Salvar dados no banco"):
        salvos = salvar_abastecimentos_df(
            df_filtrado,
            col_placa,
            col_km,
            col_litros,
            col_gasto,
            col_produto
        )

        registrar_log(
            st.session_state.get("usuario"),
            f"Salvou {salvos} regostros no banco"
        )


    #apagar banco de dados
    if st.checkbox(
        "Ver dados salvos no banco",
        key="ver_banco"
    ):
        df_banco = carregar_abastecimentos()
        st.dataframe(df_banco, use_container_width=True)

    if st.checkbox (
        "Confirmo que desejo apagar todo o banco salvo",
        key="confirmar_limpar_banco"
    ):
        if st.button(
            "Limpar Banco de Dados",
        key="btn_limpar_banco"
        ):
            limpar_banco()
            
            registrar_log(
                st.session_state.get("usuario"),
                "Limpou banco de dados"
            )
            
            st.success("Banco limpo com sucesso")

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