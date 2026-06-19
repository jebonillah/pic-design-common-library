import gdspy
import picwriter.components as pc
from picwriter.components import WaveguideTemplate, SplineYSplitter
import picwriter.toolkit as tk
import gdsfactory as gf
import numpy as np

# =======================================================================
# 0. INICIALIZACIÓN Y LIMPIEZA DE MEMORIA
# =======================================================================
gf.clear_cache()
gf.config.rich_output()
if 'PW_Y_BRANCH_TEMP' in gdspy.current_library.cells:
    gdspy.current_library.remove('PW_Y_BRANCH_TEMP')

# =======================================================================
# 1. PICWRITER: DIVISOR DE POTENCIA OPTIMIZADO
# =======================================================================
wgt = WaveguideTemplate(wg_width=0.5, clad_width=3.0, bend_radius=10.0, resist='+')
spline_widths = [0.5, 0.5, 0.6, 0.85, 1.2, 1.4, 1.45, 1.45, 1.45, 1.3, 1.2, 1.2]

pw_ysplitter = SplineYSplitter(
    wgt=wgt, length=2.0, widths=spline_widths, wg_sep=0.7,
    output_length=15.0, output_wg_sep=20.0, port=(0, 0), direction='EAST'
)

pt_in = pw_ysplitter.portlist['input']['port']
pt_out_top = pw_ysplitter.portlist['output_top']['port']
pt_out_bot = pw_ysplitter.portlist['output_bot']['port']

top_cell = gdspy.Cell('PW_Y_BRANCH_TEMP')
tk.add(top_cell, pw_ysplitter)

@gf.cell
def custom_picwriter_ysplitter():
    c = gf.Component()
    polygons_by_spec = top_cell.get_polygons(by_spec=True)
    for (layer, datatype), polygons in polygons_by_spec.items():
        for poly in polygons:
            c.add_polygon(poly, layer=(layer, datatype))

    xs = gf.cross_section.strip()
    c.add_port(name="o1", center=pt_in, width=0.5, orientation=180, cross_section=xs)
    c.add_port(name="o2", center=pt_out_top, width=0.5, orientation=0, cross_section=xs)
    c.add_port(name="o3", center=pt_out_bot, width=0.5, orientation=0, cross_section=xs)
    return c

# =======================================================================
# 2. GENERADOR PARAMÉTRICO DE MZIs (PARTE 1)
# =======================================================================
def create_mzi_5mm(fsr_nm, wl0_um=1.55, ng=4.0778):
    c = gf.Component()

    fsr_um = fsr_nm / 1000.0
    delta_l = (wl0_um**2) / (ng * fsr_um)

    core_mzi = gf.components.mzi(
        delta_length=delta_l,
        splitter=custom_picwriter_ysplitter,
        length_x=10.0
    )

    # Creamos el GC primero para conocer su tamaño físico
    gc = gf.components.grating_coupler_elliptical_te()

    # Cálculo exacto de las rectas restando los dos GCs
    target_length = 200.0
    straight_length = (target_length - core_mzi.xsize - 2 * gc.xsize) / 2.0

    mzi_ref = c << core_mzi
    wg_in = c << gf.components.straight(length=straight_length)
    wg_out = c << gf.components.straight(length=straight_length)

    gc_in = c << gc
    gc_out = c << gc

    wg_in.connect("o2", mzi_ref.ports["o1"])
    wg_out.connect("o1", mzi_ref.ports["o2"])
    gc_in.rotate(180)
    gc_in.connect("o1", wg_in.ports["o1"])
    gc_out.connect("o1", wg_out.ports["o2"])

    text_label = gf.components.text(
        text=f"MZI FSR = {fsr_nm} nm\ndelta L = {delta_l:.2f} um",
        size=25.0,
        justify="center",
        layer=(1, 0)
    )
    text_ref = c << text_label
    text_ref.move((wg_in.xsize + gc.xsize + (core_mzi.xsize / 2.0) + 50, mzi_ref.ymax + 70.0))
    print(f"MZI (ΔL = {delta_l:.2f} um)")

    return c

# =======================================================================
# 3. GENERADOR PARAMÉTRICO DE ANILLOS (PARTE 2)
# =======================================================================
def create_ring_5mm(fsr_nm, wl0_um=1.55, ng=4.0778):
    c = gf.Component()

    fsr_um = fsr_nm / 1000.0
    radius = ((wl0_um**2) / (ng * fsr_um)) / (2 * np.pi)
    xs_teorica = gf.cross_section.strip(radius_min=0.1)

    core_ring = gf.components.ring_single(
        radius=radius, gap=0.2, length_x=0,
        bend=gf.components.bend_circular, cross_section=xs_teorica
    )

    # Creamos el GC primero para conocer su tamaño físico
    gc = gf.components.grating_coupler_elliptical_te()

    # Cálculo exacto de las rectas restando los dos GCs
    target_length = 200.0
    straight_length = (target_length - core_ring.xsize - 2 * gc.xsize) / 2.0

    ring_ref = c << core_ring
    wg_in = c << gf.components.straight(length=straight_length)
    wg_out = c << gf.components.straight(length=straight_length)

    gc_in = c << gc
    gc_out = c << gc

    wg_in.connect("o2", ring_ref.ports["o1"])
    wg_out.connect("o1", ring_ref.ports["o2"])
    gc_in.rotate(180)
    gc_in.connect("o1", wg_in.ports["o1"])
    gc_out.connect("o1", wg_out.ports["o2"])

    text_label = gf.components.text(
        text=f"Ring FSR = {fsr_nm} nm\nRadius = {radius:.3f} um",
        size=25.0,
        justify="center",
        layer=(1, 0)
    )
    text_ref = c << text_label
    text_ref.move((wg_in.xsize + gc.xsize + (core_ring.xsize / 2.0), ring_ref.ymax + 70.0))

    print(f"RR (R = {radius:.3f} um)")

    return c

# =======================================================================
# 4. TAPE-OUT: ENSAMBLAJE DEL MACRO-CIRCUITO (TOP LEVEL)
# =======================================================================
if __name__ == "__main__":
    chip_final = gf.Component()

    # Instanciamos los 6 dispositivos
    m_20 = create_mzi_5mm(20)
    m_50 = create_mzi_5mm(50)
    m_100 = create_mzi_5mm(100)
    r_20 = create_ring_5mm(20)
    r_50 = create_ring_5mm(50)
    r_100 = create_ring_5mm(100)

    # Los agregamos a la celda principal
    ref_m20 = chip_final << m_20
    ref_m50 = chip_final << m_50
    ref_m100 = chip_final << m_100
    ref_r20 = chip_final << r_20
    ref_r50 = chip_final << r_50
    ref_r100 = chip_final << r_100

    # -------------------------------------------------------------------
    # FLOORPLANNING
    # -------------------------------------------------------------------

    # 1. Alineación Horizontal Perfecta:
    # Forzamos a que el borde izquierdo de todos los circuitos empiece en X = 0
    referencias = [ref_m20, ref_m50, ref_m100, ref_r20, ref_r50, ref_r100]
    for ref in referencias:
        ref.xmin = 0

    # 2. Alineación Vertical (De arriba hacia abajo):
    # Colocamos primero los MZIs y luego los RRs.
    spacing = 300.0

    # Iniciamos fijando el techo del primer MZI en Y = 0
    ref_m20.ymax = 0

    # Apilamos hacia abajo restando el espaciado
    ref_m50.ymax = ref_m20.ymin - spacing
    ref_m100.ymax = ref_m50.ymin - spacing

    ref_r20.ymax = ref_m100.ymin - spacing
    ref_r50.ymax = ref_r20.ymin - spacing
    ref_r100.ymax = ref_r50.ymin - spacing
    # -------------------------------------------------------------------

    # Exportamos el GDS unificado
    gds_filename = "Homework3_Layout.gds"
    chip_final.write_gds(gds_filename)
    print(f"\n¡TAPE-OUT EXITOSO! Archivo maestro generado: {gds_filename}")

    # Visualizamos el chip completo
    chip_final.plot()
