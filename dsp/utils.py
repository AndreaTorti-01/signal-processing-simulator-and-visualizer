import numpy as np


def H_eval(z, zeros, poles):
    """Evaluate transfer function H(z) = prod(z-zi)/prod(z-pi)."""
    if len(zeros):
        num = np.prod([z - z0 for z0 in zeros], axis=0)
    else:
        num = np.ones_like(z, dtype=complex)
    if len(poles):
        den = np.prod([z - p0 for p0 in poles], axis=0)
    else:
        den = np.ones_like(z, dtype=complex)
    return num / den
