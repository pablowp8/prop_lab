"""
app.py — AeroSim v4.0
=====================
Pantalla 1: Menú de selección de motor (pantalla completa, visual)
Pantalla 2: Simulador completo con sliders, métricas, gráficas y telemetría

Toda la física delega en simulation.py → components.py

Ejecución:  python app.py
Producción: gunicorn app:server --workers 4 --threads 4 --bind 0.0.0.0:8050
"""

import numpy as np
import dash
from dash import dcc, html, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

import simulation as sim

# ── App ───────────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG],
    title="AeroSim",
    suppress_callback_exceptions=True,
)
server = app.server


# ══════════════════════════════════════════════════════════════════════════════
#  MOTORES
# ══════════════════════════════════════════════════════════════════════════════

ENGINE_CONFIGS = {
    "OneSpoolEngine": {
        "label":    "Turbojet Monoeje",
        "subtitle": "Single Spool Turbojet",
        "icon":     "◈",
        "color":    "#00c8ff",
        "specs": [
            ("Ejes",       "1"),
            ("Aplicacion", "Caza / Misil"),
            ("Mach max",   "2.5+"),
            ("OPR tipico", "10–20"),
        ],
        "desc": (
            "Un unico eje acopla directamente el compresor con la turbina. "
            "Arquitectura simple y robusta, ideal para aplicaciones militares "
            "y velocidades supersonicas. Bajo bypass ratio, alta velocidad de salida."
        ),
        "sliders": [
            ("os_alt",  "Altitud [m]",         0,    12000, 0,    100),
            ("os_t0",   "Temperatura T0 [C]",  -70,  50,    15,   1),
            ("os_mach", "Mach",                0,    2.5,   0,    0.01),
            ("os_G",    "Flujo masico [kg/s]", 5,    200,   20,   1),
            ("os_pi",   "OPR compresor",        2,    30,    10,   0.1),
            ("os_tit",  "TIT [K]",             800,  1800,  1400, 5),
            ("os_ec",   "eta compresor",        0.6,  0.99,  0.80, 0.01),
            ("os_et",   "eta turbina",          0.6,  0.99,  0.88, 0.01),
        ],
        "runner": lambda p: sim.run_one_spool(
            alt=p["os_alt"], t0_c=p["os_t0"], mach=p["os_mach"], G=p["os_G"],
            pi_23=p["os_pi"], tit=p["os_tit"],
            eta_c=p["os_ec"], eta_t=p["os_et"],
        ),
        "sweep_params": lambda p: {
            "alt": p["os_alt"], "t0_c": p["os_t0"], "mach": p["os_mach"],
            "G": p["os_G"], "pi_23": p["os_pi"], "tit": p["os_tit"],
            "eta_c": p["os_ec"], "eta_t": p["os_et"],
        },
    },

    "TwinSpoolEngine": {
        "label":    "Turbojet Bieje",
        "subtitle": "Twin Spool Turbojet",
        "icon":     "⬡",
        "color":    "#ff6b1a",
        "specs": [
            ("Ejes",       "2 (LP + HP)"),
            ("Aplicacion", "Militar / Civil"),
            ("Mach max",   "2.0+"),
            ("OPR tipico", "15–30"),
        ],
        "desc": (
            "Dos ejes independientes: el LP mueve el compresor de baja presion "
            "y el HP el de alta. Permite optimizar la velocidad de cada etapa "
            "de compresion, mejorando el rendimiento y la estabilidad operacional."
        ),
        "sliders": [
            ("ts_alt",   "Altitud [m]",         0,    12000, 0,     100),
            ("ts_t0",    "Temperatura T0 [C]",  -70,  50,    15,    1),
            ("ts_mach",  "Mach",                0,    2.5,   0,     0.01),
            ("ts_G",     "Flujo masico [kg/s]", 5,    200,   20,    1),
            ("ts_pilpc", "OPR compresor LP",     1.1,  6,     1.6,   0.1),
            ("ts_pihpc", "OPR compresor HP",     2,    25,    12,    0.1),
            ("ts_tit",   "TIT [K]",             800,  1900,  1450,  5),
            ("ts_elpc",  "eta comp. LP",         0.6,  0.99,  0.91,  0.01),
            ("ts_ehpc",  "eta comp. HP",         0.6,  0.99,  0.85,  0.01),
            ("ts_elpt",  "eta turb. LP",         0.6,  0.99,  0.94,  0.01),
            ("ts_ehpt",  "eta turb. HP",         0.6,  0.99,  0.92,  0.01),
        ],
        "runner": lambda p: sim.run_twin_spool(
            alt=p["ts_alt"], t0_c=p["ts_t0"], mach=p["ts_mach"], G=p["ts_G"],
            pi_lpc=p["ts_pilpc"], pi_hpc=p["ts_pihpc"], tit=p["ts_tit"],
            eta_lpc=p["ts_elpc"], eta_hpc=p["ts_ehpc"],
            eta_lpt=p["ts_elpt"], eta_hpt=p["ts_ehpt"],
        ),
        "sweep_params": lambda p: {
            "alt": p["ts_alt"], "t0_c": p["ts_t0"], "mach": p["ts_mach"],
            "G": p["ts_G"], "pi_lpc": p["ts_pilpc"], "pi_hpc": p["ts_pihpc"],
            "tit": p["ts_tit"], "eta_lpc": p["ts_elpc"], "eta_hpc": p["ts_ehpc"],
            "eta_lpt": p["ts_elpt"], "eta_hpt": p["ts_ehpt"],
        },
    },

    "SingleFlowTurbofan": {
        "label":    "Turbofan",
        "subtitle": "Single Flow Turbofan",
        "icon":     "⊕",
        "color":    "#00ff9d",
        "specs": [
            ("Ejes",       "2 (Fan + HP)"),
            ("Aplicacion", "Aviacion comercial"),
            ("Mach max",   "0.9"),
            ("BPR tipico", "0.5–1.5"),
        ],
        "desc": (
            "El fan comprime tanto el flujo primario (nucleo) como el secundario "
            "(bypass). La turbina LP mueve el fan, la HP el compresor de nucleo. "
            "Compromiso entre empuje y consumo para aviacion subsonica."
        ),
        "sliders": [
            ("tf_alt",   "Altitud [m]",              0,    12000, 0,    100),
            ("tf_t0",    "Temperatura T0 [C]",       -70,  50,    15,   1),
            ("tf_mach",  "Mach",                     0,    1.0,   0,    0.01),
            ("tf_G",     "Flujo masico total [kg/s]",10,   500,   90,   5),
            ("tf_pi",    "OPR nucleo",                2,    40,    25,   0.1),
            ("tf_tit",   "TIT [K]",                  800,  2000,  1500, 5),
            ("tf_pifan", "OPR fan",                  1.1,  3.0,   1.4,  0.05),
            ("tf_bpr",   "Bypass Ratio",             0.1,  12,    0.8,  0.1),
            ("tf_ec",    "eta nucleo",                0.6,  0.99,  1.0,  0.01),
            ("tf_efan",  "eta fan",                  0.6,  0.99,  1.0,  0.01),
            ("tf_ehpt",  "eta turb. HP",             0.6,  0.99,  1.0,  0.01),
            ("tf_elpt",  "eta turb. LP",             0.6,  0.99,  1.0,  0.01),
        ],
        "runner": lambda p: sim.run_turbofan(
            alt=p["tf_alt"], t0_c=p["tf_t0"], mach=p["tf_mach"], G=p["tf_G"],
            pi_23=p["tf_pi"], tit=p["tf_tit"],
            pi_fan=p["tf_pifan"], bpr=p["tf_bpr"],
            eta_c=p["tf_ec"], eta_fan=p["tf_efan"],
            eta_hpt=p["tf_ehpt"], eta_lpt=p["tf_elpt"],
        ),
        "sweep_params": lambda p: {
            "alt": p["tf_alt"], "t0_c": p["tf_t0"], "mach": p["tf_mach"],
            "G": p["tf_G"], "pi_23": p["tf_pi"], "tit": p["tf_tit"],
            "pi_fan": p["tf_pifan"], "bpr": p["tf_bpr"],
            "eta_c": p["tf_ec"], "eta_fan": p["tf_efan"],
            "eta_hpt": p["tf_ehpt"], "eta_lpt": p["tf_elpt"],
        },
    },

    "OneSpoolTurboprop": {
        "label":    "Turboprop",
        "subtitle": "Single Spool Turboprop",
        "icon":     "✦",
        "color":    "#ffcc00",
        "specs": [
            ("Ejes",       "2 (HP + LP)"),
            ("Aplicacion", "Regional / Carga"),
            ("Mach max",   "0.6"),
            ("OPR tipico", "10–25"),
        ],
        "desc": (
            "La mayor parte de la energia se extrae para mover una helice "
            "a traves de una caja reductora. La tobera residual aporta empuje "
            "adicional. Excelente eficiencia propulsiva a baja velocidad."
        ),
        "sliders": [
            ("tp_alt",  "Altitud [m]",              0,    8000,  0,     100),
            ("tp_t0",   "Temperatura T0 [C]",       -50,  50,    15,    1),
            ("tp_mach", "Mach",                     0,    0.7,   0,     0.01),
            ("tp_G",    "Flujo masico [kg/s]",      5,    200,   90,    1),
            ("tp_pi",   "OPR compresor",             2,    30,    25,    0.1),
            ("tp_tit",  "TIT [K]",                  800,  1700,  1500,  5),
            ("tp_Wh",   "Potencia eje [kW]",         10,   2000,  200,   10),
            ("tp_etam", "eta mecanica",              0.5,  0.99,  0.70,  0.01),
            ("tp_ec",   "eta compresor",             0.6,  0.99,  1.0,   0.01),
            ("tp_ehpt", "eta turb. HP",              0.6,  0.99,  1.0,   0.01),
            ("tp_elpt", "eta turb. LP",              0.6,  0.99,  1.0,   0.01),
        ],
        "runner": lambda p: sim.run_turboprop(
            alt=p["tp_alt"], t0_c=p["tp_t0"], mach=p["tp_mach"], G=p["tp_G"],
            pi_23=p["tp_pi"], tit=p["tp_tit"],
            W_h=p["tp_Wh"] * 1000, eta_m=p["tp_etam"],
            eta_c=p["tp_ec"], eta_hpt=p["tp_ehpt"], eta_lpt=p["tp_elpt"],
        ),
        "sweep_params": lambda p: {
            "alt": p["tp_alt"], "t0_c": p["tp_t0"], "mach": p["tp_mach"],
            "G": p["tp_G"], "pi_23": p["tp_pi"], "tit": p["tp_tit"],
            "W_h": p["tp_Wh"] * 1000, "eta_m": p["tp_etam"],
            "eta_c": p["tp_ec"], "eta_hpt": p["tp_ehpt"], "eta_lpt": p["tp_elpt"],
        },
    },
}

ALL_SLIDER_IDS = [
    sid
    for cfg in ENGINE_CONFIGS.values()
    for sid, *_ in cfg["sliders"]
]


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def make_slider(sid, label, mn, mx, dfl, stp):
    return html.Div([
        html.Div([
            html.Span(label, style={"fontSize":"10px","color":"#4a6a8a",
                                    "fontFamily":"Barlow Condensed","letterSpacing":"1px"}),
            html.Span(id=f"val-{sid}", style={"fontFamily":"Share Tech Mono",
                                               "fontSize":"11px","color":"#00c8ff"}),
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


def _dark_layout(title):
    return dict(
        title=dict(text=title, font=dict(color="#4a6a8a", size=11,
                   family="Barlow Condensed"), x=0.01, y=0.97),
        plot_bgcolor="#080c12", paper_bgcolor="#0d1520",
        font=dict(color="#c8dff0", family="Share Tech Mono"),
        margin=dict(l=48, r=16, t=34, b=38), hovermode="x unified",
    )

def _ax():
    return dict(
        gridcolor="#1a3a5c", gridwidth=0.5, linecolor="#1a3a5c",
        tickfont=dict(size=9, family="Share Tech Mono", color="#4a6a8a"),
        title_font=dict(size=10, family="Share Tech Mono", color="#4a6a8a"),
        zeroline=False,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  PANTALLA 1 — MENÚ DE SELECCIÓN
# ══════════════════════════════════════════════════════════════════════════════

def make_engine_card(eid, cfg):
    """Tarjeta grande para la pantalla de selección."""
    specs_els = [
        html.Div([
            html.Span(k, style={"color":"#4a6a8a","fontSize":"9px",
                                "fontFamily":"Barlow Condensed","letterSpacing":"2px",
                                "textTransform":"uppercase","display":"block"}),
            html.Span(v, style={"color":"#c8dff0","fontSize":"13px",
                                "fontFamily":"Share Tech Mono"}),
        ], style={"marginBottom":"8px"})
        for k, v in cfg["specs"]
    ]

    return html.Div([
        # Barra de color superior
        html.Div(style={"height":"3px","background":cfg["color"],
                        "marginBottom":"20px"}),
        # Icono + nombre
        html.Div([
            html.Span(cfg["icon"], style={
                "fontSize":"36px","color":cfg["color"],
                "display":"block","marginBottom":"12px",
                "filter":f"drop-shadow(0 0 8px {cfg['color']}60)",
            }),
            html.Div(cfg["label"], style={
                "fontFamily":"Barlow Condensed","fontWeight":"900",
                "fontSize":"20px","letterSpacing":"3px","textTransform":"uppercase",
                "color":"#c8dff0","marginBottom":"4px",
            }),
            html.Div(cfg["subtitle"], style={
                "fontFamily":"Share Tech Mono","fontSize":"10px",
                "color":cfg["color"],"letterSpacing":"2px","marginBottom":"16px",
            }),
        ]),
        # Descripción
        html.P(cfg["desc"], style={
            "fontFamily":"Barlow","fontWeight":"300","fontSize":"12px",
            "color":"#6a8aaa","lineHeight":"1.6","marginBottom":"20px",
        }),
        # Specs
        html.Div(specs_els, style={
            "borderTop":"1px solid #1a3a5c","paddingTop":"16px","marginBottom":"20px",
        }),
        # Botón
        html.Div([
            html.Button("SELECCIONAR  →", id=f"btn-select-{eid}", n_clicks=0,
                        style={
                            "background":"transparent","border":f"1px solid {cfg['color']}",
                            "color":cfg["color"],"fontFamily":"Barlow Condensed",
                            "fontWeight":"700","fontSize":"11px","letterSpacing":"3px",
                            "padding":"8px 20px","cursor":"pointer","width":"100%",
                            "textTransform":"uppercase","transition":"all 0.2s",
                        }),
        ]),
    ], id=f"menu-card-{eid}", style={
        "background":"#0d1520","border":"1px solid #1a3a5c",
        "padding":"24px","cursor":"pointer","height":"100%",
        "transition":"border-color 0.2s, box-shadow 0.2s",
        "position":"relative","overflow":"hidden",
    })


menu_screen = html.Div([
    # Fondo con grid
    html.Div(style={
        "position":"fixed","inset":"0","pointerEvents":"none","zIndex":"0",
        "backgroundImage":(
            "linear-gradient(rgba(0,200,255,.03) 1px,transparent 1px),"
            "linear-gradient(90deg,rgba(0,200,255,.03) 1px,transparent 1px)"
        ),
        "backgroundSize":"40px 40px",
    }),

    # Header
    html.Div([
        html.Div([
            html.Div("AEROSIM", style={
                "fontFamily":"Barlow Condensed","fontWeight":"900",
                "fontSize":"48px","letterSpacing":"12px","color":"#00c8ff",
                "lineHeight":"1",
                "textShadow":"0 0 40px rgba(0,200,255,0.3)",
            }),
            html.Div("SIMULADOR DE AERORREACTORES", style={
                "fontFamily":"Share Tech Mono","fontSize":"11px","color":"#4a6a8a",
                "letterSpacing":"6px","marginTop":"8px",
            }),
            html.Div(style={
                "width":"60px","height":"2px","background":"#00c8ff",
                "margin":"16px auto","opacity":"0.6",
            }),
            html.P("Selecciona el tipo de motor para comenzar la simulacion", style={
                "fontFamily":"Barlow","fontWeight":"300","fontSize":"14px",
                "color":"#6a8aaa","margin":"0",
            }),
        ], style={"textAlign":"center","paddingTop":"60px","paddingBottom":"48px"}),
    ]),

    # Grid de tarjetas
    dbc.Container([
        dbc.Row([
            dbc.Col(make_engine_card(eid, cfg), width=3, className="mb-3")
            for eid, cfg in ENGINE_CONFIGS.items()
        ], className="g-3"),
    ], fluid=True, style={"maxWidth":"1400px","margin":"0 auto","padding":"0 24px"}),

    # Footer
    html.Div("AeroSim v4.0  ·  components.py  ·  © 2025", style={
        "textAlign":"center","fontFamily":"Share Tech Mono","fontSize":"10px",
        "color":"#1a3a5c","padding":"32px","marginTop":"24px",
    }),

], id="screen-menu", style={
    "minHeight":"100vh","background":"#080c12","position":"relative","zIndex":"1",
})


# ══════════════════════════════════════════════════════════════════════════════
#  PANTALLA 2 — SIMULADOR
# ══════════════════════════════════════════════════════════════════════════════

# Todos los sliders en DOM (visibles/ocultos según motor activo)
all_slider_groups = []
for eid, cfg in ENGINE_CONFIGS.items():
    group = [make_slider(sid, lbl, mn, mx, dfl, stp)
             for sid, lbl, mn, mx, dfl, stp in cfg["sliders"]]
    all_slider_groups.append(
        html.Div(group, id=f"sliders-{eid}", style={"display":"none"})
    )

sim_screen = html.Div([

    # Navbar
    html.Div([
        html.Div([
            # Botón volver
            html.Button("← MENU", id="btn-back", n_clicks=0, style={
                "background":"transparent","border":"1px solid #1a3a5c",
                "color":"#4a6a8a","fontFamily":"Barlow Condensed","fontWeight":"700",
                "fontSize":"10px","letterSpacing":"2px","padding":"4px 12px",
                "cursor":"pointer","marginRight":"20px","transition":"all 0.2s",
            }),
            html.Span("AEROSIM", style={
                "fontFamily":"Barlow Condensed","fontWeight":"900",
                "fontSize":"18px","letterSpacing":"4px","color":"#00c8ff",
            }),
        ], style={"display":"flex","alignItems":"center"}),
        html.Div([
            html.Span("● LIVE", className="nav-badge live me-3"),
            html.Span(id="sim-engine-label", className="nav-badge me-3"),
            html.Span("SESION: LAB-04", className="nav-badge"),
        ], style={"display":"flex","alignItems":"center"}),
    ], className="aerosim-nav"),

    # Alerta TIT
    html.Div(id="alert-tit", style={"display":"none"}, className="alert-tit mx-3 mt-2"),

    # Cuerpo
    dbc.Container([
        dbc.Row([

            # Izquierda: sliders del motor activo
            dbc.Col([
                html.Div(id="sim-engine-title", className="section-head mt-3"),
                html.Div(all_slider_groups, id="all-sliders-wrapper"),
            ], width=3, style={
                "background":"#0d1520","borderRight":"1px solid #1a3a5c",
                "paddingLeft":"14px","paddingRight":"14px",
                "overflowY":"auto","height":"calc(100vh - 80px)",
            }),

            # Centro: métricas + gráficas
            dbc.Col([
                dbc.Row([
                    dbc.Col(metric_card("Empuje neto",    "thrust", "kN",     "good"), width=4),
                    dbc.Col(metric_card("TIT",            "tit",    "K",      "hot"),  width=4),
                    dbc.Col(metric_card("TSFC",           "tsfc",   "mg/N s", ""),      width=4),
                ], className="mt-3 mb-1 g-1"),
                dbc.Row([
                    dbc.Col(metric_card("eta Termico",    "etath",  "%",   ""),    width=3),
                    dbc.Col(metric_card("eta Propulsivo", "etaprop","%",   ""),    width=3),
                    dbc.Col(metric_card("eta Global",     "etag",   "%",   "good"),width=3),
                    dbc.Col(metric_card("Combustible",    "fuel",   "kg/s","warn"),width=3),
                ], className="mb-1 g-1"),
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
            ], width=7, style={"overflowY":"auto","height":"calc(100vh - 80px)","paddingRight":"0"}),

            # Derecha: telemetría
            dbc.Col([
                html.Div("Telemetria", className="section-head mt-3"),
                html.Table(id="tele-table", className="tele-table w-100"),
            ], width=2, style={
                "background":"#0d1520","borderLeft":"1px solid #1a3a5c",
                "paddingLeft":"12px","paddingRight":"12px",
                "overflowY":"auto","height":"calc(100vh - 80px)",
            }),

        ], className="g-0"),
    ], fluid=True, style={"padding":"0"}),

], id="screen-sim", style={"display":"none", "minHeight":"100vh", "background":"#080c12"})


# ══════════════════════════════════════════════════════════════════════════════
#  LAYOUT RAÍZ
# ══════════════════════════════════════════════════════════════════════════════

app.layout = html.Div([
    dcc.Store(id="active-engine", data=None),
    menu_screen,
    sim_screen,
])


# ══════════════════════════════════════════════════════════════════════════════
#  CALLBACKS
# ══════════════════════════════════════════════════════════════════════════════

# 1. Seleccionar motor desde el menú → ir al simulador
@app.callback(
    Output("active-engine",  "data"),
    Output("screen-menu",    "style"),
    Output("screen-sim",     "style"),
    Output("sim-engine-label", "children"),
    Output("sim-engine-title", "children"),
    *[Output(f"sliders-{eid}", "style") for eid in ENGINE_CONFIGS],
    *[Input(f"btn-select-{eid}", "n_clicks") for eid in ENGINE_CONFIGS],
    Input("btn-back", "n_clicks"),
    State("active-engine", "data"),
    prevent_initial_call=True,
)
def navigate(*args):
    n_engines = len(ENGINE_CONFIGS)
    btn_back_clicks = args[n_engines]
    current_engine  = args[n_engines + 1]

    triggered = ctx.triggered_id or ""

    # Volver al menú
    if triggered == "btn-back":
        slider_styles = [{"display":"none"}] * n_engines
        return (
            current_engine,
            {"minHeight":"100vh","background":"#080c12","position":"relative","zIndex":"1"},
            {"display":"none","minHeight":"100vh","background":"#080c12"},
            "", "",
            *slider_styles,
        )

    # Seleccionar motor
    new_engine = None
    for eid in ENGINE_CONFIGS:
        if triggered == f"btn-select-{eid}":
            new_engine = eid
            break

    if new_engine is None:
        raise dash.exceptions.PreventUpdate

    cfg = ENGINE_CONFIGS[new_engine]
    slider_styles = [
        {"display":"block"} if eid == new_engine else {"display":"none"}
        for eid in ENGINE_CONFIGS
    ]

    nav_label = cfg["label"].upper()
    section_title = f"{cfg['icon']}  {cfg['label'].upper()}"

    return (
        new_engine,
        {"display":"none"},
        {"minHeight":"100vh","background":"#080c12"},
        nav_label,
        section_title,
        *slider_styles,
    )


# 2. Labels de sliders en tiempo real
@app.callback(
    *[Output(f"val-{sid}", "children") for sid in ALL_SLIDER_IDS],
    *[Input(f"sl-{sid}", "value") for sid in ALL_SLIDER_IDS],
)
def update_labels(*vals):
    result = []
    for sid, val in zip(ALL_SLIDER_IDS, vals):
        if val is None:
            result.append(""); continue
        if any(x in sid for x in ["mach","ec","et","efan","ehpt","elpt","elpc","ehpc","etam"]):
            result.append(f"{val:.2f}")
        elif any(x in sid for x in ["tit","alt"]):
            result.append(f"{int(val):,}")
        elif any(x in sid for x in ["bpr","pi","pifan"]):
            result.append(f"{val:.2f}")
        else:
            result.append(f"{val:.1f}")
    return result


# 3. Simulación principal
@app.callback(
    Output("m-thrust",  "children"),
    Output("m-tit",     "children"),
    Output("m-tsfc",    "children"),
    Output("m-etath",   "children"),
    Output("m-etaprop", "children"),
    Output("m-etag",    "children"),
    Output("m-fuel",    "children"),
    Output("graph-ts",  "figure"),
    Output("graph-eta", "figure"),
    Output("graph-tit", "figure"),
    Output("graph-opr", "figure"),
    Output("tele-table",  "children"),
    Output("alert-tit",   "children"),
    Output("alert-tit",   "style"),
    Input("active-engine", "data"),
    *[Input(f"sl-{sid}", "value") for sid in ALL_SLIDER_IDS],
)
def run_simulation(engine_type, *all_vals):
    if not engine_type:
        raise dash.exceptions.PreventUpdate

    cfg = ENGINE_CONFIGS[engine_type]

    # Parámetros del motor activo
    p = {}
    for sid, _, _, _, default, _ in cfg["sliders"]:
        idx = ALL_SLIDER_IDS.index(sid)
        p[sid] = all_vals[idx] if all_vals[idx] is not None else default

    # Física
    try:
        r = cfg["runner"](p)
    except Exception as e:
        empty = go.Figure().update_layout(**_dark_layout(f"Error: {e}"))
        err_row = [html.Tr([html.Td("Error", className="tele-key"),
                            html.Td(str(e)[:80], className="tele-val")])]
        return ["--"]*7 + [empty]*4 + [err_row, str(e), {"display":"block"}]

    tit_val = r["Tt4_K"]
    color   = cfg["color"]

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

    sweep_p = cfg["sweep_params"](p)

    # T-s
    Pt0 = max(r["Pt0_kPa"], 0.001)
    Pt3 = max(r["Pt3_kPa"], 0.001)
    T1,T2,T3,T4 = r["T0_K"], r["Tt3_K"], r["Tt4_K"], r["Tt5_K"]
    s1=0; s2=-0.3*np.log(Pt3/Pt0); s3=s2
    s4 = s3 + 0.4*np.log(max(T3,1)/max(T4,1))
    fig_ts = go.Figure()
    fig_ts.add_trace(go.Scatter(
        x=[s1,s2,s3,s4,s1], y=[T1,T2,T3,T4,T1],
        mode="lines+markers", line=dict(color=color, width=2),
        marker=dict(size=8, symbol="diamond",
                    color=["#00ff9d", color, "#ff6b1a", "#ffcc00", "#00ff9d"]),
        fill="toself", fillcolor=f"rgba({_hex_to_rgb(color)},0.04)",
        hovertemplate="s=%{x:.2f}<br>T=%{y:.0f} K<extra></extra>",
    ))
    for sx,tx,lbl in [(s1,T1,"Admision"),(s2,T2,"Compresor"),
                       (s3,T3,"Combustion"),(s4,T4,"Turbina")]:
        fig_ts.add_annotation(x=sx, y=tx, text=lbl,
                               font=dict(color="#c8dff0",size=9,family="Share Tech Mono"),
                               showarrow=False, yshift=12)
    fig_ts.update_layout(**_dark_layout("Diagrama T-s"))
    fig_ts.update_xaxes(title_text="Entropia rel.", **_ax())
    fig_ts.update_yaxes(title_text="T [K]", **_ax())

    # Rendimientos
    fig_eta = go.Figure()
    for c,v,col in [("eta Term.",r["eta_th"],"#00c8ff"),
                    ("eta Prop.",r["eta_prop"],"#ff6b1a"),
                    ("eta Global",r["eta_global"],color)]:
        fig_eta.add_trace(go.Bar(
            x=[c], y=[v], marker_color=col, marker_line_width=0,
            text=[f"{v:.1f}%"], textposition="outside",
            textfont=dict(color="#c8dff0",size=11,family="Share Tech Mono"), name=c,
        ))
    fig_eta.update_layout(**_dark_layout("Rendimientos"), showlegend=False,
                           yaxis_range=[0,110], bargap=0.35)
    fig_eta.update_xaxes(**_ax())
    fig_eta.update_yaxes(title_text="%", **_ax())

    # Empuje vs TIT (con punto actual marcado)
    tit_data = sim.sweep_tit(engine_type, sweep_p)
    tits_x, thrusts_y = zip(*tit_data) if tit_data else ([],[])
    fig_tit = go.Figure()
    fig_tit.add_trace(go.Scatter(
        x=list(tits_x), y=list(thrusts_y), mode="lines",
        line=dict(color="#ff6b1a", width=2),
        fill="tozeroy", fillcolor="rgba(255,107,26,0.06)", name="Barrido",
    ))
    fig_tit.add_trace(go.Scatter(
        x=[tit_val], y=[r["thrust_kN"]], mode="markers",
        marker=dict(size=10, color=color, symbol="diamond",
                    line=dict(color="#fff", width=1)),
        name="Punto actual",
    ))
    fig_tit.update_layout(**_dark_layout("Empuje vs TIT"), showlegend=False)
    fig_tit.update_xaxes(title_text="TIT [K]",  **_ax())
    fig_tit.update_yaxes(title_text="F [kN]",    **_ax())

    # 4ª: BPR o OPR sweep
    if engine_type == "SingleFlowTurbofan":
        bpr_data = sim.sweep_bpr(sweep_p)
        bprs_x, tsfcs_y = zip(*bpr_data) if bpr_data else ([],[])
        cur_bpr = p.get("tf_bpr", 0.8)
        fig_opr = go.Figure()
        fig_opr.add_trace(go.Scatter(
            x=list(bprs_x), y=list(tsfcs_y), mode="lines",
            line=dict(color="#00c8ff", width=2), name="Barrido",
        ))
        fig_opr.add_trace(go.Scatter(
            x=[cur_bpr], y=[r["TSFC_mg"]], mode="markers",
            marker=dict(size=10, color=color, symbol="diamond",
                        line=dict(color="#fff", width=1)),
            name="Punto actual",
        ))
        fig_opr.update_layout(**_dark_layout("TSFC vs BPR"), showlegend=False)
        fig_opr.update_xaxes(title_text="Bypass Ratio", **_ax())
        fig_opr.update_yaxes(title_text="TSFC [mg/N s]", **_ax())
    else:
        opr_data = sim.sweep_opr(engine_type, sweep_p)
        oprs_x, etas_y = zip(*opr_data) if opr_data else ([],[])
        fig_opr = go.Figure()
        fig_opr.add_trace(go.Scatter(
            x=list(oprs_x), y=list(etas_y), mode="lines",
            line=dict(color="#00ff9d", width=2), name="Barrido",
        ))
        fig_opr.update_layout(**_dark_layout("eta Term. vs OPR"), showlegend=False)
        fig_opr.update_xaxes(title_text="OPR",            **_ax())
        fig_opr.update_yaxes(title_text="eta Term. [%]",  **_ax())

    # Telemetría
    df = r.get("df")
    tele_rows = []
    if df is not None:
        for station in df.index:
            try:
                Tv = float(df.loc[station,"T"])
                cls_t = "hot" if Tv>1200 else ("warn" if Tv>800 else "")
                tele_rows.append((f"T [{station}]", f"{Tv:.1f} K", cls_t))
            except (TypeError, ValueError):
                pass
            try:
                Pv = float(df.loc[station,"P"])
                tele_rows.append((f"P [{station}]", f"{Pv/1000:.2f} kPa", ""))
            except (TypeError, ValueError):
                pass

    tele_rows += [
        ("---", "", ""),
        ("V jet",    f"{r['V_jet']:.1f} m/s",    "good"),
        ("V bypass", f"{r['V_bypass']:.1f} m/s",  ""),
        ("V0",       f"{r['V0']:.1f} m/s",        ""),
        ("FAR",      f"{r['FAR']:.5f}",            ""),
        ("EGT",      f"{r['EGT']:.0f} K",          "warn"),
        ("Pot eje",  f"{r['shaft_MW']:.3f} MW",    ""),
        ("m core",   f"{r['m_core']:.2f} kg/s",    ""),
        ("m bypass", f"{r['m_bypass']:.2f} kg/s",  ""),
    ]
    if engine_type == "OneSpoolTurboprop":
        tele_rows += [
            ("F helice",   f"{r.get('F_helice_kN',0):.2f} kN", "good"),
            ("F residual", f"{r.get('F_resid_kN', 0):.2f} kN", ""),
        ]

    table = []
    for k,v,cls in tele_rows:
        if k == "---":
            table.append(html.Tr([html.Td(
                "ACTUACIONES", colSpan=2,
                style={"color":"#1a3a5c","fontSize":"9px","paddingTop":"8px",
                       "fontFamily":"Share Tech Mono","letterSpacing":"2px"})]))
        else:
            table.append(html.Tr([
                html.Td(k, className="tele-key"),
                html.Td(v, className=f"tele-val {cls}"),
            ]))

    # Alerta
    tit_limit = r.get("tit_limit", 1700)
    if tit_val > tit_limit:
        alert_msg   = f"ADVERTENCIA  —  TIT {tit_val:.0f} K > LIMITE {tit_limit} K  —  RIESGO FALLO DE ALABE"
        alert_style = {"display":"block"}
    else:
        alert_msg, alert_style = "", {"display":"none"}

    return metrics + [fig_ts, fig_eta, fig_tit, fig_opr, table, alert_msg, alert_style]


def _hex_to_rgb(hex_color):
    """Convierte #rrggbb a 'r,g,b' para usar en rgba()."""
    h = hex_color.lstrip("#")
    r,g,b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"{r},{g},{b}"


if __name__ == "__main__":
    app.run(debug=True)
