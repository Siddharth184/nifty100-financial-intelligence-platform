import pandas as pd

def clean_whitespace(text: str) -> str:
    """Removes extra spaces and normalizes whitespace."""
    if not isinstance(text, str):
        return text
    return " ".join(text.split())

def remove_newlines(text: str) -> str:
    """Removes newline characters from a string."""
    if not isinstance(text, str):
        return text
    return text.replace("\n", " ").replace("\r", "")

def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardizes DataFrame column names by converting to lowercase,
    stripping whitespace, and replacing spaces/special characters with underscores.
    """
    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r'[^a-z0-9]+', '_', regex=True)
        .str.strip('_')
    )
    return df

def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies common normalization steps to an entire DataFrame:
    1. Normalizes column names
    2. Strips whitespace from string columns
    """
    df = normalize_column_names(df)
    
    # Strip whitespace for string columns
    str_cols = df.select_dtypes(include=['object', 'string']).columns
    for col in str_cols:
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
        
    return df
