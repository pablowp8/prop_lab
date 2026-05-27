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
TIT_LIMIT = 1900     # K


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
        self.L     = LHV


class Difussor(Component):
    def calculate(self, t_in, p_in, s_in, mach, pressure_ratio=1.0):
        t_out = t_in * (1 + (self.gamma - 1) * mach**2 / 2)
        p_out = p_in * (1 + self.eta*(t_out/t_in - 1)) ** (self.gamma / (self.gamma - 1))

        s = s_in
        
        return t_out, p_out, s


class Compressor(Component):
    def calculate(self, t_in, p_in, s_in, pressure_ratio):
        p_out       = p_in * pressure_ratio
        t_out       = t_in * (((-1 + pressure_ratio ** ((self.gamma - 1) / self.gamma))/ self.eta) + 1)
        work        = self.cp * (t_out - t_in)

        s = s_in + self.cp * np.log(t_out / t_in) - self.R * np.log(p_out / p_in)

        return t_out, p_out, s, work


class CombustionChamber(Component):
    def calculate(self, t_in, p_in, s_in, t_out, pressure_ratio=1.0):
        p_out      = p_in * pressure_ratio
        heat_added = self.cp * (t_out- t_in)

        s = s_in + self.cp * np.log(t_out / t_in) - self.R * np.log(p_out / p_in)
        
        FAR = (self.cp * t_out - self.cp * t_in) / (self.eta * self.L  - self.cp * t_out)
        return t_out, p_out, s, FAR

class Turbine(Component):
    def calculate(self, t_in, p_in, s_in, required_work, G, FAR):
        t_out = t_in - (required_work / ((1+FAR)*self.cp))
        p_out = p_in * ((1 - (1/self.eta)*(1-t_out/t_in)) ** (self.gamma / (self.gamma - 1)))

        s = s_in + self.cp * np.log(t_out / t_in) - self.R * np.log(p_out / p_in)
        
        g = self.gamma
        exp = (g + 1) / (2 * (g - 1))
        A = (G * t_in**0.5 / p_in) * ((self.R / g)**0.5) * ((g + 1) / 2)**exp

        return t_out, p_out, s, A
class Postcombustor(Component):
    def calculate(self, t_in, p_in, s_in, t_pc, G, FAR):

        g = self.gamma

        t_out = t_pc
        p_out = p_in
        
        FAR_ab = (self.cp * t_out - self.cp * t_in) / (self.eta * self.L  - self.cp * t_out)
        G = G*(1+FAR_ab)
        
        FAR = FAR + FAR_ab*(1 + FAR)

        s = s_in + self.cp * np.log(t_out / t_in) - self.R * np.log(p_out / p_in)

        exp = (g + 1) / (2 * (g - 1))
        A = (G * t_in**0.5 / p_in) * ((self.R / g)**0.5) * ((g + 1) / 2)**exp

        return t_out, p_out, s, A, FAR


class Nozzle(Component):
    def calculate(self, t_in, p_in, s_in, t_a, p_a, G, conf='CON'):
        param_pressure = p_in / p_a
        param_gamma    = (2 / (self.gamma + 1)) ** (self.gamma / (self.gamma - 1))
        g = self.gamma
        if conf == 'CON':
            if param_pressure <= param_gamma:       # adaptada
                p_out = p_a
                t_out = t_in * (1 / param_pressure) ** ((self.gamma - 1) / self.gamma)
                mach  = math.sqrt((2 / (self.gamma - 1)) * (param_pressure ** ((self.gamma - 1) / self.gamma) - 1))

                f_M = mach * (1 + (g - 1) / 2 * mach**2)**(-(g + 1) / (2 * (g - 1)))
                A = (G * t_in**0.5 / p_in) * ((self.R / g)**0.5) / f_M
            else:                                   # bloqueada
                p_out = p_in * param_gamma
                t_out = t_in / ((self.gamma + 1) / 2)
                mach  = 1.0
                
                exp = (g + 1) / (2 * (g - 1))
                A = (G * t_in**0.5 / p_in) * ((self.R / g)**0.5) * ((g + 1) / 2)**exp
        else:   # CON-DIV adaptada
            p_out = p_a
            t_out = t_in * (1 / param_pressure) ** ((self.gamma - 1) / self.gamma)
            mach  = math.sqrt((2 / (self.gamma - 1)) * (param_pressure ** ((self.gamma - 1) / self.gamma) - 1))
            f_M = mach * (1 + (g - 1) / 2 * mach**2)**(-(g + 1) / (2 * (g - 1)))
            A = (G * t_in**0.5 / p_in) * ((self.R / g)**0.5) / f_M
            
        v_out = mach * math.sqrt(self.gamma * self.R * t_out)

        s = s_in
        return t_out, p_out, s, v_out, A


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER INTERNO: métricas de actuaciones
# ══════════════════════════════════════════════════════════════════════════════
def _build_stations(local_vars):
    """Extrae T_X, P_X, S_X (con o sin 't' final) y los agrupa por estación."""
    stations = {}
    for name, value in local_vars.items():
        if len(name) < 3 or name[1] != '_' or name[0] not in 'TPS':
            continue
        idx_str = name[2:].rstrip('t')
        try:
            idx = float(idx_str)
        except ValueError:
            continue
        idx = int(idx) if idx.is_integer() else idx
        stations.setdefault(idx, {})[name[0]] = value
    
    for st in stations.values():
        for k in 'TPS':
            st.setdefault(k, None)
            
    return stations

def _perf(V_jet, V0, m_dot, FAR, opr, A_8, A_18=0,
          V_bypass=0.0, m_bypass=0.0, shaft_W=0.0,
          P_9=0.0, P_19=0.0, Tt0=0.0, Tt3=0.0, Tt4=0.0, Tt5=0.0,
          Pt0_kPa=0.0, Pt3_kPa=0.0, P0_kPa=0.0):
    
    # --- Presión ambiente estática [Pa] -----------------------------------
    P0 = P0_kPa * 1000.0

    # --- Gastos ------------------------------------------------------------
    m_g_core  = m_dot * (1.0 + FAR)     # gasto de gases del primario
    m_air_tot = m_dot + m_bypass        # gasto total de aire (sin combustible)
    fuel_kg_s = m_dot * FAR

    # --- Empuje (términos de presión = 0 si la tobera está adaptada) ------
    F_core   = m_g_core * V_jet    - m_dot    * V0 + A_8  * (P_9  - P0)
    F_bypass = m_bypass * V_bypass - m_bypass * V0 + A_18 * (P_19 - P0)
    F_total  = F_core + F_bypass

    # --- Velocidades equivalentes (= V_jet/V_bypass si adaptadas) ---------
    V_eq_core   = V_jet + A_8 * (P_9 - P0) / m_g_core
    V_eq_bypass = (V_bypass + A_18 * (P_19 - P0) / m_bypass
                   if m_bypass > 0.0 else 0.0)

    # --- Potencias ---------------------------------------------------------
    # Potencia calorífica aportada por el combustible
    P_cal = fuel_kg_s * LHV

    # Potencia útil = empuje · velocidad de vuelo
    P_util = F_total * V0

    # Potencia mecánica neta = incremento de energía cinética del fluido
    #   (usando V_eq para englobar el término de presión residual)
    P_mec = 0.5 * (m_g_core  * V_eq_core**2
                 + m_bypass  * V_eq_bypass**2
                 - m_air_tot * V0**2)

    # --- Rendimientos ------------------------------------------------------
    eta_m  = P_mec  / P_cal      # motor       : química -> cinética del chorro
    eta_mp = P_util / P_cal      # motopropulsor: química -> propulsiva
    eta_p  = P_util / P_mec      # propulsor   : cinética -> propulsiva
    # se cumple eta_mp = eta_m * eta_p

    # --- Actuaciones -------------------------------------------------------
    sp_thrust = F_total / m_air_tot          # empuje específico [N/(kg/s)]
    SFC       = fuel_kg_s * 1e6 / F_total    # g/(kN·s)
    TSFC_mg   = SFC * 1e6 / 9.81
        

    return {
        "thrust_kN":  F_total / 1000,
        "sp_thrust":  sp_thrust,
        "SFC":        SFC,
        "TSFC_mg":    TSFC_mg,
        "eta_m":      eta_m    * 100,
        "eta_p":      eta_p  * 100,
        "eta_mp":     eta_mp * 100,
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

    def __init__(self):
        self.dif  = Difussor()
        self.comp = Compressor()
        self.cc   = CombustionChamber()
        self.turb = Turbine()
        self.nozz = Nozzle()

    def simulate(self, T_0, P_0, mach, G, pi_23, tit,
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

        V0 = mach * speed_of_sound(T_0)
        
        S_0 = 0
        T_2t, P_2t, S_2         = self.dif.calculate(T_0, P_0, S_0, mach)
        T_3t, P_3t, S_3, W_c    = self.comp.calculate(T_2t, P_2t, S_2, pi_23)
        T_4t, P_4t, S_4, FAR         = self.cc.calculate(T_3t, P_3t, S_3, tit)
        T_5t, P_5t, S_5, A_4         = self.turb.calculate(T_4t, P_4t, S_4, W_c, G*(1+FAR), FAR)
        T_9, P_9, S_9, V_jet, A_8    = self.nozz.calculate(T_5t, P_5t, S_5, T_0, P_0, G*(1+FAR))

        df = _fill_df(
            pd.DataFrame(index=[0,1,2,2.5,3,4,4.5,5,6,7,8,9], columns=['T','P']),
            locals(),
            {0:"0", 2:"2t", 3:"3t", 4:"4t", 5:"5t", 9:"9"},
        )

        stations = _build_stations(locals())

        r = _perf(V_jet=V_jet, V0=V0, m_dot=G, FAR=FAR, opr=pi_23, A_8=A_8,
                  P_9= P_9, Tt0=T_2t, Tt3=T_3t, Tt4=T_4t, Tt5=T_5t,
                  Pt0_kPa=P_2t/1000, Pt3_kPa=P_3t/1000, P0_kPa=P_0/1000)
        r["A8"]          = A_8
        r["A8_PC"]       = A_8
        r["df"]          = df
        r["engine_type"] = "OneSpoolEngine"
        r["tit_limit"]   = TIT_LIMIT
        r["stations"]  = stations
        return r


class OneSpoolEngine_PC:
    """Turbojet monoeje: Difusor → Compresor → Cámara → Turbina → Postcombustor → Tobera."""

    def __init__(self):
        self.dif  = Difussor()
        self.comp = Compressor()
        self.cc   = CombustionChamber()
        self.turb = Turbine()
        self.pc   = Postcombustor()
        self.nozz = Nozzle()

    def simulate(self, T_0, P_0, mach, G, pi_23, tit, t_pc,
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

        V0 = mach * speed_of_sound(T_0)
        
        S_0 = 0
        T_2t, P_2t, S_2              = self.dif.calculate(T_0, P_0, S_0, mach)
        T_3t, P_3t, S_3, W_c         = self.comp.calculate(T_2t, P_2t, S_2, pi_23)
        T_4t, P_4t, S_4, FAR         = self.cc.calculate(T_3t, P_3t, S_3, tit)
        T_5t, P_5t, S_5, A_4         = self.turb.calculate(T_4t, P_4t, S_4, W_c, G*(1+FAR), FAR)
        T_7t, P_7t, S_7, A_8, FAR    = self.pc.calculate(T_5t, P_5t, S_5, t_pc, G*(1+FAR), FAR)
        T_9, P_9, S_9, V_jet, A_8pc  = self.nozz.calculate(T_7t, P_7t, S_7, T_0, P_0, G*(1+FAR))

        df = _fill_df(
            pd.DataFrame(index=[0,1,2,2.5,3,4,4.5,5,6,7,8,9], columns=['T','P']),
            locals(),
            {0:"0", 2:"2t", 3:"3t", 4:"4t", 5:"5t", 9:"9"},
        )

        stations = _build_stations(locals())

        r = _perf(V_jet=V_jet, V0=V0, m_dot=G, FAR=FAR, opr=pi_23, A_8=A_8pc,
                  P_9= P_9, Tt0=T_2t, Tt3=T_3t, Tt4=T_4t, Tt5=T_5t,
                  Pt0_kPa=P_2t/1000, Pt3_kPa=P_3t/1000, P0_kPa=P_0/1000)
        r["A8"]          = A_8
        r["A8_PC"]       = A_8pc
        r["df"]          = df
        r["engine_type"] = "OneSpoolEngine"
        r["tit_limit"]   = TIT_LIMIT
        r["stations"]  = stations
        return r


class SingleFlowTurbofan:
    """Turbofán: Fan → (bypass + HPC) → Cámara → HPT → LPT → Tobera."""

    def __init__(self):
        self.dif        = Difussor()
        self.fan        = Compressor()
        self.comp       = Compressor()
        self.cc         = CombustionChamber()
        self.hp_turbine = Turbine()
        self.lp_turbine = Turbine()
        self.pc         = Postcombustor()
        self.nozz       = Nozzle()

    def simulate(self, T_0, P_0, mach, G, pi_23, tit, pi_fan, bpr,
                 eta_dif=None, eta_c=None, eta_fan=None, eta_cc=None,
                 eta_hpt=None, eta_lpt=None, eta_noz=None):
        if eta_dif is not None: self.dif.eta         = eta_dif
        if eta_c   is not None: self.comp.eta        = eta_c
        if eta_fan is not None: self.fan.eta         = eta_fan
        if eta_cc  is not None: self.cc.eta          = eta_cc
        if eta_hpt is not None: self.hp_turbine.eta  = eta_hpt
        if eta_lpt is not None: self.lp_turbine.eta  = eta_lpt
        if eta_noz is not None: self.nozz.eta        = eta_noz

        V0 = mach * speed_of_sound(T_0)
        
        S_0 = 0
        T_2t,  P_2t, S_2           = self.dif.calculate(T_0, P_0, S_0, mach)
        T_3t,  P_3t, S_3,  W_c     = self.comp.calculate(T_2t, P_2t, S_2, pi_23)
        T_12t, P_12t, S_12 = T_2t, P_2t, S_2
        T_13t, P_13t, S_13, W_fan   = self.fan.calculate(T_12t,  P_12t, S_12, pi_fan)
        T_4t,  P_4t, S_4, FAR           = self.cc.calculate(T_3t, P_3t, S_3, tit)
        T_45t, P_45t, S_45, A_4     = self.hp_turbine.calculate(T_4t,  P_4t,  S_4, W_c, G*(1+FAR), FAR)
        T_5t,  P_5t, S_5, A_45     = self.lp_turbine.calculate(T_45t, P_45t, S_45, W_fan * bpr, G*(1+FAR), FAR)
        T_9,   P_9, S_9, V_jet, A_8   = self.nozz.calculate(T_5t,  P_5t,  S_5, T_0, P_0, G*(1+FAR))
        T_19,  P_19,  S_19,   V_bypass, A_18 = self.nozz.calculate(T_13t, P_13t, S_13, T_0, P_0, G*bpr)

        df = _fill_df(
            pd.DataFrame(index=[0,1,2,3,4,4.5,5,6,7,8,9,1.2,1.3,1.7,1.8,1.9],
                         columns=['T','P']),
            locals(),
            {0:"0", 2:"2t", 3:"3t", 4:"4t", 4.5:"45t", 5:"5t", 9:"9", 1.3:"13t"},
        )

        m_bypass = G * bpr
        opr      = pi_fan * pi_23

        r = _perf(V_jet=V_jet, V0=V0, m_dot=G, FAR=FAR, opr=opr, A_8=A_8,
                  A_18=A_18, V_bypass=V_bypass, m_bypass=m_bypass,
                  P_9=P_9, P_19=P_19, Tt0=T_2t, Tt3=T_3t, Tt4=T_4t, Tt5=T_5t,
                  Pt0_kPa=P_2t/1000, Pt3_kPa=P_3t/1000, P0_kPa=P_0/1000)
        stations = _build_stations(locals())
        
        r["A8"]          = A_8
        r["A18"]         = A_18
        r["df"]          = df
        r["opr"]         = opr
        r["bpr"]         = bpr
        r["engine_type"] = "SingleFlowTurbofan"
        r["tit_limit"]   = TIT_LIMIT
        r["stations"]  = stations
        return r


class OneSpoolTurboprop:
    """Turbohélice: Compresor → Cámara → HPT → LPT → Tobera residual."""

    def __init__(self):
        self.dif        = Difussor()
        self.comp       = Compressor()
        self.cc         = CombustionChamber()
        self.hp_turbine = Turbine()
        self.lp_turbine = Turbine()
        self.pc         = Postcombustor()
        self.nozz       = Nozzle()

    def simulate(self, T_0, P_0, mach, G, pi_23, tit, lam, eta_m, eta_h=1.0,
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

        V0 = mach * speed_of_sound(T_0)
        
        S_0 = 0
        T_2t,  P_2t, S_2           = self.dif.calculate(T_0, P_0, S_0, mach)
        T_3t,  P_3t, S_3, W_c     = self.comp.calculate(T_2t, P_2t, S_2, pi_23)
        T_4t,  P_4t, S_4, FAR      = self.cc.calculate(T_3t, P_3t, S_3, tit)
        T_45t, P_45t, S_45, A_4     = self.hp_turbine.calculate(T_4t,  P_4t,  S_4, W_c, G*(1+FAR), FAR)

        # Vtb   = math.sqrt(2 * CP * T_45t * (1 - (P_0 / P_45t)**((g-1)/g)))
        # V_jet = math.sqrt(lam) * Vtb 
        # W_lpt_spec = 0.5 * (Vtb**2 - V_jet**2)

        T_5t,  P_5t, S_5, A_45     = self.lp_turbine.calculate(T_45t, P_45t, S_45, W_c, G*(1+FAR), FAR)
        T_9,   P_9, S_9, V_jet, A_8   = self.nozz.calculate(T_5t, P_5t, S_5, T_0, P_0, G*(1+FAR))

        df = _fill_df(
            pd.DataFrame(index=[0,1,2,3,4,4.5,5,6,7,8,9], columns=['T','P']),
            locals(),
            {0:"0", 2:"2t", 3:"3t", 4:"4t", 4.5:"45t", 5:"5t", 9:"9"},
        )
        
        stations = _build_stations(locals())

        fuel_kg_s  = G * FAR
        F_residual = G * (V_jet - V0)
        F_helice   = F_residual
        F_total    = F_helice + F_residual

        eta_th = max(0.0, 1 - 1 / max(pi_23, 1.001) ** ((GAMMA - 1) / GAMMA))

        return {
            "thrust_kN":   F_total / 1000,
            "F_helice_kN": F_helice / 1000,
            "F_resid_kN":  F_residual / 1000,
            "sp_thrust":   F_total/G,
            "SFC":         fuel_kg_s / max(abs(F_total), 1) * 3600,
            "TSFC_mg":     (fuel_kg_s / max(abs(F_total), 1) * 3600) * 1e6 / 9.81,
            "eta_m":      eta_th * 100,
            "eta_p":    0.0,
            "eta_mp":  0.0,
            "fuel_kg_s":   fuel_kg_s,
            "FAR":         FAR,
            "V_jet":       V_jet,
            "V_bypass":    0.0,
            "V0":          V0,
            "m_core":      G,
            "m_bypass":    0.0,
            "shaft_MW":    0,
            "EGT":         T_5t * 0.88,
            "T0_K":        T_2t,
            "Tt3_K":       T_3t,
            "Tt4_K":       T_4t,
            "Tt5_K":       T_5t,
            "Pt0_kPa":     P_2t / 1000,
            "Pt3_kPa":     P_3t / 1000,
            "P0_kPa":      P_0 / 1000,
            "df":          df,
            "opr":         pi_23,
            "engine_type": "OneSpoolTurboprop",
            "tit_limit":   TIT_LIMIT,
            "stations":    stations
        }


# ══════════════════════════════════════════════════════════════════════════════
#  BARRIDOS PARAMÉTRICOS (para las gráficas de app.py)
# ══════════════════════════════════════════════════════════════════════════════

def sweep_tit(engine_type, base_params, n=50):
    """Barrido de TIT → lista de (tit, thrust_kN)."""
    tit_max = {"OneSpoolEngine":1700, "OneSpoolEngine_PC":1900,
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
            "OneSpoolEngine_PC":   OneSpoolEngine_PC,
            "SingleFlowTurbofan":SingleFlowTurbofan,
            "OneSpoolTurboprop": OneSpoolTurboprop}[engine_type]


# ══════════════════════════════════════════════════════════════════════════════
#  TEST RÁPIDO
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    T, P = isa_atmosphere(0, 15)

    r1 = OneSpoolEngine().simulate(223.15, 26418, 0.8, 50, 12, 1450, eta_c=1, eta_t=1)
    print(f"Monoeje   — F={r1['thrust_kN']:.2f} kN  TSFC={r1['TSFC_mg']:.2f} mg/Ns")

    r2 = OneSpoolEngine_PC().simulate(216.65, 22614, 1.6, 70, 10, 1500, 2000)
    print(f"Postcombustor     — F={r2['thrust_kN']:.2f} kN  TSFC={r2['TSFC_mg']:.2f} mg/Ns")

    r3 = SingleFlowTurbofan().simulate(216.65, 22614, 0.85, 40, 30, 1500, 1.6, 5)
    print(f"Turbofan  — F={r3['thrust_kN']:.2f} kN  TSFC={r3['TSFC_mg']:.2f} mg/Ns")

    r4 = OneSpoolTurboprop().simulate(T, P, 0.7, 90, 25, 1500, 200_000, 0.7)
    print(f"Turboprop — F={r4['thrust_kN']:.2f} kN  TSFC={r4['TSFC_mg']:.2f} mg/Ns")