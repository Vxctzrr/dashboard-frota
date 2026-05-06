import pandas as pd
import streamlit as st
import plotly.express as px
import os
import re

#Garantir que os dados estão realmente numéricos
def converter_numero_seguro(valor):
    import pandas as pd
    import re

    # nulos
    if pd.isna(valor):
        return 0.0

    # já numérico
    if isinstance(valor, (int, float)):
        return float(valor)

    v = str(valor).strip()

    if v == "":
        return 0.0

    # remove moeda e lixo
    v = re.sub(r"[^\d,.\-]", "", v)

    if v == "":
        return 0.0

    # CASO 1: tem vírgula e ponto → detectar padrão
    if "," in v and "." in v:
        if v.rfind(",") > v.rfind("."):
            # BR → 1.234,56
            v = v.replace(".", "").replace(",", ".")
        else:
            # EUA → 1,234.56
            v = v.replace(",", "")

    # CASO 2: só vírgula → decimal BR
    elif "," in v:
        v = v.replace(",", ".")

    # CASO 3: só ponto → já ok (EUA)
    # não faz nada

    try:
        return float(v)
    except:
        return 0.0
#st.cache_data.clear()

st.set_page_config(layout="wide")

#esconder UI do Streamlit
st.markdown("""
    <style>
    #MainMenu {Visibility:hidden;}
    footer {visibility: hidden;}
    header {visibiity: hidden;}
    </style> 
""", unsafe_allow_html=True)

#carregar dados
#pasta = "saida"
arquivos = st.file_uploader(
    "Envie Planilhas",
    type=["xlsx"],
    accept_multiple_files= True
)

#botão modo genérico
modo_generico = st.toggle("Modo genérico(qualquer planilha)")

dfs = []

#Dica Extra: Garantir que a pasta existe antes de tentar ler
#if not os.path.exists(pasta):
   # st.error(f"A pasta '{pasta}' não foi encontrada.")
   # st.stop()


if arquivos:
    abas_por_arquivo = {}
    for arquivo in arquivos:
        excel = pd.ExcelFile(arquivo)

        abas = excel.sheet_names

        aba_escolhida = st.selectbox(
            f"Selecione a Aba - {arquivo.name}",
            abas
        )

        df_raw = pd.read_excel(excel, sheet_name=aba_escolhida, header=None)

        #encontrar linha onde "tem placa"
        linha_inicio = None
        for i in range(len(df_raw)):
            linha = df_raw.iloc[i].astype(str).str.lower()
            if linha.str.contains("placa").any():
                linha_inicio = i
                break

        if linha_inicio is None:
            if modo_generico:
                df_temp = df_raw.copy()
                df_temp.columns = df_temp.iloc[0]
                df_temp = df_temp[1:].reset_index(drop=True)
            else:
                continue #vai pular o arquivo bugado

        df_temp = df_raw.iloc[linha_inicio:].copy()
        
        df_temp.columns = df_temp.iloc[0]
        df_temp = df_temp[1:]
        df_temp = df_temp.reset_index(drop=True)

        df_temp.columns = df_temp.columns.astype(str).str.strip().str.lower()

        df_temp = df_temp.loc[:, ~df_temp.columns.str.contains('unnamed', case=False)]

        for col in df_temp.columns:
            if df_temp[col].dtype == 'object':
                df_temp[col] = df_temp[col].astype(str).str.strip()
                df_temp[col] = df_temp[col].replace('nan', '')

        df_temp["origem"] = arquivo.name
        dfs.append(df_temp)

if not dfs:
    st.error("Nenhum arquivo válido foi enviado.")
    st.stop()

#juntar tudo
df = pd.concat(dfs, ignore_index=True)
df.columns = df.columns.str.strip().str.lower()

#Detecção automatica
col_km = None
col_litros = None
col_gasto = None
col_placa = None
col_consumo = None
#col_setor = None

#for col in df.columns:
    #if "numero frota"

for col in df.columns:
    if any(x in col for x in ["km", "rodado", "kilometragem", "hodometro"]):
        col_km = col
    elif any(x in col for x in ["litro", "litros", "quantidade", "total litros"]):
        col_litros = col
    elif "placa" in col:
        col_placa = col
    elif any(x in col for x in ["gasto", "gasto total", "valor total", "combustivel"]):
        col_gasto = col
    elif any(x in col for x in ["consumo", "média", "consumo médio"]):
        col_consumo = col

#validação
if col_km is None:
    st.error("Coluna de KM não encontrada")
    st.stop()

if col_litros is None:
    st.error("Coluna de Litros não encontrada")
    st.write("Coluas disponíveis", df.columns.tolist())
    st.stop()

if col_placa is None:
    st.error("Coluna de Placa não encontrada")
    st.stop()

if col_gasto is None:
    st.error("Coluna de Gasto não encontrada")
    st.stop()

if col_consumo is None:
    st.error("Coluna de Consumo não encontrada")
    st.stop()


#Modo genérico
if modo_generico: 
    st.title("Explorador de Planilhas")

    st.write("### Colunas Detectadas:")
    st.write(df.columns.tolist())

    #Filtros dinâmicos
    st.subheader("Filtros")

    df_filtro = df.copy()

    for col in df.columns:
        if df[col].dtype == "object":
            valores = df[col].dropna().unique()
            if len(valores) <= 50:
                selecionados = st.multiselect(f"{col}", valores)
                if selecionados:
                    df_filtro = df_filtro [df_filtro[col].isin(selecionados)]

    #Escolha de colunas
    st.subheader("Visualização")

    colunas = st.multiselect(
        "Escolha Colunas",
        df_filtro.columns,
        default=df_filtro.columns[:5]
    )
    if colunas:
        st.dataframe(df_filtro[colunas], use_container_width=True)

    #gráfico inteligente
    st.subheader("Gráfico")

    #Limpeza inteligente de números
    for col in df_filtro.columns:
        if df_filtro[col].dtype == "object":
            df_filtro[col] = (
                df_filtro[col]
                .astype(str)
                .str.replace("R$", "", regex=False)
                .str.replace(" ", "", regex=False)
                .str.replace(".", "", regex=False) #remove milhar
                .str.replace(",", "", regex=False) #remove decimal

            )
            df_filtro[col] = pd.to_numeric(df_filtro[col], errors="coerce")

    colunas_numericas = df_filtro.select_dtypes(include="number").columns
    colunas_texto = df_filtro.select_dtypes(exclude="number").columns

    #Resumo estatístico
    if len(colunas_numericas) > 0:
        st.subheader("Resumo Estatístico")
        st.dataframe(df_filtro.describe(), use_container_width=True)

    #Correlação
    if len(colunas_numericas) >= 2:
        st.subheader("Correlação Entre Variáveis")
        corr = df_filtro[colunas_numericas].corr()
        st.dataframe(corr, use_container_width=True)
    
    #arredondar números
    df_filtro[colunas_numericas] = df_filtro[colunas_numericas].round(2)

    #debug para ver colunas numericas:
    #st.write("colunas numéricas detectadas:", colunas_numericas)

    if len(colunas_numericas) == 0:
        st.warning("Nenhuma coluna numérica detectada para gráfico!")

    tipo_grafico = st.selectbox(
        "Tipo de Gráfico",
        ["Dispersão","Barras","Linha"]
    )
    if len(colunas_numericas) >= 1:
        if tipo_grafico == "Dispersão" and len(colunas_numericas) >= 2:
            x = st.selectbox("Eixo X", colunas_numericas)
            y = st.selectbox("Eixo Y", colunas_numericas, index=1)

            fig = px.scatter(df_filtro, x=x, y=y)
            st.plotly_chart(fig, use_container_width=True)

        elif tipo_grafico == "Barras":
            if len(colunas_texto) > 0:
                x = st.selectbox("Categoria", colunas_texto)
                y = st.selectbox("Valor", colunas_numericas)

                agrupado = df_filtro.groupby(x)[y].sum().reset_index()

                fig = px.bar(agrupado, x=x, y=y)
                st.plotly_chart(fig, use_container_width=True)

        elif tipo_grafico == "Linha":
            if len(colunas_numericas) >= 2:
                x = st.selectbox("Eixo X", colunas_numericas)
                y = st.selectbox("Eixo Y", colunas_numericas, index=1)

                fig = px.line(df_filtro, x=x, y=y)
                st.plotly_chart(fig, use_container_width=True)

    #Exportação
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

    #Parar o restante do dashboard
    st.stop()

#DEBUG
#st.write("Total de linhas:", df.shape)
#st.write(df.head())

#detectar coluna de gasto automaticamente (CORREÇÃO 2: hashtag adicionada)
coluna_gasto = None
for col in df.columns:
    if "gasto" in col or "valor total" in col:
        coluna_gasto = col
        break

if coluna_gasto is None:
    st.error("Nenhuma coluna de gasto encontrada")
    st.stop()

#LIMPEZA FORTE (À prova de balas)
def limpar_valor_monetario(valor):
    #Se for nulo ou vazio
    if pd.isna(valor) or str(valor).strip().lower() in ['', 'nan', 'none']:
        return 0.0
        
    #Se o Excel já entregou o dado redondinho como float ou int
    if isinstance(valor, (int, float)):
        return float(valor)
        
    #Se chegou aqui, é texto. Vamos limpar!
    v_str = str(valor).strip()
    
    #Arranca fora 'R$', letras e espaços. Deixa só números, ponto, vírgula e sinal negativo
    v_str = re.sub(r"[^\d,.-]", "", v_str)
    
    #Se sobrou só um traço ou formatação vazia
    if v_str in ["", "-", ".", ","]:
        return 0.0
        
    #Lida com o padrão brasileiro (1.500,50) vs americano (1500.50)
    if '.' in v_str and ',' in v_str:
        # Tem os dois: tira o ponto de milhar e troca vírgula decimal por ponto
        v_str = v_str.replace('.', '').replace(',', '.')
    elif ',' in v_str:
        #Só tem vírgula: converte ela pra ponto decimal
        v_str = v_str.replace(',', '.')
        
    try:
        return float(v_str)
    except:
        return 0.0 #Se der ruim em algum caso bizarro, vira 0

#Aplica a função linha a linha
df[coluna_gasto] = df[coluna_gasto].apply(limpar_valor_monetario)

#criar preço médio automaticamente se não existir
if "preço médio" not in df.columns and col_litros in df.columns:
    df["preço médio"] = df[coluna_gasto] / pd.to_numeric(df[col_litros], errors= "coerce")

#tratar data
if "data" in df.columns:
    df["data"] = pd.to_datetime(df["data"], errors="coerce")

#título
st.title("Dashboard de Consumo da Frota")
st.caption("Análise de abastecimento, eficiência e custos por veículo")
st.divider()

#UX
st.subheader("Resumo Geral")
st.divider()

st.header("Filtros")

#layout com 3 filtros lado a lado
col_f1, col_f2, col_f3 = st.columns(3)

#garatir que a coluna data está correta
if "data" in df.columns:
    df["data"] = pd.to_datetime(df["data"], errors="coerce")

with col_f1:
    setor = st.selectbox("Setor", df["origem"].unique())

#aplica filtro de setor
df_filtrado = df[df["origem"].astype(str).str.strip() == str(setor).strip()]

with col_f2:
    veiculos = df_filtrado[col_placa].dropna().unique()
    opcoes = ["Todos"] + sorted(veiculos)

    veiculo_selecionado = st.selectbox("Veículo", opcoes)

#aplica filtro de veículos
if veiculo_selecionado != "Todos": 
    df_filtrado = df_filtrado[df_filtrado[col_placa] == veiculo_selecionado]

with col_f3:
    if "data" in df_filtrado.columns:
        data_min = df_filtrado["data"].min()
        data_max = df_filtrado["data"].max()

        intervalo_datas = st.date_input(
            "Período",
            value=(data_min, data_max)
        )
    else:
        intervalo_datas = None

#Aplica filtro de datas
if intervalo_datas and len(intervalo_datas) == 2:
    data_inicio, data_fim = intervalo_datas

    df_filtrado = df_filtrado[
        (df_filtrado["data"] >= pd.to_datetime(data_inicio)) &
        (df_filtrado["data"] <= pd.to_datetime(data_fim))
    ]

st.divider()

#converter colunas em números
for col in [col_km, col_litros, col_consumo]:
    if col in df_filtrado.columns:
        df_filtrado[col] = (
            df_filtrado [col]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .str.replace(" ", "", regex=False)
        )
        df_filtrado[col] = pd.to_numeric(df_filtrado[col], errors="coerce")


st.subheader("Resumo Geral")

#métricas
total_gasto = df_filtrado[coluna_gasto].sum()
total_abastecimentos = len(df_filtrado)

if col_km not in df_filtrado.columns:
    st.error(f"Coluna KM não encontrada no filtro: {col_km}")
    st.stop()

if col_litros not in df_filtrado.columns:
    st.error(f"coluna Litros não encontrada no filtro : {col_litros}")
    st.stop()

#calculo de custo por km
total_km = pd.to_numeric(df_filtrado[col_km], errors="coerce").sum()

if total_km > 0:
    custo_km = total_gasto / total_km
else:
    custo_km = 0


#calculo seguro de km/l
total_litros = df_filtrado[col_litros].sum()

if total_litros > 0:
    media_km_l = df_filtrado[col_km].sum() / total_litros
else:
    media_km_l = 0

col1, col2 = st.columns(2)

col1.metric("Gasto Total", f"R${total_gasto:.2f}")
col2.metric("Abastecimentos", total_abastecimentos)

#métricas
col3, col4 = st.columns(2)

col3.metric("Média KM/L", f"{media_km_l:.2f}")
col4.metric("Custo por KM", f"{custo_km:.2f}")

#calculo para conferir se o consumo e custo estão elevados
#media_km_l = df_filtrado["km rodado"].sum() / df_filtrado["total de litros"].sum()
#custo_km = total_gasto / df_filtrado["km rodado"].sum()

st.subheader("Análise por veículo")

#calculo por veículo
df_filtrado[col_km] = df_filtrado[col_km].apply(converter_numero_seguro)
df_filtrado[col_litros] = df_filtrado[col_litros].apply(converter_numero_seguro)
df_filtrado[coluna_gasto] = df_filtrado[coluna_gasto].apply(converter_numero_seguro)

analise_veiculos = (
    df_filtrado.groupby(col_placa)
    .agg({
        col_km: "sum",
        col_litros: "sum",
        coluna_gasto: "sum"
    })
    .reset_index()
)

#calcular métricas
#analise_veiculos["km_l"] = (
   # pd.to_numeric(analise_veiculos[col_km], errors="coerce") /
 #   pd.to_numeric(analise_veiculos[col_litros], errors="coerce").replace(0, pd.NA)
#)

#analise_veiculos["custo_km"] = (
 #   pd.to_numeric(analise_veiculos[coluna_gasto], errors="coerce") /
  #  pd.to_numeric(analise_veiculos[col_km], errors="coerce").replace(0, pd.NA)
#)

analise_veiculos[col_km] = converter_numero_seguro(analise_veiculos[col_km])
analise_veiculos[col_litros] = converter_numero_seguro(analise_veiculos[col_litros])
analise_veiculos[coluna_gasto] = converter_numero_seguro(analise_veiculos[coluna_gasto])

km = pd.to_numeric(analise_veiculos[col_km], errors="coerce")
litros = pd.to_numeric(analise_veiculos[col_litros], errors="coerce")
gasto = pd.to_numeric(analise_veiculos[coluna_gasto], errors="coerce")

analise_veiculos["km_l"] = km / litros
analise_veiculos["custo_km"]  = gasto / km

#corrige infinitos(div/0)
analise_veiculos["km_l"] = analise_veiculos["km_l"].replace([float("inf"), -float("inf")], None)
analise_veiculos["custo_km"] = analise_veiculos["custo_km"].replace([float("inf"), -float("inf")], None)

analise_veiculos = analise_veiculos.fillna(0)
analise_veiculos = analise_veiculos[(analise_veiculos[col_litros] > 0) & (analise_veiculos[col_km] > 0)]

#arredondar números
analise_veiculos["km_l"] = analise_veiculos["km_l"].round(2)
analise_veiculos["custo_km"] = analise_veiculos["custo_km"].round(2)

#versão de texto formatada
analise_exibicao = analise_veiculos.copy()

analise_exibicao["km_l"] = analise_exibicao["km_l"].apply(lambda x: f"{x:.2f}")
analise_exibicao["custo_km"] = analise_exibicao["custo_km"].apply(lambda x: f"R${x:.2f}")

#melhorar os nomes
analise_exibicao.rename(columns={
    col_placa: "Veículo",
    "km_l": "Km/L",
    "custo_km": "R$/Km"
}, inplace=True)

st.dataframe(analise_exibicao)

#veículos com consumo ruim
ruins_consumo = analise_veiculos[analise_veiculos["km_l"] < 2]

#veículos com alto custo
ruins_custo = analise_veiculos[analise_veiculos["custo_km"] > 5]

#st.write("ANÁLISE VEÍCULOS")
#st.write(analise_veiculos)

#mostrar alertas
#for _, row in ruins_consumo.iterrows():
 #   st.warning(f"Veículo {row['placa']} com baixo rendimento: {row['km_l']:.2f}")

#for _, row in ruins_custo.iterrows():
 #       st.error(f"Veículo {row['placa']} com alto custo/km: R${row['custo_km']:.2f}")
def definir_status(row):
    if row ["km_l"] < 2 or row ["custo_km"] > 5:
        return "🔴 Crítico"
    elif row ["km_l"] < 3 or row ["custo_km"] > 4:
        return "🟡 Atenção"
    else:
        return "🟢 Normal"

analise_veiculos["status"] = analise_veiculos.apply(definir_status, axis=1)

st.subheader("Status dos Veículos")
st.dataframe(analise_veiculos)

#alerta automático
criticos = analise_veiculos[analise_veiculos["status"] == "🔴 Crítico"]

if not criticos.empty:
    st.error(f"{len(criticos)} veículo(s) em estado CRÍTICO!")
    
#ranking
ranking = (
    df_filtrado.groupby(col_placa)[coluna_gasto]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)

ranking = ranking.sort_values(by=coluna_gasto, ascending=True)

#ranking formatado com R$
ranking_formatado = ranking.copy()
ranking_formatado[coluna_gasto] = ranking_formatado[coluna_gasto].apply(lambda x: f"R$ {x:.2f}")

st.subheader("Ranking de Gastos Por Veículo")
st.dataframe(ranking_formatado, use_container_width=True)

#top 5 veículos mais caros
piores = analise_veiculos.sort_values("custo_km", ascending=False).head(5)

#melhores x piores veículos
melhor = analise_veiculos.sort_values("km_l", ascending=False).iloc[0]
pior = analise_veiculos.sort_values("km_l").iloc[0]

st.success(f"Melhor: {melhor['placa']} ({melhor['km_l']:.2f} KM/L)")
st.error(f"Pior: {pior['placa']} ({pior['km_l']:.2f} KM/L)")

st.subheader ("Top 5 Veículos mais caros")
st.dataframe(piores, use_container_width=True)

#UX²
st.subheader("Análises Visuais")

#gráfico
fig = px.bar(
    ranking,
    x="placa",
    y=coluna_gasto,
    title="Gasto por veículo",
)

#gráfico 2(inteligente)
fig2 = px.scatter(
    analise_veiculos,
    x="km_l",
    y="custo_km",
    color="status",
    size=coluna_gasto,
    hover_data=[col_placa],
    title="Eficiência vs Custo"
)


fig2.update_layout(
    xaxis_title="KM/L",
    yaxis_title= "Custo por KM",
)

st.plotly_chart(fig2, use_container_width=True)


st.plotly_chart(fig, use_container_width=True)


st.subheader("Dados Detalhados")

#tabela final formatada
df_exibicao = df_filtrado.copy()

colunas_monetarias = ["gasto total", "valor diesel", "valor arla", "preço médio", "custo/km"]

for col in df_exibicao.columns:
    if col in colunas_monetarias:
        def formatar_moeda(x):
            try:
                if pd.isna(x):
                    return "R$ 0.00"
                
                #limpa texto tipo "1.200,50"
                x = str(x).replace("R$", "").replace(".", "").replace(",", ".").strip()

                return f"R$ {float(x):.2f}"
            except:
                return "R$ 0.00"
            
            df_exibicao[col] = df_exibicao[col].apply(formatar_moeda)

    elif pd.api.types.is_numeric_dtype(df_exibicao[col]):
        df_exibicao[col] = df_exibicao[col].apply(lambda x: f"{float(x):.2f}")

#Baixar os dados
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


#debug final
#st.write("Coluna usada:", coluna_gasto)
#st.write("DF TOTAL:", df.shape)
#st.write("DF FILTRADO:", df_filtrado.shape)
#st.write(df_filtrado.head(10))
#st.write(analise_veiculos.sort_values("km_l", ascending=False).head(5))
#st.write(df_filtro.dtypes)
#kKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK EU NÃO AGUENTO MAIS VER LINHAS DE CÓDIGO NA MINHA FRENTE ALGUÉM ME AJUDA(I CAN'T HANDLE ANYMORE SEEING CODES IN FRONT OF ME SOME ONE PLEASE HELP ME)KKKKKKKK