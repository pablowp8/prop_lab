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
from engine_diagrams import build_engine_diagram

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
            ("os_p0",   "P\u2080 [kPa]",   20,  105,  101.3, 0.1),
            ("os_mach", "M\u2080",           0,  2.5,    0,   0.01),
        ],
        # ── Sección 2: Punto de diseño ───────────────────────────────────────
        "sliders_diseno": [
            ("os_tit",  "T\u2084\u209C [K]",   800, 1800, 1400,  5),
            ("os_pi",   "\u03C0\u2082\u2083",  2,   30,   10,  0.1),
            ("os_G",    "G [kg/s]",         5,  200,   20,   1),
        ],
        # ── Sección 3: Componentes ───────────────────────────────────────────
        "sliders_comp": [
            ("os_edif",  "\u03B7 difusor",    0.6, 0.99, 0.99, 0.01),
            ("os_ec",    "\u03B7 compresor",  0.6, 0.99, 0.80, 0.01),
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
            eta_c=p["tf_ec"], eta_fan=p["tf_efan"],
            eta_hpt=p["tf_ehpt"], eta_lpt=p["tf_elpt"],
        ),
        "sweep_base": lambda p: {
            "T_amb": p["tf_t0"] + 273.15, "P_amb": p["tf_p0"] * 1000,
            "mach":p["tf_mach"],    "G":p["tf_G"],
            "pi_23":p["tf_pi"],     "tit":p["tf_tit"],
            "pi_fan":p["tf_pifan"], "bpr":p["tf_bpr"],
            "eta_c":p["tf_ec"],     "eta_fan":p["tf_efan"],
            "eta_hpt":p["tf_ehpt"], "eta_lpt":p["tf_elpt"],
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
            eta_c=p["tp_ec"], eta_hpt=p["tp_ehpt"], eta_lpt=p["tp_elpt"],
        ),
        "sweep_base": lambda p: {
            "T_amb": p["tp_t0"] + 273.15, "P_amb": p["tp_p0"] * 1000,
            "mach":p["tp_mach"],  "G":p["tp_G"],
            "pi_23":p["tp_pi"],   "tit":p["tp_tit"],
            "W_h":p["tp_Wh"]*1000, "eta_m":p["tp_etam"],
            "eta_c":p["tp_ec"],   "eta_hpt":p["tp_ehpt"], "eta_lpt":p["tp_elpt"],
        },
    },
}

ALL_SLIDER_IDS = [
    sid
    for cfg in ENGINE_CONFIGS.values()
    for section in ("sliders_vuelo", "sliders_diseno", "sliders_comp")
    for sid, *_ in cfg[section]
]

# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS UI
# ══════════════════════════════════════════════════════════════════════════════

def make_slider(sid, label, mn, mx, dfl, stp):
    return html.Div([
        html.Div([
            html.Span(label, style={"fontSize":"12px","color":C["dim"],
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
#  PANTALLA 1 — MENÚ
# ══════════════════════════════════════════════════════════════════════════════

def menu_engine_card(eid, cfg):
    return html.Div([
        html.Div(style={"height":"3px","background":cfg["color"],"marginBottom":"5px"}),
        html.Div(cfg["label"], style={"fontFamily":C["mono"],"fontWeight":"900","fontSize":"25px",
                                       "letterSpacing":"2px","textTransform":"uppercase",
                                       "color":C["text"],"marginBottom":"2px","color":cfg["color"]}),
        html.Div(cfg["subtitle"], style={"fontFamily":C["mono"],"fontSize":"14px",
                                          "color":cfg["color"],"letterSpacing":"2px",
                                          "marginBottom":"12px"}),
        html.Div(build_engine_diagram(eid, df=None),
                style={"marginBottom":"10px","overflow":"hidden","lineHeight":"0"},),                  
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
            html.Div("PROP-Lab", style={"fontFamily":C["head"],"fontWeight":"900",
                                        "fontSize":"50px","letterSpacing":"8px",
                                        "color":C["accent"],"lineHeight":"1","marginBottom":"8px","marginTop":"20px"}),
            html.Div("SIMULADOR DE AERORREACTORES", style={"fontFamily":C["mono"],
                                                            "fontSize":"14px","color":C["dim"],
                                                            "letterSpacing":"6px","marginBottom":"0px"}),
            html.P("Selecciona el tipo de motor para comenzar la fase de diseño",
                   style={"fontFamily":C["head"],"fontWeight":"300","fontSize":"14px","marginTop":"20px","color":C["dim"]}),
        ], style={"textAlign":"center"}),
    ]),
    dbc.Container(
    html.Div([menu_engine_card(eid, cfg)
            for eid, cfg in ENGINE_CONFIGS.items()],
        style={"display": "grid","gridTemplateColumns": "repeat(2, 1fr)","gap": "20px",
            "justifyContent": "center","maxWidth": "2000px","margin": "0 auto"}),
    fluid=True,style={"maxWidth": "2000px","margin": "0 auto","padding": "0 100px"}),
    html.Div("PROP-Lab v4.2  ·  components.py  ·  2025", style={
        "textAlign":"center","fontFamily":C["mono"],"fontSize":"14px",
        "color":C["border"],"padding":"32px","marginTop":"16px",
    }),
], id="screen-menu", style={"minHeight":"100vh","background":C["bg"],
                              "position":"relative","zIndex":"1"})


# ══════════════════════════════════════════════════════════════════════════════
#  PANTALLA 2 — SIMULADOR
# ══════════════════════════════════════════════════════════════════════════════

def section_head(title):
    """Cabecera de sección dentro del panel de sliders."""
    return html.Div(title, style={
        "fontSize":"12px", "fontFamily":C["head"], "fontWeight":"700",
        "letterSpacing":"3px", "textTransform":"uppercase",
        "color":C["border2"], "padding":"10px 0 4px 0",
        "borderTop":f"2px solid {C['text']}", 
        "marginTop":"10px", "marginBottom": "10px",
    })

all_slider_groups = []
SECTION_LABELS = {
    "sliders_vuelo":  "COND. VUELO",
    "sliders_diseno": "PTO. DISEÑO",
    "sliders_comp":   "COMPONENTES",
}
for eid, cfg in ENGINE_CONFIGS.items():
    group = []
    for section_key, section_title in SECTION_LABELS.items():
        group.append(section_head(section_title))
        for sid, lbl, mn, mx, dfl, stp in cfg[section_key]:
            group.append(make_slider(sid, lbl, mn, mx, dfl, stp))
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
            html.Span("PROP-Lab", style={"fontFamily":C["head"],"fontWeight":"900",
                                         "fontSize":"25px","letterSpacing":"5px",
                                         "color":C["accent"],"marginLeft":"16px"}),
        ], style={"display":"flex","alignItems":"center"}),
        html.Div([
            # html.Span("● LIVE",           className="nav-badge live me-2"),
            html.Span(id="sim-eng-label", className="nav-badge me-2"),
            # html.Span("SESION: LAB-04",   className="nav-badge"),
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
                # Esquema SVG del motor
                html.Div(id="engine-diagram",
                         className="graph-card mb-1",
                         style={"padding":"0","lineHeight":"0","overflow":"hidden"}),
                dbc.Row([
                    dbc.Col(metric_card("Empuje neto",    "thrust","kN",    "good"), width=4),
                    dbc.Col(metric_card("TSFC",           "tsfc",  "mg/Ns", ""),      width=4),
                    dbc.Col(metric_card("Combustible",    "fuel",   "kg/s","warn"),width=4),
                ], className="mt-3 mb-1 g-1"),
                dbc.Row([

                    dbc.Col(html.Div(dcc.Graph(id="graph-ts",   config={"displayModeBar":False}),
                                    className="graph-card"), width=6),
                    dbc.Col(html.Div(dcc.Graph(id="graph-comp", config={"displayModeBar":False}),
                                    className="graph-card"), width=6),

                ], className="g-1 mb-1"),
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
        html.Span("PROP-Lab v4.2 · 2025", style={"marginLeft":"auto"}),
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
        f"{cfg['label'].upper()}",
        *slider_styles,
    )


# Mapa sid → step, para decidir el formato del label
_SLIDER_STEP = {
    sid: stp
    for cfg in ENGINE_CONFIGS.values()
    for section in ("sliders_vuelo", "sliders_diseno", "sliders_comp")
    for sid, _, _, _, _, stp in cfg[section]
}

@app.callback(
    *[Output(f"val-{sid}", "children") for sid in ALL_SLIDER_IDS],
    *[Input(f"sl-{sid}",   "value")    for sid in ALL_SLIDER_IDS],
)
def update_labels(*vals):
    out = []
    for sid, v in zip(ALL_SLIDER_IDS, vals):
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
    Output("m-thrust",        "children"),
    Output("m-tsfc",          "children"),
    Output("m-fuel",          "children"),
    Output("graph-ts",        "figure"),


    Output("graph-comp",      "figure"),

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

    # Parámetros del motor activo — recorre las 3 secciones
    p = {}
    for section in ("sliders_vuelo", "sliders_diseno", "sliders_comp"):
        for sid, _, _, _, default, _ in cfg[section]:
            idx = ALL_SLIDER_IDS.index(sid)
            p[sid] = all_vals[idx] if all_vals[idx] is not None else default

    # Error path: devuelve exactamente 15 valores (7 métricas + 4 figs + tabla + msg + style + diagram)
    def _err(msg_str):
        ef = go.Figure().update_layout(**_plot_layout(f"Error"))
        et = [html.Tr([html.Td("Error", className="tele-key"),
                       html.Td(msg_str[:80], className="tele-val")])]
        ed = html.Div(msg_str[:120], style={"padding":"8px","fontFamily":C["mono"],
                                             "fontSize":"10px","color":C["accent2"]})
        return ["--"]*7 + [ef,ef, et, msg_str, {"display":"block"}, ed]

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


    return metrics + [fig_ts, fig_comp,

                      table, alert_msg, alert_style, diagram]


if __name__ == "__main__":
    app.run(debug=True)
