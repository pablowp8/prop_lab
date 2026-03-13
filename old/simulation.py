"""
simulation.py — Capa adaptadora entre components.py y la interfaz Dash
=======================================================================
Responsabilidades:
  - Instanciar los motores de components.py con los parámetros del usuario
  - Ejecutar la simulación y devolver un dict normalizado para la UI
  - Calcular métricas derivadas (empuje, TSFC, rendimientos...)
  - Proporcionar funciones de barrido paramétrico para las gráficas

La UI (app.py) solo importa de aquí. Nunca toca components.py directamente.
"""

import math
import numpy as np
from components import (
    OneSpoolEngine,
    TwinSpoolEngine,
    SingleFlowTurbofan,
    OneSpoolTurboprop,
)

# ── Constantes ────────────────────────────────────────────────────────────────
LHV   = 43_200_000   # Poder calorífico inferior Jet-A [J/kg]
gamma = 1.4
R     = 287
cp    = 1004.3


# ── Helpers atmosféricos ──────────────────────────────────────────────────────

def isa_atmosphere(alt_m, t0_c):
    """Devuelve (T_amb [K], P_amb [Pa]) según ISA con desviación de temperatura."""
    T_isa = 288.15 - 0.0065 * min(alt_m, 11000)  # troposfera
    if alt_m > 11000:
        T_isa = 216.65                             # estratosfera baja
    T_amb = T_isa + (t0_c - (T_isa - 273.15))     # offset respecto ISA
    T_amb = t0_c + 273.15                          # usamos T0 directamente
    P_amb = 101325 * (1 - 2.2557e-5 * alt_m) ** 5.2559
    return T_amb, P_amb


def speed_of_sound(T_K):
    return math.sqrt(gamma * R * T_K)


# ── Métricas derivadas comunes ────────────────────────────────────────────────

def compute_performance(V_jet, V0, m_dot, FAR=0.0, V_bypass=0.0, m_bypass=0.0,
                        Tt0=None, Tt3=None, Tt4=None, Tt5=None,
                        Pt0_kPa=None, Pt3_kPa=None, P0_kPa=None,
                        shaft_W=0.0, opr=1.0):
    """Calcula métricas de actuaciones a partir de velocidades y flujos."""
    F_core    = m_dot   * ((1 + FAR) * V_jet   - V0)
    F_bypass  = m_bypass * (V_bypass - V0)
    F_total   = F_core + F_bypass                          # [N]

    fuel_flow = m_dot * FAR                                # [kg/s]
    SFC       = fuel_flow / max(abs(F_total), 1.0) * 3600  # [kg/(N·h)]
    TSFC_mg   = SFC * 1e6 / 9.81                           # [mg/N·s]

    eta_th    = max(0.0, 1 - 1 / max(opr, 1.001) ** ((gamma - 1) / gamma))
    eta_prop  = (2 * V0 / (V_jet + V0 + 1e-6)) if V0 > 0 else 0.0
    eta_global = eta_th * eta_prop

    return {
        "thrust_kN":  F_total / 1000,
        "SFC":        SFC,
        "TSFC_mg":    TSFC_mg,
        "eta_th":     eta_th  * 100,
        "eta_prop":   eta_prop * 100,
        "eta_global": eta_global * 100,
        "fuel_kg_s":  fuel_flow,
        "FAR":        FAR,
        "V_jet":      V_jet,
        "V_bypass":   V_bypass,
        "V0":         V0,
        "m_core":     m_dot,
        "m_bypass":   m_bypass,
        "shaft_MW":   shaft_W / 1e6,
        "EGT":        Tt5 * 0.88 if Tt5 else 0.0,
        # estaciones del ciclo
        "T0_K":       Tt0  or 0.0,
        "Tt3_K":      Tt3  or 0.0,
        "Tt4_K":      Tt4  or 0.0,
        "Tt5_K":      Tt5  or 0.0,
        "Pt0_kPa":    Pt0_kPa or 0.0,
        "Pt3_kPa":    Pt3_kPa or 0.0,
        "P0_kPa":     P0_kPa  or 0.0,
    }


def _nozzle_exit_velocity(engine, T7t, P7t, T_amb, P_amb):
    """Reutiliza la tobera de components.py para obtener V_salida."""
    _, _, v = engine.nozz.calculate(T7t, P7t, T_amb, P_amb)
    return v


# ═══════════════════════════════════════════════════════════════════════════════
#  ADAPTADORES POR TIPO DE MOTOR
# ═══════════════════════════════════════════════════════════════════════════════

def run_one_spool(alt, t0_c, mach, G, pi_23, tit,
                  eta_c=0.80, eta_t=0.88):
    """
    Motor monoeje (OneSpoolEngine).
    Parámetros
    ----------
    alt    : altitud [m]
    t0_c   : temperatura estática [°C]
    mach   : número de Mach
    G      : flujo másico total [kg/s]
    pi_23  : relación de presiones del compresor
    tit    : temperatura de entrada a la turbina [K]
    eta_c  : eficiencia isentrópica compresor
    eta_t  : eficiencia isentrópica turbina
    """
    T_amb, P_amb = isa_atmosphere(alt, t0_c)
    V0 = mach * speed_of_sound(T_amb)

    eng = OneSpoolEngine()
    eng.comp.eta = eta_c
    eng.turb.eta = eta_t

    df = eng.simulate(T_amb, P_amb, mach, G, pi_23, tit)

    # Extraer estaciones del DataFrame
    T2t = float(df.loc[2,   'T'])
    P2t = float(df.loc[2,   'P'])
    T3t = float(df.loc[3,   'T'])
    P3t = float(df.loc[3,   'P'])
    T4t = float(df.loc[4,   'T'])
    P4t = float(df.loc[4,   'P'])
    T5t = float(df.loc[5,   'T'])
    P5t = float(df.loc[5,   'P'])
    T9  = float(df.loc[9,   'T'])
    P9  = float(df.loc[9,   'P'])

    V_jet = _nozzle_exit_velocity(eng, T5t, P5t, T_amb, P_amb)
    FAR   = cp * (T4t - T3t) / LHV

    perf = compute_performance(
        V_jet=V_jet, V0=V0, m_dot=G, FAR=FAR,
        Tt0=T2t, Tt3=T3t, Tt4=T4t, Tt5=T5t,
        Pt0_kPa=P2t/1000, Pt3_kPa=P3t/1000,
        P0_kPa=P_amb/1000,
        opr=pi_23,
    )
    perf["df"] = df
    perf["engine_type"] = "OneSpoolEngine"
    perf["tit_limit"] = 1600
    return perf


def run_twin_spool(alt, t0_c, mach, G, pi_lpc, pi_hpc, tit,
                   eta_lpc=0.91, eta_hpc=0.85, eta_lpt=0.94, eta_hpt=0.92):
    """
    Motor bieje (TwinSpoolEngine).
    pi_lpc : relación de presiones compresor LP
    pi_hpc : relación de presiones compresor HP
    """
    T_amb, P_amb = isa_atmosphere(alt, t0_c)
    V0 = mach * speed_of_sound(T_amb)

    eng = TwinSpoolEngine()
    eng.lp_compressor.eta = eta_lpc
    eng.hp_compressor.eta = eta_hpc
    eng.lp_turbine.eta    = eta_lpt
    eng.hp_turbine.eta    = eta_hpt

    df = eng.simulate(T_amb, P_amb, mach, G, pi_lpc, pi_hpc, tit)

    T2t  = float(df.loc[2,   'T'])
    P2t  = float(df.loc[2,   'P'])
    T25t = float(df.loc[2.5, 'T'])
    P25t = float(df.loc[2.5, 'P'])
    T3t  = float(df.loc[3,   'T'])
    P3t  = float(df.loc[3,   'P'])
    T4t  = float(df.loc[4,   'T'])
    P4t  = float(df.loc[4,   'P'])
    T45t = float(df.loc[4.5, 'T'])
    P45t = float(df.loc[4.5, 'P'])
    T5t  = float(df.loc[5,   'T'])
    P5t  = float(df.loc[5,   'P'])

    V_jet = _nozzle_exit_velocity(eng, T5t, P5t, T_amb, P_amb)
    FAR   = cp * (T4t - T3t) / LHV
    opr   = pi_lpc * pi_hpc

    perf = compute_performance(
        V_jet=V_jet, V0=V0, m_dot=G, FAR=FAR,
        Tt0=T2t, Tt3=T3t, Tt4=T4t, Tt5=T5t,
        Pt0_kPa=P2t/1000, Pt3_kPa=P3t/1000,
        P0_kPa=P_amb/1000,
        opr=opr,
    )
    perf["df"]          = df
    perf["T25t_K"]      = T25t
    perf["T45t_K"]      = T45t
    perf["opr"]         = opr
    perf["engine_type"] = "TwinSpoolEngine"
    perf["tit_limit"]   = 1700
    return perf


def run_turbofan(alt, t0_c, mach, G, pi_23, tit, pi_fan, bpr,
                 eta_c=1.0, eta_fan=1.0, eta_hpt=1.0, eta_lpt=1.0):
    """
    Turbofán de flujo único (SingleFlowTurbofan).
    pi_fan : relación de presiones del fan
    bpr    : bypass ratio
    """
    T_amb, P_amb = isa_atmosphere(alt, t0_c)
    V0 = mach * speed_of_sound(T_amb)

    eng = SingleFlowTurbofan()
    eng.comp.eta       = eta_c
    eng.fan.eta        = eta_fan
    eng.hp_turbine.eta = eta_hpt
    eng.lp_turbine.eta = eta_lpt

    df = eng.simulate(T_amb, P_amb, mach, G, pi_23, tit, pi_fan, bpr)

    T2t  = float(df.loc[2,   'T'])
    P2t  = float(df.loc[2,   'P'])
    T3t  = float(df.loc[3,   'T'])
    P3t  = float(df.loc[3,   'P'])
    T4t  = float(df.loc[4,   'T'])
    P4t  = float(df.loc[4,   'P'])
    T45t = float(df.loc[4.5, 'T'])
    P45t = float(df.loc[4.5, 'P'])
    T5t  = float(df.loc[5,   'T'])
    P5t  = float(df.loc[5,   'P'])
    T13t = float(df.loc[1.3, 'T'])
    P13t = float(df.loc[1.3, 'P'])

    m_core   = G / (1 + bpr)
    m_bypass = G * bpr / (1 + bpr)

    # Velocidad tobera core
    V_jet     = _nozzle_exit_velocity(eng, T5t,  P5t,  T_amb, P_amb)
    # Velocidad tobera bypass (usa misma tobera con salida del fan)
    V_bypass  = _nozzle_exit_velocity(eng, T13t, P13t, T_amb, P_amb)

    FAR = cp * (T4t - T3t) / LHV
    opr = pi_fan * pi_23

    perf = compute_performance(
        V_jet=V_jet, V0=V0, m_dot=m_core, FAR=FAR,
        V_bypass=V_bypass, m_bypass=m_bypass,
        Tt0=T2t, Tt3=T3t, Tt4=T4t, Tt5=T5t,
        Pt0_kPa=P2t/1000, Pt3_kPa=P3t/1000,
        P0_kPa=P_amb/1000,
        opr=opr,
    )
    perf["df"]          = df
    perf["T45t_K"]      = T45t
    perf["opr"]         = opr
    perf["bpr"]         = bpr
    perf["engine_type"] = "SingleFlowTurbofan"
    perf["tit_limit"]   = 1850
    return perf


def run_turboprop(alt, t0_c, mach, G, pi_23, tit, W_h, eta_m,
                  eta_c=1.0, eta_hpt=1.0, eta_lpt=1.0):
    """
    Turbohélice monoeje (OneSpoolTurboprop).
    W_h   : potencia extraída al eje [W]
    eta_m : eficiencia mecánica de la transmisión
    """
    T_amb, P_amb = isa_atmosphere(alt, t0_c)
    V0 = mach * speed_of_sound(T_amb)

    eng = OneSpoolTurboprop()
    eng.comp.eta       = eta_c
    eng.hp_turbine.eta = eta_hpt
    eng.lp_turbine.eta = eta_lpt

    df = eng.simulate(T_amb, P_amb, mach, G, pi_23, tit, W_h, eta_m)

    T2t = float(df.loc[2,   'T'])
    P2t = float(df.loc[2,   'P'])
    T3t = float(df.loc[3,   'T'])
    P3t = float(df.loc[3,   'P'])
    T4t = float(df.loc[4,   'T'])
    P4t = float(df.loc[4,   'P'])
    T45t= float(df.loc[4.5, 'T'])
    P45t= float(df.loc[4.5, 'P'])
    T5t = float(df.loc[5,   'T'])
    P5t = float(df.loc[5,   'P'])

    V_jet = _nozzle_exit_velocity(eng, T5t, P5t, T_amb, P_amb)
    FAR   = cp * (T4t - T3t) / LHV

    # En turbohélice el empuje principal es el de la hélice
    F_residual = G * (V_jet - V0)                 # empuje residual tobera [N]
    F_helice   = W_h * eta_m / max(V0, 1.0)       # F equivalente hélice [N]
    F_total    = F_helice + F_residual

    fuel_flow = G * FAR
    SFC_shaft = fuel_flow / max(W_h * eta_m, 1.0) * 3600  # consumo específico de potencia

    eta_th = max(0.0, 1 - 1 / max(pi_23, 1.001) ** ((gamma - 1) / gamma))

    perf = {
        "thrust_kN":   F_total / 1000,
        "F_helice_kN": F_helice / 1000,
        "F_resid_kN":  F_residual / 1000,
        "SFC":         fuel_flow / max(abs(F_total), 1) * 3600,
        "TSFC_mg":     (fuel_flow / max(abs(F_total), 1) * 3600) * 1e6 / 9.81,
        "SFC_shaft":   SFC_shaft,
        "eta_th":      eta_th * 100,
        "eta_prop":    0.0,
        "eta_global":  0.0,
        "fuel_kg_s":   fuel_flow,
        "FAR":         FAR,
        "V_jet":       V_jet,
        "V_bypass":    0.0,
        "V0":          V0,
        "m_core":      G,
        "m_bypass":    0.0,
        "shaft_MW":    W_h * eta_m / 1e6,
        "EGT":         T5t * 0.88,
        "T0_K":        T2t,
        "Tt3_K":       T3t,
        "Tt4_K":       T4t,
        "Tt5_K":       T5t,
        "Pt0_kPa":     P2t / 1000,
        "Pt3_kPa":     P3t / 1000,
        "P0_kPa":      P_amb / 1000,
        "df":          df,
        "T45t_K":      T45t,
        "opr":         pi_23,
        "engine_type": "OneSpoolTurboprop",
        "tit_limit":   1500,
    }
    return perf


# ═══════════════════════════════════════════════════════════════════════════════
#  BARRIDOS PARAMÉTRICOS (para las gráficas)
# ═══════════════════════════════════════════════════════════════════════════════

def sweep_tit(engine_type, base_params, n=50):
    """Barrido de TIT de 900 K a tit_max K → lista de (tit, thrust_kN)."""
    tit_max = {"OneSpoolEngine": 1700, "TwinSpoolEngine": 1900,
               "SingleFlowTurbofan": 2000, "OneSpoolTurboprop": 1700}.get(engine_type, 1800)
    tits = np.linspace(900, tit_max, n)
    results = []
    runner  = _get_runner(engine_type)
    for t in tits:
        try:
            p = {**base_params, "tit": t}
            r = runner(**p)
            results.append((t, r["thrust_kN"]))
        except Exception:
            results.append((t, float("nan")))
    return results


def sweep_opr(engine_type, base_params, n=50):
    """Barrido de OPR de 2 a 50 → lista de (opr, eta_th)."""
    oprs = np.linspace(2, 50, n)
    results = []
    runner  = _get_runner(engine_type)
    opr_key = "pi_23" if engine_type in ("OneSpoolEngine", "SingleFlowTurbofan", "OneSpoolTurboprop") else None

    for o in oprs:
        try:
            if opr_key:
                p = {**base_params, opr_key: o}
            else:  # TwinSpool: distribuir entre LPC y HPC
                p = {**base_params, "pi_lpc": max(1.1, o ** 0.35), "pi_hpc": max(1.1, o ** 0.65)}
            r = runner(**p)
            results.append((o, r["eta_th"]))
        except Exception:
            results.append((o, float("nan")))
    return results


def sweep_bpr(base_params, n=50):
    """Solo para turbofán: barrido de BPR 1..15 → TSFC."""
    bprs = np.linspace(1, 15, n)
    results = []
    for b in bprs:
        try:
            r = run_turbofan(**{**base_params, "bpr": b})
            results.append((b, r["TSFC_mg"]))
        except Exception:
            results.append((b, float("nan")))
    return results


def _get_runner(engine_type):
    return {
        "OneSpoolEngine":    run_one_spool,
        "TwinSpoolEngine":   run_twin_spool,
        "SingleFlowTurbofan": run_turbofan,
        "OneSpoolTurboprop": run_turboprop,
    }[engine_type]
