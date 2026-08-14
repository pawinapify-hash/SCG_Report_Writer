import io

import pandas as pd


PRE_COLUMNS = [
    "Pillar",
    "Brand",
    "PRI",
    "PRI Growth",
    "Standard Rate Card",
    "Standard Rate Card Growth",
    "PRE",
    "PRE Growth",
]


def load_pre_data(file_bytes):
    df = pd.read_excel(io.BytesIO(file_bytes))
    missing = [column for column in PRE_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required PRE columns: {', '.join(missing)}")
    return df.loc[:, PRE_COLUMNS].copy()


def pre_rows_for_pillar(df, pillar):
    out = df[df["Pillar"] == pillar].copy()
    return out.drop(columns=["Pillar"], errors="ignore")


def pre_row(df, pillar, brand):
    matched = df[(df["Pillar"] == pillar) & (df["Brand"] == brand)]
    if matched.empty:
        return None
    return matched.iloc[0]
