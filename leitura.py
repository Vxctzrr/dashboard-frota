import pandas as pd


def processar_aba(excel, aba_escolhida, nome_arquivo, modo_generico):
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
            and (
                "km" in texto
                or "quilometragem" in texto
                or "hodometro" in texto
                or "litros" in texto
                or "quantidade" in texto
                or "gasto" in texto
                or "valor total" in texto
            )
        ):
            linha_cabecalho = i
            break

    if linha_cabecalho is None:
        if modo_generico:
            linha_cabecalho = 0
        else:
            return None

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

    df_temp = df_temp.loc[
        :,
        ~df_temp.columns.str.contains("unnamed", case=False, na=False)
    ]

    for col in df_temp.columns:
        if df_temp[col].dtype == "object":
            df_temp[col] = df_temp[col].astype(str).str.strip()
            df_temp[col] = df_temp[col].replace("nan", "")

    df_temp["origem"] = nome_arquivo

    return df_temp