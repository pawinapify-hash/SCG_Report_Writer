import io

import pandas as pd

CES_METRICS = [
    "CES Score",
    "Competitive Score",
    "Efficiency Score",
    "Sentiment (Influencer & Publisher)",
    "Sentiment (Consumer)",
]

CES_COLUMNS = ["Pillar", "Brand"]
for _m in CES_METRICS:
    CES_COLUMNS.append(_m)
    CES_COLUMNS.append(_m + " Growth")


def load_ces_data(file_bytes):
    df = pd.read_excel(io.BytesIO(file_bytes))
    available = [c for c in CES_COLUMNS if c in df.columns]
    return df[available]


def ces_rows_for_pillar(df, pillar):
    out = df[df["Pillar"] == pillar].copy()
    out = out.drop(columns=["Pillar"], errors="ignore")
    return out


def ces_row(df, pillar, brand):
    m = df[(df["Pillar"] == pillar) & (df["Brand"] == brand)]
    if m.empty:
        return None
    return m.iloc[0]
