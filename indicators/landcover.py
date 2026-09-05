"""Land-cover class summaries."""

import numpy as np
import pandas as pd


def summarize_landcover(landcover: np.ndarray) -> pd.Series:
    """Return class proportions suitable for a compact dashboard chart."""
    values = np.asarray(landcover, dtype=object).ravel()
    if values.size == 0:
        raise ValueError("landcover cannot be empty")
    counts = pd.Series(values).value_counts(normalize=True).mul(100).sort_values(ascending=False)
    counts.name = "percent"
    return counts