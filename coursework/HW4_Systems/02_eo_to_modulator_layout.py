import gdspy
import picwriter.components as pc
from picwriter.components import WaveguideTemplate, SplineYSplitter
import picwriter.toolkit as tk
import gdsfactory as gf
import numpy as np

# =======================================================================
# 0. CONFIGURACIÓN DE CAPAS (JERARQUÍA UNIFICADA EO + TO)
# =======================================================================
LAYER_WG = (1, 0)
LAYER_P = (20, 0)
LAYER_N = (21, 0)
LAYER_PPLUS = (22, 0)
LAYER_NPLUS = (23, 0)
LAYER_VIA1 = (43, 0)
LAYER_VIA2 = (44, 0)
LAYER_METAL_MID = (45, 0)
LAYER_HEATER = (47, 0)
LAYER_METAL_TOP = (49, 0)

gf.clear_cache()
gf.config.rich_output()
gdspy.current_library.cells.clear()

# =======================================================================
# 1. DIVISOR ÓPTICO Y-SPLITTER
# =======================================================================
wgt = WaveguideTemplate(wg_width=0.5, clad_width=3.0, bend_radius=10.0, resist='+')
spline_widths = [0.5, 0.5, 0.6, 0.85, 1.2, 1.4, 1.45, 1.45, 1.45, 1.3, 1.2, 1.2]
pw_ysplitter = SplineYSplitter(wgt=wgt, length=2.0, widths=spline_widths, wg_sep=0.7, output_length=15.0, output_wg_sep=20.0, port=(0, 0), direction='EAST')
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
    c.add_port(name="o1", center=pw_ysplitter.portlist['input']['port'], width=0.5, orientation=180, cross_section=xs)
    c.add_port(name="o2", center=pw_ysplitter.portlist['output_top']['port'], width=0.5, orientation=0, cross_section=xs)
    c.add_port(name="o3", center=pw_ysplitter.portlist['output_bot']['port'], width=0.5, orientation=0, cross_section=xs)
    return c

# =======================================================================
# 2. BLOQUE ELECTRO-ÓPTICO (EO): MZM Y ANILLO
# =======================================================================
@gf.cell
def custom_eo_mzm_arm_top(length=500.0, **kwargs):
    c = gf.Component()
    wg = c << gf.components.straight(length=length)
    rp = c << gf.components.rectangle(size=(length, 2.0), layer=LAYER_P, centered=True)
    rp.move((length/2, 1.25))
    rn = c << gf.components.rectangle(size=(length, 2.0), layer=LAYER_N, centered=True)
    rn.move((length/2, -1.25))
    rpp = c << gf.components.rectangle(size=(length, 2.0), layer=LAYER_PPLUS, centered=True)
    rpp.move((length/2, 3.5))
    rnn = c << gf.components.rectangle(size=(length, 2.0), layer=LAYER_NPLUS, centered=True)
    rnn.move((length/2, -3.5))
    for i in range(int(length // 15)):
        x_pos = (i * 15) + 7.5
        vp, vn = c << gf.components.rectangle(size=(1.5, 1.5), layer=LAYER_VIA2, centered=True), c << gf.components.rectangle(size=(1.5, 1.5), layer=LAYER_VIA2, centered=True)
        vp.move((x_pos, 3.5)); vn.move((x_pos, -3.5))
    c.add_ports(wg.ports); return c

@gf.cell
def custom_eo_mzm_arm_bot(length=500.0, **kwargs):
    c = gf.Component()
    wg = c << gf.components.straight(length=length)
    rp = c << gf.components.rectangle(size=(length, 2.0), layer=LAYER_P, centered=True)
    rp.move((length/2, -1.25))
    rn = c << gf.components.rectangle(size=(length, 2.0), layer=LAYER_N, centered=True)
    rn.move((length/2, 1.25))
    rpp = c << gf.components.rectangle(size=(length, 2.0), layer=LAYER_PPLUS, centered=True)
    rpp.move((length/2, -3.5))
    rnn = c << gf.components.rectangle(size=(length, 2.0), layer=LAYER_NPLUS, centered=True)
    rnn.move((length/2, 3.5))
    for i in range(int(length // 15)):
        x_pos = (i * 15) + 7.5
        vp, vn = c << gf.components.rectangle(size=(1.5, 1.5), layer=LAYER_VIA2, centered=True), c << gf.components.rectangle(size=(1.5, 1.5), layer=LAYER_VIA2, centered=True)
        vp.move((x_pos, -3.5)); vn.move((x_pos, 3.5))
    c.add_ports(wg.ports); return c

@gf.cell
def gsg_traveling_wave_electrodes(length=500.0):
    c = gf.Component()
    s_w, g_w, g_y = 16.0, 8.0, 15.0
    s_trace = c << gf.components.rectangle(size=(length, s_w), layer=LAYER_METAL_TOP, centered=True)
    s_trace.move((length/2, 0))
    g_top = c << gf.components.rectangle(size=(length, g_w), layer=LAYER_METAL_TOP, centered=True)
    g_top.move((length/2, g_y))
    g_bot = c << gf.components.rectangle(size=(length, g_w), layer=LAYER_METAL_TOP, centered=True)
    g_bot.move((length/2, -g_y))
    pad_s, pad_pitch = 60.0, 80.0
    def add_gsg_station(x_pos, is_term=False):
        ps, pgt, pgb = [c << gf.components.rectangle(size=(pad_s, pad_s), layer=LAYER_METAL_TOP, centered=True) for _ in range(3)]
        ps.move((x_pos, 0)); pgt.move((x_pos, pad_pitch)); pgb.move((x_pos, -pad_pitch))
        xe_pad = x_pos + (pad_s/2) if not is_term else x_pos - (pad_s/2)
        xe_trace = 0.0 if not is_term else length
        c.add_polygon([(xe_pad, pad_s/2), (xe_pad, -pad_s/2), (xe_trace, -s_w/2), (xe_trace, s_w/2)], layer=LAYER_METAL_TOP)
        c.add_polygon([(xe_pad, pad_pitch+pad_s/2), (xe_pad, pad_pitch-pad_s/2), (xe_trace, g_y-g_w/2), (xe_trace, g_y+g_w/2)], layer=LAYER_METAL_TOP)
        c.add_polygon([(xe_pad, -pad_pitch+pad_s/2), (xe_pad, -pad_pitch-pad_s/2), (xe_trace, -g_y-g_w/2), (xe_trace, -g_y+g_w/2)], layer=LAYER_METAL_TOP)
        t = c << gf.components.text("GSG IN" if not is_term else "50 OHM", size=15, layer=LAYER_METAL_TOP, justify='center')
        t.move((x_pos, pad_pitch + 45))
    add_gsg_station(-150, False); add_gsg_station(length+150, True)
    return c

@gf.cell
def mzm_electro_optic(length=500.0):
    chip = gf.Component()
    split_in = chip << custom_picwriter_ysplitter()
    arm_top = chip << custom_eo_mzm_arm_top(length=length)
    arm_top.connect("o1", split_in.ports["o2"])
    arm_bot = chip << custom_eo_mzm_arm_bot(length=length)
    arm_bot.connect("o1", split_in.ports["o3"])
    split_out = chip << custom_picwriter_ysplitter()
    split_out.rotate(180)
    split_out.connect("o3", arm_top.ports["o2"])
    gsg = chip << gsg_traveling_wave_electrodes(length=length)
    gsg.move((arm_top.xmin, 0))
    chip.add_port(name="o1", port=split_in.ports["o1"])
    chip.add_port(name="o2", port=split_out.ports["o1"])
    return chip

def route_to_gsg_style_pad(c, center, r_start, ang_start, x_pad, y_pad, label, is_right=True):
    x1, y1 = center[0] + r_start * np.cos(np.deg2rad(ang_start)), center[1] + r_start * np.sin(np.deg2rad(ang_start))
    ref_m_in = c << gf.components.rectangle(size=(3, 3), layer=LAYER_METAL_TOP, centered=True)
    ref_m_in.move((x1, y1))
    ref_via = c << gf.components.rectangle(size=(1.5, 1.5), layer=LAYER_VIA2, centered=True)
    ref_via.move((x1, y1))
    pad_s, trace_w, taper_len = 60.0, 2.5, 50.0

    if is_right:
        x_pad_edge = x_pad - pad_s/2
        x_taper_end = x_pad_edge - taper_len
    else:
        x_pad_edge = x_pad + pad_s/2
        x_taper_end = x_pad_edge + taper_len

    p_s = c << gf.components.rectangle(size=(pad_s, pad_s), layer=LAYER_METAL_TOP, centered=True)
    p_s.move((x_pad, y_pad))
    c.add_polygon([(x_pad_edge, y_pad + pad_s/2), (x_pad_edge, y_pad - pad_s/2), (x_taper_end, y_pad - trace_w/2), (x_taper_end, y_pad + trace_w/2)], layer=LAYER_METAL_TOP)

    cx, cy = (x1 + x_taper_end) / 2, (y1 + y_pad) / 2
    length = np.hypot(x_taper_end - x1, y_pad - y1)
    angle_deg = np.rad2deg(np.arctan2(y_pad - y1, x_taper_end - x1))
    trace = c << gf.components.rectangle(size=(length, trace_w), layer=LAYER_METAL_TOP, centered=True)
    trace.rotate(angle_deg)
    trace.move((cx, cy))

    txt = c << gf.components.text(label, size=12, layer=LAYER_METAL_TOP, justify='center')
    txt.move((x_pad + (50 if is_right else -50), y_pad - 6))

@gf.cell(check_instances=False)
def ring_electro_optic(radius=40.0, gap=0.2, wg_width=0.5):
    c = gf.Component()
    xs_wg = gf.cross_section.strip(width=wg_width)
    ring = c << gf.components.ring_single(radius=radius, gap=gap, length_x=0, length_y=0, bend=gf.components.bend_circular, cross_section=xs_wg)
    center = (0, gap + (wg_width / 2.0) + radius)
    r_h, r_p, r_n = radius, radius - 1.2, radius + 1.2

    def add_arc(layer, r, w, ang, st_ang):
        xs = gf.cross_section.cross_section(width=w, layer=layer)
        a = c << gf.components.bend_circular(radius=r, angle=ang, cross_section=xs)
        a.move(origin=(0, r), destination=center); a.rotate(st_ang, center=center)

    add_arc(LAYER_HEATER, r_h, 2.0, 300, 30); add_arc(LAYER_P, r_p, 2.0, 80, 30); add_arc(LAYER_N, r_n, 2.0, 80, 30)
    add_arc(LAYER_P, r_p, 2.0, 210, 120); add_arc(LAYER_N, r_n, 2.0, 210, 120)

    X_R, X_L, PITCH = 220, -220, 80
    route_to_gsg_style_pad(c, center, r_n, 30, X_R, center[1] + PITCH, "LSB+", True)
    route_to_gsg_style_pad(c, center, r_p, 0, X_R, center[1], "LSB-", True)
    route_to_gsg_style_pad(c, center, r_h, 310, X_R, center[1] - PITCH, "H+", True)
    route_to_gsg_style_pad(c, center, r_n, 150, X_L, center[1] + PITCH, "MSB+", False)
    route_to_gsg_style_pad(c, center, r_p, 180, X_L, center[1], "MSB-", False)
    route_to_gsg_style_pad(c, center, r_h, 230, X_L, center[1] - PITCH, "H-", False)

    c.add_ports(ring.ports); return c

# =======================================================================
# 4. BLOQUE TERMO-ÓPTICO (TO): MZM Y ANILLO
# =======================================================================
@gf.cell
def custom_via_array():
    """Genera el Pad-Stack avanzado para los contactos TO"""
    c = gf.Component()
    c << gf.components.rectangle(size=(6.0, 6.0), layer=LAYER_HEATER, centered=True)
    c << gf.components.rectangle(size=(6.0, 6.0), layer=LAYER_METAL_MID, centered=True)
    c << gf.components.rectangle(size=(6.0, 6.0), layer=LAYER_METAL_TOP, centered=True)
    for i in [-2, -1, 0, 1, 2]:
        for j in [-2, -1, 0, 1, 2]:
            v1 = c << gf.components.rectangle(size=(0.4, 0.4), layer=LAYER_VIA1, centered=True)
            v1.move((i, j))
    for i in [-1.5, -0.5, 0.5, 1.5]:
        for j in [-1.5, -0.5, 0.5, 1.5]:
            v2 = c << gf.components.rectangle(size=(0.4, 0.4), layer=LAYER_VIA2, centered=True)
            v2.move((i, j))
    return c

@gf.cell
def custom_heater_straight(length=100.0, **kwargs):
    """Guía de onda recta con calentador y Pads de 60x60"""
    c = gf.Component()
    wg = c << gf.components.straight(length=length)

    # Filamento calentador sobre la guía
    h = c << gf.components.rectangle(size=(length, 2.0), layer=LAYER_HEATER, centered=True)
    h.move((length/2, 0))

    pad_s = 60.0

    # Contacto Izquierdo
    v1 = c << custom_via_array(); v1.move((0, 0))
    tr1 = c << gf.components.rectangle(size=(4.0, 40.0), layer=LAYER_METAL_TOP, centered=True)
    tr1.move((0, 20))
    p1 = c << gf.components.rectangle(size=(pad_s, pad_s), layer=LAYER_METAL_TOP, centered=True)
    p1.move((0, 40 + pad_s/2))

    # Contacto Derecho
    v2 = c << custom_via_array(); v2.move((length, 0))
    tr2 = c << gf.components.rectangle(size=(4.0, 40.0), layer=LAYER_METAL_TOP, centered=True)
    tr2.move((length, 20))
    p2 = c << gf.components.rectangle(size=(pad_s, pad_s), layer=LAYER_METAL_TOP, centered=True)
    p2.move((length, 40 + pad_s/2))

    c.add_ports(wg.ports)
    return c

@gf.cell(check_instances=False)
def ring_thermo_optic(radius=9.326, gap=0.2, wg_width=0.5):
    """Anillo TO Pads de 60x60"""
    c = gf.Component()
    xs_wg = gf.cross_section.strip(radius_min=5.0)
    ring = c << gf.components.ring_single(radius=radius, gap=gap, length_x=0, length_y=0, bend=gf.components.bend_circular, cross_section=xs_wg)

    xs_h = gf.cross_section.cross_section(width=2.0, layer=LAYER_HEATER, radius_min=5.0)
    center_y = gap + (wg_width / 2.0) + radius
    h_ref = c << gf.components.bend_circular(radius=radius, angle=180, cross_section=xs_h)
    h_ref.move(origin=(0, radius), destination=(0, center_y))
    h_ref.rotate(90, center=(0, center_y))

    # Pilares de Vías en los extremos del calentador
    vs1 = c << custom_via_array(); vs1.move((radius, center_y))
    vs2 = c << custom_via_array(); vs2.move((-radius, center_y))

    pad_s = 60.0
    tr_len = 35.0

    # Pistas y Pads Derechos
    tr1 = c << gf.components.rectangle(size=(tr_len, 4.0), layer=LAYER_METAL_TOP, centered=True)
    tr1.move((radius + tr_len/2, center_y))
    p1 = c << gf.components.rectangle(size=(pad_s, pad_s), layer=LAYER_METAL_TOP, centered=True)
    p1.move((radius + tr_len + pad_s/2, center_y))

    # Pistas y Pads Izquierdos
    tr2 = c << gf.components.rectangle(size=(tr_len, 4.0), layer=LAYER_METAL_TOP, centered=True)
    tr2.move((-radius - tr_len/2, center_y))
    p2 = c << gf.components.rectangle(size=(pad_s, pad_s), layer=LAYER_METAL_TOP, centered=True)
    p2.move((-radius - tr_len - pad_s/2, center_y))

    c.add_ports(ring.ports); return c

# =======================================================================
# 5. ENSAMBLAJE MAESTRO GLOBAL
# =======================================================================
def create_ultimate_master_chip():
    chip = gf.Component("PHOTONICS_FULL_TAPE_OUT")
    gc = gf.components.grating_coupler_elliptical_te()

    # Cálculos físicos para el MZM TO
    fsr_nm = 10.0
    ng = 4.1
    wl0 = 1.55
    fsr_um = fsr_nm / 1000.0
    delta_l = (wl0**2) / (ng * fsr_um)
    radius_to = delta_l / (2 * np.pi)

    # 1. Instanciar los 4 componentes
    eo_mzm = chip << mzm_electro_optic(length=500.0)
    eo_rr = chip << ring_electro_optic(radius=40.0)
    # Reemplazamos la macro genérica por nuestro brazo TO personalizado
    to_mzm = chip << gf.components.mzi(delta_length=delta_l, splitter=custom_picwriter_ysplitter, length_x=100.0, straight_x_top=custom_heater_straight)
    to_rr = chip << ring_thermo_optic(radius=radius_to)

    # 2. Centrado Geométrico en X
    for dev in [eo_mzm, eo_rr, to_mzm, to_rr]:
        center_x = (dev.ports["o1"].x + dev.ports["o2"].x) / 2.0
        dev.movex(-center_x)

    # 3. Separación en Y (Ajustada para que los Pads gigantes no colisionen)
    to_mzm.movey(300)
    to_rr.movey(100)
    eo_mzm.movey(-100)
    eo_rr.movey(-400)

    # 4. Alineación de Acopladores Ópticos
    X_IN = -450
    X_OUT = 450

    labels = [
        (eo_mzm, "EO MZM (GSG)"),
        (eo_rr, "EO Ring\nRadius = 40 um"),
        (to_mzm, f"TO MZM \nDelta L = {delta_l:.1f} um \nFSR = 10nm"),
        (to_rr, f"TO Ring \nRadius = {radius_to:.2f} um \nFSR = 10nm")
    ]

    for ref, label in labels:
        # Guía y Grating Entrada
        dist_in = abs(X_IN - ref.ports["o1"].x)
        win = chip << gf.components.straight(length=dist_in)
        win.connect("o2", ref.ports["o1"])
        gcin = chip << gc
        gcin.rotate(180).connect("o1", win.ports["o1"])

        # Guía y Grating Salida
        dist_out = abs(X_OUT - ref.ports["o2"].x)
        wout = chip << gf.components.straight(length=dist_out)
        wout.connect("o1", ref.ports["o2"])
        gcout = chip << gc
        gcout.connect("o1", wout.ports["o2"])

        # Etiqueta
        txt = chip << gf.components.text(label, size=20, layer=LAYER_METAL_TOP, justify='left')
        txt.move((X_OUT + 50, ref.y + 20))

    return chip

if __name__ == "__main__":
    final_chip = create_ultimate_master_chip()
    final_chip.write_gds("HW4_Layout.gds")
    print("✅ TAPE-OUT COMPLETADO: Todos los pads del chip (EO y TO) estandarizados a 60x60 um.")
    final_chip.plot()
