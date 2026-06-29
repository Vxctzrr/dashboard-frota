#gráficos Plotly
import plotly.express as px

def grafico_gasto_veiculo(ranking, col_placa, col_gasto):
    return px.bar(
        ranking,
        x=col_placa,
        y=col_gasto,
        title="Gasto por Veículo"
    )


def grafico_eficiencia(analise_veiculos, col_gasto, col_placa):
    fig = px.scatter(
        analise_veiculos,
        x="km_l",
        y="custo_km",
        color="status",
        size=col_gasto,
        hover_data=[col_placa],
        title="Eficiência vs Custo"
    )

    fig.update_layout(
        xaxis_title="KM/L",
        yaxis_title="Custo por KM"
    )

    return fig


def grafico_volume_combustivel(volume_mensal, col_litros):
    return px.bar(
        volume_mensal,
        x="mes",
        y=col_litros,
        color="tipo_combustivel",
        barmode="group",
        title="Volume Mensal por Combustível"
    )
    