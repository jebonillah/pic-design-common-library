import numpy as np

def sellmeier_index(wavelength, b1, b2, b3, c1, c2, c3):
    """
    Description:
        Calculates the refractive index of a material at a given wavelength 
        using the standard 3-term Sellmeier equation.
        
    Inputs:
        wavelength (float): The vacuum wavelength in micrometers (um).
        b1, b2, b3 (float): Sellmeier coefficients (numerator).
        c1, c2, c3 (float): Sellmeier coefficients (denominator, in um^2).
        
    Outputs:
        n (float): The calculated refractive index.
        
    Units:
        wavelength and c_i coefficients must be in micrometers. n is dimensionless.
        
    Example:
        >>> # SiO2 around 1.55 um
        >>> sellmeier_index(1.55, 0.696, 0.407, 0.897, 0.0046, 0.0135, 97.93)
        1.444
    """
    # Sellmeier formula: n^2 = 1 + sum(B_i * lambda^2 / (lambda^2 - C_i))
    n_squared = 1.0 + \
                (b1 * wavelength**2) / (wavelength**2 - c1) + \
                (b2 * wavelength**2) / (wavelength**2 - c2) + \
                (b3 * wavelength**2) / (wavelength**2 - c3)
                
    return np.sqrt(n_squared)

def get_silicon_index(wavelength):
    """
    Description:
        Returns the refractive index of Silicon (Si) at room temperature 
        using empirical Sellmeier coefficients.
        
    Inputs:
        wavelength (float): Operating wavelength.
        
    Outputs:
        n_si (float): Refractive index of Silicon.
        
    Units:
        wavelength is in micrometers (um). n_si is dimensionless.
        
    Example:
        >>> get_silicon_index(1.55)
        3.4777
    """
    # Typical Sellmeier coefficients for Silicon (near-IR)
    # n^2 - 1 = 10.6684293 * w^2 / (w^2 - 0.0909122) + 0.003043475 * w^2 / (w^2 - 1.54133408) + 1.54133408 * w^2 / (w^2 - 5391570.77)
    return sellmeier_index(wavelength, 10.6684293, 0.003043475, 1.54133408, 
                           0.0909122, 1.54133408, 5391570.77)
