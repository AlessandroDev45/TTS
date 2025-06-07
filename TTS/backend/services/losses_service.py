# backend/services/losses_service.py
"""
Serviço para cálculos de perdas em transformadores
"""
import sys
import pathlib
import math
import logging
import numpy as np
import itertools
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Any

# --- Path Setup ---
current_file = pathlib.Path(__file__).absolute()
current_dir = current_file.parent
backend_dir = current_dir.parent
root_dir = backend_dir.parent
if str(root_dir) not in sys.path: sys.path.insert(0, str(root_dir))
if str(backend_dir) not in sys.path: sys.path.insert(0, str(backend_dir))
# --- End Path Setup ---

try:
    from utils import constants as const
    from utils.constants import (
        potencia_magnet_data, perdas_nucleo_data,
        potencia_magnet_data_H110_27, perdas_nucleo_data_H110_27,
        FATOR_CONSTRUCAO_PERDAS_H110_27, FATOR_CONSTRUCAO_POTENCIA_MAG_H110_27,
        FATOR_EXCITACAO_DEFAULT_TRIFASICO, FATOR_EXCITACAO_DEFAULT_MONOFASICO,
        SUT_BT_VOLTAGE, EPS_CURRENT_LIMIT, DUT_POWER_LIMIT,
        CAPACITORS_BY_VOLTAGE, Q_SWITCH_POWERS,
        CS_SWITCHES_BY_VOLTAGE_TRI, CS_SWITCHES_BY_VOLTAGE_MONO,
        SUT_AT_MIN_VOLTAGE, SUT_AT_MAX_VOLTAGE, SUT_AT_STEP_VOLTAGE
    )
except ImportError as e:
    logging.critical(f"Falha crítica: Não foi possível importar 'constants': {e}. O serviço de perdas não funcionará.")
    class MockConstants: # Minimal mock for critical attributes
        EPSILON = 1e-6; SQRT_3 = 1.732050807568877
        potencia_magnet_data = {}; perdas_nucleo_data = {}
        potencia_magnet_data_H110_27 = {}; perdas_nucleo_data_H110_27 = {}
        FATOR_CONSTRUCAO_PERDAS_H110_27 = 1.15; FATOR_CONSTRUCAO_POTENCIA_MAG_H110_27 = 1.2
        FATOR_EXCITACAO_DEFAULT_TRIFASICO = 3; FATOR_EXCITACAO_DEFAULT_MONOFASICO = 5
        SUT_BT_VOLTAGE = 480; EPS_CURRENT_LIMIT = 2000; DUT_POWER_LIMIT = 1350 # kW limit for active power
        CAPACITORS_BY_VOLTAGE = {'13.8': ['CAP1A1', 'CAP1B1', 'CAP1C1'], '23.9': [], '41.4': [], '71.7': []} # Example
        Q_SWITCH_POWERS = {"generic_cp": [1.2, 2.4, 4.8, 9.6, 19.2]} # Example values
        CS_SWITCHES_BY_VOLTAGE_TRI = {'13.8': ['CS1A1', 'CS1B1', 'CS1C1', 'CS1A2', 'CS1B2', 'CS1C2']} # Example
        CS_SWITCHES_BY_VOLTAGE_MONO = {'13.8': ['CS1A', 'CS1B']} # Example
        SUT_AT_MIN_VOLTAGE = 14000; SUT_AT_MAX_VOLTAGE = 140000; SUT_AT_STEP_VOLTAGE = 3000
    const = MockConstants()
    potencia_magnet_data, perdas_nucleo_data, potencia_magnet_data_H110_27, perdas_nucleo_data_H110_27 = const.potencia_magnet_data, const.perdas_nucleo_data, const.potencia_magnet_data_H110_27, const.perdas_nucleo_data_H110_27
    FATOR_CONSTRUCAO_PERDAS_H110_27, FATOR_CONSTRUCAO_POTENCIA_MAG_H110_27 = const.FATOR_CONSTRUCAO_PERDAS_H110_27, const.FATOR_CONSTRUCAO_POTENCIA_MAG_H110_27
    FATOR_EXCITACAO_DEFAULT_TRIFASICO, FATOR_EXCITACAO_DEFAULT_MONOFASICO = const.FATOR_EXCITACAO_DEFAULT_TRIFASICO, const.FATOR_EXCITACAO_DEFAULT_MONOFASICO
    SUT_BT_VOLTAGE, EPS_CURRENT_LIMIT, DUT_POWER_LIMIT = const.SUT_BT_VOLTAGE, const.EPS_CURRENT_LIMIT, const.DUT_POWER_LIMIT
    CAPACITORS_BY_VOLTAGE, Q_SWITCH_POWERS = const.CAPACITORS_BY_VOLTAGE, const.Q_SWITCH_POWERS
    CS_SWITCHES_BY_VOLTAGE_TRI, CS_SWITCHES_BY_VOLTAGE_MONO = const.CS_SWITCHES_BY_VOLTAGE_TRI, const.CS_SWITCHES_BY_VOLTAGE_MONO
    SUT_AT_MIN_VOLTAGE, SUT_AT_MAX_VOLTAGE, SUT_AT_STEP_VOLTAGE = const.SUT_AT_MIN_VOLTAGE, const.SUT_AT_MAX_VOLTAGE, const.SUT_AT_STEP_VOLTAGE


log = logging.getLogger(__name__)
epsilon = const.EPSILON

# --- Pydantic Models ---
class NoLoadLossesInput(BaseModel):
    perdas_vazio_ui: float = Field(..., gt=0, description="Perdas em vazio fornecidas pelo usuário em kW")
    peso_nucleo_ui: float = Field(..., gt=0, description="Peso do núcleo fornecido pelo usuário em Toneladas")
    corrente_excitacao_ui: float = Field(..., gt=0, description="Corrente de excitação fornecida pelo usuário em %")
    inducao_ui: float = Field(..., gt=0, description="Indução no núcleo fornecida pelo usuário em Tesla")
    corrente_exc_1_1_ui: Optional[float] = Field(None, gt=0, description="Corrente de excitação a 1.1pu em % (opcional)")
    corrente_exc_1_2_ui: Optional[float] = Field(None, gt=0, description="Corrente de excitação a 1.2pu em % (opcional)")
    frequencia: float = Field(..., gt=0)
    tensao_bt_kv: float = Field(..., gt=0)
    corrente_nominal_bt: float = Field(..., gt=0)
    tipo_transformador: str = "Trifásico"
    steel_type: str = "M4"
    potencia_mva: float = Field(..., gt=0)

class LoadLossesInput(BaseModel):
    temperatura_referencia: int = Field(..., ge=25)
    perdas_carga_kw_u_min: float = Field(..., gt=0)
    perdas_carga_kw_u_nom: float = Field(..., gt=0)
    perdas_carga_kw_u_max: float = Field(..., gt=0)
    potencia_mva: float = Field(..., gt=0)
    impedancia: float = Field(..., gt=0)
    tensao_at_kv: float = Field(..., gt=0)
    tensao_at_tap_maior_kv: float = Field(..., gt=0)
    tensao_at_tap_menor_kv: float = Field(..., gt=0)
    impedancia_tap_maior: float = Field(..., gt=0)
    impedancia_tap_menor: float = Field(..., gt=0)
    corrente_nominal_at_a: float = Field(..., gt=0)
    corrente_nominal_at_tap_maior_a: float = Field(..., gt=0)
    corrente_nominal_at_tap_menor_a: float = Field(..., gt=0)
    tipo_transformador: str = "Trifásico"
    perdas_vazio_kw_calculada: float = Field(..., gt=0)


# --- Helper Functions (safe_float, interpolate_losses_table_data) ---
def safe_float(value, default=0.0):
    try: return float(value) if value is not None and str(value).strip() != "" else default
    except (ValueError, TypeError): return default

def interpolate_losses_table_data(table_name: str, induction: float, frequency: float, steel_type: str = "M4") -> float:
    if steel_type == "M4":
        table = potencia_magnet_data if table_name == "potencia_magnet" else perdas_nucleo_data
    elif steel_type == "H110-27":
        table = potencia_magnet_data_H110_27 if table_name == "potencia_magnet" else perdas_nucleo_data_H110_27
    else:
        log.error(f"Tipo de aço desconhecido para interpolação: {steel_type}")
        return 0.0
    
    if not table:
        log.error(f"Tabela '{table_name}' para aço '{steel_type}' está vazia ou não definida.")
        return 0.0

    inductions = sorted(list(set(k[0] for k in table.keys())))
    frequencies = sorted(list(set(k[1] for k in table.keys())))

    if not inductions or not frequencies:
        log.error(f"Listas de indução/frequência vazias para tabela '{table_name}', aço '{steel_type}'.")
        return 0.0

    i0 = max((i for i in inductions if i <= induction), default=inductions[0])
    i1 = min((i for i in inductions if i >= induction), default=inductions[-1])
    f0 = max((f for f in frequencies if f <= frequency), default=frequencies[0])
    f1 = min((f for f in frequencies if f >= frequency), default=frequencies[-1])

    if induction < inductions[0] or induction > inductions[-1] or \
       frequency < frequencies[0] or frequency > frequencies[-1]:
        log.warning(f"Indução ({induction}T) ou Frequência ({frequency}Hz) fora do range da tabela {table_name} ({steel_type}). Usando valor do ponto mais próximo.")
        clamped_i = max(inductions[0], min(inductions[-1], induction))
        clamped_f = max(frequencies[0], min(frequencies[-1], frequency))
        closest_i = min(inductions, key=lambda x: abs(x - clamped_i))
        closest_f = min(frequencies, key=lambda x: abs(x - clamped_f))
        return table.get((closest_i, closest_f), 0.0)

    if abs(i0 - i1) < epsilon and abs(f0 - f1) < epsilon: return table.get((i0, f0), 0.0)
    if abs(i0 - i1) < epsilon: 
        v0, v1 = table.get((i0, f0), 0.0), table.get((i0, f1), 0.0)
        return v0 + (v1 - v0) * (frequency - f0) / (f1 - f0) if abs(f1 - f0) > epsilon else v0
    if abs(f0 - f1) < epsilon: 
        v0, v1 = table.get((i0, f0), 0.0), table.get((i1, f0), 0.0)
        return v0 + (v1 - v0) * (induction - i0) / (i1 - i0) if abs(i1 - i0) > epsilon else v0

    q11, q12 = table.get((i0, f0), 0.0), table.get((i0, f1), 0.0)
    q21, q22 = table.get((i1, f0), 0.0), table.get((i1, f1), 0.0)
    r1_num = (i1 - induction) * q11 + (induction - i0) * q21
    r1_den = (i1 - i0)
    r1 = r1_num / r1_den if r1_den > epsilon else (q11 if induction <= i0 else q21)
    r2_num = (i1 - induction) * q12 + (induction - i0) * q22
    r2_den = (i1 - i0)
    r2 = r2_num / r2_den if r2_den > epsilon else (q12 if induction <= i0 else q22)
    p_num = (f1 - frequency) * r1 + (frequency - f0) * r2
    p_den = (f1 - f0)
    p_result = p_num / p_den if p_den > epsilon else (r1 if frequency <=f0 else r2)
    return p_result


# --- Capacitor Bank Calculation Helpers ---
def generate_q_combinations(num_switches=5):
    q_indices = list(range(1, num_switches + 1))
    combinations = []
    for i in range(1, num_switches + 1):
        combinations.extend(itertools.combinations(q_indices, i))
    return [list(comb) for comb in combinations]

def calculate_q_combination_power(q_combination: List[int], available_caps_for_voltage: List[str]) -> float:
    total_power = 0.0
    power_steps = Q_SWITCH_POWERS.get("generic_cp")
    if not power_steps or len(power_steps) != 5:
        log.error("Generic Q switch power profile is missing or invalid.")
        return 0.0
    if not q_combination: return 0.0

    power_per_cap_unit = sum(power_steps[q - 1] for q in q_combination)
    total_power = power_per_cap_unit * len(available_caps_for_voltage)
    return total_power

def select_target_bank_voltage_keys(max_test_voltage_kv: float) -> tuple[Optional[str], Optional[str]]:
    if not CAPACITORS_BY_VOLTAGE: return None, None
    cap_bank_voltages_num = sorted([float(v_str) for v_str in CAPACITORS_BY_VOLTAGE.keys()])
    if not cap_bank_voltages_num: return None, None

    target_v_cf_key, target_v_sf_key = None, None

    for v_bank_num in cap_bank_voltages_num:
        if max_test_voltage_kv <= (v_bank_num * 1.1) + epsilon:
            target_v_cf_key = str(v_bank_num)
            break
    if target_v_cf_key is None: target_v_cf_key = str(cap_bank_voltages_num[-1])

    for v_bank_num in cap_bank_voltages_num:
        if max_test_voltage_kv <= v_bank_num + epsilon:
            target_v_sf_key = str(v_bank_num)
            break
    if target_v_sf_key is None: target_v_sf_key = str(cap_bank_voltages_num[-1])
    
    return target_v_cf_key, target_v_sf_key

def get_cs_configuration(target_bank_voltage_key: Optional[str], use_group1_only: bool, circuit_type: str) -> str:
    if target_bank_voltage_key is None: return "N/A (V Alvo Inv.)"
    cs_switch_dict = CS_SWITCHES_BY_VOLTAGE_TRI if circuit_type == "Trifásico" else CS_SWITCHES_BY_VOLTAGE_MONO
    available_switches = cs_switch_dict.get(target_bank_voltage_key, [])
    
    if not available_switches:
        log.warning(f"No CS switches found for key '{target_bank_voltage_key}' (Type: {circuit_type}). Available keys: {list(cs_switch_dict.keys())}")
        return f"N/A (Sem CS p/ {target_bank_voltage_key}kV)"
    
    cs_config_list = []
    for switch_name in available_switches:
        is_group_2_switch = len(switch_name) > 4 and switch_name.endswith("2")
        if use_group1_only and circuit_type == "Trifásico" and is_group_2_switch:
            log.debug(f"Skipping Group 2 CS switch {switch_name} for {target_bank_voltage_key}kV (Trifásico, Group1 only).")
            continue
        cs_config_list.append(switch_name)
    return ", ".join(sorted(cs_config_list)) if cs_config_list else "N/A"

def find_best_q_configuration(target_bank_voltage_key: Optional[str], required_power_mvar: float, use_group1_only: bool) -> tuple[str, float]:
    if target_bank_voltage_key is None or required_power_mvar is None or required_power_mvar <= epsilon:
        return "N/A", 0.0
    
    all_available_caps = CAPACITORS_BY_VOLTAGE.get(target_bank_voltage_key, [])
    if not all_available_caps:
        log.warning(f"No capacitors found for key '{target_bank_voltage_key}'. Available keys: {list(CAPACITORS_BY_VOLTAGE.keys())}")
        return f"N/A (Sem Caps p/ {target_bank_voltage_key}kV)", 0.0

    if use_group1_only:
        available_caps = [cap for cap in all_available_caps if len(cap) > 4 and cap.endswith("1")]
        if not available_caps: # Fallback if no group 1 caps found but group1_only was true
            log.warning(f"No Group 1 caps for {target_bank_voltage_key}kV, using all available as fallback.")
            available_caps = all_available_caps
    else:
        available_caps = all_available_caps

    if not available_caps:
        return f"N/A (Sem Caps Sel. p/ {target_bank_voltage_key}kV)", 0.0

    q_combinations = generate_q_combinations()
    best_combination, min_power_above_req = None, float("inf")

    for q_comb in q_combinations:
        current_power = calculate_q_combination_power(q_comb, available_caps)
        if current_power >= required_power_mvar - epsilon:
            if current_power < min_power_above_req - epsilon or \
               (abs(current_power - min_power_above_req) < epsilon and best_combination and len(q_comb) < len(best_combination)):
                min_power_above_req = current_power
                best_combination = q_comb
    
    if best_combination:
        return ", ".join([f"Q{q}" for q in sorted(best_combination)]), min_power_above_req
    else:
        max_possible = calculate_q_combination_power([1,2,3,4,5], available_caps)
        return f"N/A (Req {required_power_mvar:.1f} > Max {max_possible:.1f})", max_possible

def suggest_capacitor_bank_config_overall(max_voltage_kv: float, max_power_mvar_required: float, circuit_type: str) -> Dict[str, Any]:
    if max_voltage_kv <= epsilon or max_power_mvar_required <= epsilon:
        return {"cs_config": "N/A", "q_config": "N/A", "q_provided_mvar": 0.0}

    target_v_cf_key, _ = select_target_bank_voltage_keys(max_voltage_kv)
    if target_v_cf_key is None:
        return {"cs_config": "N/A (Erro V)", "q_config": "N/A", "q_provided_mvar": 0.0}

    group1_caps = [cap for cap in CAPACITORS_BY_VOLTAGE.get(target_v_cf_key, []) if len(cap) > 4 and cap.endswith("1")]
    max_power_group1 = calculate_q_combination_power([1,2,3,4,5], group1_caps) if group1_caps else 0.0
    use_group1_only = max_power_mvar_required <= max_power_group1 + epsilon

    cs_config = get_cs_configuration(target_v_cf_key, use_group1_only, circuit_type)
    q_config, q_provided = find_best_q_configuration(target_v_cf_key, max_power_mvar_required, use_group1_only)
    
    return {"cs_config": cs_config, "q_config": q_config, "q_provided_mvar": q_provided}


# --- No-Load Losses Calculation ---
def calculate_no_load_losses(data_in: Dict[str, Any]) -> Dict[str, Any]:
    try:
        data = NoLoadLossesInput(**data_in)
    except Exception as e:
        log.error(f"Erro de validação Pydantic em NoLoadLossesInput: {e}")
        raise ValueError(f"Dados de entrada para perdas em vazio inválidos: {e}")

    sqrt_3_factor = const.SQRT_3 if data.tipo_transformador.lower() == "trifásico" else 1.0
    peso_nucleo_kg_ui = data.peso_nucleo_ui * 1000

    fator_perdas_aco = interpolate_losses_table_data("perdas_nucleo", data.inducao_ui, data.frequencia, data.steel_type)
    fator_potencia_mag_aco = interpolate_losses_table_data("potencia_magnet", data.inducao_ui, data.frequencia, data.steel_type)

    if data.steel_type == "H110-27":
        fator_perdas_aco *= FATOR_CONSTRUCAO_PERDAS_H110_27
        fator_potencia_mag_aco *= FATOR_CONSTRUCAO_POTENCIA_MAG_H110_27

    if fator_perdas_aco <= epsilon: raise ValueError("Fator de perdas do aço calculado é zero ou negativo.")
    
    peso_nucleo_calc_kg = (data.perdas_vazio_ui * 1000) / fator_perdas_aco
    peso_nucleo_calc_ton = peso_nucleo_calc_kg / 1000
    potencia_mag_aco_kvar = (fator_potencia_mag_aco * peso_nucleo_calc_kg) / 1000
    
    den_corr_exc_calc = data.tensao_bt_kv * sqrt_3_factor
    corrente_excitacao_calc_a = potencia_mag_aco_kvar / den_corr_exc_calc if den_corr_exc_calc > epsilon else 0.0
    corrente_excitacao_percentual_calc = (corrente_excitacao_calc_a / data.corrente_nominal_bt) * 100 if data.corrente_nominal_bt > epsilon else 0.0

    tensao_teste_1_1_kv = data.tensao_bt_kv * 1.1
    tensao_teste_1_2_kv = data.tensao_bt_kv * 1.2
    
    # Project currents (from % input) for 1.0pu
    corrente_excitacao_projeto_a = data.corrente_nominal_bt * (data.corrente_excitacao_ui / 100.0)
    
    fator_exc_default = FATOR_EXCITACAO_DEFAULT_TRIFASICO if data.tipo_transformador.lower() == "trifásico" else FATOR_EXCITACAO_DEFAULT_MONOFASICO
    
    # Currents for 1.1pu and 1.2pu based on UI inputs, or default factors if UI inputs are not provided
    corrente_exc_1_1_proj_a = (data.corrente_nominal_bt * (data.corrente_exc_1_1_ui / 100.0)) \
        if data.corrente_exc_1_1_ui is not None else (fator_exc_default * corrente_excitacao_projeto_a)
        
    corrente_exc_1_2_proj_a = (data.corrente_nominal_bt * (data.corrente_exc_1_2_ui / 100.0)) \
        if data.corrente_exc_1_2_ui is not None else None # No default for 1.2pu if not provided

    fator_perdas_projeto_w_kg = (data.perdas_vazio_ui * 1000) / peso_nucleo_kg_ui if peso_nucleo_kg_ui > epsilon else 0.0 # W/kg
    
    potencia_ensaio_1pu_projeto_kva = data.tensao_bt_kv * corrente_excitacao_projeto_a * sqrt_3_factor
    potencia_mag_projeto_kvar = potencia_ensaio_1pu_projeto_kva # Approximation for project
    fator_pot_mag_projeto_var_kg = (potencia_mag_projeto_kvar * 1000) / peso_nucleo_kg_ui if peso_nucleo_kg_ui > epsilon else 0.0 # VAR/kg
    
    sut_eps_analysis_results = {}
    scenarios_no_load = {
        "1.0pu": {"Vtest_kv": data.tensao_bt_kv, "Itest_a": corrente_excitacao_projeto_a},
        "1.1pu": {"Vtest_kv": tensao_teste_1_1_kv, "Itest_a": corrente_exc_1_1_proj_a},
    }
    if corrente_exc_1_2_proj_a is not None:
         scenarios_no_load["1.2pu"] = {"Vtest_kv": tensao_teste_1_2_kv, "Itest_a": corrente_exc_1_2_proj_a}

    for scen_key, scen_params in scenarios_no_load.items():
        V_teste_dut_lv_kv = scen_params["Vtest_kv"]
        I_exc_dut_lv_a = scen_params["Itest_a"]
        
        if V_teste_dut_lv_kv is None or I_exc_dut_lv_a is None or V_teste_dut_lv_kv <= epsilon or I_exc_dut_lv_a <= epsilon:
            sut_eps_analysis_results[scen_key] = {"status": "Dados de ensaio insuficientes", "taps_info": []}
            continue

        V_target_sut_hv_v = V_teste_dut_lv_kv * 1000
        taps_sut_hv_v_all = np.arange(SUT_AT_MIN_VOLTAGE, SUT_AT_MAX_VOLTAGE + SUT_AT_STEP_VOLTAGE, SUT_AT_STEP_VOLTAGE)
        taps_sut_hv_v = taps_sut_hv_v_all[taps_sut_hv_v_all > epsilon]

        if not taps_sut_hv_v.any():
            sut_eps_analysis_results[scen_key] = {"status": "Faixa SUT AT inválida", "taps_info": []}
            continue
        
        diffs = {tap_v: abs(tap_v - V_target_sut_hv_v) for tap_v in taps_sut_hv_v}
        taps_ordenados_v = sorted(taps_sut_hv_v, key=lambda tap_v: diffs[tap_v])
        top_taps_v = taps_ordenados_v[:5] 

        taps_info_list = []
        for V_sut_hv_tap_v_selected in top_taps_v:
            if SUT_BT_VOLTAGE <= epsilon: continue
            ratio_sut = V_sut_hv_tap_v_selected / SUT_BT_VOLTAGE
            I_sut_lv_a = I_exc_dut_lv_a * ratio_sut 
            percent_limite_eps = (I_sut_lv_a / EPS_CURRENT_LIMIT) * 100 if EPS_CURRENT_LIMIT > epsilon else float('inf')
            taps_info_list.append({
                "sut_tap_kv": round(V_sut_hv_tap_v_selected / 1000, 2),
                "corrente_eps_a": round(I_sut_lv_a, 2),
                "percent_limite_eps": round(percent_limite_eps, 1) # 1 decimal for percentage
            })
        taps_info_list.sort(key=lambda x: x["sut_tap_kv"])
        sut_eps_analysis_results[scen_key] = {"status": "OK", "taps_info": taps_info_list}

    results = {
        "calculos_baseados_aco": { # Based on M4 steel properties and calculated core weight
            "peso_nucleo_calc_ton": round(peso_nucleo_calc_ton, 3),
            "potencia_mag_aco_kvar": round(potencia_mag_aco_kvar, 2),
            "corrente_excitacao_calc_a": round(corrente_excitacao_calc_a, 2),
            "corrente_excitacao_percentual_calc": round(corrente_excitacao_percentual_calc, 2),
        },
        "calculos_vazio": { # Based on project inputs and some calculations
            "tensao_teste_1_1_kv": round(tensao_teste_1_1_kv, 2),
            "corrente_excitacao_1_1_calc_a": round(corrente_exc_1_1_proj_a, 2), # Corrected to use proj_a
            "tensao_teste_1_2_kv": round(tensao_teste_1_2_kv, 2) if corrente_exc_1_2_proj_a is not None else None,
            "corrente_excitacao_1_2_calc_a": round(corrente_exc_1_2_proj_a, 2) if corrente_exc_1_2_proj_a is not None else None,
            "fator_perdas_projeto_w_kg": round(fator_perdas_projeto_w_kg, 3),
            "fator_pot_mag_projeto_var_kg": round(fator_pot_mag_projeto_var_kg, 3)
        },
        "analise_sut_eps_vazio": sut_eps_analysis_results
    }
    return results


# --- SUT/EPS Compensated Current (Load Losses) ---
def calculate_sut_eps_current_compensated(
    tensao_ref_dut_kv: float, corrente_ref_dut_a: float,
    q_power_provided_sf_mvar: Optional[float], cap_bank_voltage_sf_kv: Optional[float],
    q_power_provided_cf_mvar: Optional[float], cap_bank_voltage_cf_kv: Optional[float],
    tipo_transformador: str, V_sut_hv_tap_v: float
) -> Dict[str, float]:
    
    if any(v is None or (isinstance(v, (int,float)) and v <= epsilon) for v in [tensao_ref_dut_kv, corrente_ref_dut_a, V_sut_hv_tap_v, SUT_BT_VOLTAGE]):
        log.warning("SUT/EPS compensated: Invalid base inputs. Returning uncompensated.")
        ratio_sut_fallback = V_sut_hv_tap_v / SUT_BT_VOLTAGE if SUT_BT_VOLTAGE > epsilon else 0
        I_dut_reflected_fallback = corrente_ref_dut_a * ratio_sut_fallback
        percent_fallback = (I_dut_reflected_fallback / EPS_CURRENT_LIMIT) * 100 if EPS_CURRENT_LIMIT > epsilon else float('inf')
        return {"corrente_eps_sf_a": I_dut_reflected_fallback, "percent_limite_sf": percent_fallback,
                "corrente_eps_cf_a": I_dut_reflected_fallback, "percent_limite_cf": percent_fallback}

    ratio_sut = V_sut_hv_tap_v / SUT_BT_VOLTAGE
    I_dut_reflected_amps = corrente_ref_dut_a * ratio_sut
    sqrt_3_factor = const.SQRT_3 if tipo_transformador == "Trifásico" else 1.0
    
    results_comp = {
        "corrente_eps_sf_a": I_dut_reflected_amps, 
        "percent_limite_sf": (abs(I_dut_reflected_amps)/EPS_CURRENT_LIMIT)*100 if EPS_CURRENT_LIMIT > 0 else float('inf'),
        "corrente_eps_cf_a": I_dut_reflected_amps, 
        "percent_limite_cf": (abs(I_dut_reflected_amps)/EPS_CURRENT_LIMIT)*100 if EPS_CURRENT_LIMIT > 0 else float('inf')
    }
    if I_dut_reflected_amps < 0 : 
        results_comp["percent_limite_sf"] *= -1
        results_comp["percent_limite_cf"] *= -1


    # S/F Compensation
    if q_power_provided_sf_mvar is not None and q_power_provided_sf_mvar > epsilon and \
       cap_bank_voltage_sf_kv is not None and cap_bank_voltage_sf_kv > epsilon:
        Cap_Correct_factor_sf = 0.25 if cap_bank_voltage_sf_kv in [13.8, 23.9] else \
                                0.75 if cap_bank_voltage_sf_kv in [41.4, 71.7] else 1.0
        q_denom_sf = ((tensao_ref_dut_kv / cap_bank_voltage_sf_kv)**2 * Cap_Correct_factor_sf) if cap_bank_voltage_sf_kv > epsilon else 0
        pteste_mvar_corrected_sf = q_power_provided_sf_mvar * q_denom_sf if q_denom_sf > epsilon else 0
        I_cap_base_sf_den = (tensao_ref_dut_kv * sqrt_3_factor)
        I_cap_base_sf = (pteste_mvar_corrected_sf * 1000.0) / I_cap_base_sf_den if I_cap_base_sf_den > epsilon else 0
        I_cap_adjustment_sf = I_cap_base_sf * ratio_sut
        I_eps_sf_net = I_dut_reflected_amps - I_cap_adjustment_sf
        results_comp["corrente_eps_sf_a"] = I_eps_sf_net
        results_comp["percent_limite_sf"] = (abs(I_eps_sf_net) / EPS_CURRENT_LIMIT) * 100 if EPS_CURRENT_LIMIT > epsilon else float('inf')
        if I_eps_sf_net < 0: results_comp["percent_limite_sf"] *= -1

    # C/F Compensation
    if q_power_provided_cf_mvar is not None and q_power_provided_cf_mvar > epsilon and \
       cap_bank_voltage_cf_kv is not None and cap_bank_voltage_cf_kv > epsilon:
        Cap_Correct_factor_cf = 1.0 # Always 1.0 for C/F
        q_denom_cf = ((tensao_ref_dut_kv / cap_bank_voltage_cf_kv)**2 * Cap_Correct_factor_cf) if cap_bank_voltage_cf_kv > epsilon else 0
        pteste_mvar_corrected_cf = q_power_provided_cf_mvar * q_denom_cf if q_denom_cf > epsilon else 0
        I_cap_base_cf_den = (tensao_ref_dut_kv * sqrt_3_factor)
        I_cap_base_cf = (pteste_mvar_corrected_cf * 1000.0) / I_cap_base_cf_den if I_cap_base_cf_den > epsilon else 0
        I_cap_adjustment_cf = I_cap_base_cf * ratio_sut
        I_eps_cf_net = I_dut_reflected_amps - I_cap_adjustment_cf
        results_comp["corrente_eps_cf_a"] = I_eps_cf_net
        results_comp["percent_limite_cf"] = (abs(I_eps_cf_net) / EPS_CURRENT_LIMIT) * 100 if EPS_CURRENT_LIMIT > epsilon else float('inf')
        if I_eps_cf_net < 0: results_comp["percent_limite_cf"] *= -1
        
    return results_comp


# --- Status String Generation Helper (Load Losses) ---
def get_scenario_status_string(
    test_voltage_kv: float, 
    bank_voltage_cf_kv: Optional[float], 
    power_cf_required_mvar: Optional[float],
    test_current_a: Optional[float], 
    active_power_kw: Optional[float]
) -> str:
    status_parts = []
    events = 0
    
    test_v = safe_float(test_voltage_kv, 0.0)
    bank_v_cf = safe_float(bank_voltage_cf_kv, 0.0)
    power_cf_req = safe_float(power_cf_required_mvar, 0.0)
    current_a = safe_float(test_current_a, 0.0)
    active_p_kw = safe_float(active_power_kw, 0.0)

    # 1. Voltage Check (C/F bank)
    if bank_v_cf > epsilon:
        limit_v_cf = bank_v_cf * 1.1 # 110% of nominal bank voltage for C/F
        if test_v > limit_v_cf + epsilon:
            percent_above = ((test_v / limit_v_cf) - 1) * 100 if limit_v_cf > epsilon else float('inf')
            status_parts.append(f"(V) > Limite ({percent_above:.0f}%)")
            events += 1
    
    # 2. Current Check (EPS Current Limit)
    if current_a > EPS_CURRENT_LIMIT + epsilon:
        status_parts.append(f"(A) > Limite ({current_a:.0f}A)")
        events += 1

    # 3. Active Power Check (DUT Power Limit - assuming this is for active power output from source)
    if active_p_kw > DUT_POWER_LIMIT + epsilon: # DUT_POWER_LIMIT is in kW
        status_parts.append(f"(P) > Limite ({active_p_kw:.0f}kW)")
        events += 1

    # 4. Reactive Power Check (using required power for C/F)
    # Thresholds from Dash ParameterAnalyzer
    potencia_critica_mvar = 93.6 
    potencia_alerta_mvar = 46.8

    if power_cf_req > potencia_critica_mvar + epsilon:
        status_parts.append(f"CapBank Q_req ↑ ({potencia_critica_mvar:.0f}+ MVAr)")
        events +=1
    elif power_cf_req > potencia_alerta_mvar + epsilon:
        status_parts.append(f"CapBank Q_req ↑ ({potencia_alerta_mvar:.0f}+ MVAr)")
        events +=1

    if not status_parts: return "OK"
    if events > 1: status_parts.append(f"({events})")
    return " | ".join(status_parts)


# --- Load Losses Calculation (Main Function) ---
def calculate_load_losses(data_in: Dict[str, Any]) -> Dict[str, Any]:
    try:
        data = LoadLossesInput(**data_in)
    except Exception as e:
        log.error(f"Erro de validação Pydantic em LoadLossesInput: {e}")
        raise ValueError(f"Dados de entrada para perdas em carga inválidos: {e}")

    sqrt_3_factor = const.SQRT_3 if data.tipo_transformador.lower() == "trifásico" else 1.0
    
    perdas_carga_sem_vazio_nom = data.perdas_carga_kw_u_nom - data.perdas_vazio_kw_calculada
    if perdas_carga_sem_vazio_nom <= epsilon:
        raise ValueError("Perdas em carga (sem vazio) nominais devem ser positivas.")
    
    temp_factor = (235.0 + 25.0) / (235.0 + data.temperatura_referencia) # Copper at 25C to Tref
    perdas_pu_nominal = (perdas_carga_sem_vazio_nom / (data.potencia_mva * 1000.0)) * 100 if data.potencia_mva > epsilon else 0.0
    resistencia_percentual = perdas_pu_nominal
    reatancia_percentual = math.sqrt(max(0, data.impedancia**2 - resistencia_percentual**2))
    fp_curto_circuito = resistencia_percentual / data.impedancia if data.impedancia > epsilon else 0.0
    i2r_perdas_nom = perdas_carga_sem_vazio_nom * 0.85 # Assume 85% are I2R
    perdas_adicionais_nom = perdas_carga_sem_vazio_nom - i2r_perdas_nom

    condicoes_nominais_results = {
        "temperatura_referencia": data.temperatura_referencia,
        "perdas_tap_nominal": round(data.perdas_carga_kw_u_nom, 2),
        "perdas_por_unidade": round(perdas_pu_nominal, 4),
        "impedancia_entrada": round(data.impedancia, 4),
        "resistencia_percentual": round(resistencia_percentual, 4),
        "reatancia_percentual": round(reatancia_percentual, 4),
        "fator_potencia_curto_circuito": round(fp_curto_circuito, 4),
        "fator_correcao_temperatura": round(temp_factor, 4),
        "i2r_perdas": round(i2r_perdas_nom, 2),
        "perdas_adicionais": round(perdas_adicionais_nom, 2),
    }

    cenarios_config_list = [
        ("Nominal", data.tensao_at_kv, data.corrente_nominal_at_a, data.impedancia, data.perdas_carga_kw_u_nom),
        ("Menor", data.tensao_at_tap_menor_kv, data.corrente_nominal_at_tap_menor_a, data.impedancia_tap_menor, data.perdas_carga_kw_u_min),
        ("Maior", data.tensao_at_tap_maior_kv, data.corrente_nominal_at_tap_maior_a, data.impedancia_tap_maior, data.perdas_carga_kw_u_max),
    ]

    all_taps_data = []
    max_overall_test_v_kv = 0.0
    max_overall_q_mvar_req = 0.0 # Track required Q for overall bank suggestion
    
    test_types_standard = ["25°C", "Frio", "Quente"]
    test_types_overload = ["1.2 pu", "1.4 pu"]
    
    for tap_label, Vnom_kv_tap, Inom_a_tap, Z_percent_tap, Pcarga_total_kw_tap in cenarios_config_list:
        current_tap_data: Dict[str, Any] = {"nome_tap": tap_label, "cenarios_do_tap": []}
        
        Pcarga_sem_vazio_kw_tap = Pcarga_total_kw_tap - data.perdas_vazio_kw_calculada
        if Pcarga_sem_vazio_kw_tap <= epsilon:
            log.warning(f"Perdas carga s/vazio inválidas para Tap {tap_label}. Pulando cenários.")
            all_taps_data.append(current_tap_data)
            continue
        
        Pcc_frio_kw_tap = Pcarga_sem_vazio_kw_tap * temp_factor # Losses at 25C for this tap
        Vcc_kv_tap = (Vnom_kv_tap / 100.0) * Z_percent_tap

        current_test_types = test_types_standard
        if data.tensao_at_kv >= 230: # As per Dash logic
            current_test_types.extend(test_types_overload)

        for test_type_label in current_test_types:
            scen_res_dict: Dict[str, Any] = {"nome_cenario_teste": test_type_label}
            Vtest_kv_scen, Itest_a_scen, Pativa_kw_scen = 0.0, 0.0, 0.0
            
            if test_type_label == "25°C": # Test with losses at 25C
                Vtest_kv_scen, Itest_a_scen, Pativa_kw_scen = Vcc_kv_tap, Inom_a_tap, Pcc_frio_kw_tap
            elif test_type_label == "Frio": # Energization, total losses at Tref
                ratio_sqrt_frio = math.sqrt(Pcarga_total_kw_tap / Pcc_frio_kw_tap) if Pcc_frio_kw_tap > epsilon else 0.0
                Vtest_kv_scen, Itest_a_scen, Pativa_kw_scen = Vcc_kv_tap * ratio_sqrt_frio, Inom_a_tap * ratio_sqrt_frio, Pcarga_total_kw_tap
            elif test_type_label == "Quente": # Load losses at Tref
                ratio_sqrt_quente = math.sqrt(Pcarga_sem_vazio_kw_tap / Pcc_frio_kw_tap) if Pcc_frio_kw_tap > epsilon else 0.0
                Vtest_kv_scen, Itest_a_scen, Pativa_kw_scen = Vcc_kv_tap * ratio_sqrt_quente, Inom_a_tap * ratio_sqrt_quente, Pcarga_sem_vazio_kw_tap
            elif "pu" in test_type_label: 
                pu_factor = 1.2 if "1.2" in test_type_label else 1.4
                Vtest_kv_scen, Itest_a_scen = Vcc_kv_tap * pu_factor, Inom_a_tap * pu_factor
                Pativa_kw_scen = Pcarga_sem_vazio_kw_tap * (pu_factor**2) # Losses scale with I^2

            Pteste_kva_scen = Vtest_kv_scen * Itest_a_scen * sqrt_3_factor
            Pteste_mva_scen = Pteste_kva_scen / 1000.0
            Pteste_mvar_req_scen = math.sqrt(max(0, Pteste_kva_scen**2 - Pativa_kw_scen**2)) / 1000.0 if Pteste_kva_scen >= Pativa_kw_scen else 0.0

            scen_res_dict["test_params_cenario"] = {
                "tensao_kv": round(Vtest_kv_scen,2), "corrente_a": round(Itest_a_scen,2),
                "pativa_kw": round(Pativa_kw_scen,2), "pteste_mva": round(Pteste_mva_scen,3),
                "pteste_mvar_req": round(Pteste_mvar_req_scen,3)
            }
            max_overall_test_v_kv = max(max_overall_test_v_kv, Vtest_kv_scen)
            max_overall_q_mvar_req = max(max_overall_q_mvar_req, Pteste_mvar_req_scen)

            target_v_cf_key, target_v_sf_key = select_target_bank_voltage_keys(Vtest_kv_scen)
            
            # S/F Bank Configuration
            bank_sf_details: Dict[str, Any] = {"tensao_disp_kv": None, "q_provided_mvar": 0.0, "cs_config": "N/A", "q_config": "N/A"}
            if target_v_sf_key and Pteste_mvar_req_scen > epsilon:
                g1_caps_sf = [c for c in CAPACITORS_BY_VOLTAGE.get(target_v_sf_key, []) if len(c) > 4 and c.endswith("1")]
                max_p_g1_sf = calculate_q_combination_power([1,2,3,4,5], g1_caps_sf) if g1_caps_sf else 0.0
                use_g1_sf = Pteste_mvar_req_scen <= max_p_g1_sf + epsilon
                bank_sf_details["tensao_disp_kv"] = float(target_v_sf_key)
                bank_sf_details["cs_config"] = get_cs_configuration(target_v_sf_key, use_g1_sf, data.tipo_transformador)
                q_cfg_sf, q_prov_sf = find_best_q_configuration(target_v_sf_key, Pteste_mvar_req_scen, use_g1_sf)
                bank_sf_details["q_config"], bank_sf_details["q_provided_mvar"] = q_cfg_sf, q_prov_sf
            scen_res_dict["cap_bank_sf"] = bank_sf_details
            
            # C/F Bank Configuration
            bank_cf_details: Dict[str, Any] = {"tensao_disp_kv": None, "q_provided_mvar": 0.0, "cs_config": "N/A", "q_config": "N/A"}
            if target_v_cf_key and Pteste_mvar_req_scen > epsilon:
                g1_caps_cf = [c for c in CAPACITORS_BY_VOLTAGE.get(target_v_cf_key, []) if len(c) > 4 and c.endswith("1")]
                max_p_g1_cf = calculate_q_combination_power([1,2,3,4,5], g1_caps_cf) if g1_caps_cf else 0.0
                use_g1_cf = Pteste_mvar_req_scen <= max_p_g1_cf + epsilon
                bank_cf_details["tensao_disp_kv"] = float(target_v_cf_key)
                bank_cf_details["cs_config"] = get_cs_configuration(target_v_cf_key, use_g1_cf, data.tipo_transformador)
                q_cfg_cf, q_prov_cf = find_best_q_configuration(target_v_cf_key, Pteste_mvar_req_scen, use_g1_cf)
                bank_cf_details["q_config"], bank_cf_details["q_provided_mvar"] = q_cfg_cf, q_prov_cf
            scen_res_dict["cap_bank_cf"] = bank_cf_details
            
            scen_res_dict["status_cenario"] = get_scenario_status_string(
                Vtest_kv_scen, bank_cf_details["tensao_disp_kv"], Pteste_mvar_req_scen, # Use required Q for status
                Itest_a_scen, Pativa_kw_scen
            )
            
            sut_eps_taps_info_list = []
            taps_sut_hv_v_all_iter = np.arange(SUT_AT_MIN_VOLTAGE, SUT_AT_MAX_VOLTAGE + SUT_AT_STEP_VOLTAGE, SUT_AT_STEP_VOLTAGE)
            taps_sut_hv_v_iter = taps_sut_hv_v_all_iter[taps_sut_hv_v_all_iter > epsilon]
            if taps_sut_hv_v_iter.any():
                diffs_sut = {tap_v_sut: abs(tap_v_sut - (Vtest_kv_scen*1000)) for tap_v_sut in taps_sut_hv_v_iter}
                top_taps_v_sut = sorted(taps_sut_hv_v_iter, key=lambda tap_v_sut: diffs_sut[tap_v_sut])[:5] # Top 5 closest
                for V_sut_hv_tap_v_sel_iter in top_taps_v_sut:
                    comp_curr_res = calculate_sut_eps_current_compensated(
                        Vtest_kv_scen, Itest_a_scen,
                        bank_sf_details["q_provided_mvar"], bank_sf_details["tensao_disp_kv"],
                        bank_cf_details["q_provided_mvar"], bank_cf_details["tensao_disp_kv"],
                        data.tipo_transformador, V_sut_hv_tap_v_sel_iter
                    )
                    sut_eps_taps_info_list.append({
                        "sut_tap_kv": round(V_sut_hv_tap_v_sel_iter / 1000, 2),
                        "corrente_eps_sf_a": round(comp_curr_res["corrente_eps_sf_a"],2),
                        "percent_limite_sf": round(comp_curr_res["percent_limite_sf"],1),
                        "corrente_eps_cf_a": round(comp_curr_res["corrente_eps_cf_a"],2),
                        "percent_limite_cf": round(comp_curr_res["percent_limite_cf"],1),
                    })
                sut_eps_taps_info_list.sort(key=lambda x_sut: x_sut["sut_tap_kv"])
            scen_res_dict["sut_eps_analysis"] = sut_eps_taps_info_list
            current_tap_data["cenarios_do_tap"].append(scen_res_dict)
        all_taps_data.append(current_tap_data)

    overall_bank_sug = suggest_capacitor_bank_config_overall(max_overall_test_v_kv, max_overall_q_mvar_req, data.tipo_transformador)
    
    final_load_results = {
        "condicoes_nominais": condicoes_nominais_results,
        "cenarios_detalhados_por_tap": all_taps_data, # Corrected key name
        "sugestao_geral_banco": {
            **overall_bank_sug,
            "max_v_overall_kv": round(max_overall_test_v_kv,2),
            "max_q_overall_mvar_req": round(max_overall_q_mvar_req,3)
        }
    }
    return final_load_results