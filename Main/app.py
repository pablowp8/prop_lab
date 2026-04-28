"""
AeroSim v4.2 — app.py
Pantalla 1 : Menú de selección de motor
Pantalla 2 : Simulador (sliders · métricas · esquema SVG · gráficas · telemetría)

Física delegada a simulation.py → components.py
Ejecución:  python app.py
Producción: gunicorn app:server --workers 4 --threads 4 --bind 0.0.0.0:8050
"""

import numpy as np
import dash
from dash import dcc, html, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

import simulation as sim

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="PROP-Lab",
    suppress_callback_exceptions=True,
)
server = app.server

# ── Paleta claro (coincide con CSS vars por defecto) ──────────────────────────
C = {
    "bg":      "#edeae4",
    "panel":   "#f5f3ef",
    "panel2":  "#ebe7e0",
    "border":  "#78736F",
    "border2": "#605B55",
    "text":    "#18243c",
    "dim":     "#616264",
    "accent":  "#1a4d8f",
    "accent2": "#b83232",
    "accent3": "#1a6644",
    "warn":    "#9c4d00",
    "mono":    "Share Tech Mono, monospace",
    "head":    "Barlow Condensed, sans-serif",
}

# ══════════════════════════════════════════════════════════════════════════════
#  MOTORES
# ══════════════════════════════════════════════════════════════════════════════
ENGINE_CONFIGS = {
    "OneSpoolEngine": {
        "label":    "Turborreactor Monoeje",
        "subtitle": "Single Spool Turbojet",
        "color":    "#1a4d8f",
        # ── Sección 1: Condiciones de vuelo ──────────────────────────────────
        "sliders_vuelo": [
            ("os_t0",   "T\u2080 [°C]",   -70,  50,    15,   1),
            ("os_p0",   "P\u2080 [kPa]",   20,  105,  101.325, 0.1),
            ("os_mach", "M\u2080",           0,  2.5,    0,   0.01),
        ],
        # ── Sección 2: Punto de diseño ───────────────────────────────────────
        "sliders_diseno": [
            ("os_tit",  "T\u2084\u209C [K]",   800, 1800, 1400,  5),
            ("os_pi",   "\u03C0\u2082\u2083",  2,   30,   18,  0.1),
            ("os_G",    "G [kg/s]",         5,  200,   20,   1),
        ],
        # ── Sección 3: Componentes ───────────────────────────────────────────
        "sliders_comp": [
            ("os_edif",  "\u03B7 difusor",    0.6, 0.99, 0.99, 0.01),
            ("os_ec",    "\u03B7 compresor",  0.6, 0.99, 0.92, 0.01),
            ("os_ecc",   "\u03B7 camara",     0.6, 0.99, 0.99, 0.01),
            ("os_et",    "\u03B7 turbina",    0.6, 0.99, 0.88, 0.01),
            ("os_enoz",  "\u03B7 tobera",     0.6, 0.99, 0.99, 0.01),
        ],
        "engine_cls": sim.OneSpoolEngine,
        "runner": lambda p: sim.OneSpoolEngine().simulate(
            p["os_t0"] + 273.15, p["os_p0"] * 1000,
            p["os_mach"], p["os_G"], p["os_pi"], p["os_tit"],
            eta_dif=p["os_edif"], eta_c=p["os_ec"], eta_cc=p["os_ecc"],
            eta_t=p["os_et"], eta_noz=p["os_enoz"],
        ),
        "sweep_base": lambda p: {
            "T_amb": p["os_t0"] + 273.15, "P_amb": p["os_p0"] * 1000,
            "mach":p["os_mach"], "G":p["os_G"],
            "pi_23":p["os_pi"],  "tit":p["os_tit"],
            "eta_dif":p["os_edif"], "eta_c":p["os_ec"], "eta_cc":p["os_ecc"],
            "eta_t":p["os_et"],  "eta_noz":p["os_enoz"],
        },
    },
    "TwinSpoolEngine": {
        "label":    "Turborreactor Bieje",
        "subtitle": "Twin Spool Turbojet",
        "color":    "#b83232",
        "sliders_vuelo": [
            ("ts_t0",   "T\u2080 [°C]",  -70,  50,   15,   1),
            ("ts_p0",   "P\u2080 [kPa]",  20, 105, 101.3, 0.1),
            ("ts_mach", "M\u2080",          0,  2.5,   0,  0.01),
        ],
        "sliders_diseno": [
            ("ts_tit",   "T\u2084\u209C [K]",     800, 1900, 1450,  5),
            ("ts_pilpc", "\u03C0\u2095 (LP)",    1.1,    6,  1.6, 0.1),
            ("ts_pihpc", "\u03C0\u2090 (HP)",      2,   25,   12, 0.1),
            ("ts_G",     "G [kg/s]",               5,  200,   20,  1),
        ],
        "sliders_comp": [
            ("ts_edif",  "\u03B7 difusor",     0.6, 0.99, 0.99, 0.01),
            ("ts_elpc",  "\u03B7 comp. LP",    0.6, 0.99, 0.91, 0.01),
            ("ts_ehpc",  "\u03B7 comp. HP",    0.6, 0.99, 0.85, 0.01),
            ("ts_ecc",   "\u03B7 camara",      0.6, 0.99, 0.99, 0.01),
            ("ts_ehpt",  "\u03B7 turb. HP",    0.6, 0.99, 0.92, 0.01),
            ("ts_elpt",  "\u03B7 turb. LP",    0.6, 0.99, 0.94, 0.01),
            ("ts_enoz",  "\u03B7 tobera",      0.6, 0.99, 0.99, 0.01),

        ],
        "engine_cls": sim.TwinSpoolEngine,
        "runner": lambda p: sim.TwinSpoolEngine().simulate(
            p["ts_t0"] + 273.15, p["ts_p0"] * 1000,
            p["ts_mach"], p["ts_G"],
            p["ts_pilpc"], p["ts_pihpc"], p["ts_tit"],
            eta_dif=p["ts_edif"], eta_lpc=p["ts_elpc"], eta_hpc=p["ts_ehpc"],
            eta_cc=p["ts_ecc"], eta_lpt=p["ts_elpt"], eta_hpt=p["ts_ehpt"],
            eta_noz=p["ts_enoz"],
        ),
        "sweep_base": lambda p: {
            "T_amb": p["ts_t0"] + 273.15, "P_amb": p["ts_p0"] * 1000,
            "mach":p["ts_mach"],    "G":p["ts_G"],
            "pi_lpc":p["ts_pilpc"], "pi_hpc":p["ts_pihpc"], "tit":p["ts_tit"],
            "eta_dif":p["ts_edif"], "eta_lpc":p["ts_elpc"], "eta_hpc":p["ts_ehpc"],
            "eta_cc":p["ts_ecc"],   "eta_lpt":p["ts_elpt"], "eta_hpt":p["ts_ehpt"],
            "eta_noz":p["ts_enoz"],
        },
    },
    "SingleFlowTurbofan": {
        "label":    "Turbofan",
        "subtitle": "Single Flow Turbofan",
        "color":    "#1a6644",
        "sliders_vuelo": [
            ("tf_t0",   "T\u2080 [°C]",  -70,  50,   15,   1),
            ("tf_p0",   "P\u2080 [kPa]",  20, 105, 101.3, 0.1),
            ("tf_mach", "M\u2080",          0,  1.0,   0,  0.01),
        ],
        "sliders_diseno": [
            ("tf_tit",   "T\u2084\u209C [K]",          800, 2000, 1500,  5),
            ("tf_pi",    "\u03C0\u2082\u2083 nucleo", 2,   40,   25, 0.1),
            ("tf_G",     "G [kg/s]",                10,  500,   90,  5),
            ("tf_bpr",   "\u039B (BPR)",     0.1,  12,  0.8,  0.1),
            ("tf_pifan", "\u03C0 fan",             1.1,  3.0,  1.4, 0.05),
        ],
        "sliders_comp": [
            ("tf_edif",  "\u03B7 difusor",   0.6, 0.99, 0.99, 0.01),
            ("tf_efan",  "\u03B7 fan",       0.6, 0.99, 1.0,  0.01),
            ("tf_ec",    "\u03B7 compresor", 0.6, 0.99, 1.0,  0.01),
            ("tf_ecc",   "\u03B7 camara",    0.6, 0.99, 0.99, 0.01),
            ("tf_ehpt",  "\u03B7 turb. HP",  0.6, 0.99, 1.0,  0.01),
            ("tf_elpt",  "\u03B7 turb. LP",  0.6, 0.99, 1.0,  0.01),
            ("tf_enoz",  "\u03B7 tobera",    0.6, 0.99, 0.99, 0.01),

        ],
        "engine_cls": sim.SingleFlowTurbofan,
        "runner": lambda p: sim.SingleFlowTurbofan().simulate(
            p["tf_t0"] + 273.15, p["tf_p0"] * 1000,
            p["tf_mach"], p["tf_G"], p["tf_pi"], p["tf_tit"],
            p["tf_pifan"], p["tf_bpr"],
            eta_dif=p["tf_edif"], eta_c=p["tf_ec"], eta_fan=p["tf_efan"],
            eta_cc=p["tf_ecc"],
            eta_hpt=p["tf_ehpt"], eta_lpt=p["tf_elpt"],
            eta_noz=p["tf_enoz"],
        ),
        "sweep_base": lambda p: {
            "T_amb": p["tf_t0"] + 273.15, "P_amb": p["tf_p0"] * 1000,
            "mach":p["tf_mach"],    "G":p["tf_G"],
            "pi_23":p["tf_pi"],     "tit":p["tf_tit"],
            "pi_fan":p["tf_pifan"], "bpr":p["tf_bpr"],
            "eta_dif":p["tf_edif"], "eta_c":p["tf_ec"], "eta_fan":p["tf_efan"],
            "eta_cc":p["tf_ecc"],
            "eta_hpt":p["tf_ehpt"], "eta_lpt":p["tf_elpt"],
            "eta_noz":p["tf_enoz"],
        },
    },
    "OneSpoolTurboprop": {
        "label":    "Turbohélice",
        "subtitle": "Single Spool Turboprop",
        "color":    "#9c4d00",
        "sliders_vuelo": [
            ("tp_t0",   "T\u2080 [°C]",  -50,  50,  15,   1),
            ("tp_p0",   "P\u2080 [kPa]",  20, 105, 101.3, 0.1),
            ("tp_mach", "M\u2080",          0,  0.7,  0,  0.01),
        ],
        "sliders_diseno": [
            ("tp_tit",  "T\u2084t [K]",          800, 1700, 1500,  5),
            ("tp_pi",   "\u03C0\u2082\u2083",       2,   30,   25, 0.1),
            ("tp_G",    "G [kg/s]",                 5,  200,   90,  1),
            ("tp_Wh",    "W\u2095 [kW]",       10, 2000,  200, 10),
            ("tp_etam",  "\u03B7 mecanica",   0.5, 0.99, 0.70, 0.01),
        ],
        "sliders_comp": [
            ("tp_edif",  "\u03B7 difusor",    0.6, 0.99, 0.99, 0.01),
            ("tp_ec",    "\u03B7 compresor",  0.6, 0.99, 1.0,  0.01),
            ("tp_ecc",   "\u03B7 camara",     0.6, 0.99, 0.99, 0.01),
            ("tp_ehpt",  "\u03B7 turb. HP",   0.6, 0.99, 1.0,  0.01),
            ("tp_elpt",  "\u03B7 turb. LP",   0.6, 0.99, 1.0,  0.01),
            ("tp_enoz",  "\u03B7 tobera",     0.6, 0.99, 0.99, 0.01),

        ],
        "engine_cls": sim.OneSpoolTurboprop,
        "runner": lambda p: sim.OneSpoolTurboprop().simulate(
            p["tp_t0"] + 273.15, p["tp_p0"] * 1000,
            p["tp_mach"], p["tp_G"], p["tp_pi"], p["tp_tit"],
            p["tp_Wh"] * 1000, p["tp_etam"],
            eta_dif=p["tp_edif"], eta_c=p["tp_ec"], eta_cc=p["tp_ecc"],
            eta_hpt=p["tp_ehpt"], eta_lpt=p["tp_elpt"],
            eta_noz=p["tp_enoz"],
        ),
        "sweep_base": lambda p: {
            "T_amb": p["tp_t0"] + 273.15, "P_amb": p["tp_p0"] * 1000,
            "mach":p["tp_mach"],  "G":p["tp_G"],
            "pi_23":p["tp_pi"],   "tit":p["tp_tit"],
            "W_h":p["tp_Wh"]*1000, "eta_m":p["tp_etam"],
            "eta_dif":p["tp_edif"], "eta_c":p["tp_ec"], "eta_cc":p["tp_ecc"],
            "eta_hpt":p["tp_ehpt"], "eta_lpt":p["tp_elpt"],
            "eta_noz":p["tp_enoz"],
        },
    },
}

ALL_SLIDER_IDS = [
    sid
    for cfg in ENGINE_CONFIGS.values()
    for section in ("sliders_vuelo", "sliders_diseno", "sliders_comp")
    for sid, *_ in cfg[section]
]

# IDs que tienen label visible (val-{sid}) — solo vuelo y diseño,
# porque los sliders de comp están ocultos sin Span de valor.
ALL_LABEL_IDS = [
    sid
    for cfg in ENGINE_CONFIGS.values()
    for section in ("sliders_vuelo", "sliders_diseno")
    for sid, *_ in cfg[section]
]

# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS UI
# ══════════════════════════════════════════════════════════════════════════════
# Inputs
def make_slider(sid, label, mn, mx, dfl, stp):
    return html.Div([
        html.Div([
            html.Span(label, style={"fontSize":"0.75rem","color":C["accent"],   # Variable
                                    "fontFamily":C["mono"]}),
            html.Span(id=f"val-{sid}", style={"fontFamily":C["mono"],  # Valor numérico
                                               "fontSize":"0.75rem","color":C["accent"]}),
        ], style={"display":"flex","justifyContent":"space-between","marginBottom":"3px"}),
        dcc.Slider(id=f"sl-{sid}", min=mn, max=mx, value=dfl, step=stp,
                   marks=None, tooltip={"always_visible":False}, className="mb-1"),
    ], className="mb-2")


def metric_card(label, mid, unit, cls=""):
    return html.Div([
        html.Div(label, className="metric-label"),
        html.Div([
            html.Span("--", id=f"m-{mid}", className="metric-val"),
            html.Span(unit, className="metric-unit"),
        ]),
    ], className=f"metric-card {cls} mb-1")



def _rgba(hex_color, alpha=0.12):
    """Convierte #rrggbb a rgba() para Plotly fillcolor."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"rgba({r},{g},{b},{alpha})"

def _plot_layout(title):
    return dict(
        title=dict(text=title, font=dict(color=C["dim"],size=11,family=C["head"]),
                   x=0.01, y=0.97),
        plot_bgcolor=C["panel"], paper_bgcolor=C["panel"],
        font=dict(color=C["text"], family=C["mono"]),
        margin=dict(l=50,r=16,t=34,b=38), hovermode="x unified",
    )


def _ax(title_text=None):
    d = dict(
        gridcolor=C["border"], gridwidth=0.8,
        linecolor=C["border2"], linewidth=1,
        tickfont=dict(size=9,family=C["mono"],color=C["dim"]),
        title_font=dict(size=10,family=C["mono"],color=C["dim"]),
        zeroline=True, zerolinecolor=C["border2"], zerolinewidth=1,
    )
    if title_text:
        d["title_text"] = title_text
    return d


def _isa(h_m):
    """Atmósfera Estándar Internacional (ISA). Devuelve (T [K], P [Pa])."""
    T0, P0, L, g, R = 288.15, 101325.0, 0.0065, 9.80665, 287.05
    if h_m <= 11000:
        T = T0 - L * h_m
        P = P0 * (T / T0) ** (g / (L * R))
    else:
        T11 = T0 - L * 11000
        P11 = P0 * (T11 / T0) ** (g / (L * R))
        T   = T11
        P   = P11 * np.exp(-g * (h_m - 11000) / (R * T11))
    return T, P


# ══════════════════════════════════════════════════════════════════════════════
#  ESQUEMA SVG DEL MOTOR
# ══════════════════════════════════════════════════════════════════════════════

def build_engine_diagram(engine_type, df):
    """
    Esquema del motor usando Plotly shapes + annotations.
    Compatible con todas las versiones de Dash (sin dangerously_allow_html).
    """
    def tv(st):
        try:    return float(df.loc[st, "T"]) if df is not None and st in df.index else None
        except: return None
    def pv(st):
        try:    return float(df.loc[st, "P"]) / 1000 if df is not None and st in df.index else None
        except: return None
def _rgba(h, a=0.15):
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{a})"


def _tv(df, st):
    try:    return float(df.loc[st, "T"]) if df is not None and st in df.index else None
    except: return None


def _pv(df, st):
    try:    return float(df.loc[st, "P"]) / 1000 if df is not None and st in df.index else None
    except: return None


# ══════════════════════════════════════════════════════════════════════════════
#  MOTOR 1 — OneSpoolEngine   Turborreactor Monoeje  (esquema 3D interactivo)
# ══════════════════════════════════════════════════════════════════════════════
def _build_onespool(df):
    S, A = [], []

    # ── Eje de simetría ───────────────────────────────────────────────────────
    # S.append(dict(type="line", x0=5, x1=715, y0=0.50, y1=0.50,
    #              line=dict(color=C["border"], width=0.5, dash="dot")))

    # ── Zona fría: difusor + compresor (azul) ─────────────────────────────────
    S.append(dict(
        type="path",
        path=("M 20,0.15 "
              "C 32,0.10 58,0.13 110,0.13 "
              "L 260,0.22 L 260,0.78 "
              "L 110,0.87 "
              "C 58,0.87 32,0.9 20,0.85 Z"),
        fillcolor=_rgba("#4a90d9", 0.2),
        line=dict(color="rgba(0,0,0,0)", width=0),
        layer="below",
    ))

    # ── Zona caliente: cámara + turbina (rojo) ────────────────────────────────
    S.append(dict(
        type="path",
        path=("M 260,0.22 L 370,0.22 L 370,0.78 L 260,0.78 Z"),
        fillcolor=_rgba("#e28800", 0.2),
        line=dict(color="rgba(0,0,0,0)", width=0),
        layer="below",
    ))
    
    S.append(dict(
        type="path",
        path=("M 370,0.22 L 472,0.1578 "
              "L 472,0.8522 L 370,0.78 Z"),
        fillcolor=_rgba("#b83232", 0.2),
        line=dict(color="rgba(0,0,0,0)", width=0),
        layer="below",
    ))

    # ── Zona tobera (morado) ──────────────────────────────────────────────────
    S.append(dict(
        type="path",
        path=("M 472 0.1578"
              "C 528,0.33 552,0.35 580,0.33 "
              "C 598,0.31 618,0.29 630,0.30 "
              "L 630,0.7 "
              "C 618,0.71 598,0.69 580,0.67 "
              "C 552,0.65 528,0.67 472 0.8422 Z"),

        fillcolor=_rgba("#b83232", 0.2),
        line=dict(color="rgba(0,0,0,0)", width=0),
        layer="below",
    ))

    # ── Banda 3D superior — difusor+compresor ─────────────────────────────────
    S.append(dict(
        type="path",
        path=("M 20,0.12 "
              "C 32,0.06 58,0.08 110,0.10 "
              "L 260,0.19 L 260,0.22 "
              "L 110,0.13 "
              "C 58,0.13 32,0.10 20,0.15 Z"),
        fillcolor=_rgba("#888888", 0.32),
        line=dict(color="rgba(0,0,0,0)", width=0),
        layer="above",
    ))
    # ── Banda 3D inferior — difusor+compresor ────────────────────────────────
    S.append(dict(
        type="path",
        path=("M 20,0.88 "
              "C 32,0.94 58,0.9 110,0.90 "
              "L 260,0.81 L 260,0.78 "
              "L 110,0.87 "
              "C 58,0.87 32,0.9 20,0.85 Z"),
        fillcolor=_rgba("#888888", 0.32),
        line=dict(color="rgba(0,0,0,0)", width=0),
        layer="above",
    ))
    # ── Banda 3D superior — zona caliente ────────────────────────────────────
    S.append(dict(
        type="path",
        path=("M 260,0.19 L 370,0.19 L 472 0.1278"
              "L 472,0.1578 L 370,0.22 L 260,0.22 Z"),
        fillcolor=_rgba("#888888", 0.32),
        line=dict(color="rgba(0,0,0,0)", width=0),
        layer="above",
    ))
    # ── Banda 3D inferior — zona caliente ────────────────────────────────────
    S.append(dict(
        type="path",
        path=("M 260,0.81 L 370,0.81 L 472,0.8722"
              "L 472,0.8522 L 370,0.78 L 260,0.78 Z"),
        fillcolor=_rgba("#888888", 0.32),
        line=dict(color="rgba(0,0,0,0)", width=0),
        layer="above",
    ))
    # ── Banda 3D superior — tobera ───────────────────────────────────────────
    S.append(dict(
        type="path",
        path=("M 472 0.1278"
              "C 528,0.30 552,0.32 580,0.3 "
              "C 598,0.28 618,0.26 630,0.27"
              "L 630,0.30 "
              "C 618,0.29 598,0.31 580,0.33 "
              "C 552,0.35 528,0.33 472,0.1578 Z"),
        fillcolor=_rgba("#888888", 0.32),
        line=dict(color="rgba(0,0,0,0)", width=0),
        layer="above",
    ))
    # ── Banda 3D inferior — tobera ───────────────────────────────────────────
    S.append(dict(
        type="path",
        path=("M 472 0.8722 "
        "C 528,0.70 552,0.68 580,0.70 "
        "C 598,0.72 618,0.74 630,0.73 "
        "L 630,0.70 "
        "C 618,0.71 598,0.69 580,0.67 "
        "C 552,0.65 528,0.67 472,0.8422 Z"),
        fillcolor=_rgba("#888888", 0.32),
        line=dict(color="rgba(0,0,0,0)", width=0),
        layer="above",
    ))

    # ── Cara exterior superior ────────────────────────────────────────────────
    S.append(dict(
        type="path",
        path=("M 20,0.12 "
              "C 32,0.06 58,0.10 110,0.10 "
              "L 260,0.19 L 370,0.19 L 472 0.1278"
              "C 528,0.30 552,0.32 580,0.3 "
              "C 598,0.28 618,0.26 630,0.27"),
        fillcolor="rgba(0,0,0,0)",
        line=dict(color="#2a2a2a", width=1.4),
    ))
    # ── Cara interior superior ────────────────────────────────────────────────
    S.append(dict(
        type="path",
        path=("M 20,0.15 "
              "C 32,0.10 58,0.13 110,0.13 "
              "L 260,0.22 L 370,0.22 L 472 0.1578"
              "C 528,0.33 552,0.35 580,0.33 "
              "C 598,0.31 618,0.29 630,0.30"),
        fillcolor="rgba(0,0,0,0)",
        line=dict(color="#555555", width=1.4),
    ))
    # ── Cierre vertical derecho — carcasa superior abierta ────────────────────
    S.append(dict(
        type="line", x0=630, x1=630, y0=0.27, y1=0.30,
        line=dict(color="#2a2a2a", width=1.4),
    ))

    S.append(dict(
        type="line", x0=20, x1=20, y0=0.12, y1=0.15,
        line=dict(color="#2a2a2a", width=1.4),
    ))
    # ── Cara exterior inferior ────────────────────────────────────────────────
    S.append(dict(
        type="path",
        path=("M 20,0.88 "
        "C 32,0.94 58,0.90 110,0.90 "
        "L 260,0.81 L 370,0.81 L 472 0.8722 "
        "C 528,0.70 552,0.68 580,0.70 "
        "C 598,0.72 618,0.74 630,0.73"),
        fillcolor="rgba(0,0,0,0)",
        line=dict(color="#2a2a2a", width=1.4),
    ))
    # ── Cara interior inferior ────────────────────────────────────────────────
    S.append(dict(
        type="path",
        path=("M 20,0.85 "
        "C 32,0.90 58,0.87 110,0.87 "
        "L 260,0.78 L 370,0.78 L 472 0.8422 "
        "C 528,0.67 552,0.65 580,0.67 "
        "C 598,0.69 618,0.71 630,0.70"),
        fillcolor="rgba(0,0,0,0)",
        line=dict(color="#555555", width=1.4),
    ))
    # ── Cierre vertical derecho — carcasa inferior abierta ────────────────────
    S.append(dict(
        type="line", x0=630, x1=630, y0=0.7, y1=0.73,
        line=dict(color="#2a2a2a", width=1.4),
    ))
    # ── Cierre vertical izquierdo — carcasa inferior abierta ────────────────────
    S.append(dict(
        type="line", x0=20, x1=20, y0=0.85, y1=0.88,
        line=dict(color="#2a2a2a", width=1.4),
    ))

    # ── Ojiva ─────────────────────────────────────────────────────────────────
    S.append(dict(
        type="path",
        path=("M 20,0.50 "
              "C 33,0.44 56,0.42 90,0.41 "
              "L 90,0.59 "
              "C 56,0.58 33,0.56 20,0.50 Z"),
        fillcolor=_rgba("#aaaaaa", 0.65),
        line=dict(color="#444444", width=1.6),
        layer="above",
    ))
    S.append(dict(
        type="path",
        path=("M 22,0.50 C 35,0.46 57,0.44 84,0.43 "
              "L 84,0.46 C 57,0.47 35,0.48 22,0.50 Z"),
        fillcolor=_rgba("#ffffff", 0.40),
        line=dict(color="rgba(0,0,0,0)", width=0),
        layer="above",
    ))

    S.append(dict(
        type="path",
        path=("M 630,0.50 "
            "C 617,0.44 594,0.42 560,0.41 "
            "L 560,0.59 "
            "C 594,0.58 617,0.56 630,0.50 Z"),
        fillcolor=_rgba("#aaaaaa", 0.65),
        line=dict(color="#444444", width=1.6),
        layer="above",
    ))

    S.append(dict(
        type="path",
        path=("M 628,0.50 C 615,0.46 593,0.44 566,0.43 "
            "L 566,0.46 C 593,0.47 615,0.48 628,0.50 Z"),
        fillcolor=_rgba("#ffffff", 0.40),
        line=dict(color="rgba(0,0,0,0)", width=0),
        layer="above",
    ))

    # ── Eje mecánico (radio mayor) ────────────────────────────────────────────
    S.append(dict(
        type="rect", x0=90, x1=560, y0=0.447, y1=0.553,
        fillcolor=_rgba("#999999", 0.60),
        line=dict(color="#555555", width=1.3),
        layer="above",
    ))
    S.append(dict(
        type="rect", x0=90, x1=560, y0=0.447, y1=0.468,
        fillcolor=_rgba("#ffffff", 0.28),
        line=dict(color="rgba(0,0,0,0)", width=0),
        layer="above",
    ))

    # ── Sub-eje compresor→turbina (dentro de la cámara) ───────────────────────
    S.append(dict(
        type="rect", x0=120, x1=464, y0=0.453, y1=0.547,
        fillcolor=_rgba("#777777", 0.75),
        line=dict(color="#444444", width=1.1),
        layer="above",
    ))

    # ── Palas del compresor (ancho→estrecho, línea recta) ─────────────────────
    for xi in range(118, 258, 16):
        t = (xi - 110) / (260 - 110)
        y_top = 0.13 + t * 0.09
        y_bot = 0.87 - t * 0.09
        S.append(dict(
            type="line", x0=xi, x1=xi + 6, y0=0.553, y1=y_top,
            line=dict(color=_rgba("#1a4d8f", 0.72), width=4),
        ))
        S.append(dict(
            type="line", x0=xi, x1=xi + 6, y0=0.447, y1=y_bot,
            line=dict(color=_rgba("#1a4d8f", 0.72), width=4),
        ))

    # ── Cámara de combustión (pared recta) ────────────────────────────────────
    S.append(dict(
        type="path",
        path="M 260,0.30 L 260,0.70 L 276,0.60 L 354,0.60 L 370,0.70 L 370,0.30 L 354,0.4, L 276,0.4 Z",
        fillcolor=_rgba("#999999", 0.60),
        line=dict(color="#555555", width=1.3),
        layer="below",
    ))

    # ── Palas de la turbina (estrecha→ancha, más corta) ───────────────────────
    for xi in range(377, 472, 16):
        t = (xi - 370) / (470 - 370)
        y_top = 0.22 - t * 0.06
        y_bot = 0.78 + t * 0.06
        S.append(dict(
            type="line", x0=xi + 6, x1=xi, y0=0.553, y1=y_top,
            line=dict(color=_rgba("#b83232", 0.78), width=4),
        ))
        S.append(dict(
            type="line", x0=xi + 6, x1=xi, y0=0.447, y1=y_bot,
            line=dict(color=_rgba("#b83232", 0.78), width=4),
        ))

    # ── Líneas de estación ────────────────────────────────────────────────────
    ST_Y0, ST_Y1 = 0.02, 0.98
    STATIONS = [
        (20,  "0"),
        (110, "2"),
        (260, "3"),
        (370, "4"),
        (450, "5"),
        (552, "8"),
        (630, "9"),
    ]
    for sx, slbl in STATIONS:
        S.append(dict(
            type="line", x0=sx, x1=sx, y0=ST_Y0, y1=ST_Y1,
            line=dict(color=C["border"], width=0.8, dash="dot"),
        ))
        A.append(dict(
            x=sx, y=ST_Y0 - 0.02,
            text=f"<b>{slbl}</b>",
            showarrow=False,
            font=dict(size=9, color=C["dim"], family="mono"),
            xref="x", yref="y", yanchor="top",
        ))

    # ── Figura base ───────────────────────────────────────────────────────────
    fig = go.Figure()
    fig.update_layout(
        shapes=S,
        annotations=A,
        plot_bgcolor=C["panel"],
        paper_bgcolor=C["panel"],
        autosize=True,
        margin=dict(l=0, r=0, t=10, b=10),
        height=210,
        xaxis=dict(domain=[0.05, 0.93],range=[0, 635], visible=False, fixedrange=True),
        yaxis=dict(range=[0, 1],   visible=False, fixedrange=True),
        showlegend=False,
        hovermode="closest",
    )

    # ── Zonas interactivas (scatter invisible para hover y click) ─────────────
    ZONES = [
        ("difusor",   "DIFUSOR",    110,  2),
        ("compresor", "COMPRESOR",  260, 3),
        ("camara",    "CÁMARA CC",  370, 4),
        ("turbina",   "TURBINA",    470, 5),
        ("tobera",    "TOBERA",     630, 9),
    ]
    zone_colors = {
        "difusor":   "#4a7abf",
        "compresor": "#1a4d8f",
        "camara":    "#b83232",
        "turbina":   "#cc5500",
        "tobera":    "#7055aa",
    }

    for i, (zone_id, label, xc, st) in enumerate(ZONES):
        T_val = _tv(df, st)
        P_val = _pv(df, st)
        t_str = f"{T_val:.1f} K"   if T_val is not None else "—"
        p_str = f"{P_val:.2f} kPa" if P_val is not None else "—"
        col   = zone_colors[zone_id]
 
        # ── Cable ficticio: línea de puntos desde el componente hasta el borde ──
        # Usamos paper x para el extremo derecho (1.0 = borde del plot)
        # y data x para el origen en el componente.
        cable_y_val = 0.15 + i * 0.14   # escalonado verticalmente: 0.15, 0.29, 0.43, 0.57, 0.71
        # Segmento horizontal desde componente hasta borde derecho del diagrama
        S.append(dict(
            type="line",
            x0=xc, x1=635,
            y0=cable_y_val, y1=cable_y_val,
            line=dict(color=col, width=1, dash="dot"),
            layer="above",
        ))
        # Punto de sensor en el componente
        S.append(dict(
            type="circle",
            x0=xc - 4, x1=xc + 4,
            y0=cable_y_val - 0.02, y1=cable_y_val + 0.02,
            fillcolor=col,
            line=dict(color=col, width=1),
            layer="above",
        ))
        # Etiqueta del cable en el borde
        A.append(dict(
            x=635, y=cable_y_val,
            text=f"<b style='color:{col}'>●</b>",
            showarrow=False,
            font=dict(size=10, color=col, family=C["mono"]),
            xref="x", yref="y",
            xanchor="left",
        ))
 
        fig.add_trace(go.Scatter(
            x=[xc], y=[cable_y_val],
            mode="markers",
            marker=dict(size=36, color="rgba(0,0,0,0)",
                        line=dict(color="rgba(0,0,0,0)", width=0)),
            customdata=[[zone_id, label, st, t_str, p_str]],
            hoverinfo="none",
            hovertemplate=None,
            name=zone_id,
            showlegend=False,
        ))
 
    return dcc.Graph(
        id="onespool-diagram",
        figure=fig,
        config={"displayModeBar": False, "staticPlot": False},
        style={"height": "100%", "width": "100%"},
    )

# ══════════════════════════════════════════════════════════════════════════════
#  MOTORES 2-4  (version original: cajas rectangulares, sin cambios)
# ══════════════════════════════════════════════════════════════════════════════

def _hex_rgba(h, a=0.12):
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{a})"


def _box(S, A, x0, x1, y0, y1, color, label):
    S.append(dict(
        type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
        fillcolor=_hex_rgba(color, 0.15),
        line=dict(color=color, width=1.5),
        layer="below",
    ))
    A.append(dict(
        x=(x0+x1)/2, y=(y0+y1)/2,
        text=f"<b>{label}</b>",
        showarrow=False,
        font=dict(size=9, color=color, family="Share Tech Mono"),
        xref="x", yref="y",
    ))


def _station_orig(S, A, x, label, t_val, p_val, cy=0.5):
    S.append(dict(
        type="line", x0=x, x1=x, y0=cy-0.28, y1=cy+0.28,
        line=dict(color=C["border"], width=0.8, dash="dot"),
    ))
    A.append(dict(
        x=x, y=cy+0.35, text=f"T<sub>t{label}</sub>",
        showarrow=False,
        font=dict(size=8, color=C["dim"], family="Share Tech Mono"),
        xref="x", yref="y",
    ))
    if t_val is not None:
        A.append(dict(
            x=x, y=cy+0.47, text=f"{t_val:.0f} K",
            showarrow=False,
            font=dict(size=7, color=C["accent"], family="Share Tech Mono"),
            xref="x", yref="y",
        ))
    if p_val is not None:
        A.append(dict(
            x=x, y=cy-0.40, text=f"{p_val:.0f} kPa",
            showarrow=False,
            font=dict(size=7, color=C["dim"], family="Share Tech Mono"),
            xref="x", yref="y",
        ))


def _build_original(engine_type, df):
    CK = {
        "intake": "#5a8abf", "fan": "#1a7a5a", "lpc": "#2a70b0",
        "hpc":    C["accent"], "comb": C["accent2"], "hpt": "#cc6600",
        "lpt":    C["warn"],   "nozzle": "#7055aa",   "prop": C["accent3"],
    }
    cy = 0.5
    S, A = [], []

    S.append(dict(type="line", x0=10, x1=790, y0=cy, y1=cy,
                  line=dict(color=C["border"], width=0.5, dash="dot")))

    if engine_type == "TwinSpoolEngine":
        _box(S, A, 25,  95,  cy-0.14, cy+0.14, CK["intake"], "INTAKE")
        _box(S, A, 100, 190, cy-0.20, cy+0.20, CK["lpc"],    "LPC")
        _box(S, A, 195, 310, cy-0.28, cy+0.28, CK["hpc"],    "HPC")
        _box(S, A, 315, 445, cy-0.22, cy+0.22, CK["comb"],   "COMB")
        _box(S, A, 450, 545, cy-0.26, cy+0.26, CK["hpt"],    "HPT")
        _box(S, A, 550, 645, cy-0.20, cy+0.20, CK["lpt"],    "LPT")
        _box(S, A, 650, 725, cy-0.14, cy+0.14, CK["nozzle"], "NOZ")
        stations = [(25,"0",0),(100,"2",2),(195,"2.5",2.5),(315,"3",3),
                    (450,"4",4),(550,"4.5",4.5),(650,"5",5),(725,"9",9)]

    elif engine_type == "SingleFlowTurbofan":
        _box(S, A, 25,  110, cy-0.32, cy+0.32, CK["fan"],    "FAN")
        _box(S, A, 115, 235, cy-0.32, cy-0.12, CK["lpc"],    "BYPASS")
        _box(S, A, 115, 235, cy-0.10, cy+0.22, CK["hpc"],    "HPC")
        _box(S, A, 240, 370, cy-0.18, cy+0.18, CK["comb"],   "COMB")
        _box(S, A, 375, 470, cy-0.20, cy+0.20, CK["hpt"],    "HPT")
        _box(S, A, 475, 575, cy-0.26, cy+0.26, CK["lpt"],    "LPT")
        _box(S, A, 580, 670, cy-0.30, cy+0.30, CK["nozzle"], "NOZ")
        stations = [(25,"0",0),(115,"1.3",2),(240,"3",3),
                    (375,"4",4),(475,"4.5",4.5),(580,"5",5),(670,"8",8)]

    else:  # OneSpoolTurboprop
        _box(S, A, 5,   33,  cy-0.36, cy+0.36, CK["prop"],   "PROP")
        _box(S, A, 38,  110, cy-0.14, cy+0.14, CK["intake"], "INTAKE")
        _box(S, A, 115, 225, cy-0.26, cy+0.26, CK["hpc"],    "COMP")
        _box(S, A, 230, 370, cy-0.22, cy+0.22, CK["comb"],   "COMB")
        _box(S, A, 375, 475, cy-0.24, cy+0.24, CK["hpt"],    "HPT")
        _box(S, A, 480, 580, cy-0.20, cy+0.20, CK["lpt"],    "LPT")
        _box(S, A, 585, 665, cy-0.14, cy+0.14, CK["nozzle"], "NOZ")
        stations = [(38,"0",0),(115,"2",2),(230,"3",3),
                    (375,"4",4),(480,"4.5",4.5),(585,"5",5),(665,"9",9)]

    for sx, slbl, st_id in stations:
        _station_orig(S, A, sx, slbl, _tv(df, st_id), _pv(df, st_id), cy)

    fig = go.Figure()
    fig.update_layout(
        shapes=S, annotations=A,
        plot_bgcolor=C["panel"], paper_bgcolor=C["panel"],
        margin=dict(l=0, r=0, t=0, b=0),
        height=200,
        xaxis=dict(range=[0, 800], visible=False, fixedrange=True),
        yaxis=dict(range=[0, 1],   visible=False, fixedrange=True),
        showlegend=False,
    )
    return dcc.Graph(
        figure=fig,
        config={"displayModeBar": False, "staticPlot": True},
        style={"height": "100%", "width": "100%"},
    )


# ══════════════════════════════════════════════════════════════════════════════
#  API PUBLICA
# ══════════════════════════════════════════════════════════════════════════════

def build_engine_diagram(engine_type: str, df=None):
    """
    Retorna dcc.Graph con el esquema del motor.

    engine_type : "OneSpoolEngine" | "TwinSpoolEngine" |
                  "SingleFlowTurbofan" | "OneSpoolTurboprop"
    df          : DataFrame con indice = station_id, columnas T [K] y P [Pa]
                  Puede ser None para uso estatico en las tarjetas del menu.
    """
    if engine_type == "OneSpoolEngine":
        return _build_onespool(df)
    return _build_original(engine_type, df)

# ══════════════════════════════════════════════════════════════════════════════
#  PANTALLA 1 — MENÚ
# ══════════════════════════════════════════════════════════════════════════════

def menu_engine_card(eid, cfg):
    return html.Div([
        html.Div(style={"height":"3px","background":cfg["color"],"marginBottom":"5px"}),
        html.Div(cfg["label"], style={"fontFamily":C["mono"],"fontWeight":"900","fontSize":"1.9vw", # Turborreactor monoeje
                                       "letterSpacing":"2px","textTransform":"uppercase",
                                       "color":C["text"],"marginBottom":"2px","color":cfg["color"]}),
        html.Div(cfg["subtitle"], style={"fontFamily":C["mono"],"fontSize":"1.2vw", # Single Spool Turbojet
                                          "color":cfg["color"],
                                          "marginBottom":"12px"}),
        html.Div(html.Img(src="/assets/onespool2.svg", style={"width":"100%"})),                  
        html.Button("DISEÑO", id=f"btn-select-{eid}", n_clicks=0, style={
            "background":"transparent","border":f"1px solid {cfg['color']}",
            "color":cfg["color"],"fontFamily":C["head"],"fontWeight":"700",
            "fontSize":"13px","letterSpacing":"3px","padding":"8px 0",
            "cursor":"pointer","width":"100%","textTransform":"uppercase",}),
        
    ], id=f"menu-card-{eid}", style={
        "background":C["panel"],"border":f"1px solid {C['border']}",
        "padding":"22px 20px","height":"100%",
    })


menu_screen = html.Div([
    html.Div([
        html.Div([
            #html.Div("REF-DOC-SIM-001", style={"fontFamily":C["mono"],"fontSize":"9px",
            #                                    "color":C["border2"],"letterSpacing":"4px",
            #                                    "marginBottom":"10px"}),
            html.Div("PROP-LAB", style={"fontFamily":C["head"],"fontWeight":"800",
                                        "fontSize":"3.6vw","letterSpacing":"4px",
                                        "color":C["accent"],"lineHeight":"1","marginBottom":"8px","marginTop":"20px"}),
            html.Div("SIMULADOR DE AERORREACTORES", style={"fontFamily":C["mono"],
                                                            "fontSize":"1vw","color":C["dim"],
                                                            "letterSpacing":"6px","marginBottom":"1.2vw"}),
            #html.P("Selecciona el tipo de motor para comenzar la fase de diseño",
            #       style={"fontFamily":C["head"],"fontWeight":"300","fontSize":"1vepx","marginTop":"20px","color":C["dim"]}),
        ], style={"textAlign":"center","background":C["bg"]}),
    ]),
    dbc.Container(
    html.Div([menu_engine_card(eid, cfg)
            for eid, cfg in ENGINE_CONFIGS.items()],
        style={"display": "grid","gridTemplateColumns": "repeat(2, 1fr)","gap": "20px",
            "justifyContent": "center","maxWidth": "2000px","margin": "0 auto"}),
    fluid=True,style={"maxWidth": "2000px","margin": "0 auto","padding": "0 5%"}),
    html.Div("PROP-Lab v4.2  ·  components.py  ·  2025", style={
        "textAlign":"center","fontFamily":C["mono"],"fontSize":"14px",
        "color":C["border"],"padding":"32px","marginTop":"16px",
    }),
], id="screen-menu", style={"minHeight":"100vh","background":C["bg"],"backgroundImage":"none",
                              "position":"relative","zIndex":"1"})


# ══════════════════════════════════════════════════════════════════════════════
#  PANTALLA 2 — SIMULADOR
# ══════════════════════════════════════════════════════════════════════════════

def section_head(title):
    return html.Div(title, className="section-head")

all_slider_groups = []
SECTION_LABELS = {
    "sliders_vuelo":  "CONDICIONES DE VUELO",
    "sliders_diseno": "PUNTO DE DISEÑO",
}
for eid, cfg in ENGINE_CONFIGS.items():
    group = []
    for section_key, section_title in SECTION_LABELS.items():
        group.append(section_head(section_title))
        for sid, lbl, mn, mx, dfl, stp in cfg[section_key]:
            group.append(make_slider(sid, lbl, mn, mx, dfl, stp))
    for sid, lbl, mn, mx, dfl, stp in cfg["sliders_comp"]:
        group.append(
            html.Div(
                dcc.Slider(id=f"sl-{sid}", min=mn, max=mx, value=dfl, step=stp,
                           marks=None, tooltip={"always_visible":False}),
                style={"display":"none"}
            )
        )
    all_slider_groups.append(html.Div(group, id=f"sliders-{eid}", style={"display":"none"}))
PANEL_R = {"background":C["panel"],"borderLeft":f"1px solid {C['border']}",
            "paddingLeft":"12px","paddingRight":"12px",
            "overflowY":"auto","height":"calc(100vh - 80px)"}
PANEL_C = {"overflowY":"auto","height":"calc(100vh - 80px)","paddingRight":"0"}

PANEL_INPUTS = {
    "background": C["panel"],
    "border": f"1px solid {C['border']}",
    "paddingTop":"5px","paddingLeft": "10px", "paddingRight": "10px",
    "overflowY": "auto",
    "height": "100vh",
}
PANEL_OUTPUTS_L = {
    "background": C["panel"],
    "border": f"1px solid {C['border']}",
    "paddingLeft": "10px", "paddingRight": "10px",
    "overflowY": "auto",
    "height": "30vh",
}
PANEL_DIAGRAM = {
    "background": C["panel"],
    "border": f"1px solid {C['border']}",
    "paddingLeft": "8px", "paddingRight": "8px",
    "height": "40vh",
    "overflow": "hidden",
}
PANEL_GRAPHS = {
    "background": C["panel"],
    "border": f"1px solid {C['border']}",
    "paddingLeft": "8px", "paddingRight": "8px",
    "overflowY": "auto",
    "height": "calc(100vh - 80px)",
}

sim_screen = html.Div([

    # Navbar
    html.Div([
        html.Div([
            html.Button("← MENU", id="btn-back", n_clicks=0),
            html.Span("PROP-Lab", style={"fontFamily":C["head"],"fontWeight":"900",
                                         "fontSize":"25px","letterSpacing":"5px",
                                         "color":C["accent"],"marginLeft":"16px"}),
        ], style={"display":"flex","alignItems":"center"}),
        html.Div([
            html.Span("● LIVE",           className="nav-badge live me-2"),
            html.Span(id="sim-eng-label", className="nav-badge me-2"),
            html.Span("SESION: LAB-04",   className="nav-badge"),
        ], style={"display":"flex","alignItems":"center"}),
    ], className="aerosim-nav"),

    html.Div(id="alert-tit", style={"display":"none"}, className="alert-tit mx-3 mt-2"),

    html.Div([

    # ── COL A (20%) — izquierda: sliders ─────────────────────────────────
    html.Div([
        html.Div([
            html.Div(all_slider_groups),
        ], style=PANEL_INPUTS),
        html.Div(style={"height":"6px"}),
    ], style={"width":"20%","display":"flex","flexDirection":"column",
              "paddingRight":"6px"}),

    # ── COL B (50%) — centro: diagrama + telemetría + métricas ───────────
    html.Div([

        # Panel B1 — título + diagrama
        html.Div([
            html.Div(id="sim-eng-title", className="section-head",
                     style={"padding":"8px 0 4px 0"}),
            html.Div(id="engine-diagram",
                     style={"lineHeight":"0","overflow":"hidden",
                            "height":"calc(35vh - 30px)"}),
        ], style=PANEL_DIAGRAM),

        

        # Panel B3 — métricas + gauges
        html.Div([
            #dbc.Row([
            #    dbc.Col(metric_card("Empuje neto",        "thrust","kN",   "good"), width=4),
            #    dbc.Col(metric_card("Consumo específico", "tsfc",  "mg/Ns",""),     width=4),
            #    dbc.Col(metric_card("Combustible",        "fuel",  "kg/s", "warn"), width=4),
            #], className="g-1 mt-1"),
            dbc.Row([
                dbc.Col(html.Div(
                    dcc.Graph(id="graph-gauge-thrust", config={"displayModeBar":False},
                              style={"height":"100%","width":"100%"}),
                    style={"aspectRatio":"1/1","maxWidth":"220px","margin":"0 auto"}),
                width=6),
                dbc.Col(html.Div(
                    dcc.Graph(id="graph-gauge-epr", config={"displayModeBar":False},
                              style={"height":"100%","width":"100%"}),
                    style={"aspectRatio":"1/1","maxWidth":"220px","margin":"0 auto"}),
                width=6),
            ], className="g-0 mt-1"),
        ], style={"paddingTop":"4px"}),

    ], style={"width":"50%","paddingLeft":"6px","paddingRight":"6px",
              "display":"flex","flexDirection":"column"}),

    # ── COL C (30%) — derecha: selector + gráficas + actuaciones ─────────
    html.Div([

        # Selector de gráfica
        html.Div([
            html.Div("Gráficas", className="section-head mt-2"),
            html.Div([
                html.Button("Ciclo T-s",      id="btn-chart-ts",   n_clicks=0, className="chart-btn chart-btn-active"),
                html.Button("Mapa Compresor", id="btn-chart-comp", n_clicks=0, className="chart-btn"),
            ], className="chart-selector mb-1"),
        ]),

        # Gráficas
        html.Div([
            html.Div(dcc.Graph(id="graph-ts",   config={"displayModeBar":False},
                               style={"height":"260px"}),
                     id="wrap-ts", className="graph-card mb-1"),
            html.Div(dcc.Graph(id="graph-comp", config={"displayModeBar":False},
                               style={"height":"260px"}),
                     id="wrap-comp", className="graph-card mb-1",
                     style={"display":"none"}),
            # Telemetría oculta — ID necesario para el callback
            html.Div(html.Table(id="tele-table", className="tele-table"),
                     style={"display":"none"}),
        ], style=PANEL_GRAPHS),

        # Panel B2 — telemetría del componente clicado
        html.Div([
            html.Div("TELEMETRÍA", className="section-head",
                     style={"padding":"8px 0 4px 0"}),
            html.Div(id="comp-tele-panel"),
        ], style=PANEL_OUTPUTS_L),

        # Botón ACTUACIONES
        html.Button("▸  ACTUACIONES", id="btn-actuaciones", n_clicks=0,
                    className="btn-actuaciones mt-3"),

    ], style={"width":"30%","paddingLeft":"6px",
              "display":"flex","flexDirection":"column"}),

], style={
    "display":"flex","flexDirection":"row",
    "padding":"6px 10px",
    "height":"calc(100vh - 80px)",
    "overflow":"hidden",
}),

html.Div([
    html.Span([html.Span("FISICA:", className="lbl"), " components.py"]),
    html.Span([html.Span("UI:",     className="lbl"), " app.py"]),
    html.Span("PROP-Lab v4.2 · 2025", style={"marginLeft":"auto"}),
], className="sim-footer"),

], id="screen-sim", style={"display":"none","minHeight":"100vh","background":C["bg"]})


# ══════════════════════════════════════════════════════════════════════════════
#  PANTALLA ACTUACIONES
# ══════════════════════════════════════════════════════════════════════════════

_BTN_BACK_STYLE = {
    "background":"transparent","border":"1px solid var(--border2)",
    "color":"var(--dim)","fontFamily":"var(--head)","fontWeight":"700",
    "fontSize":"10px","letterSpacing":"2px","padding":"4px 12px","cursor":"pointer",
    "transition":"all 0.15s",
}

def _act_slider(slider_id, label, mn, mx, val, step, marks):
    return html.Div([
        html.Div([
            html.Span(label, style={"fontSize":"11px","color":C["dim"],
                                    "fontFamily":C["head"],"letterSpacing":"1px"}),
            html.Span(id=f"act-val-{slider_id}", style={"fontFamily":C["mono"],
                                                         "fontSize":"11px","color":C["accent"]}),
        ], style={"display":"flex","justifyContent":"space-between","marginBottom":"3px"}),
        dcc.Slider(id=f"act-sl-{slider_id}", min=mn, max=mx, value=val, step=step,
                   marks=marks,
                   tooltip={"always_visible":False},
                   className="act-slider"),
    ], style={"padding":"10px 14px 14px","background":C["panel"],
              "border":"1px solid "+C["border"],"marginBottom":"8px"})

act_screen = html.Div([
    dbc.Navbar([
        html.Span("PROP-Lab", className="aerosim-logo"),
        html.Div([
            html.Span(id="act-eng-label", className="nav-badge"),
            html.Span("ACTUACIONES", className="nav-badge live"),
            html.Button("← DISEÑO", id="btn-act-back", n_clicks=0,
                        style=_BTN_BACK_STYLE),
        ], style={"display":"flex","gap":"10px","alignItems":"center"}),
    ], className="aerosim-nav", dark=False),

    dbc.Container([
        dbc.Row([
            # ── Izquierda: Empuje vs Mach (Despegue) ──────────────────
            dbc.Col([
                html.Div("Empuje vs Mach  —  Despegue", className="section-head mt-3"),
                _act_slider("t0", "T₀ [°C]", -40, 50, 15, 1,
                            {-40:"-40°", -20:"-20°", 0:"0°", 15:"ISA", 35:"35°", 50:"50°"}),
                html.Div(dcc.Graph(id="graph-act-thrust",
                                   config={"displayModeBar":False}),
                         className="graph-card"),
            ], width=6),
            # ── Derecha: TSFC vs Mach (Crucero) ───────────────────────
            dbc.Col([
                html.Div("Empuje vs Mach  —  Crucero", className="section-head mt-3"),
                _act_slider("alt", "Altitud [m]", 0, 13000, 10000, 100,
                            {0:"0", 3000:"3 km", 6000:"6 km",
                             10000:"10 km", 13000:"13 km"}),
                html.Div(dcc.Graph(id="graph-act-tsfc",
                                   config={"displayModeBar":False}),
                         className="graph-card"),
            ], width=6),
        ], className="mt-1 g-2"),
    ], fluid=True, style={"padding":"0 12px"}),

    html.Div([
        html.Span([html.Span("FISICA:", className="lbl"), " components.py"]),
        html.Span([html.Span("UI:",     className="lbl"), " app.py"]),
        html.Span("PROP-Lab v4.2 · 2025", style={"marginLeft":"auto"}),
    ], className="sim-footer"),

], id="screen-actuaciones",
   style={"display":"none","minHeight":"100vh","background":C["bg"]})


# ══════════════════════════════════════════════════════════════════════════════
#  LAYOUT RAÍZ
# ══════════════════════════════════════════════════════════════════════════════

app.layout = html.Div([
    dcc.Store(id="active-engine", data=None),
    dcc.Store(id="eta-override-store", data={}),
    menu_screen,
    sim_screen,
    act_screen,
], style={"background":C["bg"]})


# ══════════════════════════════════════════════════════════════════════════════
#  CALLBACKS
# ══════════════════════════════════════════════════════════════════════════════

@app.callback(
    Output("active-engine",  "data"),
    Output("screen-menu",    "style"),
    Output("screen-sim",     "style"),
    Output("sim-eng-label",  "children"),
    Output("sim-eng-title",  "children"),
    *[Output(f"sliders-{eid}", "style") for eid in ENGINE_CONFIGS],
    *[Input(f"btn-select-{eid}", "n_clicks") for eid in ENGINE_CONFIGS],
    Input("btn-back", "n_clicks"),
    State("active-engine", "data"),
    prevent_initial_call=True,
)
def navigate(*args):
    n = len(ENGINE_CONFIGS)
    current   = args[n + 1]
    triggered = ctx.triggered_id or ""

    if triggered == "btn-back":
        return (
            current,
            {"minHeight":"100vh","background":C["bg"],"position":"relative","zIndex":"1"},
            {"display":"none","minHeight":"100vh","background":C["bg"]},
            "", "",
            *[{"display":"none"}] * n,
        )

    new_engine = next((eid for eid in ENGINE_CONFIGS
                       if triggered == f"btn-select-{eid}"), None)
    if not new_engine:
        raise dash.exceptions.PreventUpdate

    cfg = ENGINE_CONFIGS[new_engine]
    slider_styles = [
        {"display":"block"} if eid == new_engine else {"display":"none"}
        for eid in ENGINE_CONFIGS
    ]
    return (
        new_engine,
        {"display":"none"},
        {"minHeight":"100vh","background":C["bg"]},
        cfg["label"].upper(),
        f"{cfg['label'].upper()}",
        *slider_styles,
    )


@app.callback(
    Output("wrap-ts",        "style"),
    Output("wrap-comp",      "style"),
    Output("btn-chart-ts",   "className"),
    Output("btn-chart-comp", "className"),
    Input("btn-chart-ts",    "n_clicks"),
    Input("btn-chart-comp",  "n_clicks"),
    prevent_initial_call=True,
)
def select_chart(_n_ts, _n_comp):
    if ctx.triggered_id == "btn-chart-comp":
        return {"display":"none"}, {}, "chart-btn", "chart-btn chart-btn-active"
    return {}, {"display":"none"}, "chart-btn chart-btn-active", "chart-btn"


# Mapa sid → step, para decidir el formato del label
_SLIDER_STEP = {
    sid: stp
    for cfg in ENGINE_CONFIGS.values()
    for section in ("sliders_vuelo", "sliders_diseno", "sliders_comp")
    for sid, _, _, _, _, stp in cfg[section]
}

@app.callback(
    *[Output(f"val-{sid}", "children") for sid in ALL_LABEL_IDS],
    *[Input(f"sl-{sid}",   "value")    for sid in ALL_LABEL_IDS],
)
def update_labels(*vals):
    out = []
    for sid, v in zip(ALL_LABEL_IDS, vals):
        if v is None:
            out.append(""); continue
        stp = _SLIDER_STEP.get(sid, 1)
        if stp >= 1:          # enteros (T en K, G, W_h, T0 en C)
            out.append(f"{v:.0f}")
        elif stp >= 0.1:      # un decimal (OPR, BPR, P0)
            out.append(f"{v:.1f}")
        else:                 # dos decimales (Mach, etas)
            out.append(f"{v:.2f}")
    return out


@app.callback(
    #Output("m-thrust",        "children"),
   # Output("m-tsfc",          "children"),
    #Output("m-fuel",          "children"),
    Output("graph-ts",           "figure"),
    Output("graph-comp",         "figure"),
    Output("graph-gauge-thrust", "figure"),
    Output("graph-gauge-epr",    "figure"),
    Output("tele-table",         "children"),
    Output("alert-tit",       "children"),
    Output("alert-tit",       "style"),
    Output("engine-diagram",  "children"),
    Input("active-engine", "data"),
    Input("eta-override-store",  "data"),
    *[Input(f"sl-{sid}", "value") for sid in ALL_SLIDER_IDS],
)
def run_simulation(engine_type, eta_overrides, *all_vals):
    if not engine_type:
        raise dash.exceptions.PreventUpdate

    cfg   = ENGINE_CONFIGS[engine_type]
    color = cfg["color"]

    # Parámetros del motor activo — recorre las 3 secciones
    p = {}
    for section in ("sliders_vuelo", "sliders_diseno", "sliders_comp"):
        for sid, _, _, _, default, _ in cfg[section]:
            idx = ALL_SLIDER_IDS.index(sid)
            p[sid] = all_vals[idx] if all_vals[idx] is not None else default
        if eta_overrides is None:
            eta_overrides = {}
        if engine_type == "OneSpoolEngine":
            for sid, val in eta_overrides.items():
                if val is not None and sid in p:
                    p[sid] = float(val)
    # Error path
    def _err(msg_str):
        ef = go.Figure().update_layout(**_plot_layout("Error"))
        et = [html.Tr([html.Td("Error", className="tele-key"),
                       html.Td(msg_str[:80], className="tele-val")])]
        ed = html.Div(msg_str[:120], style={"padding":"8px","fontFamily":C["mono"],
                                             "fontSize":"10px","color":C["accent2"]})
        return  [ef, ef, ef, ef, et, msg_str, {"display":"block"}, ed]

    try:
        r = cfg["runner"](p)
    except Exception as e:
        return _err(str(e))

    tit_val = r["Tt4_K"]

    # Métricas
    metrics = [
        f"{r['thrust_kN']:.2f}",
        f"{r['TSFC_mg']:.3f}",
        f"{r['fuel_kg_s']:.4f}",
    ]

    # ── Diagrama T-s ──────────────────────────────────────────────────────
    # Entropía relativa: Δs = cp·ln(T2/T1) - R·ln(P2/P1)  [kJ/kg·K]
    # Estaciones: 0(estática) → 0t(ram) → 2t(dif) → 3t(comp) → 4t(cc)
    #             → 5t(turb) → 9(tobera salida) → 0(cierre)
    _cp = 1.0043   # kJ/kg·K
    _R  = 0.2871   # kJ/kg·K

    def _ds(T1, P1, T2, P2):
        """Incremento de entropía entre dos estados [kJ/kg·K]."""
        return _cp * np.log(max(T2,1)/max(T1,1)) - _R * np.log(max(P2,0.001)/max(P1,0.001))

    df_st = r.get("df")

    # Recoge T y P de cada estación desde el DataFrame de simulación
    def _st(station):
        try:
            T = float(df_st.loc[station, "T"])
            P = float(df_st.loc[station, "P"]) / 1000   # Pa → kPa
            return T, P
        except Exception:
            return None, None

    T0s,  P0s  = r["T0_K"],  r["P0_kPa"]    # estática entrada (0)
    T0t,  P0t  = _st(0)                       # estación 0 en df = 2t (difusor entrada)
    T2t,  P2t  = _st(2)                       # salida difusor
    T3t,  P3t  = _st(3)                       # salida compresor
    T4t,  P4t  = _st(4)                       # salida cámara (TIT)
    T5t,  P5t  = _st(5)                       # salida turbina
    T9,   P9   = _st(9)                       # salida tobera (estática)

    # Fallback si alguna estación no está en el df
    if T2t  is None: T2t,  P2t  = r["T0_K"],   r["Pt0_kPa"]
    if T3t  is None: T3t,  P3t  = r["Tt3_K"],  r["Pt3_kPa"]
    if T4t  is None: T4t,  P4t  = r["Tt4_K"],  r["Pt3_kPa"]
    if T5t  is None: T5t,  P5t  = r["Tt5_K"],  r["Pt3_kPa"]
    if T9   is None: T9,   P9   = r["Tt5_K"],  r["P0_kPa"]

    # Entropía acumulada [kJ/kg·K] — s=0 en el estado estático de entrada
    s0s  = 0.0
    s0t  = s0s + _ds(T0s, P0s, T2t, P2t)      # ram: compresión isentrópica ideal
    s2t  = s0t + _ds(T2t, P2t, T2t, P2t)      # difusor (mismo punto, sin irreversibilidad adicional)
    s3t  = s2t + _ds(T2t, P2t, T3t, P3t)      # compresor (irreversible → s aumenta)
    s4t  = s3t + _ds(T3t, P3t, T4t, P4t)      # cámara combustión (isobara → s sube por calor)
    s5t  = s4t + _ds(T4t, P4t, T5t, P5t)      # turbina (irreversible → s aumenta un poco)
    s9   = s5t + _ds(T5t, P5t, T9,  P9)       # expansión en tobera

    # Puntos del ciclo (cierra en 0s)
    ss = [s0s,  s0t,  s3t,  s4t,  s5t,  s9,   s0s]
    Ts = [T0s,  T2t,  T3t,  T4t,  T5t,  T9,   T0s]
    labels = ["[0] Entrada", "[2t] Difusor", "[3t] Compresor",
              "[4t] TIT", "[5t] Turbina", "[9] Tobera", ""]

    fig_ts = go.Figure()
    # Área del ciclo
    fig_ts.add_trace(go.Scatter(
        x=ss, y=Ts, mode="lines",
        line=dict(color=color, width=0), fill="toself",
        fillcolor=_rgba(color, 0.10),
        showlegend=False, hoverinfo="skip",
    ))
    # Línea del ciclo
    fig_ts.add_trace(go.Scatter(
        x=ss, y=Ts,
        mode="lines+markers",
        line=dict(color=color, width=1.5),
        marker=dict(
            size=7, symbol="square",
            color=[C["accent"], C["accent"], C["accent"],
                   C["accent2"], C["warn"], C["accent3"], C["accent"]],
            line=dict(color=C["panel"], width=1.5),
        ),
        hovertemplate="s=%{x:.4f} kJ/kg·K<br>T=%{y:.1f} K<extra></extra>",
        showlegend=False,
    ))
    # Etiquetas de estación
    for sx, tx, lbl in zip(ss[:-1], Ts[:-1], labels[:-1]):
        fig_ts.add_annotation(
            x=sx, y=tx, text=lbl,
            font=dict(color=C["dim"], size=8, family=C["mono"]),
            showarrow=False, yshift=13,
            bgcolor=C["panel"], bordercolor=C["border"],
            borderwidth=1, borderpad=3,
        )
    fig_ts.update_layout(**_plot_layout("Diagrama T-s  [kJ/kg·K]"))
    fig_ts.update_xaxes(**_ax("Entropía relativa  s  [kJ/kg·K]"))
    fig_ts.update_yaxes(**_ax("Temperatura  T  [K]"))



    # ── Línea de funcionamiento del compresor ─────────────────────────────
    # Barrido de OPR manteniendo todos los demás parámetros fijos
    # Eje X: flujo másico reducido  W√T/P (proporcional a G·√T2t/P2t)
    # Eje Y: relación de presiones del compresor
    sweep_p = cfg["sweep_base"](p)
    opr_key = "pi_lpc" if engine_type == "TwinSpoolEngine" else "pi_23"
    opr_cur = r.get("opr", p.get("os_pi", p.get("ts_pilpc", p.get("tf_pi", p.get("tp_pi", 10)))))
    T2t = r["T0_K"]; P2t = r["Pt0_kPa"] * 1000

    oprs   = np.linspace(1.5, 50, 60)
    w_red  = []   # flujo másico reducido (u.a.)
    pi_pts = []
    for o in oprs:
        try:
            if engine_type == "TwinSpoolEngine":
                pp = {**sweep_p, "pi_lpc": max(1.1, o**0.4), "pi_hpc": max(1.1, o**0.6)}
            else:
                pp = {**sweep_p, opr_key: o}
            cls = ENGINE_CONFIGS[engine_type]["engine_cls"]
            rr  = cls().simulate(**pp)
            # Flujo másico reducido: G·√(T2t) / P2t  (en u.a.)
            T2_loc = rr["T0_K"]; P2_loc = rr["Pt0_kPa"] * 1000
            G_loc  = sweep_p.get("G", 20)
            w_red.append(G_loc * np.sqrt(T2_loc) / max(P2_loc, 1))
            pi_pts.append(o)
        except Exception:
            pass

    # Punto de funcionamiento actual
    G_cur  = sweep_p.get("G", 20)
    wred_cur = G_cur * np.sqrt(T2t) / max(P2t, 1)
    pi_cur   = opr_cur if engine_type != "TwinSpoolEngine" else p.get("ts_pilpc", 1.6)

    fig_comp = go.Figure()
    # Curva de la línea de funcionamiento
    if w_red:
        fig_comp.add_trace(go.Scatter(
            x=w_red, y=pi_pts, mode="lines",
            line=dict(color=color, width=2),
            name="Linea funcionamiento",
            hovertemplate="W_red=%{x:.3f}<br>π=%{y:.2f}<extra></extra>",
        ))
    # Punto de diseño actual
    fig_comp.add_trace(go.Scatter(
        x=[wred_cur], y=[pi_cur], mode="markers",
        marker=dict(size=10, color=C["accent2"], symbol="diamond",
                    line=dict(color=C["text"], width=1.5)),
        name="Pto. diseño",
        hovertemplate="W_red=%{x:.3f}<br>π=%{y:.2f}<extra></extra>",
    ))
    # Líneas de margen de surge (zona de inestabilidad, ~15% sobre la línea)
    if w_red:
        w_surge = [w * 0.85 for w in w_red]
        fig_comp.add_trace(go.Scatter(
            x=w_surge, y=pi_pts, mode="lines",
            line=dict(color=C["accent2"], width=1, dash="dash"),
            name="Limite surge",
            hoverinfo="skip",
        ))
        fig_comp.add_vrect(
            x0=0, x1=min(w_surge),
            fillcolor=_rgba(C["accent2"], 0.07),
            line_width=0, layer="below",
        )
    fig_comp.update_layout(
        **_plot_layout("Linea de funcionamiento  [Compresor]"),
        legend=dict(font=dict(size=8, family=C["mono"], color=C["dim"]),
                    bgcolor="rgba(0,0,0,0)", borderwidth=0,
                    x=0.02, y=0.98),
    )
    fig_comp.update_xaxes(**_ax("Flujo masico reducido  W√T/P  [u.a.]"))
    fig_comp.update_yaxes(**_ax("Relacion de presiones  π"))


    # ── Telemetría con subíndices ─────────────────────────────────────────
    SUB = {"fontSize":"0.72em", "lineHeight":"1"}

    def tele_label(var, station):
        """Celda con Tt4 o Pt4 usando html.Sub"""
        return html.Td(
            [var, html.Sub(f"t{station}", style=SUB)],
            className="tele-key"
        )

    def tele_row(key_el, val, cls=""):
        return html.Tr([
            html.Td(key_el, className="tele-key") if isinstance(key_el, list) else key_el,
            html.Td(val, className=f"tele-val {cls}"),
        ])

    def sep_row(title):
        return html.Tr([html.Td(title, colSpan=2,
            style={"color":C["border2"],"fontSize":"8px","paddingTop":"10px",
                   "fontFamily":C["head"],"letterSpacing":"3px",
                   "fontWeight":"700","textTransform":"uppercase"})])

    df = r.get("df")
    table = []
    if df is not None:
        for station in df.index:
            if station in (0, 1):
                continue
            try:
                Tv  = float(df.loc[station,"T"])
                cls = "hot" if Tv>1200 else ("warn" if Tv>800 else "")
                table.append(html.Tr([
                    tele_label("T", station),
                    html.Td(f"{Tv:.1f} K", className=f"tele-val {cls}"),
                ]))
            except (TypeError, ValueError): pass
            try:
                Pv = float(df.loc[station,"P"])
                table.append(html.Tr([
                    tele_label("P", station),
                    html.Td(f"{Pv/1000:.2f} kPa", className="tele-val"),
                ]))
            except (TypeError, ValueError): pass

    table += [
        sep_row("ACTUACIONES"),
        tele_row(["V", html.Sub("jet",    style=SUB)], f"{r['V_jet']:.1f} m/s",    "good"),
        tele_row(["V", html.Sub("bypass", style=SUB)], f"{r['V_bypass']:.1f} m/s", ""),
        tele_row(["V", html.Sub("0",      style=SUB)], f"{r['V0']:.1f} m/s",        ""),
        tele_row("FAR",                                f"{r['FAR']:.5f}",            ""),
        tele_row("EGT",                                f"{r['EGT']:.0f} K",          "warn"),
        tele_row(["W", html.Sub("eje",    style=SUB)], f"{r['shaft_MW']:.3f} MW",   ""),
        tele_row(["m", html.Sub("core",   style=SUB)], f"{r['m_core']:.2f} kg/s",   ""),
        tele_row(["m", html.Sub("bypass", style=SUB)], f"{r['m_bypass']:.2f} kg/s", ""),
    ]
    if engine_type == "OneSpoolTurboprop":
        table += [
            tele_row(["F", html.Sub("helice",  style=SUB)], f"{r.get('F_helice_kN',0):.2f} kN","good"),
            tele_row(["F", html.Sub("residual",style=SUB)], f"{r.get('F_resid_kN', 0):.2f} kN",""),
        ]

    # ── Alerta TIT ────────────────────────────────────────────────────────
    tit_limit = r.get("tit_limit", 1700)
    if tit_val > tit_limit:
        alert_msg   = f"ADVERTENCIA — TIT {tit_val:.0f} K > LIMITE {tit_limit} K — RIESGO FALLO ALABE"
        alert_style = {"display":"block"}
    else:
        alert_msg, alert_style = "", {"display":"none"}

    # ── Esquema SVG ───────────────────────────────────────────────────────
    diagram = build_engine_diagram(engine_type, r.get("df"))

    # ── Indicadores analógicos (Empuje / EPR) ────────────────────────────
    thrust_val = r["thrust_kN"]
    thrust_max = max(300.0, round(thrust_val * 1.8 / 50) * 50)

    _opr    = max(r.get("opr", r["Pt3_kPa"] / max(r["Pt0_kPa"], 0.001)), 1.0)
    _T4     = max(r["Tt4_K"], 1.0)
    _T5     = max(r["Tt5_K"], 1.0)
    epr_val = max(1.0, min(_opr * (_T5 / _T4) ** 3.5, 4.99))

    def _analog_gauge(value, vmin, vmax, title, suffix, zones, n_major=6):
        """Gauge analógico dibujado con scatter + shapes: cara, arco de colores,
        marcas de escala, aguja con pivote y lectura numérica central."""

        # ── Geometría ────────────────────────────────────────────────────
        # Espacio de coordenadas normalizado [0,1]×[0,1]
        # El arco va de 225° (mín, izq.) a −45° (máx, der.) en sentido horario
        CX, CY   = 0.50, 0.52     # centro del instrumento
        ANG_MIN  = 225.0           # ángulo para vmin (°, sistema antihorario)
        SWEEP    = 270.0           # barrido total del arco (°)
        RB       = 0.44            # radio bisel exterior
        RF       = 0.42            # radio cara
        RO       = 0.40            # borde exterior arco de colores
        RI       = 0.30            # borde interior arco de colores
        RT_OUT   = 0.29            # marcas menores — exterior
        RT_MIN   = 0.26            # marcas menores — interior
        RT_MAJ   = 0.21            # marcas mayores — interior
        RL       = 0.14            # etiquetas de escala
        RN       = 0.34            # longitud aguja
        RTAIL    = 0.055           # contrapeso aguja (cola)

        def a2r(ang_deg):          # grados → radianes
            return np.radians(ang_deg)
        def v2a(v):                # valor → ángulo (decrece hacia la derecha)
            return ANG_MIN - (v - vmin) / (vmax - vmin) * SWEEP
        def xy(ang_deg, r):
            ar = a2r(ang_deg)
            return CX + r * np.cos(ar), CY + r * np.sin(ar)

        shapes, annotations = [], []
        traces = []

        # ── Bisel (anillo exterior) ───────────────────────────────────
        t = np.linspace(0, 2 * np.pi, 160)
        xo = list(CX + RB * np.cos(t));  yo = list(CY + RB * np.sin(t))
        xi = list(CX + RF * np.cos(t[::-1])); yi = list(CY + RF * np.sin(t[::-1]))
        traces.append(go.Scatter(x=xo + xi, y=yo + yi,
                                 fill="toself", fillcolor=C["text"],
                                 line=dict(width=0), mode="lines",
                                 showlegend=False, hoverinfo="skip"))

        # ── Cara del instrumento ──────────────────────────────────────
        traces.append(go.Scatter(x=CX + RF * np.cos(t), y=CY + RF * np.sin(t),
                                 fill="toself", fillcolor=C["panel"],
                                 line=dict(color=C["border2"], width=0.5),
                                 mode="lines", showlegend=False, hoverinfo="skip"))

        # ── Arcos de colores (zonas) ──────────────────────────────────
        for v0, v1, col in zones:
            a0 = v2a(max(v0, vmin));  a1 = v2a(min(v1, vmax))
            # linspace de a0 a a1 va en sentido HORARIO porque a1 < a0
            angs = np.linspace(a2r(a0), a2r(a1), 60)
            xoa = list(CX + RO * np.cos(angs))
            yoa = list(CY + RO * np.sin(angs))
            xia = list(CX + RI * np.cos(angs[::-1]))
            yia = list(CY + RI * np.sin(angs[::-1]))
            traces.append(go.Scatter(x=xoa + xia, y=yoa + yia,
                                     fill="toself", fillcolor=col,
                                     line=dict(width=0), mode="lines",
                                     showlegend=False, hoverinfo="skip"))

        # ── Marcas menores ────────────────────────────────────────────
        for i in range(n_major * 5 + 1):
            v   = vmin + i * (vmax - vmin) / (n_major * 5)
            ang = v2a(v)
            x0, y0 = xy(ang, RT_MIN)
            x1, y1 = xy(ang, RT_OUT)
            shapes.append(dict(type="line", x0=x0, y0=y0, x1=x1, y1=y1,
                               line=dict(color=C["border2"], width=0.7)))

        # ── Marcas mayores + etiquetas ────────────────────────────────
        for i in range(n_major + 1):
            v   = vmin + i * (vmax - vmin) / n_major
            ang = v2a(v)
            x0, y0 = xy(ang, RT_MAJ)
            x1, y1 = xy(ang, RT_OUT)
            shapes.append(dict(type="line", x0=x0, y0=y0, x1=x1, y1=y1,
                               line=dict(color=C["dim"], width=1.8)))
            xl, yl = xy(ang, RL)
            lbl = (f"{v:.1f}" if (vmax - vmin) < 5
                   else f"{int(round(v))}")
            annotations.append(dict(x=xl, y=yl, text=lbl, showarrow=False,
                                    font=dict(size=8, family=C["mono"],
                                              color=C["dim"])))

        # ── Aguja ─────────────────────────────────────────────────────
        needle_ang = v2a(max(vmin, min(value, vmax)))
        xn, yn   = xy(needle_ang, RN)
        xt, yt   = xy(needle_ang + 180, RTAIL)
        # Sombra de la aguja (desplazada ligeramente)
        shapes.append(dict(type="line",
                           x0=xt + 0.004, y0=yt - 0.004,
                           x1=xn + 0.004, y1=yn - 0.004,
                           line=dict(color="rgba(0,0,0,0.15)", width=3)))
        # Aguja principal
        shapes.append(dict(type="line",
                           x0=xt, y0=yt, x1=xn, y1=yn,
                           line=dict(color=C["accent2"], width=2.2)))

        # ── Pivote central ────────────────────────────────────────────
        traces.append(go.Scatter(
            x=[CX], y=[CY], mode="markers",
            marker=dict(size=11, color=C["accent"],
                        line=dict(color=C["panel"], width=2.5)),
            showlegend=False, hoverinfo="skip"))

        # ── Valor numérico ─────────────────────────────────────────────
        annotations.append(dict(
            x=CX, y=CY - 0.19,
            text=f"{value:.1f}{suffix}",
            showarrow=False,
            font=dict(size=15, family=C["mono"], color=C["accent"])))

        # ── Título ────────────────────────────────────────────────────
        annotations.append(dict(
            x=CX, y=0.05,
            text=title,
            showarrow=False,
            font=dict(size=9, family=C["head"], color=C["dim"])))

        # ── Figura final ──────────────────────────────────────────────
        fig = go.Figure(data=traces)
        fig.update_layout(
            shapes=shapes,
            annotations=annotations,
            paper_bgcolor=C["bg"],
            plot_bgcolor=C["bg"],
            xaxis=dict(range=[0, 1], showgrid=False, zeroline=False,
                       showticklabels=False, fixedrange=True),
            yaxis=dict(range=[0, 1], showgrid=False, zeroline=False,
                       showticklabels=False, fixedrange=True,
                       scaleanchor="x", scaleratio=1),
            margin=dict(l=2, r=2, t=2, b=2),
            showlegend=False,
            dragmode=False,
        )
        return fig

    fig_gauge_thrust = _analog_gauge(
        thrust_val, 0, thrust_max,
        "EMPUJE", " kN",
        [(0,               thrust_max * 0.5,  "rgba(26,102,68,0.18)"),
         (thrust_max * 0.5, thrust_max * 0.8, "rgba(26,77,143,0.14)"),
         (thrust_max * 0.8, thrust_max,       "rgba(184,50,50,0.22)")],
    )
    fig_gauge_epr = _analog_gauge(
        epr_val, 1.0, 5.0,
        "EPR", "",
        [(1.0, 2.2, "rgba(26,77,143,0.14)"),
         (2.2, 3.8, "rgba(26,102,68,0.18)"),
         (3.8, 5.0, "rgba(184,50,50,0.22)")],
        n_major=4,
    )

    return [fig_ts, fig_comp, fig_gauge_thrust, fig_gauge_epr,
                      table, alert_msg, alert_style, diagram]


# ── Navegación sim ↔ actuaciones ─────────────────────────────────────────────
@app.callback(
    Output("screen-sim",         "style", allow_duplicate=True),
    Output("screen-actuaciones", "style"),
    Output("act-eng-label",      "children"),
    Input("btn-actuaciones",     "n_clicks"),
    Input("btn-act-back",        "n_clicks"),
    State("active-engine",       "data"),
    prevent_initial_call=True,
)
def nav_actuaciones(_n_fwd, _n_back, engine_type):
    _show = {"minHeight":"100vh","background":C["bg"]}
    _hide = {"display":"none","minHeight":"100vh","background":C["bg"]}
    lbl   = ENGINE_CONFIGS[engine_type]["label"].upper() if engine_type else ""
    if ctx.triggered_id == "btn-actuaciones":
        return _hide, _show, lbl
    return _show, _hide, lbl


# ── Labels reactivos de los sliders de actuaciones ───────────────────────────
@app.callback(
    Output("act-val-t0",  "children"),
    Output("act-val-alt", "children"),
    Input("act-sl-t0",    "value"),
    Input("act-sl-alt",   "value"),
)
def act_slider_labels(t0, alt):
    return (f"{t0:+.0f} °C" if t0 is not None else "—",
            f"{int(alt):,} m  ({alt/1000:.1f} km)" if alt is not None else "—")


# ── Cálculo de curvas de actuación ────────────────────────────────────────────
@app.callback(
    Output("graph-act-thrust", "figure"),
    Output("graph-act-tsfc",   "figure"),
    Input("btn-actuaciones",   "n_clicks"),
    Input("act-sl-t0",         "value"),
    Input("act-sl-alt",        "value"),
    State("active-engine",     "data"),
    *[State(f"sl-{sid}", "value") for sid in ALL_SLIDER_IDS],
    prevent_initial_call=True,
)
def compute_actuaciones(_n, t0_c, alt_m, engine_type, *all_vals):
    if not engine_type:
        raise dash.exceptions.PreventUpdate

    cfg   = ENGINE_CONFIGS[engine_type]
    color = cfg["color"]
    cls   = cfg["engine_cls"]

    # Parámetros del punto de diseño
    p = {}
    for section in ("sliders_vuelo", "sliders_diseno", "sliders_comp"):
        for sid, _, _, _, default, _ in cfg[section]:
            idx = ALL_SLIDER_IDS.index(sid)
            p[sid] = all_vals[idx] if all_vals[idx] is not None else default
    base = cfg["sweep_base"](p)

    # Rango de Mach según tipo de motor
    mach_max = {"OneSpoolTurboprop": 0.7,
                "SingleFlowTurbofan": 1.0}.get(engine_type, 2.0)
    machs = np.linspace(0, mach_max, 45)

    t0_k  = (t0_c  if t0_c  is not None else 15) + 273.15
    alt   = alt_m if alt_m is not None else 10000
    T_cr, P_cr = _isa(alt)

    def run(mach, T_amb, P_amb):
        try:
            r = cls().simulate(**{**base, "T_amb": T_amb, "P_amb": P_amb, "mach": mach})
            return r["thrust_kN"], r["TSFC_mg"]
        except Exception:
            return None, None

    # ── Empuje vs Mach (condiciones de despegue: h=0, T=slider) ──────
    P_sl = 101325.0   # presión ISA a nivel del mar
    x_f, y_f = [], []
    for m in machs:
        thrust, _ = run(m, t0_k, P_sl)
        if thrust is not None:
            x_f.append(m); y_f.append(thrust)

    title_f = f"Empuje vs Mach  —  T₀ = {t0_c:+.0f} °C,  h = 0 m"
    fig_thrust = go.Figure()
    fig_thrust.add_trace(go.Scatter(
        x=x_f, y=y_f, mode="lines",
        line=dict(color=color, width=2.5),
        fill="tozeroy", fillcolor=_rgba(color, 0.07),
        hovertemplate="M = %{x:.3f}<br>F = %{y:.2f} kN<extra></extra>",
        showlegend=False,
    ))
    fig_thrust.update_layout(**_plot_layout(title_f))
    fig_thrust.update_xaxes(**_ax("Número de Mach  [ — ]"))
    fig_thrust.update_yaxes(**_ax("Empuje  [kN]"))

    # ── Empuje vs Mach (condiciones de crucero: h=slider, T=ISA) ────
    x_s, y_s = [], []
    for m in machs:
        thrust_cr, _ = run(m, T_cr, P_cr)
        if thrust_cr is not None:
            x_s.append(m); y_s.append(thrust_cr)

    h_km    = alt / 1000
    T_isa   = T_cr - 273.15
    title_s = f"Empuje vs Mach  —  h = {h_km:.1f} km,  T_ISA = {T_isa:.1f} °C"
    fig_tsfc = go.Figure()
    fig_tsfc.add_trace(go.Scatter(
        x=x_s, y=y_s, mode="lines",
        line=dict(color=color, width=2.5),
        fill="tozeroy", fillcolor=_rgba(color, 0.07),
        hovertemplate="M = %{x:.3f}<br>F = %{y:.2f} kN<extra></extra>",
        showlegend=False,
    ))
    fig_tsfc.update_layout(**_plot_layout(title_s))
    fig_tsfc.update_xaxes(**_ax("Número de Mach  [ — ]"))
    fig_tsfc.update_yaxes(**_ax("Empuje  [kN]"))

    return fig_thrust, fig_tsfc

# ── Mapa zona → sid de rendimiento (OneSpoolEngine) ───────────────────────────
_ETA_MAP = {
    "difusor":   ("os_edif",  "η difusor",  None,        None),
    "compresor": ("os_ec",    "η compresor","W_comp",    "Trabajo [kJ/kg]"),
    "camara":    ("os_ecc",   "η cámara",   "FAR",       "FAR"),
    "turbina":   ("os_et",    "η turbina",  "shaft_MW",  "Potencia eje [MW]"),
    "tobera":    ("os_enoz",  "η tobera",   "V_jet",     "V_jet [m/s]"),
}
_ZONE_COLORS = {
    "difusor":   "#4a7abf",
    "compresor": "#1a4d8f",
    "camara":    "#b83232",
    "turbina":   "#cc5500",
    "tobera":    "#7055aa",
}
 
 
@app.callback(
    Output("comp-tele-panel", "children"),
    Input("onespool-diagram",   "clickData"),
    State("eta-override-store", "data"),
    prevent_initial_call=True,
)
def on_comp_click(clickData, eta_overrides):
    """Dibuja el panel de telemetría al hacer click en una zona del diagrama."""
    if clickData is None:
        raise dash.exceptions.PreventUpdate
    try:
        cd = clickData["points"][0].get("customdata", [])
        if len(cd) < 5:
            raise dash.exceptions.PreventUpdate
        zone_id, label, station, t_str, p_str = cd
    except Exception:
        raise dash.exceptions.PreventUpdate
 
    if eta_overrides is None:
        eta_overrides = {}
 
    col = _ZONE_COLORS.get(zone_id, C["dim"])
    eta_sid, eta_label, extra_key, extra_label = _ETA_MAP.get(
        zone_id, (None, None, None, None)
    )
    # Valor actual del rendimiento (override si existe, si no el valor por defecto)
    eta_default = {
        "os_edif": 0.99, "os_ec": 0.92, "os_ecc": 0.99,
        "os_et": 0.88, "os_enoz": 0.99,
    }
    current_eta = eta_overrides.get(eta_sid, eta_default.get(eta_sid)) if eta_sid else None
 
    def row(lbl, val):
        return html.Tr([
            html.Td(lbl, className="tele-key"),
            html.Td(val, className="tele-val"),
        ])
 
    rows = [
        html.Tr([html.Td(label, colSpan=2, style={
            "color": col, "fontFamily": C["head"], "fontWeight": "700",
            "fontSize": "11px", "letterSpacing": "2px",
            "paddingBottom": "6px", "borderBottom": f"1px solid {col}",
        })]),
        row("Tt salida", t_str),
        row("Pt salida", p_str),
    ]
 
    if eta_sid:
        rows.append(html.Tr([
            html.Td(eta_label, className="tele-key"),
            html.Td(dcc.Input(
                id={"type": "eta-input", "zone": zone_id},
                type="number", min=0.60, max=1.00, step=0.01,
                value=current_eta,
                placeholder="0.60–1.00",
                style={
                    "width": "70px", "fontFamily": C["mono"], "fontSize": "10px",
                    "background": C["panel2"], "color": C["accent"],
                    "border": f"1px solid {C['border']}", "padding": "2px 4px",
                },
                debounce=True,
            ), className="tele-val"),
        ]))
        rows.append(html.Tr([html.Td(
            "↵ Intro para aplicar",
            colSpan=2,
            style={"fontFamily":C["mono"],"fontSize":"8px",
                   "color":C["dim"],"fontStyle":"italic","paddingTop":"3px"},
        )]))
 
    return [html.Table(rows, className="tele-table w-100")]
 
 
@app.callback(
    Output("eta-override-store", "data"),
    Input({"type": "eta-input", "zone": dash.ALL}, "value"),
    State({"type": "eta-input", "zone": dash.ALL}, "id"),
    State("eta-override-store", "data"),
    prevent_initial_call=True,
)
def update_eta_store(values, ids, current_store):
    """Cuando el usuario escribe un η en el panel, lo guarda en el Store.
    run_simulation escucha el Store y relanza el cálculo automáticamente."""
    if not values or not ids:
        raise dash.exceptions.PreventUpdate
    store = dict(current_store or {})
    for id_dict, val in zip(ids, values):
        zone_id = id_dict["zone"]
        eta_sid = _ETA_MAP.get(zone_id, (None,))[0]
        if eta_sid and val is not None:
            try:
                v = float(val)
                if 0.60 <= v <= 1.00:
                    store[eta_sid] = v
            except (TypeError, ValueError):
                pass
    return store

if __name__ == "__main__":
    app.run(debug=True)
