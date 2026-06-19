import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

# ==========================================
# UTILIDADES: Funciones de Conversión
# ==========================================
def mw_to_dbm(mw):
    """Convierte potencia lineal (mW) a dBm."""
    return 10 * np.log10(mw)

def dbm_to_mw(dbm):
    """Convierte dBm a potencia lineal (mW)."""
    return 10**(dbm / 10.0)

def ratio_to_db(ratio, mode='power'):
    """Convierte razón lineal a dB (10log para potencia, 20log para campo)."""
    if mode == 'power':
        return 10 * np.log10(ratio)
    elif mode == 'field':
        return 20 * np.log10(ratio)
    else:
        raise ValueError("Mode must be 'power' or 'field'")

print("=== VERIFICACIÓN DE ENTREGABLES (DELIVERABLES) ===\n")

# ==========================================
# PARTE 5B: Link Budget & Conversions
# ==========================================
print("--- Task 5B: Chip-Scale Link Budget ---")

# Datos de entrada
P_in_mW = 2.0
L_waveguide_mm = 9.0
L_waveguide_cm = L_waveguide_mm / 10.0  # Conversión mm -> cm

# Pérdidas (Losses)
loss_input_coupling = 3.2 # dB
loss_prop_db_cm = 1.8     # dB/cm
loss_coupler = 0.5        # dB
loss_output_coupling = 3.0 # dB

# 1. Calcular Potencia de Entrada en dBm
P_in_dbm = mw_to_dbm(P_in_mW)
print(f"Input Power: {P_in_mW} mW = {P_in_dbm:.2f} dBm")

# 2. Calcular Pérdidas Totales
loss_propagation = loss_prop_db_cm * L_waveguide_cm
total_loss = loss_input_coupling + loss_propagation + loss_coupler + loss_output_coupling

print(f"Propagation Loss ({L_waveguide_mm}mm @ {loss_prop_db_cm}dB/cm): {loss_propagation:.2f} dB")
print(f"Total Link Loss: {total_loss:.2f} dB")

# Identificar contribución dominante
losses = {
    "Input Coupling": loss_input_coupling,
    "Propagation": loss_propagation,
    "Coupler": loss_coupler,
    "Output Coupling": loss_output_coupling
}
dominant_source = max(losses, key=losses.get)
print(f"Dominant Loss Contribution: {dominant_source} ({losses[dominant_source]} dB)")

# 3. Calcular Potencia de Salida
P_out_dbm = P_in_dbm - total_loss
P_out_mw = dbm_to_mw(P_out_dbm)

print(f"Output Power: {P_out_dbm:.2f} dBm = {P_out_mw:.4f} mW")

# 4. Caso Hipotético: Mejora en propagación (0.7 dB/cm)
loss_prop_new = 0.7 * L_waveguide_cm
total_loss_new = loss_input_coupling + loss_prop_new + loss_coupler + loss_output_coupling
print(f"New Total Loss (with 0.7 dB/cm): {total_loss_new:.2f} dB\n")


# ==========================================
# PARTE 5C: Cutback Method Analysis
# ==========================================
print("--- Task 5C: Cutback Method Analysis ---")

# Datos experimentales
L_mm = np.array([2, 5, 10, 20])
P_out_uW = np.array([480, 410, 320, 210])
P_in_uW = 1000.0

# Conversión unidades
L_cm = L_mm / 10.0
IL_dB = -10 * np.log10(P_out_uW / P_in_uW)

# Regresión Lineal
slope, intercept, r_value, p_value, std_err = linregress(L_cm, IL_dB)

# Graficar
L_fit = np.linspace(0, 2.5, 100)
IL_fit = slope * L_fit + intercept

plt.figure(figsize=(8, 6))
plt.scatter(L_cm, IL_dB, color='darkred', s=100, label='Measured Data')
plt.plot(L_fit, IL_fit, 'b--', linewidth=2, label=f'Fit: $\\alpha$={slope:.2f} dB/cm')
plt.title('Task 5C: Cutback Method Analysis')
plt.xlabel('Length [cm]')
plt.ylabel('Insertion Loss [dB]')
plt.grid(True, linestyle=':')
plt.legend()
plt.tight_layout()
plt.savefig('cutback_method_plot.png')
print(f"Alpha (Slope): {slope:.4f} dB/cm")
print(f"Coupling Loss (Intercept): {intercept:.4f} dB")
print(f"R-squared: {r_value**2:.4f}\n")


# ==========================================
# PARTE 4: Modelo de Lorentz y Respuesta Dipolar
# Referencia: Notas de Clase (Castañeda), Pág. 8-10
# ==========================================
print("--- Task 4: Lorentz Oscillator Plotting (Castañeda Model) ---")

# 1. Definir rango de frecuencia normalizada (w_norm = omega / omega_0)
w_norm = np.linspace(0.0, 2.0, 1000)

# 2. Parámetros del modelo
# gamma: Coeficiente de atenuación normalizado
gamma = 0.15

# 3. Calcular la elongación del dipolo eléctrico (Ecs. 2.42a y 2.42b)
# Asumimos que el factor de amplitud (e^2 E_abs / m_e) y w_0 se normalizan a 1
# para propósitos de visualización de la forma de la curva.
denominador = (1 - w_norm**2)**2 + (gamma * w_norm)**2

# Parte real (Dispersión)
p_R = (1 - w_norm**2) / denominador

# Parte imaginaria (Absorción)
p_I = (gamma * w_norm) / denominador

# 4. Establecer límites aproximados para la zona de Dispersión Anómala (DA)
# La región DA ocurre entre los máximos y mínimos de p_R
w_min_DA = np.sqrt(max(0, 1 - gamma))
w_max_DA = np.sqrt(1 + gamma)

# ==========================================
# Graficación (Replicando estilo de Fig. 2.12)
# ==========================================
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 9), sharex=True)

# --- PANEL SUPERIOR: p_R (Dispersión) ---
ax1.plot(w_norm, p_R, color='tab:blue', linewidth=2.5, label=r'$p_R(\omega)$ (Dispersión)')
ax1.axhline(0, color='black', linewidth=1, alpha=0.5)
ax1.axvline(1.0, color='gray', linestyle=':', alpha=0.8) # Línea de resonancia w=w_0

# Marcar regiones DN y DA
ax1.axvspan(w_min_DA, w_max_DA, color='gray', alpha=0.2, label='Zona DA')
ax1.text(0.5, max(p_R)*0.8, 'DN', fontsize=14, fontweight='bold', ha='center', va='center', color='darkblue')
ax1.text(1.0, max(p_R)*0.8, 'DA', fontsize=14, fontweight='bold', ha='center', va='center', color='black')
ax1.text(1.5, max(p_R)*0.8, 'DN', fontsize=14, fontweight='bold', ha='center', va='center', color='darkblue')

ax1.set_ylabel(r'Elongación Real $p_R(\omega)$', fontsize=12, fontweight='bold')
ax1.legend(loc='upper right')
ax1.grid(True, linestyle=':', alpha=0.6)

# --- PANEL INFERIOR: p_I (Absorción) ---
ax2.plot(w_norm, p_I, color='tab:orange', linewidth=2.5, label=r'$p_I(\omega)$ (Absorción)')
ax2.axhline(0, color='black', linewidth=1, alpha=0.5)
ax2.axvline(1.0, color='gray', linestyle=':', alpha=0.8)

# Marcar región AD (Absorción Disipativa)
ax2.axvspan(w_min_DA, w_max_DA, color='gray', alpha=0.2)
ax2.text(1.0, max(p_I)*0.5, 'AD', fontsize=14, fontweight='bold', ha='center', va='center', color='darkred')

ax2.set_xlabel(r'Frecuencia Normalizada ($\omega / \omega_0$)', fontsize=12, fontweight='bold')
ax2.set_ylabel(r'Elongación Imag. $p_I(\omega)$', fontsize=12, fontweight='bold')
ax2.legend(loc='upper right')
ax2.grid(True, linestyle=':', alpha=0.6)

# Título y guardado
plt.suptitle('Respuesta Dipolar: Modelo de Lorentz', fontsize=15, fontweight='bold')
plt.tight_layout()
plt.savefig('lorentz_oscillator_plot.png')
plt.show()

print("Gráfica 'lorentz_oscillator_plot.png' generada con éxito.")
