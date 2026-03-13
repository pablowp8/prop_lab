
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math
import sys

class Component:
    def __init__(self, eta=1.0):
        self.eta = eta
        self.gamma = 1.4
        self.cp = 1004.3  # J/kgK (Specific heat at constant pressure)
        self.R = 287
        
class Difussor(Component):
    def calculate(self, t_in, p_in, mach, pressure_ratio=1.0):
        
        # Calculate temperature 
        t_in_t = t_in * (1 + (self.gamma - 1) * mach**2 / 2)
        t_out = t_in_t
        # Calculate pressure
        p_in_t = p_in * (1 + (self.gamma - 1) * mach**2 / 2)**(self.gamma / (self.gamma - 1))
        p_out = p_in_t * pressure_ratio
        
        return t_out, p_out

class Compressor(Component):
    def calculate(self, t_in, p_in, pressure_ratio):
        # Calculate discharge pressure
        p_out = p_in * pressure_ratio
        
        # Calculate ideal exit temperature (Isentropic)
        t_out_ideal = t_in * (pressure_ratio**((self.gamma - 1) / self.gamma))
        
        # Calculate actual exit temperature based on isentropic efficiency
        t_out= t_in + (t_out_ideal - t_in) / self.eta
        
        # Specific work required (W = cp * deltaT)
        work = self.cp * (t_out - t_in)
        
        return t_out, p_out, work

class CombustionChamber(Component):
    def calculate(self, t_in, p_in, tit, pressure_ratio=1.0):
        # TIT = Turbine Inlet Temperature
        # Accounting for a 5% pressure drop (standard assumption)
        p_out = p_in * pressure_ratio 
        heat_added = self.cp * (tit - t_in)
        
        return tit, p_out, heat_added

class Turbine(Component):
    def calculate(self, t_in, p_in, required_work):
        # Temperature drop needed to provide the required work
        t_out = t_in - (required_work / self.cp)
        
        # Calculate the exit pressure needed for that work/temperature drop
        # Using the isentropic relationship: P_ratio = (T_ratio)^(gamma / (gamma - 1))
        # Account for turbine efficiency (eta)
        p_out = p_in * (1 - (t_in - t_out) / (self.eta * t_in))**(self.gamma / (self.gamma - 1))
        
        return t_out, p_out
    
class Postcombustor(Component):
    def calculate(self, t_in, p_in):
        t_out, p_out = t_in, p_in
        return t_out, p_out
    
class Nozzle(Component):
    def calculate(self, t_in, p_in, t_a, p_a, conf='CON'):
        if conf == 'CON':
            param_pressure = p_in / p_a
            param_gamma = ((self.gamma + 1) / 2)**(self.gamma / (self.gamma-1))
            if param_pressure <= param_gamma:  # ADAPTADA
                p_out = p_a
                t_out = t_in * (1 / param_pressure)**((self.gamma - 1) / self.gamma)
                mach = math.sqrt((2 / (self.gamma - 1)) * (param_pressure**((self.gamma - 1) / self.gamma) - 1 ))
                v_out = mach * math.sqrt(self.gamma * self.R * t_out)
            else: # BLOQUEADA
                p_out = p_in / (((self.gamma + 1) / 2)**(self.gamma / (self.gamma-1))) 
                t_out = t_in / ((self.gamma + 1) / 2)
                mach = 1
                v_out = mach * math.sqrt(self.gamma * self.R * t_out)
        elif conf == 'CON-DIV': # ADAPTADA
            param_pressure = p_in / p_a
            p_out = p_a
            t_out = t_in * (1 / param_pressure)**((self.gamma - 1) / self.gamma)
            mach = math.sqrt((2 / (self.gamma - 1)) * (param_pressure**((self.gamma - 1) / self.gamma) - 1 ))
            v_out = mach * math.sqrt(self.gamma * self.R * t_out)
        
        return t_out, p_out, v_out
    
class OneSpoolEngine:
    def __init__(self):
        self.dif = Difussor()
        self.comp = Compressor(eta=0.8)
        self.cc = CombustionChamber()
        self.turb = Turbine(eta=0.88)
        self.pc = Postcombustor()
        self.nozz = Nozzle()
        
        self.out = pd.DataFrame(index=[0, 1, 2, 2.5, 3, 4, 4.5, 5, 6, 7, 8, 9], columns=['T', 'P'])

    def simulate(self, T_amb, P_amb, mach, G, pi_23, T_4t):
        
        T_2t, P_2t = self.dif.calculate(T_amb, P_amb, mach)
        # 1. Compression
        T_3t, P_3t, W_c = self.comp.calculate(T_2t, P_amb, pi_23)
        # 2. Combustion
        T_4t, P_4t, Q_in = self.cc.calculate(T_3t, P_3t, T_4t)
        # 3. Turbine (Acoplated to compressor)
        T_5t, P_5t = self.turb.calculate(T_4t, P_4t, W_c)
        
        T_7t, P_7t = self.pc.calculate(T_5t, P_5t)
        
        T_9, P_9, Vs = self.nozz.calculate(T_7t, P_7t, T_amb, P_amb)
        
        # Output diccionary
        
        mapping = {
            0: "0",
            1: "1t",
            2: "2t",
            2.5: "25t",
            3: "3t",
            4: "4t",
            4.5: "45t",
            5: "5t",
            6: "6t",
            7: "7t",
            8: "8t",
            9: "9"
                }
        
        current_vars = locals() # Captura todas las variables definidas arriba
        
        for station, suffix in mapping.items():
            t_var = f"T_{suffix}"
            p_var = f"P_{suffix}"
            
            # Solo si AMBAS variables existen en el código, rellenamos el DataFrame
            if t_var in current_vars and p_var in current_vars:
                self.out.loc[station, 'T'] = current_vars[t_var]
                self.out.loc[station, 'P'] = current_vars[p_var]

        return self.out
    

class TwinSpoolEngine:
    def __init__(self):
        
        self.dif = Difussor()
        # Eje de Baja Presión (LP Spool)
        self.lp_compressor = Compressor(eta=0.91)
        self.lp_turbine = Turbine(eta=0.94)
        
        # Eje de Alta Presión (HP Spool)
        self.hp_compressor = Compressor(eta=0.85)
        self.hp_turbine = Turbine(eta=0.92)
        
        self.cc = CombustionChamber()
        self.pc = Postcombustor()
        self.nozz = Nozzle()
        
        self.out = pd.DataFrame(index=[0, 1, 2, 2.5, 3, 4, 4.5, 5, 6, 7, 8, 9], columns=['T', 'P'])

    def simulate(self, T_amb, P_amb, mach, G, pi_lpc, pi_hpc, T_4t):
        
        T_2t, P_2t = self.dif.calculate(T_amb, P_amb, mach)
        # 1. LP COMPRESSOR
        T_25t, P_25t, w_lpc = self.lp_compressor.calculate(T_2t, P_2t, pi_lpc)
        
        # 2. HP COMPRESSOR (HP Spool) - Solo aire del núcleo (1 kg)
        T_3t, P_3t, w_hpc = self.hp_compressor.calculate(T_25t, P_25t, pi_hpc)
        
        # 3. COMBUSTOR
        T_4t, P_4t, Qin = self.cc.calculate(T_3t, P_3t, T_4t)
        
        # 4. HP TURBINE - Mueve únicamente al HP Compressor
        T_45t, P_45t = self.hp_turbine.calculate(T_4t, P_4t, w_hpc)
        
        # 5. LP TURBINE - Mueve únicamente al LP Compressor
        T_5t, P_5t = self.lp_turbine.calculate(T_45t, P_45t, w_lpc)
        
        T_7t, P_7t = self.pc.calculate(T_5t, P_5t)
        
        T_9, P_9, Vs = self.nozz.calculate(T_7t, P_7t, T_amb, P_amb)
        
        # Output diccionary
        
        mapping = {
            0: "0",
            1: "1t",
            2: "2t",
            2.5: "25t",
            3: "3t",
            4: "4t",
            4.5: "45t",
            5: "5t",
            6: "6t",
            7: "7t",
            8: "8t",
            9: "9"
                }
        
        current_vars = locals() # Captura todas las variables definidas arriba
        
        for station, suffix in mapping.items():
            t_var = f"T_{suffix}"
            p_var = f"P_{suffix}"
            
            # Solo si AMBAS variables existen en el código, rellenamos el DataFrame
            if t_var in current_vars and p_var in current_vars:
                self.out.loc[station, 'T'] = current_vars[t_var]
                self.out.loc[station, 'P'] = current_vars[p_var]

        return self.out
    
class SingleFlowTurbofan:
    def __init__(self):
        
        self.dif = Difussor()
        # Eje de Baja Presión (LP Spool)
        self.lp_turbine = Turbine(eta=1)
        self.fan = Compressor(eta=1)
        
        # Eje de Alta Presión (HP Spool)
        self.comp = Compressor(eta=1)
        self.hp_turbine = Turbine(eta=1)
        
        self.cc = CombustionChamber()
        self.pc = Postcombustor()
        self.nozz = Nozzle()
        
        self.out = pd.DataFrame(index=[0, 1, 2, 3, 4, 4.5, 5, 6, 7, 8, 9, 1.2, 1.3, 1.7, 1.8, 1.9], columns=['T', 'P'])

    def simulate(self, T_amb, P_amb, mach, G, pi_23, T_4t, pi_fan, bpr):
        
        T_2t, P_2t = self.dif.calculate(T_amb, P_amb, mach)
        # 1. COMPRESSOR
        T_3t, P_3t, W_c = self.comp.calculate(T_2t, P_2t, pi_23)
        
        # 2. FAN
        T_12t, P_12t = T_2t, P_2t
        T_13t, P_13t, W_fan = self.fan.calculate(T_12t, P_12t, pi_fan)
        
        # 3. COMBUSTOR
        T_4t, P_4t, Qin = self.cc.calculate(T_3t, P_3t, T_4t)
        
        # 4. HP TURBINE - Mueve únicamente al HP Compressor
        T_45t, P_45t = self.hp_turbine.calculate(T_4t, P_4t, W_c)
        
        # 5. LP TURBINE - Mueve únicamente al LP Compressor
        T_5t, P_5t = self.lp_turbine.calculate(T_45t, P_45t, W_fan*bpr)
        
        T_7t, P_7t = self.pc.calculate(T_5t, P_5t)
        
        T_9, P_9, Vs = self.nozz.calculate(T_7t, P_7t, T_amb, P_amb)
        
        # Output diccionary
        
        mapping = {
            0: "0",
            1: "1t",
            2: "2t",
            3: "3t",
            4: "4t",
            4.5: "45t",
            5: "5t",
            6: "6t",
            7: "7t",
            8: "8t",
            9: "9",
            1.2: "12t",
            1.3: "13t",
            1.7: "17t",
            1.8: "18t",
            1.9: "19t"
                }
        
        current_vars = locals() # Captura todas las variables definidas arriba
        
        for station, suffix in mapping.items():
            t_var = f"T_{suffix}"
            p_var = f"P_{suffix}"
            
            # Solo si AMBAS variables existen en el código, rellenamos el DataFrame
            if t_var in current_vars and p_var in current_vars:
                self.out.loc[station, 'T'] = current_vars[t_var]
                self.out.loc[station, 'P'] = current_vars[p_var]

        return self.out
    
    
class OneSpoolTurboprop:
    def __init__(self):
        
        self.dif = Difussor()
        # Eje de Baja Presión (LP Spool)
        self.lp_turbine = Turbine(eta=1)
        
        # Eje de Alta Presión (HP Spool)
        self.comp = Compressor(eta=1)
        self.hp_turbine = Turbine(eta=1)
        
        self.cc = CombustionChamber()
        
        self.pc = Postcombustor()
        self.nozz = Nozzle()
        
        self.out = pd.DataFrame(index=[0, 1, 2, 3, 4, 4.5, 5, 6, 7, 8, 9], columns=['T', 'P'])

    def simulate(self, T_amb, P_amb, mach, G, pi_23, T_4t, W_h, eta_m):
        
        T_2t, P_2t = self.dif.calculate(T_amb, P_amb, mach)
        # 1. COMPRESSOR
        T_3t, P_3t, W_c = self.comp.calculate(T_2t, P_2t, pi_23)
        
        # 3. COMBUSTOR
        T_4t, P_4t, Qin = self.cc.calculate(T_3t, P_3t, T_4t)
        
        # 4. HP TURBINE - Mueve únicamente al HP Compressor
        T_45t, P_45t = self.hp_turbine.calculate(T_4t, P_4t, W_c)
        
        # 5. LP TURBINE - Mueve únicamente al LP Compressor
        T_5t, P_5t = self.lp_turbine.calculate(T_45t, P_45t, W_h*eta_m)
        
        T_7t, P_7t = self.pc.calculate(T_5t, P_5t)
        
        T_9, P_9, Vs = self.nozz.calculate(T_7t, P_7t, T_amb, P_amb)
        
        # Output diccionary
        
        mapping = {
            0: "0",
            1: "1t",
            2: "2t",
            3: "3t",
            4: "4t",
            4.5: "45t",
            5: "5t",
            6: "6t",
            7: "7t",
            8: "8t",
            9: "9",
                }
        
        current_vars = locals() # Captura todas las variables definidas arriba
        
        for station, suffix in mapping.items():
            t_var = f"T_{suffix}"
            p_var = f"P_{suffix}"
            
            # Solo si AMBAS variables existen en el código, rellenamos el DataFrame
            if t_var in current_vars and p_var in current_vars:
                self.out.loc[station, 'T'] = current_vars[t_var]
                self.out.loc[station, 'P'] = current_vars[p_var]

        return self.out


if __name__ == "__main__":
    
    
    engine1 = OneSpoolEngine()
    out1 = engine1.simulate(T_amb=288, P_amb=101325, mach=0, G=20, pi_23=10, T_4t=1400)
    
    engine2 = TwinSpoolEngine()
    out2 = engine2.simulate(T_amb=288, P_amb=101325, mach=0, G=20, pi_lpc=1.6, pi_hpc=12, T_4t=1450)
    
    engine3 = SingleFlowTurbofan()
    out3 = engine3.simulate(T_amb=288, P_amb=101325, mach=0, G=90, pi_23=25, T_4t=1500, pi_fan=1.4, bpr=0.8)
    
    engine4 = OneSpoolTurboprop()
    out4 = engine4.simulate(T_amb=288, P_amb=101325, mach=0, G=90, pi_23=25, T_4t=1500, W_h=200000, eta_m=0.7)
        
    
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        