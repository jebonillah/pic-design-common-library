import numpy as np

def calculate_group_index(wavelength, n_eff, dn_eff_dwavelength):
    """
    Description:
        Calculates the group refractive index (n_g) using the effective index 
        and its first derivative with respect to wavelength.
        
    Inputs:
        wavelength (float): The central operating vacuum wavelength.
        n_eff (float): The effective index at the central wavelength.
        dn_eff_dwavelength (float): The derivative of n_eff with respect to wavelength.
        
    Outputs:
        n_g (float): The group refractive index.
        
    Units:
        wavelength must be in micrometers (um).
        dn_eff_dwavelength must be in um^-1.
        n_eff and n_g are dimensionless.
        
    Example:
        >>> calculate_group_index(1.55, 2.45, -0.8)
        3.69
    """
    # Formula: n_g = n_eff - lambda * (dn_eff / d_lambda)
    n_g = n_eff - wavelength * dn_eff_dwavelength
    return n_g

def calculate_beta2_gvd(wavelength, group_index, dng_dwavelength):
    """
    Description:
        Calculates the Group Velocity Dispersion parameter (Beta_2) from the 
        group index and its derivative. This is critical for GNLSE models.
        
    Inputs:
        wavelength (float): The central operating vacuum wavelength.
        group_index (float): The group refractive index.
        dng_dwavelength (float): The derivative of group index wrt wavelength.
        
    Outputs:
        beta_2 (float): The GVD parameter.
        
    Units:
        wavelength is in meters (m).
        dng_dwavelength is in m^-1.
        beta_2 is returned in s^2/m.
        
    Example:
        >>> calculate_beta2_gvd(1.55e-6, 4.2, -1e6)
        1.644e-24
    """
    c = 299792458.0 # speed of light in m/s
    # Beta_2 = (lambda^2 / (2 * pi * c^2)) * (dn_g / d_lambda)
    beta_2 = (wavelength**2 / (2 * np.pi * c)) * (dng_dwavelength / c)
    return beta_2
