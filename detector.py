def detectar_colunas(df):
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

    if col_consumo is None:
        col_consumo = col_km

    return {
        "produto": col_produto,
        "km": col_km,
        "litros": col_litros,
        "gasto": col_gasto,
        "placa": col_placa,
        "consumo": col_consumo,
    }