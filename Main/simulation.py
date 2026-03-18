"""
components.py — Física de aerorreactores
===================================================
Clases de componentes y motores. Cada motor expone:

    resultado = Motor().simulate(T_amb, P_amb, mach, G, *params_motor)

simulate() devuelve un dict completo con:
  - df          : DataFrame con T y P por estación
  - thrust_kN   : empuje neto [kN]
  - TSFC_mg     : consumo específico [mg/N·s]
  - eta_th/prop/global : rendimientos [%]
  - fuel_kg_s   : flujo de combustible [kg/s]
  - FAR         : relación combustible/aire
  - V_jet, V_bypass, V0 : velocidades [m/s]
  - m_core, m_bypass    : flujos másicos [kg/s]
  - shaft_MW    : potencia de eje [MW]
  - EGT         : temperatura gases de escape [K]
  - T0_K, Tt3_K, Tt4_K, Tt5_K : temperaturas de ciclo [K]
  - Pt0_kPa, Pt3_kPa, P0_kPa  : presiones de ciclo [kPa]
  - engine_type : identificador string
  - tit_limit   : límite de alerta TIT [K]

Uso desde app.py:
    eng = OneSpoolEngine()
    r   = eng.simulate(T_amb, P_amb, mach, G, pi_23, tit,
                       eta_c=0.80, eta_t=0.88)
"""

import math
import numpy as np
import pandas as pd

# ── Constantes ────────────────────────────────────────────────────────────────
LHV   = 43_200_000   # Poder calorífico inferior Jet-A [J/kg]
GAMMA = 1.4
R_GAS = 287          # [J/kg·K]
CP    = 1004.3       # [J/kg·K]


# ── Utilidades atmosféricas (módulo) ──────────────────────────────────────────

def isa_atmosphere(alt_m, t0_c):
    """Devuelve (T_amb [K], P_amb [Pa]) con ISA estándar."""
    T_amb = t0_c + 273.15
    P_amb = 101325 * (1 - 2.2557e-5 * alt_m) ** 5.2559
    return T_amb, P_amb

def speed_of_sound(T_K):
    return math.sqrt(GAMMA * R_GAS * T_K)


# ══════════════════════════════════════════════════════════════════════════════
#  COMPONENTES BASE
# ══════════════════════════════════════════════════════════════════════════════

class Component:
    def __init__(self, eta=1.0):
        self.eta   = eta
        self.gamma = GAMMA
        self.cp    = CP
        self.R     = R_GAS


class Difussor(Component):
    def calculate(self, t_in, p_in, mach, pressure_ratio=1.0):
        t_out = t_in * (1 + (self.gamma - 1) * mach**2 / 2)
        p_out = p_in * (1 + (self.gamma - 1) * mach**2 / 2) ** (self.gamma / (self.gamma - 1))
        p_out *= pressure_ratio
        return t_out, p_out


class Compressor(Component):
    def calculate(self, t_in, p_in, pressure_ratio):
        p_out       = p_in * pressure_ratio
        t_out_ideal = t_in * (pressure_ratio ** ((self.gamma - 1) / self.gamma))
        t_out       = t_in + (t_out_ideal - t_in) / self.eta
        work        = self.cp * (t_out - t_in)
        return t_out, p_out, work


class CombustionChamber(Component):
    def calculate(self, t_in, p_in, tit, pressure_ratio=1.0):
        p_out      = p_in * pressure_ratio
        heat_added = self.cp * (tit - t_in)
        return tit, p_out, heat_added


class Turbine(Component):
    def calculate(self, t_in, p_in, required_work):
        t_out = t_in - (required_work / self.cp)
        p_out = p_in * (1 - (t_in - t_out) / (self.eta * t_in)) ** (self.gamma / (self.gamma - 1))
        return t_out, p_out


class Postcombustor(Component):
    def calculate(self, t_in, p_in):
        return t_in, p_in


class Nozzle(Component):
    def calculate(self, t_in, p_in, t_a, p_a, conf='CON'):
        if conf == 'CON':
            param_pressure = p_in / p_a
            param_gamma    = ((self.gamma + 1) / 2) ** (self.gamma / (self.gamma - 1))
            if param_pressure <= param_gamma:       # adaptada
                p_out = p_a
                t_out = t_in * (1 / param_pressure) ** ((self.gamma - 1) / self.gamma)
                mach  = math.sqrt((2 / (self.gamma - 1)) * (param_pressure ** ((self.gamma - 1) / self.gamma) - 1))
            else:                                   # bloqueada
                p_out = p_in / param_gamma
                t_out = t_in / ((self.gamma + 1) / 2)
                mach  = 1.0
        else:   # CON-DIV adaptada
            param_pressure = p_in / p_a
            p_out = p_a
            t_out = t_in * (1 / param_pressure) ** ((self.gamma - 1) / self.gamma)
            mach  = math.sqrt((2 / (self.gamma - 1)) * (param_pressure ** ((self.gamma - 1) / self.gamma) - 1))

        v_out = mach * math.sqrt(self.gamma * self.R * t_out)
        return t_out, p_out, v_out


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER INTERNO: métricas de actuaciones
# ══════════════════════════════════════════════════════════════════════════════

def _perf(V_jet, V0, m_dot, FAR, opr,
          V_bypass=0.0, m_bypass=0.0, shaft_W=0.0,
          Tt0=0.0, Tt3=0.0, Tt4=0.0, Tt5=0.0,
          Pt0_kPa=0.0, Pt3_kPa=0.0, P0_kPa=0.0):
    """Calcula el dict de actuaciones comunes a todos los motores."""
    F_core   = m_dot    * ((1 + FAR) * V_jet    - V0)
    F_bypass = m_bypass * (V_bypass  - V0)
    F_total  = F_core + F_bypass

    fuel_kg_s = m_dot * FAR
    SFC       = fuel_kg_s / max(abs(F_total), 1.0) * 3600
    TSFC_mg   = SFC * 1e6 / 9.81

    eta_th    = max(0.0, 1 - 1 / max(opr, 1.001) ** ((GAMMA - 1) / GAMMA))
    eta_prop  = (2 * V0 / (V_jet + V0 + 1e-6)) if V0 > 0 else 0.0
    eta_global = eta_th * eta_prop

    return {
        "thrust_kN":  F_total / 1000,
        "SFC":        SFC,
        "TSFC_mg":    TSFC_mg,
        "eta_th":     eta_th    * 100,
        "eta_prop":   eta_prop  * 100,
        "eta_global": eta_global * 100,
        "fuel_kg_s":  fuel_kg_s,
        "FAR":        FAR,
        "V_jet":      V_jet,
        "V_bypass":   V_bypass,
        "V0":         V0,
        "m_core":     m_dot,
        "m_bypass":   m_bypass,
        "shaft_MW":   shaft_W / 1e6,
        "EGT":        Tt5 * 0.88,
        "T0_K":       Tt0,
        "Tt3_K":      Tt3,
        "Tt4_K":      Tt4,
        "Tt5_K":      Tt5,
        "Pt0_kPa":    Pt0_kPa,
        "Pt3_kPa":    Pt3_kPa,
        "P0_kPa":     P0_kPa,
    }


def _fill_df(df, local_vars, mapping):
    """Rellena el DataFrame de estaciones desde las variables locales del simulate."""
    for station, suffix in mapping.items():
        t_var, p_var = f"T_{suffix}", f"P_{suffix}"
        if t_var in local_vars and p_var in local_vars:
            df.loc[station, 'T'] = local_vars[t_var]
            df.loc[station, 'P'] = local_vars[p_var]
    return df


# ══════════════════════════════════════════════════════════════════════════════
#  MOTORES
# ══════════════════════════════════════════════════════════════════════════════

class OneSpoolEngine:
    """Turbojet monoeje: Difusor → Compresor → Cámara → Turbina → Tobera."""

    TIT_LIMIT = 1600   # K — alerta de integridad estructural

    def __init__(self):
        self.dif  = Difussor()
        self.comp = Compressor(eta=0.80)
        self.cc   = CombustionChamber()
        self.turb = Turbine(eta=0.88)
        self.pc   = Postcombustor()
        self.nozz = Nozzle()

    def simulate(self, T_amb, P_amb, mach, G, pi_23, tit,
                 eta_dif=None, eta_c=None, eta_cc=None,
                 eta_t=None, eta_noz=None):
        """
        Parámetros
        ----------
        T_amb, P_amb : condiciones estáticas de entrada [K, Pa]
        mach         : número de Mach de vuelo
        G            : flujo másico [kg/s]
        pi_23        : relación de presiones del compresor
        tit          : temperatura de entrada a turbina [K]
        eta_c, eta_t : rendimientos isentrópicos (opcional, sobreescribe __init__)
        """
        if eta_dif is not None: self.dif.eta  = eta_dif
        if eta_c   is not None: self.comp.eta = eta_c
        if eta_cc  is not None: self.cc.eta   = eta_cc
        if eta_t   is not None: self.turb.eta = eta_t
        if eta_noz is not None: self.nozz.eta = eta_noz

        V0 = mach * speed_of_sound(T_amb)

        T_2t, P_2t         = self.dif.calculate(T_amb, P_amb, mach)
        T_3t, P_3t, W_c    = self.comp.calculate(T_2t, P_amb, pi_23)
        T_4t, P_4t, _      = self.cc.calculate(T_3t, P_3t, tit)
        T_5t, P_5t         = self.turb.calculate(T_4t, P_4t, W_c)
        T_7t, P_7t         = self.pc.calculate(T_5t, P_5t)
        T_9, P_9, V_jet    = self.nozz.calculate(T_7t, P_7t, T_amb, P_amb)

        df = _fill_df(
            pd.DataFrame(index=[0,1,2,2.5,3,4,4.5,5,6,7,8,9], columns=['T','P']),
            locals(),
            {0:"0", 2:"2t", 3:"3t", 4:"4t", 5:"5t", 9:"9"},
        )

        FAR = CP * (T_4t - T_3t) / LHV
        r = _perf(V_jet=V_jet, V0=V0, m_dot=G, FAR=FAR, opr=pi_23,
                  Tt0=T_2t, Tt3=T_3t, Tt4=T_4t, Tt5=T_5t,
                  Pt0_kPa=P_2t/1000, Pt3_kPa=P_3t/1000, P0_kPa=P_amb/1000)
        r["df"]          = df
        r["engine_type"] = "OneSpoolEngine"
        r["tit_limit"]   = self.TIT_LIMIT
        return r


class TwinSpoolEngine:
    """Turbojet bieje: LPC → HPC → Cámara → HPT → LPT → Tobera."""

    TIT_LIMIT = 1700

    def __init__(self):
        self.dif           = Difussor()
        self.lp_compressor = Compressor(eta=0.91)
        self.hp_compressor = Compressor(eta=0.85)
        self.cc            = CombustionChamber()
        self.hp_turbine    = Turbine(eta=0.92)
        self.lp_turbine    = Turbine(eta=0.94)
        self.pc            = Postcombustor()
        self.nozz          = Nozzle()

    def simulate(self, T_amb, P_amb, mach, G, pi_lpc, pi_hpc, tit,
                 eta_dif=None, eta_lpc=None, eta_hpc=None, eta_cc=None,
                 eta_lpt=None, eta_hpt=None, eta_noz=None):
        if eta_dif is not None: self.dif.eta            = eta_dif
        if eta_lpc is not None: self.lp_compressor.eta  = eta_lpc
        if eta_hpc is not None: self.hp_compressor.eta  = eta_hpc
        if eta_cc  is not None: self.cc.eta             = eta_cc
        if eta_lpt is not None: self.lp_turbine.eta     = eta_lpt
        if eta_hpt is not None: self.hp_turbine.eta     = eta_hpt
        if eta_noz is not None: self.nozz.eta           = eta_noz

        V0 = mach * speed_of_sound(T_amb)

        T_2t,  P_2t           = self.dif.calculate(T_amb, P_amb, mach)
        T_25t, P_25t, W_lpc   = self.lp_compressor.calculate(T_2t,  P_2t,  pi_lpc)
        T_3t,  P_3t,  W_hpc   = self.hp_compressor.calculate(T_25t, P_25t, pi_hpc)
        T_4t,  P_4t,  _       = self.cc.calculate(T_3t, P_3t, tit)
        T_45t, P_45t          = self.hp_turbine.calculate(T_4t,  P_4t,  W_hpc)
        T_5t,  P_5t           = self.lp_turbine.calculate(T_45t, P_45t, W_lpc)
        T_7t,  P_7t           = self.pc.calculate(T_5t, P_5t)
        T_9,   P_9,   V_jet   = self.nozz.calculate(T_7t, P_7t, T_amb, P_amb)

        df = _fill_df(
            pd.DataFrame(index=[0,1,2,2.5,3,4,4.5,5,6,7,8,9], columns=['T','P']),
            locals(),
            {0:"0", 2:"2t", 2.5:"25t", 3:"3t", 4:"4t", 4.5:"45t", 5:"5t", 9:"9"},
        )

        FAR = CP * (T_4t - T_3t) / LHV
        opr = pi_lpc * pi_hpc
        r = _perf(V_jet=V_jet, V0=V0, m_dot=G, FAR=FAR, opr=opr,
                  Tt0=T_2t, Tt3=T_3t, Tt4=T_4t, Tt5=T_5t,
                  Pt0_kPa=P_2t/1000, Pt3_kPa=P_3t/1000, P0_kPa=P_amb/1000)
        r["df"]          = df
        r["opr"]         = opr
        r["engine_type"] = "TwinSpoolEngine"
        r["tit_limit"]   = self.TIT_LIMIT
        return r


class SingleFlowTurbofan:
    """Turbofán: Fan → (bypass + HPC) → Cámara → HPT → LPT → Tobera."""

    TIT_LIMIT = 1850

    def __init__(self):
        self.dif        = Difussor()
        self.fan        = Compressor(eta=1.0)
        self.comp       = Compressor(eta=1.0)
        self.cc         = CombustionChamber()
        self.hp_turbine = Turbine(eta=1.0)
        self.lp_turbine = Turbine(eta=1.0)
        self.pc         = Postcombustor()
        self.nozz       = Nozzle()

    def simulate(self, T_amb, P_amb, mach, G, pi_23, tit, pi_fan, bpr,
                 eta_dif=None, eta_c=None, eta_fan=None, eta_cc=None,
                 eta_hpt=None, eta_lpt=None, eta_noz=None):
        if eta_dif is not None: self.dif.eta         = eta_dif
        if eta_c   is not None: self.comp.eta        = eta_c
        if eta_fan is not None: self.fan.eta          = eta_fan
        if eta_cc  is not None: self.cc.eta          = eta_cc
        if eta_hpt is not None: self.hp_turbine.eta  = eta_hpt
        if eta_lpt is not None: self.lp_turbine.eta  = eta_lpt
        if eta_noz is not None: self.nozz.eta        = eta_noz

        V0 = mach * speed_of_sound(T_amb)

        T_2t,  P_2t           = self.dif.calculate(T_amb, P_amb, mach)
        T_3t,  P_3t,  W_c     = self.comp.calculate(T_2t, P_2t, pi_23)
        T_13t, P_13t, W_fan   = self.fan.calculate(T_2t,  P_2t, pi_fan)
        T_4t,  P_4t,  _       = self.cc.calculate(T_3t, P_3t, tit)
        T_45t, P_45t          = self.hp_turbine.calculate(T_4t,  P_4t,  W_c)
        T_5t,  P_5t           = self.lp_turbine.calculate(T_45t, P_45t, W_fan * bpr)
        T_7t,  P_7t           = self.pc.calculate(T_5t, P_5t)
        T_9,   P_9,   V_jet   = self.nozz.calculate(T_7t,  P_7t,  T_amb, P_amb)
        _,     _,     V_bypass = self.nozz.calculate(T_13t, P_13t, T_amb, P_amb)

        df = _fill_df(
            pd.DataFrame(index=[0,1,2,3,4,4.5,5,6,7,8,9,1.2,1.3,1.7,1.8,1.9],
                         columns=['T','P']),
            locals(),
            {0:"0", 2:"2t", 3:"3t", 4:"4t", 4.5:"45t", 5:"5t", 9:"9", 1.3:"13t"},
        )

        m_core   = G / (1 + bpr)
        m_bypass = G * bpr / (1 + bpr)
        FAR      = CP * (T_4t - T_3t) / LHV
        opr      = pi_fan * pi_23

        r = _perf(V_jet=V_jet, V0=V0, m_dot=m_core, FAR=FAR, opr=opr,
                  V_bypass=V_bypass, m_bypass=m_bypass,
                  Tt0=T_2t, Tt3=T_3t, Tt4=T_4t, Tt5=T_5t,
                  Pt0_kPa=P_2t/1000, Pt3_kPa=P_3t/1000, P0_kPa=P_amb/1000)
        r["df"]          = df
        r["opr"]         = opr
        r["bpr"]         = bpr
        r["engine_type"] = "SingleFlowTurbofan"
        r["tit_limit"]   = self.TIT_LIMIT
        return r


class OneSpoolTurboprop:
    """Turbohélice: Compresor → Cámara → HPT → LPT → Tobera residual."""

    TIT_LIMIT = 1500

    def __init__(self):
        self.dif        = Difussor()
        self.comp       = Compressor(eta=1.0)
        self.cc         = CombustionChamber()
        self.hp_turbine = Turbine(eta=1.0)
        self.lp_turbine = Turbine(eta=1.0)
        self.pc         = Postcombustor()
        self.nozz       = Nozzle()

    def simulate(self, T_amb, P_amb, mach, G, pi_23, tit, W_h, eta_m,
                 eta_dif=None, eta_c=None, eta_cc=None,
                 eta_hpt=None, eta_lpt=None, eta_noz=None):
        """
        W_h   : potencia extraída al eje [W]
        eta_m : eficiencia mecánica de la transmisión
        """
        if eta_dif is not None: self.dif.eta         = eta_dif
        if eta_c   is not None: self.comp.eta        = eta_c
        if eta_cc  is not None: self.cc.eta          = eta_cc
        if eta_hpt is not None: self.hp_turbine.eta  = eta_hpt
        if eta_lpt is not None: self.lp_turbine.eta  = eta_lpt
        if eta_noz is not None: self.nozz.eta        = eta_noz

        V0 = mach * speed_of_sound(T_amb)

        T_2t,  P_2t           = self.dif.calculate(T_amb, P_amb, mach)
        T_3t,  P_3t,  W_c     = self.comp.calculate(T_2t, P_2t, pi_23)
        T_4t,  P_4t,  _       = self.cc.calculate(T_3t, P_3t, tit)
        T_45t, P_45t          = self.hp_turbine.calculate(T_4t,  P_4t,  W_c)
        T_5t,  P_5t           = self.lp_turbine.calculate(T_45t, P_45t, W_h * eta_m)
        T_7t,  P_7t           = self.pc.calculate(T_5t, P_5t)
        T_9,   P_9,   V_jet   = self.nozz.calculate(T_7t, P_7t, T_amb, P_amb)

        df = _fill_df(
            pd.DataFrame(index=[0,1,2,3,4,4.5,5,6,7,8,9], columns=['T','P']),
            locals(),
            {0:"0", 2:"2t", 3:"3t", 4:"4t", 4.5:"45t", 5:"5t", 9:"9"},
        )

        FAR        = CP * (T_4t - T_3t) / LHV
        fuel_kg_s  = G * FAR
        F_residual = G * (V_jet - V0)
        F_helice   = W_h * eta_m / max(V0, 1.0)
        F_total    = F_helice + F_residual

        eta_th = max(0.0, 1 - 1 / max(pi_23, 1.001) ** ((GAMMA - 1) / GAMMA))

        return {
            "thrust_kN":   F_total / 1000,
            "F_helice_kN": F_helice / 1000,
            "F_resid_kN":  F_residual / 1000,
            "SFC":         fuel_kg_s / max(abs(F_total), 1) * 3600,
            "TSFC_mg":     (fuel_kg_s / max(abs(F_total), 1) * 3600) * 1e6 / 9.81,
            "eta_th":      eta_th * 100,
            "eta_prop":    0.0,
            "eta_global":  0.0,
            "fuel_kg_s":   fuel_kg_s,
            "FAR":         FAR,
            "V_jet":       V_jet,
            "V_bypass":    0.0,
            "V0":          V0,
            "m_core":      G,
            "m_bypass":    0.0,
            "shaft_MW":    W_h * eta_m / 1e6,
            "EGT":         T_5t * 0.88,
            "T0_K":        T_2t,
            "Tt3_K":       T_3t,
            "Tt4_K":       T_4t,
            "Tt5_K":       T_5t,
            "Pt0_kPa":     P_2t / 1000,
            "Pt3_kPa":     P_3t / 1000,
            "P0_kPa":      P_amb / 1000,
            "df":          df,
            "opr":         pi_23,
            "engine_type": "OneSpoolTurboprop",
            "tit_limit":   self.TIT_LIMIT,
        }


# ══════════════════════════════════════════════════════════════════════════════
#  BARRIDOS PARAMÉTRICOS (para las gráficas de app.py)
# ══════════════════════════════════════════════════════════════════════════════

def sweep_tit(engine_type, base_params, n=50):
    """Barrido de TIT → lista de (tit, thrust_kN)."""
    tit_max = {"OneSpoolEngine":1700, "TwinSpoolEngine":1900,
               "SingleFlowTurbofan":2000, "OneSpoolTurboprop":1700}.get(engine_type, 1800)
    results, cls = [], _engine_class(engine_type)
    for t in np.linspace(900, tit_max, n):
        try:
            results.append((t, cls().simulate(**{**base_params, "tit": t})["thrust_kN"]))
        except Exception:
            results.append((t, float("nan")))
    return results


def sweep_opr(engine_type, base_params, n=50):
    """Barrido de OPR → lista de (opr, eta_th)."""
    results, cls = [], _engine_class(engine_type)
    for o in np.linspace(2, 50, n):
        try:
            if engine_type == "TwinSpoolEngine":
                p = {**base_params, "pi_lpc": max(1.1, o**0.35), "pi_hpc": max(1.1, o**0.65)}
            else:
                p = {**base_params, "pi_23": o}
            results.append((o, cls().simulate(**p)["eta_th"]))
        except Exception:
            results.append((o, float("nan")))
    return results


def sweep_bpr(base_params, n=50):
    """Solo turbofán: barrido de BPR → lista de (bpr, TSFC_mg)."""
    results = []
    for b in np.linspace(1, 15, n):
        try:
            results.append((b, SingleFlowTurbofan().simulate(**{**base_params, "bpr": b})["TSFC_mg"]))
        except Exception:
            results.append((b, float("nan")))
    return results


def _engine_class(engine_type):
    return {"OneSpoolEngine":    OneSpoolEngine,
            "TwinSpoolEngine":   TwinSpoolEngine,
            "SingleFlowTurbofan":SingleFlowTurbofan,
            "OneSpoolTurboprop": OneSpoolTurboprop}[engine_type]


# ══════════════════════════════════════════════════════════════════════════════
#  TEST RÁPIDO
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    T, P = isa_atmosphere(0, 15)

    r1 = OneSpoolEngine().simulate(T, P, 0, 20, 10, 1400)
    print(f"Monoeje   — F={r1['thrust_kN']:.2f} kN  TSFC={r1['TSFC_mg']:.2f} mg/Ns")

    r2 = TwinSpoolEngine().simulate(T, P, 0, 20, 1.6, 12, 1450)
    print(f"Bieje     — F={r2['thrust_kN']:.2f} kN  TSFC={r2['TSFC_mg']:.2f} mg/Ns")

    r3 = SingleFlowTurbofan().simulate(T, P, 0, 90, 25, 1500, 1.4, 0.8)
    print(f"Turbofan  — F={r3['thrust_kN']:.2f} kN  TSFC={r3['TSFC_mg']:.2f} mg/Ns")

    r4 = OneSpoolTurboprop().simulate(T, P, 0, 90, 25, 1500, 200_000, 0.7)
    print(f"Turboprop — F={r4['thrust_kN']:.2f} kN  TSFC={r4['TSFC_mg']:.2f} mg/Ns")
