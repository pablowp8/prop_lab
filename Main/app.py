"""
AeroSim v4.2 — app.py
Pantalla 1 : Menú de selección de motor
Pantalla 2 : Simulador (sliders · métricas · esquema SVG · gráficas · telemetría)

Física delegada a simulation.py → components.py
Ejecución:  python app.py hola
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
    title="AeroSim",
    suppress_callback_exceptions=True,
)
server = app.server

# ── Paleta claro (coincide con CSS vars por defecto) ──────────────────────────
C = {
    "bg":      "#edeae4",
    "panel":   "#f5f3ef",
    "panel2":  "#ebe7e0",
    "border":  "#c8beb4",
    "border2": "#a89e94",
    "text":    "#18243c",
    "dim":     "#6e82a0",
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
        "label":    "Turbojet Monoeje",
        "subtitle": "Single Spool Turbojet",
        "icon":     "◈",
        "color":    "#1a4d8f",
        "specs": [("Ejes","1"),("Aplicacion","Caza / Misil"),("Mach max","2.5+"),("OPR tipico","10–20")],
        "desc": "Un unico eje acopla el compresor con la turbina. Arquitectura simple y robusta para aplicaciones militares y velocidades supersonicas.",
        "sliders": [
            ("os_alt",  "Altitud [m]",         0,    12000, 0,    100),
            ("os_t0",   "Temperatura T0 [C]",  -70,  50,    15,   1),
            ("os_mach", "Mach",                0,    2.5,   0,    0.01),
            ("os_G",    "Flujo masico [kg/s]", 5,    200,   20,   1),
            ("os_pi",   "OPR compresor",       2,    30,    10,   0.1),
            ("os_tit",  "TIT [K]",             800,  1800,  1400, 5),
            ("os_ec",   "eta compresor",       0.6,  0.99,  0.80, 0.01),
            ("os_et",   "eta turbina",         0.6,  0.99,  0.88, 0.01),
        ],
        "engine_cls": sim.OneSpoolEngine,
        "runner": lambda p: sim.OneSpoolEngine().simulate(
            *sim.isa_atmosphere(p["os_alt"], p["os_t0"]),
            p["os_mach"], p["os_G"], p["os_pi"], p["os_tit"],
            eta_c=p["os_ec"], eta_t=p["os_et"],
        ),
        "sweep_base": lambda p: {
            "mach":p["os_mach"], "G":p["os_G"],
            "pi_23":p["os_pi"],  "tit":p["os_tit"],
            "eta_c":p["os_ec"],  "eta_t":p["os_et"],
            **dict(zip(["T_amb","P_amb"], sim.isa_atmosphere(p["os_alt"], p["os_t0"]))),
        },
    },
    "TwinSpoolEngine": {
        "label":    "Turbojet Bieje",
        "subtitle": "Twin Spool Turbojet",
        "icon":     "⬡",
        "color":    "#b83232",
        "specs": [("Ejes","2 (LP + HP)"),("Aplicacion","Militar / Civil"),("Mach max","2.0+"),("OPR tipico","15–30")],
        "desc": "Dos ejes independientes LP y HP permiten optimizar la velocidad de cada etapa de compresion, mejorando rendimiento y estabilidad.",
        "sliders": [
            ("ts_alt",   "Altitud [m]",         0,    12000, 0,     100),
            ("ts_t0",    "Temperatura T0 [C]",  -70,  50,    15,    1),
            ("ts_mach",  "Mach",                0,    2.5,   0,     0.01),
            ("ts_G",     "Flujo masico [kg/s]", 5,    200,   20,    1),
            ("ts_pilpc", "OPR compresor LP",    1.1,  6,     1.6,   0.1),
            ("ts_pihpc", "OPR compresor HP",    2,    25,    12,    0.1),
            ("ts_tit",   "TIT [K]",             800,  1900,  1450,  5),
            ("ts_elpc",  "eta comp. LP",        0.6,  0.99,  0.91,  0.01),
            ("ts_ehpc",  "eta comp. HP",        0.6,  0.99,  0.85,  0.01),
            ("ts_elpt",  "eta turb. LP",        0.6,  0.99,  0.94,  0.01),
            ("ts_ehpt",  "eta turb. HP",        0.6,  0.99,  0.92,  0.01),
        ],
        "engine_cls": sim.TwinSpoolEngine,
        "runner": lambda p: sim.TwinSpoolEngine().simulate(
            *sim.isa_atmosphere(p["ts_alt"], p["ts_t0"]),
            p["ts_mach"], p["ts_G"],
            p["ts_pilpc"], p["ts_pihpc"], p["ts_tit"],
            eta_lpc=p["ts_elpc"], eta_hpc=p["ts_ehpc"],
            eta_lpt=p["ts_elpt"], eta_hpt=p["ts_ehpt"],
        ),
        "sweep_base": lambda p: {
            "mach":p["ts_mach"],   "G":p["ts_G"],
            "pi_lpc":p["ts_pilpc"],"pi_hpc":p["ts_pihpc"], "tit":p["ts_tit"],
            "eta_lpc":p["ts_elpc"],"eta_hpc":p["ts_ehpc"],
            "eta_lpt":p["ts_elpt"],"eta_hpt":p["ts_ehpt"],
            **dict(zip(["T_amb","P_amb"], sim.isa_atmosphere(p["ts_alt"], p["ts_t0"]))),
        },
    },
    "SingleFlowTurbofan": {
        "label":    "Turbofan",
        "subtitle": "Single Flow Turbofan",
        "icon":     "⊕",
        "color":    "#1a6644",
        "specs": [("Ejes","2 (Fan + HP)"),("Aplicacion","Aviacion comercial"),("Mach max","0.9"),("BPR tipico","0.5–1.5")],
        "desc": "El fan comprime flujo primario y secundario. La turbina LP mueve el fan y la HP el compresor de nucleo. Optimo para aviacion subsonica.",
        "sliders": [
            ("tf_alt",   "Altitud [m]",              0,    12000, 0,    100),
            ("tf_t0",    "Temperatura T0 [C]",       -70,  50,    15,   1),
            ("tf_mach",  "Mach",                     0,    1.0,   0,    0.01),
            ("tf_G",     "Flujo masico total [kg/s]",10,   500,   90,   5),
            ("tf_pi",    "OPR nucleo",               2,    40,    25,   0.1),
            ("tf_tit",   "TIT [K]",                  800,  2000,  1500, 5),
            ("tf_pifan", "OPR fan",                  1.1,  3.0,   1.4,  0.05),
            ("tf_bpr",   "Bypass Ratio",             0.1,  12,    0.8,  0.1),
            ("tf_ec",    "eta nucleo",               0.6,  0.99,  1.0,  0.01),
            ("tf_efan",  "eta fan",                  0.6,  0.99,  1.0,  0.01),
            ("tf_ehpt",  "eta turb. HP",             0.6,  0.99,  1.0,  0.01),
            ("tf_elpt",  "eta turb. LP",             0.6,  0.99,  1.0,  0.01),
        ],
        "engine_cls": sim.SingleFlowTurbofan,
        "runner": lambda p: sim.SingleFlowTurbofan().simulate(
            *sim.isa_atmosphere(p["tf_alt"], p["tf_t0"]),
            p["tf_mach"], p["tf_G"], p["tf_pi"], p["tf_tit"],
            p["tf_pifan"], p["tf_bpr"],
            eta_c=p["tf_ec"], eta_fan=p["tf_efan"],
            eta_hpt=p["tf_ehpt"], eta_lpt=p["tf_elpt"],
        ),
        "sweep_base": lambda p: {
            "mach":p["tf_mach"],   "G":p["tf_G"],
            "pi_23":p["tf_pi"],    "tit":p["tf_tit"],
            "pi_fan":p["tf_pifan"],"bpr":p["tf_bpr"],
            "eta_c":p["tf_ec"],    "eta_fan":p["tf_efan"],
            "eta_hpt":p["tf_ehpt"],"eta_lpt":p["tf_elpt"],
            **dict(zip(["T_amb","P_amb"], sim.isa_atmosphere(p["tf_alt"], p["tf_t0"]))),
        },
    },
    "OneSpoolTurboprop": {
        "label":    "Turboprop",
        "subtitle": "Single Spool Turboprop",
        "icon":     "✦",
        "color":    "#9c4d00",
        "specs": [("Ejes","2 (HP + LP)"),("Aplicacion","Regional / Carga"),("Mach max","0.6"),("OPR tipico","10–25")],
        "desc": "La mayor parte de la energia mueve una helice via caja reductora. La tobera residual aporta empuje adicional. Optimo a baja velocidad.",
        "sliders": [
            ("tp_alt",  "Altitud [m]",         0,    8000,  0,     100),
            ("tp_t0",   "Temperatura T0 [C]",  -50,  50,    15,    1),
            ("tp_mach", "Mach",                0,    0.7,   0,     0.01),
            ("tp_G",    "Flujo masico [kg/s]", 5,    200,   90,    1),
            ("tp_pi",   "OPR compresor",       2,    30,    25,    0.1),
            ("tp_tit",  "TIT [K]",             800,  1700,  1500,  5),
            ("tp_Wh",   "Potencia eje [kW]",   10,   2000,  200,   10),
            ("tp_etam", "eta mecanica",         0.5,  0.99,  0.70,  0.01),
            ("tp_ec",   "eta compresor",        0.6,  0.99,  1.0,   0.01),
            ("tp_ehpt", "eta turb. HP",         0.6,  0.99,  1.0,   0.01),
            ("tp_elpt", "eta turb. LP",         0.6,  0.99,  1.0,   0.01),
        ],
        "engine_cls": sim.OneSpoolTurboprop,
        "runner": lambda p: sim.OneSpoolTurboprop().simulate(
            *sim.isa_atmosphere(p["tp_alt"], p["tp_t0"]),
            p["tp_mach"], p["tp_G"], p["tp_pi"], p["tp_tit"],
            p["tp_Wh"] * 1000, p["tp_etam"],
            eta_c=p["tp_ec"], eta_hpt=p["tp_ehpt"], eta_lpt=p["tp_elpt"],
        ),
        "sweep_base": lambda p: {
            "mach":p["tp_mach"], "G":p["tp_G"],
            "pi_23":p["tp_pi"],  "tit":p["tp_tit"],
            "W_h":p["tp_Wh"]*1000, "eta_m":p["tp_etam"],
            "eta_c":p["tp_ec"],  "eta_hpt":p["tp_ehpt"], "eta_lpt":p["tp_elpt"],
            **dict(zip(["T_amb","P_amb"], sim.isa_atmosphere(p["tp_alt"], p["tp_t0"]))),
        },
    },
}

ALL_SLIDER_IDS = [
    sid for cfg in ENGINE_CONFIGS.values() for sid, *_ in cfg["sliders"]
]

# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS UI
# ══════════════════════════════════════════════════════════════════════════════

def make_slider(sid, label, mn, mx, dfl, stp):
    return html.Div([
        html.Div([
            html.Span(label, style={"fontSize":"10px","color":C["dim"],
                                    "fontFamily":C["head"],"letterSpacing":"1px"}),
            html.Span(id=f"val-{sid}", style={"fontFamily":C["mono"],
                                               "fontSize":"11px","color":C["accent"]}),
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

    CK = {
        "intake": "#5a8abf", "fan":    "#1a7a5a", "lpc":  "#2a70b0",
        "hpc":    C["accent"],"comb":  C["accent2"],"hpt": "#cc6600",
        "lpt":    C["warn"],  "nozzle":"#7055aa",  "prop": C["accent3"],
    }

    # Coordenadas en espacio normalizado x:[0,1] y:[0,1]
    # cy_n = eje central normalizado
    W, H = 800, 1.0
    cy = 0.5

    shapes = []
    annotations = []

    def _hex_rgba(h, a=0.12):
        h = h.lstrip("#")
        r,g,b = int(h[0:2],16),int(h[2:4],16),int(h[4:6],16)
        return f"rgba({r},{g},{b},{a})"

    def box(x0, x1, y0, y1, color, label):
        shapes.append(dict(
            type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
            fillcolor=_hex_rgba(color, 0.15),
            line=dict(color=color, width=1.5),
            layer="below",
        ))
        annotations.append(dict(
            x=(x0+x1)/2, y=(y0+y1)/2,
            text=f"<b>{label}</b>",
            showarrow=False,
            font=dict(size=9, color=color, family="Share Tech Mono"),
            xref="x", yref="y",
        ))

    def station(x, label, t_val, p_val):
        # Línea vertical punteada
        shapes.append(dict(
            type="line", x0=x, x1=x, y0=cy-0.28, y1=cy+0.28,
            line=dict(color=C["border"], width=0.8, dash="dot"),
        ))
        # Etiqueta estación Tt{n}
        t_text = f"T<sub>t{label}</sub>"
        val_text = f"{t_val:.0f} K" if t_val is not None else ""
        p_text   = f"{p_val:.0f} kPa" if p_val is not None else ""
        annotations.append(dict(
            x=x, y=cy+0.35,
            text=t_text,
            showarrow=False,
            font=dict(size=8, color=C["dim"], family="Share Tech Mono"),
            xref="x", yref="y",
        ))
        if val_text:
            annotations.append(dict(
                x=x, y=cy+0.47,
                text=val_text,
                showarrow=False,
                font=dict(size=7, color=C["accent"], family="Share Tech Mono"),
                xref="x", yref="y",
            ))
        if p_text:
            annotations.append(dict(
                x=x, y=cy-0.40,
                text=p_text,
                showarrow=False,
                font=dict(size=7, color=C["dim"], family="Share Tech Mono"),
                xref="x", yref="y",
            ))

    # Eje central
    shapes.append(dict(
        type="line", x0=10, x1=790, y0=cy, y1=cy,
        line=dict(color=C["border"], width=0.5, dash="dot"),
    ))

    # ── Geometría ────────────────────────────────────────────────────────
    if engine_type == "OneSpoolEngine":
        box(30,  110, cy-0.16, cy+0.16, CK["intake"], "INTAKE")
        box(115, 225, cy-0.26, cy+0.26, CK["hpc"],    "COMP")
        box(230, 370, cy-0.22, cy+0.22, CK["comb"],   "COMB")
        box(375, 485, cy-0.24, cy+0.24, CK["hpt"],    "TURB")
        box(490, 580, cy-0.16, cy+0.16, CK["nozzle"], "NOZ")
        stations = [(30,"0",0),(115,"2",2),(230,"3",3),
                    (375,"4",4),(490,"5",5),(580,"9",9)]
        title = "MONOEJE  ·  Brayton simple"

    elif engine_type == "TwinSpoolEngine":
        box(25,  95,  cy-0.14, cy+0.14, CK["intake"], "INTAKE")
        box(100, 190, cy-0.20, cy+0.20, CK["lpc"],    "LPC")
        box(195, 310, cy-0.28, cy+0.28, CK["hpc"],    "HPC")
        box(315, 445, cy-0.22, cy+0.22, CK["comb"],   "COMB")
        box(450, 545, cy-0.26, cy+0.26, CK["hpt"],    "HPT")
        box(550, 645, cy-0.20, cy+0.20, CK["lpt"],    "LPT")
        box(650, 725, cy-0.14, cy+0.14, CK["nozzle"], "NOZ")
        stations = [(25,"0",0),(100,"2",2),(195,"2.5",2.5),(315,"3",3),
                    (450,"4",4),(550,"4.5",4.5),(650,"5",5),(725,"9",9)]
        title = "BIEJE  ·  LP + HP"

    elif engine_type == "SingleFlowTurbofan":
        box(25,  110, cy-0.32, cy+0.32, CK["fan"],    "FAN")
        box(115, 235, cy-0.32, cy-0.12, CK["lpc"],    "BYPASS")
        box(115, 235, cy-0.10, cy+0.22, CK["hpc"],    "HPC")
        box(240, 370, cy-0.18, cy+0.18, CK["comb"],   "COMB")
        box(375, 470, cy-0.20, cy+0.20, CK["hpt"],    "HPT")
        box(475, 575, cy-0.26, cy+0.26, CK["lpt"],    "LPT")
        box(580, 670, cy-0.30, cy+0.30, CK["nozzle"], "NOZ")
        stations = [(25,"0",0),(115,"1.3",2),(240,"3",3),
                    (375,"4",4),(475,"4.5",4.5),(580,"5",5),(670,"8",8)]
        title = "TURBOFAN  ·  Fan + Nucleo"

    else:  # Turboprop
        box(5,   33,  cy-0.36, cy+0.36, CK["prop"],   "PROP")
        box(38,  110, cy-0.14, cy+0.14, CK["intake"], "INTAKE")
        box(115, 225, cy-0.26, cy+0.26, CK["hpc"],    "COMP")
        box(230, 370, cy-0.22, cy+0.22, CK["comb"],   "COMB")
        box(375, 475, cy-0.24, cy+0.24, CK["hpt"],    "HPT")
        box(480, 580, cy-0.20, cy+0.20, CK["lpt"],    "LPT")
        box(585, 665, cy-0.14, cy+0.14, CK["nozzle"], "NOZ")
        stations = [(38,"0",0),(115,"2",2),(230,"3",3),
                    (375,"4",4),(480,"4.5",4.5),(585,"5",5),(665,"9",9)]
        title = "TURBOPROP  ·  Helice + Tobera"

    for (sx, slbl, st_id) in stations:
        station(sx, slbl, tv(st_id), pv(st_id))

    # Título esquina superior derecha
    annotations.append(dict(
        x=790, y=0.97,
        text=title,
        showarrow=False,
        font=dict(size=8, color=C["border2"], family="Share Tech Mono"),
        xref="x", yref="y", xanchor="right",
    ))

    fig = go.Figure()
    fig.update_layout(
        shapes=shapes,
        annotations=annotations,
        plot_bgcolor=C["panel"],
        paper_bgcolor=C["panel"],
        margin=dict(l=0, r=0, t=0, b=0),
        height=110,
        xaxis=dict(range=[0, 800], visible=False, fixedrange=True),
        yaxis=dict(range=[0, 1],   visible=False, fixedrange=True),
        showlegend=False,
    )

    return dcc.Graph(
        figure=fig,
        config={"displayModeBar": False, "staticPlot": True},
        style={"height":"110px"},
    )


# ══════════════════════════════════════════════════════════════════════════════
#  PANTALLA 1 — MENÚ
# ══════════════════════════════════════════════════════════════════════════════

def menu_engine_card(eid, cfg):
    specs = [
        html.Div([
            html.Span(k, style={"display":"block","color":C["dim"],"fontSize":"8px",
                                "fontFamily":C["head"],"letterSpacing":"3px",
                                "textTransform":"uppercase","marginBottom":"1px"}),
            html.Span(v, style={"color":C["text"],"fontSize":"13px","fontFamily":C["mono"]}),
        ], style={"marginBottom":"10px"})
        for k, v in cfg["specs"]
    ]
    return html.Div([
        html.Div(style={"height":"3px","background":cfg["color"],"marginBottom":"18px"}),
        html.Div(cfg["icon"], style={"fontSize":"30px","color":cfg["color"],
                                     "display":"block","marginBottom":"10px","lineHeight":"1"}),
        html.Div(cfg["label"], style={"fontFamily":C["head"],"fontWeight":"900","fontSize":"18px",
                                       "letterSpacing":"2px","textTransform":"uppercase",
                                       "color":C["text"],"marginBottom":"2px"}),
        html.Div(cfg["subtitle"], style={"fontFamily":C["mono"],"fontSize":"9px",
                                          "color":cfg["color"],"letterSpacing":"2px",
                                          "marginBottom":"12px"}),
        html.P(cfg["desc"], style={"fontFamily":C["head"],"fontWeight":"300","fontSize":"12px",
                                    "color":C["dim"],"lineHeight":"1.6","marginBottom":"16px"}),
        html.Div(specs, style={"borderTop":f"1px solid {C['border']}",
                                "paddingTop":"12px","marginBottom":"16px"}),
        html.Button("SELECCIONAR  →", id=f"btn-select-{eid}", n_clicks=0, style={
            "background":"transparent","border":f"1px solid {cfg['color']}",
            "color":cfg["color"],"fontFamily":C["head"],"fontWeight":"700",
            "fontSize":"10px","letterSpacing":"3px","padding":"8px 0",
            "cursor":"pointer","width":"100%","textTransform":"uppercase",
        }),
    ], id=f"menu-card-{eid}", style={
        "background":C["panel"],"border":f"1px solid {C['border']}",
        "padding":"22px 20px","height":"100%",
    })


menu_screen = html.Div([
    html.Div([
        html.Div(style={
            "height":"3px",
            "background":f"linear-gradient(90deg,{C['accent']} 0%,{C['border']} 100%)",
            "marginBottom":"48px",
        }),
        html.Div([
            html.Div("REF-DOC-SIM-001", style={"fontFamily":C["mono"],"fontSize":"9px",
                                                "color":C["border2"],"letterSpacing":"4px",
                                                "marginBottom":"10px"}),
            html.Div("AEROSIM", style={"fontFamily":C["head"],"fontWeight":"900",
                                        "fontSize":"52px","letterSpacing":"14px",
                                        "color":C["accent"],"lineHeight":"1","marginBottom":"8px"}),
            html.Div("SIMULADOR DE AERORREACTORES", style={"fontFamily":C["mono"],
                                                            "fontSize":"10px","color":C["dim"],
                                                            "letterSpacing":"6px","marginBottom":"16px"}),
            html.P("Selecciona el tipo de motor para comenzar la simulacion",
                   style={"fontFamily":C["head"],"fontWeight":"300","fontSize":"14px",
                          "color":C["dim"],"margin":"0"}),
        ], style={"textAlign":"center","paddingBottom":"40px"}),
    ]),
    dbc.Container([
        dbc.Row([
            dbc.Col(menu_engine_card(eid, cfg), width=3, className="mb-3")
            for eid, cfg in ENGINE_CONFIGS.items()
        ], className="g-3"),
    ], fluid=True, style={"maxWidth":"1400px","margin":"0 auto","padding":"0 24px"}),
    html.Div("AeroSim v4.2  ·  components.py  ·  2025", style={
        "textAlign":"center","fontFamily":C["mono"],"fontSize":"10px",
        "color":C["border"],"padding":"32px","marginTop":"16px",
    }),
], id="screen-menu", style={"minHeight":"100vh","background":C["bg"],
                              "position":"relative","zIndex":"1"})


# ══════════════════════════════════════════════════════════════════════════════
#  PANTALLA 2 — SIMULADOR
# ══════════════════════════════════════════════════════════════════════════════

all_slider_groups = []
for eid, cfg in ENGINE_CONFIGS.items():
    group = [make_slider(sid, lbl, mn, mx, dfl, stp)
             for sid, lbl, mn, mx, dfl, stp in cfg["sliders"]]
    all_slider_groups.append(html.Div(group, id=f"sliders-{eid}", style={"display":"none"}))

PANEL_L = {"background":C["panel"],"borderRight":f"1px solid {C['border']}",
            "paddingLeft":"14px","paddingRight":"14px",
            "overflowY":"auto","height":"calc(100vh - 80px)"}
PANEL_R = {"background":C["panel"],"borderLeft":f"1px solid {C['border']}",
            "paddingLeft":"12px","paddingRight":"12px",
            "overflowY":"auto","height":"calc(100vh - 80px)"}
PANEL_C = {"overflowY":"auto","height":"calc(100vh - 80px)","paddingRight":"0"}

sim_screen = html.Div([

    # Navbar
    html.Div([
        html.Div([
            html.Button("← MENU", id="btn-back", n_clicks=0),
            html.Span("AEROSIM", style={"fontFamily":C["head"],"fontWeight":"900",
                                         "fontSize":"18px","letterSpacing":"5px",
                                         "color":C["accent"],"marginLeft":"16px"}),
        ], style={"display":"flex","alignItems":"center"}),
        html.Div([
            html.Span("● LIVE",           className="nav-badge live me-2"),
            html.Span(id="sim-eng-label", className="nav-badge me-2"),
            html.Span("SESION: LAB-04",   className="nav-badge"),
        ], style={"display":"flex","alignItems":"center"}),
    ], className="aerosim-nav"),

    html.Div(id="alert-tit", style={"display":"none"}, className="alert-tit mx-3 mt-2"),

    dbc.Container([
        dbc.Row([

            # Izquierda: sliders
            dbc.Col([
                html.Div(id="sim-eng-title", className="section-head mt-3"),
                html.Div(all_slider_groups),
            ], width=3, style=PANEL_L),

            # Centro: métricas + esquema SVG + gráficas
            dbc.Col([
                dbc.Row([
                    dbc.Col(metric_card("Empuje neto",    "thrust","kN",    "good"), width=4),
                    dbc.Col(metric_card("TIT",            "tit",   "K",     "hot"),  width=4),
                    dbc.Col(metric_card("TSFC",           "tsfc",  "mg/Ns", ""),      width=4),
                ], className="mt-3 mb-1 g-1"),
                dbc.Row([
                    dbc.Col(metric_card("eta Termico",    "etath",  "%",   ""),    width=3),
                    dbc.Col(metric_card("eta Propulsivo", "etaprop","%",   ""),    width=3),
                    dbc.Col(metric_card("eta Global",     "etag",   "%",   "good"),width=3),
                    dbc.Col(metric_card("Combustible",    "fuel",   "kg/s","warn"),width=3),
                ], className="mb-1 g-1"),
                # Esquema SVG del motor
                html.Div(id="engine-diagram",
                         className="graph-card mb-1",
                         style={"padding":"0","lineHeight":"0","overflow":"hidden"}),
                dbc.Row([
                    dbc.Col(html.Div(dcc.Graph(id="graph-ts",  config={"displayModeBar":False}),
                                    className="graph-card"), width=6),
                    dbc.Col(html.Div(dcc.Graph(id="graph-eta", config={"displayModeBar":False}),
                                    className="graph-card"), width=6),
                ], className="g-1 mb-1"),
                dbc.Row([
                    dbc.Col(html.Div(dcc.Graph(id="graph-tit", config={"displayModeBar":False}),
                                    className="graph-card"), width=6),
                    dbc.Col(html.Div(dcc.Graph(id="graph-opr", config={"displayModeBar":False}),
                                    className="graph-card"), width=6),
                ], className="g-1"),
            ], width=7, style=PANEL_C),

            # Derecha: telemetría
            dbc.Col([
                html.Div("Telemetria", className="section-head mt-3"),
                html.Table(id="tele-table", className="tele-table w-100"),
            ], width=2, style=PANEL_R),

        ], className="g-0"),
    ], fluid=True, style={"padding":"0"}),

    html.Div([
        html.Span([html.Span("FISICA:", className="lbl"), " components.py"]),
        html.Span([html.Span("UI:",     className="lbl"), " app.py"]),
        html.Span("AeroSim v4.2 · 2025", style={"marginLeft":"auto"}),
    ], className="sim-footer"),

], id="screen-sim", style={"display":"none","minHeight":"100vh","background":C["bg"]})


# ══════════════════════════════════════════════════════════════════════════════
#  LAYOUT RAÍZ
# ══════════════════════════════════════════════════════════════════════════════

app.layout = html.Div([
    dcc.Store(id="active-engine", data=None),
    menu_screen,
    sim_screen,
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
        f"{cfg['icon']}  {cfg['label'].upper()}",
        *slider_styles,
    )


@app.callback(
    *[Output(f"val-{sid}", "children") for sid in ALL_SLIDER_IDS],
    *[Input(f"sl-{sid}",   "value")    for sid in ALL_SLIDER_IDS],
)
def update_labels(*vals):
    out = []
    for sid, v in zip(ALL_SLIDER_IDS, vals):
        if v is None:
            out.append(""); continue
        if any(x in sid for x in ["mach","_ec","_et","efan","ehpt","elpt","elpc","ehpc","etam"]):
            out.append(f"{v:.2f}")
        elif any(x in sid for x in ["tit","alt"]):
            out.append(f"{int(v):,}")
        else:
            out.append(f"{v:.2f}" if v < 100 else f"{v:.1f}")
    return out


@app.callback(
    Output("m-thrust",        "children"),
    Output("m-tit",           "children"),
    Output("m-tsfc",          "children"),
    Output("m-etath",         "children"),
    Output("m-etaprop",       "children"),
    Output("m-etag",          "children"),
    Output("m-fuel",          "children"),
    Output("graph-ts",        "figure"),
    Output("graph-eta",       "figure"),
    Output("graph-tit",       "figure"),
    Output("graph-opr",       "figure"),
    Output("tele-table",      "children"),
    Output("alert-tit",       "children"),
    Output("alert-tit",       "style"),
    Output("engine-diagram",  "children"),
    Input("active-engine", "data"),
    *[Input(f"sl-{sid}", "value") for sid in ALL_SLIDER_IDS],
)
def run_simulation(engine_type, *all_vals):
    if not engine_type:
        raise dash.exceptions.PreventUpdate

    cfg   = ENGINE_CONFIGS[engine_type]
    color = cfg["color"]

    # Parámetros del motor activo
    p = {}
    for sid, _, _, _, default, _ in cfg["sliders"]:
        idx  = ALL_SLIDER_IDS.index(sid)
        p[sid] = all_vals[idx] if all_vals[idx] is not None else default

    # Error path: devuelve exactamente 15 valores (7 métricas + 4 figs + tabla + msg + style + diagram)
    def _err(msg_str):
        ef = go.Figure().update_layout(**_plot_layout(f"Error"))
        et = [html.Tr([html.Td("Error", className="tele-key"),
                       html.Td(msg_str[:80], className="tele-val")])]
        ed = html.Div(msg_str[:120], style={"padding":"8px","fontFamily":C["mono"],
                                             "fontSize":"10px","color":C["accent2"]})
        return ["--"]*7 + [ef,ef,ef,ef, et, msg_str, {"display":"block"}, ed]

    try:
        r = cfg["runner"](p)
    except Exception as e:
        return _err(str(e))

    tit_val = r["Tt4_K"]

    # Métricas
    metrics = [
        f"{r['thrust_kN']:.2f}",
        f"{tit_val:.0f}",
        f"{r['TSFC_mg']:.3f}",
        f"{r['eta_th']:.1f}",
        f"{r['eta_prop']:.1f}",
        f"{r['eta_global']:.1f}",
        f"{r['fuel_kg_s']:.4f}",
    ]

    sweep_p = cfg["sweep_base"](p)

    # ── Diagrama T-s ──────────────────────────────────────────────────────
    Pt0 = max(r["Pt0_kPa"], 0.001)
    Pt3 = max(r["Pt3_kPa"], 0.001)
    T1,T2,T3,T4 = r["T0_K"], r["Tt3_K"], r["Tt4_K"], r["Tt5_K"]
    s1=0; s2=-0.3*np.log(Pt3/Pt0); s3=s2
    s4 = s3 + 0.4*np.log(max(T3,1)/max(T4,1))
    fig_ts = go.Figure()
    fig_ts.add_trace(go.Scatter(
        x=[s1,s2,s3,s4,s1], y=[T1,T2,T3,T4,T1], mode="lines",
        line=dict(color=color, width=0), fill="toself",
        fillcolor=_rgba(color, 0.10),
        showlegend=False, hoverinfo="skip",
    ))
    fig_ts.add_trace(go.Scatter(
        x=[s1,s2,s3,s4,s1], y=[T1,T2,T3,T4,T1],
        mode="lines+markers", line=dict(color=color, width=1.5),
        marker=dict(size=7, symbol="square", color=[C["accent3"],C["accent"],C["accent2"],C["warn"],C["accent3"]],
                    line=dict(color=C["panel"], width=1.5)),
        hovertemplate="s=%{x:.3f}<br>T=%{y:.1f} K<extra></extra>",
        showlegend=False,
    ))
    for sx,tx,lbl in [(s1,T1,"[0] Entrada"),(s2,T2,"[3] Compresor"),
                       (s3,T3,"[4] Combustion"),(s4,T4,"[5] Turbina")]:
        fig_ts.add_annotation(x=sx, y=tx, text=lbl,
                               font=dict(color=C["dim"],size=8,family=C["mono"]),
                               showarrow=False, yshift=13,
                               bgcolor=C["panel"], bordercolor=C["border"],
                               borderwidth=1, borderpad=3)
    fig_ts.update_layout(**_plot_layout("Diagrama T-s  [ciclo Brayton]"))
    fig_ts.update_xaxes(**_ax("Entropia relativa  [kJ/kg·K]"))
    fig_ts.update_yaxes(**_ax("Temperatura  [K]"))

    # ── Rendimientos ──────────────────────────────────────────────────────
    fig_eta = go.Figure()
    for lbl, val, col, pat in [
        ("eta Termico",    r["eta_th"],     C["accent"],  "/"),
        ("eta Propulsivo", r["eta_prop"],   C["accent2"], "x"),
        ("eta Global",     r["eta_global"], color,        ""),
    ]:
        mk = dict(color=col, opacity=0.85, line=dict(color=col,width=1))
        if pat:
            mk["pattern"] = dict(shape=pat, size=4, fgcolor=C["panel"], fgopacity=0.4)
        fig_eta.add_trace(go.Bar(
            x=[lbl], y=[val], marker=mk,
            text=[f"{val:.1f}%"], textposition="outside",
            textfont=dict(color=C["text"],size=10,family=C["mono"]), name=lbl,
        ))
    fig_eta.update_layout(**_plot_layout("Rendimientos del ciclo  [%]"),
                           showlegend=False, yaxis_range=[0,115], bargap=0.35)
    fig_eta.update_xaxes(**_ax())
    fig_eta.update_yaxes(**_ax("%"))

    # ── Empuje vs TIT ─────────────────────────────────────────────────────
    tit_data = sim.sweep_tit(engine_type, sweep_p)
    txs, tys = zip(*tit_data) if tit_data else ([],[])
    fig_tit = go.Figure()
    fig_tit.add_trace(go.Scatter(
        x=list(txs), y=list(tys), mode="lines",
        line=dict(color=C["accent2"],width=1.5),
        fill="tozeroy", fillcolor=_rgba(C["accent2"], 0.10),
        showlegend=False,
    ))
    fig_tit.add_trace(go.Scatter(
        x=[tit_val], y=[r["thrust_kN"]], mode="markers",
        marker=dict(size=9,color=color,symbol="square",
                    line=dict(color=C["text"],width=1.5)),
        showlegend=False,
    ))
    fig_tit.add_vline(x=tit_val, line_width=1, line_dash="dot", line_color=C["border2"])
    fig_tit.update_layout(**_plot_layout("Empuje neto  vs  TIT"))
    fig_tit.update_xaxes(**_ax("TIT  [K]"))
    fig_tit.update_yaxes(**_ax("Empuje  [kN]"))

    # ── BPR o OPR sweep ───────────────────────────────────────────────────
    if engine_type == "SingleFlowTurbofan":
        bpr_data = sim.sweep_bpr(sweep_p)
        bxs, bys = zip(*bpr_data) if bpr_data else ([],[])
        cur_bpr  = p.get("tf_bpr", 0.8)
        fig_opr  = go.Figure()
        fig_opr.add_trace(go.Scatter(
            x=list(bxs), y=list(bys), mode="lines",
            line=dict(color=C["accent3"],width=1.5),
            fill="tozeroy", fillcolor=_rgba(C["accent3"], 0.10), showlegend=False,
        ))
        fig_opr.add_trace(go.Scatter(
            x=[cur_bpr], y=[r["TSFC_mg"]], mode="markers",
            marker=dict(size=9,color=color,symbol="square",
                        line=dict(color=C["text"],width=1.5)),
            showlegend=False,
        ))
        fig_opr.add_vline(x=cur_bpr, line_width=1, line_dash="dot", line_color=C["border2"])
        fig_opr.update_layout(**_plot_layout("TSFC  vs  Bypass Ratio"))
        fig_opr.update_xaxes(**_ax("Bypass Ratio"))
        fig_opr.update_yaxes(**_ax("TSFC  [mg/N·s]"))
    else:
        opr_data = sim.sweep_opr(engine_type, sweep_p)
        oxs, oys = zip(*opr_data) if opr_data else ([],[])
        fig_opr  = go.Figure()
        fig_opr.add_trace(go.Scatter(
            x=list(oxs), y=list(oys), mode="lines",
            line=dict(color=C["accent3"],width=1.5),
            fill="tozeroy", fillcolor=_rgba(C["accent3"], 0.10), showlegend=False,
        ))
        fig_opr.update_layout(**_plot_layout("eta Termico  vs  OPR"))
        fig_opr.update_xaxes(**_ax("OPR"))
        fig_opr.update_yaxes(**_ax("eta Termico  [%]"))

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

    return metrics + [fig_ts, fig_eta, fig_tit, fig_opr,
                      table, alert_msg, alert_style, diagram]


if __name__ == "__main__":
    app.run(debug=True)
