"""
engine_diagrams.py
Esquemas estáticos de motores para PROP-Lab.
Retorna dcc.Graph listo para insertar en el layout.

API pública:
    build_engine_diagram(engine_type, df)  ->  dcc.Graph
"""

from dash import dcc
import plotly.graph_objects as go

# ── Paleta (misma que C en app.py) ────────────────────────────────────────────
_C = {
    "panel":   "#f5f3ef",
    "border":  "#78736F",
    "border2": "#605B55",
    "dim":     "#616264",
    "accent":  "#1a4d8f",
    "accent2": "#b83232",
    "accent3": "#1a6644",
    "warn":    "#9c4d00",
}


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
#  MOTOR 1 — OneSpoolEngine   Turborreactor Monoeje  (esquema mejorado)
# ══════════════════════════════════════════════════════════════════════════════
#
#  Geometria inspirada en seccion transversal real.
#  Tobera convergente-divergente con garganta muy cerca de la salida (x=720)
#  para que visualmente se lea como convergente simple.
#
#  Estaciones: St.0 x=30  St.2 x=130  St.3 x=365
#              St.4 x=490 St.5 x=590  St.9 x=720
#  Todas las lineas de estacion tienen la misma altura (y0=0.14, y1=0.86).
#
def _build_onespool(df):
    S, A = [], []

    # ── Eje de simetria (referencia) ─────────────────────────────────────────
    S.append(dict(type="line", x0=10, x1=800, y0=0.50, y1=0.50,
                  line=dict(color=_C["border"], width=0.5, dash="dot")))

    # ── RELLENOS DE ZONA (por debajo de la carcasa) ───────────────────────────

    # Zona fria: difusor + compresor  (azul)
    S.append(dict(
        type="path",
        path=("M 20,0.50 "
              "C 38,0.33 62,0.24 120,0.22 "
              "L 365,0.22 L 365,0.78 "
              "C 62,0.76 38,0.67 20,0.50 Z"),
        fillcolor=_rgba("#4a90d9", 0.16),
        line=dict(color="rgba(0,0,0,0)", width=0),
        layer="below",
    ))

    # Zona caliente: camara + turbina  (rojo/naranja)
    S.append(dict(
        type="path",
        path=("M 365,0.22 L 590,0.24 "
              "C 640,0.27 680,0.33 720,0.38 "
              "L 720,0.62 "
              "C 680,0.67 640,0.73 590,0.76 "
              "L 365,0.78 Z"),
        fillcolor=_rgba("#cc4400", 0.16),
        line=dict(color="rgba(0,0,0,0)", width=0),
        layer="below",
    ))

    # Tobera CD  (morado)
    S.append(dict(
        type="path",
        path=("M 720,0.38 C 745,0.36 768,0.355 790,0.37 "
              "L 790,0.63 C 768,0.645 745,0.64 720,0.62 Z"),
        fillcolor=_rgba("#7055aa", 0.18),
        line=dict(color="rgba(0,0,0,0)", width=0),
        layer="below",
    ))

    # ── CARCASA EXTERIOR ──────────────────────────────────────────────────────
    # Superior
    S.append(dict(
        type="path",
        path=("M 20,0.50 "
              "C 38,0.33 62,0.24 120,0.22 "
              "L 590,0.22 "
              "C 640,0.22 680,0.27 720,0.38 "
              "C 745,0.36 768,0.355 790,0.37"),
        fillcolor="rgba(0,0,0,0)",
        line=dict(color="#444444", width=2.2),
    ))
    # Inferior (espejo)
    S.append(dict(
        type="path",
        path=("M 20,0.50 "
              "C 38,0.67 62,0.76 120,0.78 "
              "L 590,0.78 "
              "C 640,0.78 680,0.73 720,0.62 "
              "C 745,0.64 768,0.645 790,0.63"),
        fillcolor="rgba(0,0,0,0)",
        line=dict(color="#444444", width=2.2),
    ))

    # ── CONO DE ENTRADA (ojiva) ───────────────────────────────────────────────
    S.append(dict(
        type="path",
        path=("M 20,0.50 "
              "C 32,0.45 52,0.43 78,0.42 "
              "L 78,0.58 "
              "C 52,0.57 32,0.55 20,0.50 Z"),
        fillcolor=_rgba("#999999", 0.55),
        line=dict(color="#666666", width=1.3),
        layer="above",
    ))

    # ── EJE MECANICO DEL MOTOR ────────────────────────────────────────────────
    S.append(dict(
        type="rect", x0=78, x1=610, y0=0.466, y1=0.534,
        fillcolor=_rgba("#888888", 0.45),
        line=dict(color="#777777", width=0.8),
        layer="above",
    ))

    # ── PALAS DEL COMPRESOR (lineas diagonales, multi-etapa) ─────────────────
    # x: 130 a 358, paso 18
    for xi in range(135, 360, 18):
        S.append(dict(
            type="line", x0=xi, x1=xi + 7, y0=0.534, y1=0.225,
            line=dict(color=_rgba("#1a4d8f", 0.65), width=1.1),
        ))
        S.append(dict(
            type="line", x0=xi, x1=xi + 7, y0=0.466, y1=0.775,
            line=dict(color=_rgba("#1a4d8f", 0.65), width=1.1),
        ))

    # ── CAMARA DE COMBUSTION ──────────────────────────────────────────────────
    # Pared anular interior
    S.append(dict(
        type="path",
        path="M 370,0.30 L 370,0.70 L 485,0.70 L 485,0.30 Z",
        fillcolor=_rgba("#b83232", 0.10),
        line=dict(color="#b83232", width=1.0),
        layer="below",
    ))
    # Llama superior
    S.append(dict(
        type="path",
        path=("M 382,0.43 "
              "C 402,0.38 432,0.36 462,0.40 "
              "C 432,0.44 402,0.46 382,0.43 Z"),
        fillcolor=_rgba("#ff6600", 0.65),
        line=dict(color="#ff8800", width=0.5),
        layer="above",
    ))
    # Llama inferior
    S.append(dict(
        type="path",
        path=("M 382,0.57 "
              "C 402,0.54 432,0.56 462,0.60 "
              "C 432,0.64 402,0.62 382,0.57 Z"),
        fillcolor=_rgba("#ff6600", 0.65),
        line=dict(color="#ff8800", width=0.5),
        layer="above",
    ))
    # Inyector de combustible
    S.append(dict(type="line", x0=372, x1=385, y0=0.35, y1=0.43,
                  line=dict(color="#cc8800", width=2.0)))
    S.append(dict(type="line", x0=372, x1=385, y0=0.65, y1=0.57,
                  line=dict(color="#cc8800", width=2.0)))

    # ── PALAS DE LA TURBINA ───────────────────────────────────────────────────
    # x: 495 a 582, paso 18
    for xi in range(498, 582, 18):
        S.append(dict(
            type="line", x0=xi + 7, x1=xi, y0=0.534, y1=0.245,
            line=dict(color=_rgba("#cc5500", 0.70), width=1.2),
        ))
        S.append(dict(
            type="line", x0=xi + 7, x1=xi, y0=0.466, y1=0.755,
            line=dict(color=_rgba("#cc5500", 0.70), width=1.2),
        ))

    # ── GARGANTA DE LA TOBERA (linea de minimo area) ──────────────────────────
    S.append(dict(
        type="line", x0=720, x1=720, y0=0.38, y1=0.62,
        line=dict(color="#7055aa", width=1.0, dash="dash"),
    ))

    # ── CHORRO DE ESCAPE ──────────────────────────────────────────────────────
    S.append(dict(
        type="path",
        path=("M 790,0.37 C 820,0.38 855,0.42 875,0.50 "
              "C 855,0.58 820,0.62 790,0.63 Z"),
        fillcolor=_rgba("#ff5500", 0.28),
        line=dict(color="#ff7700", width=0.7),
        layer="below",
    ))
    S.append(dict(
        type="path",
        path=("M 790,0.42 C 818,0.44 845,0.47 865,0.50 "
              "C 845,0.53 818,0.56 790,0.58 Z"),
        fillcolor=_rgba("#ffaa00", 0.42),
        line=dict(color="#ffcc00", width=0.5),
        layer="below",
    ))

    # ── LINEAS DE ESTACION (misma altura todas) ───────────────────────────────
    ST_Y0, ST_Y1 = 0.14, 0.86
    STATIONS = [
        (30,  "0"),
        (130, "2"),
        (365, "3"),
        (490, "4"),
        (590, "5"),
        (720, "9"),
    ]
    for sx, slbl in STATIONS:
        S.append(dict(
            type="line", x0=sx, x1=sx, y0=ST_Y0, y1=ST_Y1,
            line=dict(color=_C["border"], width=0.9, dash="dot"),
        ))
        A.append(dict(
            x=sx, y=ST_Y0 - 0.05,
            text=f"<b>{slbl}</b>",
            showarrow=False,
            font=dict(size=8, color=_C["dim"], family="Share Tech Mono"),
            xref="x", yref="y", yanchor="top",
        ))

    # ── ETIQUETAS DE COMPONENTES (en español) ─────────────────────────────────
    COMP_LABELS = [
        ( 80,  "DIFUSOR",    "#4a7abf"),
        (247,  "COMPRESOR",  "#1a4d8f"),
        (427,  "CAMARA",     "#b83232"),
        (540,  "TURBINA",    "#cc5500"),
        (655,  "TOBERA",     "#7055aa"),
    ]
    for cx, name, col in COMP_LABELS:
        A.append(dict(
            x=cx, y=ST_Y1 + 0.05,
            text=f"<b>{name}</b>",
            showarrow=False,
            font=dict(size=8, color=col, family="Share Tech Mono"),
            xref="x", yref="y", yanchor="bottom",
        ))

    # ── FIGURA ────────────────────────────────────────────────────────────────
    fig = go.Figure()
    fig.update_layout(
        shapes=S,
        annotations=A,
        plot_bgcolor=_C["panel"],
        paper_bgcolor=_C["panel"],
        margin=dict(l=0, r=0, t=0, b=0),
        height=130,
        xaxis=dict(range=[0, 870], visible=False, fixedrange=True),
        yaxis=dict(range=[0, 1],   visible=False, fixedrange=True),
        showlegend=False,
    )
    return dcc.Graph(
        figure=fig,
        config={"displayModeBar": False, "staticPlot": True},
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
        line=dict(color=_C["border"], width=0.8, dash="dot"),
    ))
    A.append(dict(
        x=x, y=cy+0.35, text=f"T<sub>t{label}</sub>",
        showarrow=False,
        font=dict(size=8, color=_C["dim"], family="Share Tech Mono"),
        xref="x", yref="y",
    ))
    if t_val is not None:
        A.append(dict(
            x=x, y=cy+0.47, text=f"{t_val:.0f} K",
            showarrow=False,
            font=dict(size=7, color=_C["accent"], family="Share Tech Mono"),
            xref="x", yref="y",
        ))
    if p_val is not None:
        A.append(dict(
            x=x, y=cy-0.40, text=f"{p_val:.0f} kPa",
            showarrow=False,
            font=dict(size=7, color=_C["dim"], family="Share Tech Mono"),
            xref="x", yref="y",
        ))


def _build_original(engine_type, df):
    CK = {
        "intake": "#5a8abf", "fan": "#1a7a5a", "lpc": "#2a70b0",
        "hpc":    _C["accent"], "comb": _C["accent2"], "hpt": "#cc6600",
        "lpt":    _C["warn"],   "nozzle": "#7055aa",   "prop": _C["accent3"],
    }
    cy = 0.5
    S, A = [], []

    S.append(dict(type="line", x0=10, x1=790, y0=cy, y1=cy,
                  line=dict(color=_C["border"], width=0.5, dash="dot")))

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
        plot_bgcolor=_C["panel"], paper_bgcolor=_C["panel"],
        margin=dict(l=0, r=0, t=0, b=0),
        height=110,
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
