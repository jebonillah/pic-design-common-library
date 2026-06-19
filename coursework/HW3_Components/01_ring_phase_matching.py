import os
import tidy3d as td
import numpy as np
from tidy3d.plugins.mode import ModeSolver

# 1. AUTENTICACIÓN
os.environ["TIDY3D_KEY"] = "API KEY"

# 2. PARÁMETROS BÁSICOS
w, h = 0.50, 0.22
lda0 = 1.55
offset = 0.01

lambdas = [lda0 - offset, lda0, lda0 + offset]
freqs = [td.constants.C_0 / l for l in lambdas]
freq_center = [td.constants.C_0 / lda0]

# FSRs solicitados en la tarea (en nm)
fsrs_nm = [20, 50, 100]

# 3. ESTRUCTURA BASE
si = td.Medium(permittivity=3.47**2)
sio2 = td.Medium(permittivity=1.44**2)

wg_core = td.Structure(
    geometry=td.Box(center=(0, 0, 0), size=(td.inf, w, h)),
    medium=si
)

boundaries = td.BoundarySpec(
    x=td.Boundary.periodic(),
    y=td.Boundary.pml(),
    z=td.Boundary.pml()
)

sim = td.Simulation(
    size=(0, 3, 3),
    grid_spec=td.GridSpec.auto(wavelength=lda0),
    structures=[wg_core],
    medium=sio2,
    boundary_spec=boundaries,
    run_time=1e-12,
)
plane = td.Box(center=(0, 0, 0), size=(0, 3, 3))


# =====================================================================
# FASE 1: CÁLCULO DEL ÍNDICE DE GRUPO (GUÍA RECTA)
# =====================================================================
print("FASE 1: Calculando dispersión (Guía Recta)...")
solver_recta = td.plugins.mode.ModeSolver(
    simulation=sim,
    mode_spec=td.ModeSpec(num_modes=1, target_neff=2.4),
    freqs=freqs, plane=plane
)
data_recta = solver_recta.solve()

neffs_recta = [float(data_recta.n_eff.sel(f=f, mode_index=0).values) for f in freqs]
neff_base = neffs_recta[1]  # n_eff a 1550 nm

derivada = (neffs_recta[2] - neffs_recta[0]) / (2 * offset)
n_g_simulado = neff_base - lda0 * derivada

print(f" -> n_eff (1550nm): {neff_base:.4f}")
print(f" -> n_g (Grupo):    {n_g_simulado:.4f}\n")


# =====================================================================
# FASE 2: CÁLCULO DINÁMICO DE RADIOS
# =====================================================================
print("FASE 2: Calculando Radios Exactos con el n_g simulado...")
radios_calculados = []
for fsr in fsrs_nm:
    fsr_um = fsr / 1000.0
    # Fórmula estricta: R = lambda^2 / (2 * pi * ng * FSR)
    R = (lda0**2) / (2 * np.pi * n_g_simulado * fsr_um)
    radios_calculados.append(R)
    print(f" -> FSR {fsr:3} nm requiere R = {R:.3f} um")


# =====================================================================
# FASE 3: ANÁLISIS DE PHASE MATCHING (GUÍAS CURVAS)
# =====================================================================
print("\nFASE 3: Evaluando Phase Matching para los Radios Calculados...")

for fsr, R in zip(fsrs_nm, radios_calculados):
    print(f"\nANILLO FSR = {fsr:3} nm (R = {R:.3f} um) :")

    mode_spec_curvo = td.ModeSpec(
        num_modes=1,
        target_neff=2.4,
        bend_radius=R,
        bend_axis=1
    )

    try:
        # Aquí es donde Tidy3D evalúa si la geometría es físicamente posible.
        solver_curvo = ModeSolver(
            simulation=sim,
            mode_spec=mode_spec_curvo,
            freqs=freq_center, plane=plane
        )

        # Si sobrevive la validación, intentamos resolver el modo
        data_curvo = solver_curvo.solve()

        neff_curva = float(np.real(data_curvo.n_eff.sel(f=freq_center[0], mode_index=0).values))
        delta_neff = abs(neff_base - neff_curva)
        delta_beta = (2 * np.pi / lda0) * delta_neff

        print(f" -> n_eff recta:    {neff_base:.4f}")
        print(f" -> n_eff en curva: {neff_curva:.4f}")
        print(f" -> Mismatch (dn):  {delta_neff:.4f}")
        print(f" -> Desfase (dBeta): {delta_beta:.4f} rad/um")

        if delta_neff > 0.03:
            print(" -> VEREDICTO: VIOLACIÓN DE PHASE MATCHING (No Viable)")
        else:
            print(" -> VEREDICTO: Acoplamiento Viable")

    except ValueError as e:
        print(" -> ERROR DEL SIMULADOR: El radio es menor a la mitad del plano de simulación.")
        print(" -> VEREDICTO: IMPOSIBLE DE SIMULAR O FABRICAR. Físicamente inviable.")
