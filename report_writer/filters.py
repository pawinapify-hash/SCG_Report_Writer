import pandas as pd


def resolve_sheet(sheets, sheet_name):
    if not sheets:
        return pd.DataFrame()
    if sheet_name:
        if sheet_name not in sheets:
            raise KeyError(
                f"Sheet '{sheet_name}' not found. Available: {list(sheets.keys())}"
            )
        return sheets[sheet_name]
    return next(iter(sheets.values()))


def apply_filters(df, spec):
    if not spec:
        return df
    out = df

    for f in spec.get("filters", []):
        col = f["column"]
        op = f.get("operator", "==")
        value = f["value"]
        if col not in out.columns:
            raise KeyError(f"Column '{col}' not found. Available: {list(out.columns)}")
        if op == "==":
            out = out[out[col] == value]
        elif op == "!=":
            out = out[out[col] != value]
        elif op == ">":
            out = out[out[col] > value]
        elif op == ">=":
            out = out[out[col] >= value]
        elif op == "<":
            out = out[out[col] < value]
        elif op == "<=":
            out = out[out[col] <= value]
        elif op == "contains":
            out = out[
                out[col].astype(str).str.contains(str(value), case=False, na=False, regex=False)
            ]
        elif op == "isin":
            vals = value if isinstance(value, list) else [value]
            out = out[out[col].isin(vals)]
        else:
            raise ValueError(f"Unsupported filter operator: {op}")

    columns = spec.get("columns")
    if columns:
        missing = [c for c in columns if c not in out.columns]
        if missing:
            raise KeyError(f"Columns not found: {missing}. Available: {list(out.columns)}")
        out = out[columns]

    max_rows = spec.get("max_rows")
    if max_rows:
        out = out.head(max_rows)

    return out
