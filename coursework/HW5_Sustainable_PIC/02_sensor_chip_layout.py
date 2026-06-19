import gdspy
import picwriter.components as pc
from picwriter.components import WaveguideTemplate, SplineYSplitter
import picwriter.toolkit as tk
import gdsfactory as gf
import numpy as np

# =======================================================================
# 0. CONFIGURACIÓN DE PLATAFORMA (Jerarquía Pasiva Si3N4)
# =======================================================================
LAYER_WG = (1, 0)
LAYER_TEXT = (2, 0)

gf.clear_cache()
gf.config.rich_output()
gdspy.current_library.cells.clear()

# Parámetros físicos
W_SI3N4 = 0.400        # Ancho monomodo TE (400 nm)
R_MIN = 30.0           # Radio de curvatura sin Bend Loss
WL0 = 0.780            # Central wavelength (780 nm)

xs_si3n4 = gf.cross_section.cross_section(
    width=W_SI3N4,
    layer=LAYER_WG,
    radius=R_MIN
)

# Grating Coupler
gc_780 = gf.components.grating_coupler_elliptical_te(cross_section=xs_si3n4)

# =======================================================================
# 1. DIVISOR ÓPTICO Y-SPLITTER
# =======================================================================
wgt = WaveguideTemplate(wg_width=W_SI3N4, clad_width=3.0, bend_radius=R_MIN, resist='+')

# Vector de anchos escalado matemáticamente para una entrada/salida de 0.4 um
spline_widths = [0.4, 0.4, 0.48, 0.68, 0.96, 1.12, 1.16, 1.16, 1.16, 1.04, 0.96, 0.96]

# Separación (wg_sep) ajustada a 0.4 um, respetando el límite geométrico del taper
pw_ysplitter = SplineYSplitter(
    wgt=wgt, length=2.0, widths=spline_widths, wg_sep=0.4,
    output_length=15.0, output_wg_sep=20.0, port=(0, 0), direction='EAST'
)

top_cell = gdspy.Cell('PW_Y_BRANCH_TEMP')
tk.add(top_cell, pw_ysplitter)

@gf.cell
def custom_picwriter_ysplitter():
    c = gf.Component()
    polygons_by_spec = top_cell.get_polygons(by_spec=True)
    for (layer, datatype), polygons in polygons_by_spec.items():
        for poly in polygons:
            c.add_polygon(poly, layer=LAYER_WG)

    c.add_port(name="o1", center=pw_ysplitter.portlist['input']['port'], width=W_SI3N4, orientation=180, cross_section=xs_si3n4)
    c.add_port(name="o2", center=pw_ysplitter.portlist['output_top']['port'], width=W_SI3N4, orientation=0, cross_section=xs_si3n4)
    c.add_port(name="o3", center=pw_ysplitter.portlist['output_bot']['port'], width=W_SI3N4, orientation=0, cross_section=xs_si3n4)
    return c

# =======================================================================
# 2. NÚCLEOS SENSORIALES PASIVOS (REF, RR, MZI)
# =======================================================================
@gf.cell
def passive_reference_wg(length=100.0):
    c = gf.Component()
    wg = c << gf.components.straight(length=length, cross_section=xs_si3n4)
    c.add_ports(wg.ports)
    return c

@gf.cell(check_instances=False)
def passive_ring_sensor(radius=30.0, gap=0.150):
    c = gf.Component()
    ring = c << gf.components.ring_single(
        radius=radius, gap=gap, length_x=0, length_y=0,
        bend=gf.components.bend_circular, cross_section=xs_si3n4
    )
    c.add_ports(ring.ports)
    return c

@gf.cell
def passive_mzi_sensor(delta_l=50.0, length_arm=100.0):
    c = gf.Component()
    mzi = c << gf.components.mzi(
        delta_length=delta_l,
        length_x=length_arm,
        splitter=custom_picwriter_ysplitter,
        combiner=custom_picwriter_ysplitter,
        cross_section=xs_si3n4
    )
    c.add_ports(mzi.ports)
    return c

# =======================================================================
# 3. ENSAMBLAJE MAESTRO GLOBAL (ALINEACIÓN DINÁMICA)
# =======================================================================
def create_ultimate_passive_chip():
    chip = gf.Component("HW5_PICS_TAPE_OUT")

    # Parámetros exigidos
    DELTA_L = 50.0
    L_ARM = 100.0
    DIST_GC_YB = 50.0
    RADIUS = 30.0

    ref_wg = chip << passive_reference_wg(length=L_ARM)
    mzi = chip << passive_mzi_sensor(delta_l=DELTA_L, length_arm=L_ARM)
    ring = chip << passive_ring_sensor(radius=RADIUS)

    # Centrado Geométrico del MZI
    mzi_center_x = (mzi.ports["o1"].x + mzi.ports["o2"].x) / 2.0
    mzi.movex(-mzi_center_x)

    # PLANOS MAESTROS (Fijados por el MZI)
    X_IN = mzi.ports["o1"].x - DIST_GC_YB
    X_OUT = mzi.ports["o2"].x + DIST_GC_YB

    # Alinear en X y separar en Y
    for dev, pos_y in [(ref_wg, 300), (ring, -300)]:
        dev_center_x = (dev.ports["o1"].x + dev.ports["o2"].x) / 2.0
        dev.movex(-dev_center_x)
        dev.movey(pos_y)

    labels = [
        (ref_wg, "Reference Waveguide"),
        (mzi, f"MZI Sensor\ndL = {DELTA_L} um | L_arm = {L_ARM} um"),
        (ring, f"Ring Sensor\nRadius = {RADIUS} um")
    ]

    for ref, label in labels:
        dist_in = abs(X_IN - ref.ports["o1"].x)
        win = chip << gf.components.straight(length=dist_in, cross_section=xs_si3n4)
        win.connect("o2", ref.ports["o1"])
        gcin = chip << gc_780
        gcin.rotate(180).connect("o1", win.ports["o1"])

        dist_out = abs(X_OUT - ref.ports["o2"].x)
        wout = chip << gf.components.straight(length=dist_out, cross_section=xs_si3n4)
        wout.connect("o1", ref.ports["o2"])
        gcout = chip << gc_780
        gcout.connect("o1", wout.ports["o2"])

        txt = chip << gf.components.text(label, size=25, layer=LAYER_TEXT, justify='left')
        txt.move((X_OUT + gc_780.xsize + 20, ref.y + 20))

    global TOTAL_CHIP_LENGTH
    TOTAL_CHIP_LENGTH = abs(X_OUT - X_IN) + 2 * gc_780.xsize

    return chip

# =======================================================================
# 4. CÁLCULOS ANALÍTICOS Y REPORTE
# =======================================================================
def generate_design_report():
    print("\n" + "="*50)
    print(" 🛠️ REPORTE DE DISEÑO FOTÓNICO - HW5 (Si3N4)")
    print("="*50)
    print(f"🔹 Waveguide Width: {W_SI3N4*1000:.0f} nm (Single-mode TE @ 780nm)")
    print(f"🔹 MZI Sensor:")
    print(f"   - Sensing Arm Length (L_arm): 100 um")
    print(f"   - Path Imbalance (Delta L): 50.0 um")
    print(f"🔹 Ring Resonator Sensor:")
    print(f"   - Bend Radius: 30.0 um")
    print(f"   - Coupling Gap: 150 nm")
    print(f"🔹 Footprint General:")
    print(f"   - Chip total active length: {TOTAL_CHIP_LENGTH:.2f} um")

    # n_eff estimado de la simulación FDE anterior para la guía de 400nm
    n_eff_approx, n_clad, theta_deg = 1.66, 1.453, 8.0
    period_um = WL0 / (n_eff_approx - n_clad * np.sin(np.deg2rad(theta_deg)))
    print(f"🔹 Grating Coupler (Analítico a 780 nm):")
    print(f"   - Injection Angle: {theta_deg} grados")
    print(f"   - Theoretical Period (Λ): {period_um*1000:.2f} nm")
    print("="*50)

if __name__ == "__main__":
    final_chip = create_ultimate_passive_chip()
    gds_name = "HW5_PIC_Layout.gds"
    final_chip.write_gds(gds_name)
    generate_design_report()

    print(f"\n✅ TAPE-OUT COMPLETADO: Archivo guardado como '{gds_name}'")
    final_chip.plot()
