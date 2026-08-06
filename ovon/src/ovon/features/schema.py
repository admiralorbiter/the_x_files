from dataclasses import dataclass
from typing import Tuple
import numpy as np

@dataclass(frozen=True)
class EnvironmentalFeatureVector:
    """
    Explicit environmental feature vector schema preventing silent truncation or mismatched dimensions.
    """
    feature_names: Tuple[str, ...]
    values: np.ndarray

    def __post_init__(self):
        vals = np.asarray(self.values, dtype=float)
        if len(self.feature_names) != len(vals):
            raise ValueError(
                f"Feature vector dimension mismatch: feature_names length ({len(self.feature_names)}) "
                f"does not match values length ({len(vals)})."
            )
        object.__setattr__(self, "values", vals)

    def get_value(self, name: str) -> float:
        """Lookup feature value by name."""
        if name not in self.feature_names:
            raise KeyError(f"Feature '{name}' not found in feature_names: {self.feature_names}")
        idx = self.feature_names.index(name)
        return float(self.values[idx])
