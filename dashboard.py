import pandas as pd
import streamlit as st
import plotly.express as px
import re

st.set_page_config(layout="wide")


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


def converter_numero_ou_nan(valor):
    if pd.isna(valor):
        return pd.NA

    if isinstance(valor, (int, float)):
        return float(valor)

    v = str(valor).strip()

    if not re.search(r"\d", v):
        return pd.NA

    v = re.sub(r"[^\d,.\-]", "", v)

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
        return pd.NA


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

        df_raw = pd.read_excel(excel, sheet_name=aba_escolhida, header=None)

        linha_cabecalho = None

        for i in range(len(df_raw)):
            linha = (
                df_raw.iloc[i]
                .astype(str)
                .str.strip()
                .str.lower()
            )

            texto = " ".join(map(str, linha.fillna("").tolist()))

            if (
                "placa" in texto
                or "km" in texto
                or "quilometragem" in texto
                or "hodometro" in texto
                or "hodômetro" in texto
                or "litros" in texto
                or "quantidade" in texto
                or "gasto" in texto
                or "valor total" in texto
            ):
                linha_cabecalho = i
                break

        if linha_cabecalho is None:
            if modo_generico:
                linha_cabecalho = 0
            else:
                continue

        cabecalho = df_raw.iloc[linha_cabecalho]

        df_temp = df_raw.iloc[linha_cabecalho + 1:].copy()
        df_temp.columns = cabecalho
        df_temp = df_temp.reset_index(drop=True)

        df_temp.columns = df_temp.columns.astype(str)

        df_temp = df_temp.loc[
            :,
            ~df_temp.columns.str.contains("unnamed", case=False, na=False)
        ]

        df_temp.columns = (
            df_temp.columns
            .astype(str)
            .str.strip()
            .str.lower()
        )

        for col in df_temp.columns:
            if df_temp[col].dtype == "object":
                df_temp[col] = df_temp[col].astype(str).str.strip()
                df_temp[col] = df_temp[col].replace("nan", "")

        df_temp["origem"] = arquivo.name
        dfs.append(df_temp)

if not dfs:
    st.error("Nenhum arquivo válido foi enviado.")
    st.stop()

df = pd.concat(dfs, ignore_index=True)
df.columns = df.columns.str.strip().str.lower()


col_produto = None
col_km = None
col_litros = None
col_gasto = None
col_placa = None
col_consumo = None

for col in df.columns:
    nome = str(col).strip().lower()

    if (
        "produto" in nome
        or "combustivel" in nome
        or "combustível" in nome
    ):
        col_produto = col

    elif (
        "km rodado" in nome
        or "quilometragem" in nome
        or "hodometro" in nome
        or "hodômetro" in nome
        or "odometro" in nome
        or "odômetro" in nome
        or "distancia" in nome
        or nome == "km"
        or "km total" in nome
    ):
        col_km = col

    elif (
        "total de litros" in nome
        or "litros" in nome
        or "quantidade" in nome
    ):
        col_litros = col

    elif "placa" in nome:
        col_placa = col

    elif (
        "gasto total" in nome
        or "valor total" in nome
        or "gasto" in nome
    ):
        col_gasto = col

    elif (
        "média" in nome
        or "media" in nome
        or "consumo" in nome
    ):
        col_consumo = col


if modo_generico:
    st.title("Explorador de Planilhas")

    st.write("### Colunas Detectadas:")
    st.write(df.columns.tolist())

    st.subheader("Filtros")

    df_filtro = df.copy()

    for col in df.columns:
        if df[col].dtype == "object":
            valores = df[col].dropna().unique()
            if len(valores) <= 50:
                selecionados = st.multiselect(f"{col}", valores)
                if selecionados:
                    df_filtro = df_filtro[df_filtro[col].isin(selecionados)]

    st.subheader("Visualização")

    colunas = st.multiselect(
        "Escolha Colunas",
        df_filtro.columns,
        default=df_filtro.columns[:5]
    )

    if colunas:
        st.dataframe(df_filtro[colunas], use_container_width=True)

    st.subheader("Gráfico")

    df_grafico = df_filtro.copy()

    for col in df_grafico.columns:
        convertido = df_grafico[col].apply(converter_numero_ou_nan)

        if convertido.notna().mean() >= 0.7:
            df_grafico[col] = pd.to_numeric(convertido, errors="coerce")

    colunas_numericas = df_grafico.select_dtypes(include="number").columns
    colunas_texto = df_grafico.select_dtypes(exclude="number").columns

    if len(colunas_numericas) > 0:
        st.subheader("Resumo Estatístico")
        st.dataframe(df_grafico[colunas_numericas].describe(), use_container_width=True)

    if len(colunas_numericas) >= 2:
        st.subheader("Correlação Entre Variáveis")
        corr = df_grafico[colunas_numericas].corr()
        st.dataframe(corr, use_container_width=True)

    if len(colunas_numericas) == 0:
        st.warning("Nenhuma coluna numérica detectada para gráfico.")
    else:
        tipo_grafico = st.selectbox(
            "Tipo de Gráfico",
            ["Dispersão", "Barras", "Linha"]
        )

        if tipo_grafico == "Dispersão" and len(colunas_numericas) >= 2:
            x = st.selectbox("Eixo X", colunas_numericas)
            y = st.selectbox("Eixo Y", colunas_numericas, index=1)

            fig = px.scatter(df_grafico, x=x, y=y)
            st.plotly_chart(fig, use_container_width=True)

        elif tipo_grafico == "Barras" and len(colunas_texto) > 0:
            x = st.selectbox("Categoria", colunas_texto)
            y = st.selectbox("Valor", colunas_numericas)

            agrupado = df_grafico.groupby(x)[y].sum().reset_index()

            fig = px.bar(agrupado, x=x, y=y)
            st.plotly_chart(fig, use_container_width=True)

        elif tipo_grafico == "Linha" and len(colunas_numericas) >= 2:
            x = st.selectbox("Eixo X", colunas_numericas)
            y = st.selectbox("Eixo Y", colunas_numericas, index=1)

            fig = px.line(df_grafico, x=x, y=y)
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Exportar")

    from io import BytesIO
    buffer = BytesIO()
    df_filtro.to_excel(buffer, index=False)
    buffer.seek(0)

    st.download_button(
        "Baixar Dados Filtrados",
        buffer,
        "dados_filtrados.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.stop()


if col_km is None:
    st.error("Coluna de KM não encontrada.")
    st.write("Colunas disponíveis:", df.columns.tolist())
    st.stop()

if col_litros is None:
    st.error("Coluna de Litros não encontrada.")
    st.write("Colunas disponíveis:", df.columns.tolist())
    st.stop()

if col_placa is None:
    st.error("Coluna de Placa não encontrada.")
    st.write("Colunas disponíveis:", df.columns.tolist())
    st.stop()

if col_gasto is None:
    st.error("Coluna de Gasto não encontrada.")
    st.write("Colunas disponíveis:", df.columns.tolist())
    st.stop()

if col_consumo is None:
    col_consumo = col_km


df[col_gasto] = df[col_gasto].apply(converter_numero_seguro)
df[col_litros] = df[col_litros].apply(converter_numero_seguro)
df[col_km] = df[col_km].apply(converter_numero_seguro)

if "data" in df.columns:
    df["data"] = pd.to_datetime(
        df["data"],
        errors="coerce",
        dayfirst=True
    )

    df = df[df["data"].notna()].copy()
    df["mes"] = df["data"].dt.to_period("M").astype(str)

if col_produto:
    df["tipo_combustivel"] = df[col_produto].apply(classificar_combustivel)


if "preço médio" not in df.columns:
    df["preço médio"] = df[col_gasto] / df[col_litros].replace(0, pd.NA)


st.title("Dashboard de Consumo da Frota")
st.caption("Análise de abastecimento, eficiência e custos por veículo")
st.divider()

st.header("Filtros")

col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    setor = st.selectbox("Setor", df["origem"].dropna().unique())

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

with col_f3:
    if "data" in df_filtrado.columns and not df_filtrado.empty:
        data_min = df_filtrado["data"].min().date()
        data_max = df_filtrado["data"].max().date()

        intervalo_datas = st.date_input(
            "Período",
            value=(data_min, data_max),
            key="filtro_periodo_principal"
        )
    else:
        intervalo_datas = None

if intervalo_datas and len(intervalo_datas) == 2:
    data_inicio, data_fim = intervalo_datas

    df_filtrado = df_filtrado[
        (df_filtrado["data"].dt.date >= data_inicio) &
        (df_filtrado["data"].dt.date <= data_fim)
    ].copy()

if df_filtrado.empty:
    st.warning("Nenhum registro encontrado para os filtros selecionados.")
    st.stop()

if "data" in df_filtrado.columns:
    df_filtrado["mes"] = df_filtrado["data"].dt.to_period("M").astype(str)

st.divider()


st.subheader("Resumo Geral")

total_gasto = df_filtrado[col_gasto].sum()
total_abastecimentos = len(df_filtrado)
total_km = df_filtrado[col_km].sum()
total_litros = df_filtrado[col_litros].sum()

media_km_l = total_km / total_litros if total_litros > 0 else 0
custo_km = total_gasto / total_km if total_km > 0 else 0

col1, col2 = st.columns(2)
col1.metric("Gasto Total", f"R$ {total_gasto:.2f}")
col2.metric("Abastecimentos", total_abastecimentos)

col3, col4 = st.columns(2)
col3.metric("Média KM/L", f"{media_km_l:.2f}")
col4.metric("Custo por KM", f"R$ {custo_km:.2f}")


st.subheader("Análise por Veículo")

analise_veiculos = (
    df_filtrado.groupby(col_placa)
    .agg({
        col_km: "sum",
        col_litros: "sum",
        col_gasto: "sum"
    })
    .reset_index()
)

analise_veiculos["km_l"] = analise_veiculos[col_km] / analise_veiculos[col_litros].replace(0, pd.NA)
analise_veiculos["custo_km"] = analise_veiculos[col_gasto] / analise_veiculos[col_km].replace(0, pd.NA)

analise_veiculos = analise_veiculos.replace([float("inf"), -float("inf")], 0)
analise_veiculos = analise_veiculos.fillna(0)

analise_veiculos = analise_veiculos[
    (analise_veiculos[col_km] > 0) &
    (analise_veiculos[col_litros] > 0)
].copy()

if analise_veiculos.empty:
    st.warning("Nenhum veículo encontrado para os filtros selecionados.")
    st.stop()

analise_veiculos["km_l"] = analise_veiculos["km_l"].round(2)
analise_veiculos["custo_km"] = analise_veiculos["custo_km"].round(2)


def definir_status(row):
    if row["km_l"] < 2 or row["custo_km"] > 5:
        return "🔴 Crítico"
    elif row["km_l"] < 3 or row["custo_km"] > 4:
        return "🟡 Atenção"
    else:
        return "🟢 Normal"


analise_veiculos["status"] = analise_veiculos.apply(definir_status, axis=1)

analise_exibicao = analise_veiculos.copy()

analise_exibicao.rename(columns={
    col_placa: "Veículo",
    col_km: "KM",
    col_litros: "Litros",
    col_gasto: "Gasto",
    "km_l": "Km/L",
    "custo_km": "R$/Km",
    "status": "Status"
}, inplace=True)

st.dataframe(analise_exibicao, use_container_width=True)


st.subheader("Status dos Veículos")
st.dataframe(analise_veiculos, use_container_width=True)

criticos = analise_veiculos[analise_veiculos["status"] == "🔴 Crítico"]

if not criticos.empty:
    st.error(f"{len(criticos)} veículo(s) em estado CRÍTICO!")


ranking = (
    df_filtrado.groupby(col_placa)[col_gasto]
    .sum()
    .sort_values(ascending=True)
    .reset_index()
)

ranking_formatado = ranking.copy()
ranking_formatado[col_gasto] = ranking_formatado[col_gasto].apply(lambda x: f"R$ {x:.2f}")

st.subheader("Ranking de Gastos Por Veículo")
st.dataframe(ranking_formatado, use_container_width=True)


piores = analise_veiculos.sort_values("custo_km", ascending=False).head(5)

melhor = analise_veiculos.sort_values("km_l", ascending=False).iloc[0]
pior = analise_veiculos.sort_values("km_l").iloc[0]

st.success(f"Melhor: {melhor[col_placa]} ({melhor['km_l']:.2f} KM/L)")
st.error(f"Pior: {pior[col_placa]} ({pior['km_l']:.2f} KM/L)")

st.subheader("Top 5 Veículos Mais Caros")
st.dataframe(piores, use_container_width=True)


st.subheader("Volume de Combustível por Mês")

if (
    col_produto is not None
    and "mes" in df_filtrado.columns
    and "tipo_combustivel" in df_filtrado.columns
):
    df_volume = df_filtrado.copy()

    volume_mensal = (
        df_volume.groupby(["mes", "tipo_combustivel"])[col_litros]
        .sum()
        .reset_index()
    )

    volume_mensal[col_litros] = volume_mensal[col_litros].round(2)

    tabela_volume = (
        volume_mensal.pivot(
            index="mes",
            columns="tipo_combustivel",
            values=col_litros
        )
        .fillna(0)
        .round(2)
    )

    st.dataframe(
        tabela_volume.style.format("{:,.2f}"),
        use_container_width=True
    )

    fig_comb = px.bar(
        volume_mensal,
        x="mes",
        y=col_litros,
        color="tipo_combustivel",
        barmode="group",
        text=col_litros,
        title="Volume Mensal por Combustível"
    )

    fig_comb.update_traces(
        texttemplate="%{text:.2f} L",
        textposition="outside"
    )

    st.plotly_chart(fig_comb, use_container_width=True)

else:
    st.warning("Não foi possível gerar o volume mensal por combustível.")


st.subheader("Análises Visuais")

fig = px.bar(
    ranking,
    x=col_placa,
    y=col_gasto,
    title="Gasto por Veículo"
)

st.plotly_chart(fig, use_container_width=True)

fig2 = px.scatter(
    analise_veiculos,
    x="km_l",
    y="custo_km",
    color="status",
    size=col_gasto,
    hover_data=[col_placa],
    title="Eficiência vs Custo"
)

fig2.update_layout(
    xaxis_title="KM/L",
    yaxis_title="Custo por KM"
)

st.plotly_chart(fig2, use_container_width=True)


st.subheader("Dados Detalhados")

df_exibicao = df_filtrado.copy()

colunas_monetarias = [
    col_gasto,
    "gasto total",
    "valor diesel",
    "valor arla",
    "preço médio",
    "custo/km"
]

for col in df_exibicao.columns:
    if col in colunas_monetarias:
        df_exibicao[col] = df_exibicao[col].apply(
            lambda x: f"R$ {converter_numero_seguro(x):.2f}"
        )

    elif pd.api.types.is_numeric_dtype(df_exibicao[col]):
        df_exibicao[col] = df_exibicao[col].apply(lambda x: f"{float(x):.2f}")

st.dataframe(df_exibicao, use_container_width=True)


from io import BytesIO

st.subheader("Exportar Dados")

buffer = BytesIO()
df_filtrado.to_excel(buffer, index=False)
buffer.seek(0)

st.download_button(
    "Baixar dados",
    buffer,
    "dados_filtrados.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)