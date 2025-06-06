# utils/constants.py - No changes needed here, as it's a constants file
"""
Centraliza constantes numéricas e textuais usadas na aplicação,
especialmente valores de normas e parâmetros físicos/componentes.
"""
import numpy as np

# --- Constantes Físicas (Podem ficar em config.py também) ---
PI = 3.141592653589793  # Já em config.py
MU_0 = 4 * np.pi * 1e-7  # Já em config.py


# --- Constante para Comparações de Ponto Flutuante ---
EPSILON = 1e-6  # Tolerância para comparações de ponto flutuante


# --- Constantes Normativas e de Ensaio (IEC 60060-1:2010) ---

# Tempos Nominais (µs)
LIGHTNING_IMPULSE_FRONT_TIME_NOM = 1.2
LIGHTNING_IMPULSE_TAIL_TIME_NOM = 50.0
SWITCHING_IMPULSE_PEAK_TIME_NOM = 250.0
SWITCHING_IMPULSE_TAIL_TIME_NOM = 2500.0
CHOPPED_IMPULSE_CHOP_TIME_MIN = 2.0  # Tempo mínimo de corte
CHOPPED_IMPULSE_CHOP_TIME_MAX = 6.0  # Tempo máximo de corte


# Tolerâncias (%) - Expressas como fração decimal
LIGHTNING_FRONT_TOLERANCE = 0.30  # ±30% para T1
LIGHTNING_TAIL_TOLERANCE = 0.20  # ±20% para T2
LIGHTNING_PEAK_TOLERANCE = 0.03  # ±3% para Vp (Vt)
LIGHTNING_OVERSHOOT_MAX = 10.0  # ≤ 10% para Overshoot (β)


SWITCHING_PEAK_TOLERANCE = 0.03  # ±3% para Vp
SWITCHING_PEAK_TIME_TOLERANCE = 0.20  # ±20% para Tp
SWITCHING_TAIL_TOLERANCE = 0.60  # ±60% para T2 (ou Td conforme norma)
SWITCHING_TIME_ABOVE_90_MIN = 200.0  # Td ≥ 200 µs
SWITCHING_TIME_TO_ZERO_MIN = (1000.0  # Tz (tempo até primeiro zero após pico) - Verificar definição exata na norma
)


CHOPPED_FRONT_TOLERANCE = 0.30  # ±30% para T1 subjetivo
CHOPPED_PEAK_TOLERANCE = 0.05  # ±5% para Vc (tensão no instante do corte)
CHOPPED_UNDERSHOOT_MAX = 0.20  # ≤ 20% para Undershoot após colapso

# --- Parâmetros Físicos (Exemplo Gerador Haefely & Componentes) ---
# (Estes valores são exemplos e DEVEM ser ajustados para o equipamento real)
L_PER_STAGE_H = 5e-6  # Indutância por estágio (Henry)
C_PER_STAGE_F = 1.5e-6  # Capacitância por estágio (Farad)
C_DIVIDER_HIGH_VOLTAGE_F = 600e-12  # Divisor para Vmax >= 1200kV (Farad)
C_DIVIDER_LOW_VOLTAGE_F = 1200e-12  # Divisor para Vmax < 1200kV (Farad)
C_CHOPPING_GAP_F = 600e-12  # Capacitância parasita do gap de corte (Farad)
R_PARASITIC_OHM = 5.0  # Resistência parasita estimada do circuito (Ohm)

# --- Constantes para Análises Dielétricas ---
# Rigidez dielétrica de diferentes materiais em kV/mm
RIGIDEZ_OLEO_MINERAL = 12.5  # média entre 10-15 kV/mm
RIGIDEZ_PAPEL_IMPREGNADO = 50.0  # média entre 40-60 kV/mm
RIGIDEZ_AR_NIVEL_MAR = 3.0  # kV/mm
RIGIDEZ_SF6 = 7.5  # média entre 7-8 kV/mm
ALTITUDE_CONST = 8150  # metros

# --- Constantes para Tensão Induzida ---
INDICAO_LIMITE = 1.9 # T - Limite físico típico para indução no núcleo
INDUCACAO_LIMITE = 1.9 # T - Limite físico típico para indução no núcleo (Adicionado para resolver erro de Pylance)

# --- Constantes para Análises de Temperatura ---
SQRT_3 = 1.732050807568877
CALOR_ESPECIFICO_OLEO = 1.880  # kJ/(kg·K)
CALOR_ESPECIFICO_COBRE = 0.385  # kJ/(kg·K)
CALOR_ESPECIFICO_FERRO = 0.450  # kJ/(kg·K)
TEMP_AMBIENTE_REFERENCIA = 20  # °C


# --- Constantes Normativas e de Ensaio (IEC 60060-1:2010) ---

# Tempos Nominais (µs)
LIGHTNING_IMPULSE_FRONT_TIME_NOM = 1.2
LIGHTNING_IMPULSE_TAIL_TIME_NOM = 50.0
SWITCHING_IMPULSE_PEAK_TIME_NOM = 250.0
SWITCHING_IMPULSE_TAIL_TIME_NOM = 2500.0
CHOPPED_IMPULSE_CHOP_TIME_MIN = 2.0  # Tempo mínimo de corte
CHOPPED_IMPULSE_CHOP_TIME_MAX = 6.0  # Tempo máximo de corte


# Tolerâncias (%) - Expressas como fração decimal
LIGHTNING_FRONT_TOLERANCE = 0.30  # ±30% para T1
LIGHTNING_TAIL_TOLERANCE = 0.20  # ±20% para T2
LIGHTNING_PEAK_TOLERANCE = 0.03  # ±3% para Vp (Vt)
LIGHTNING_OVERSHOOT_MAX = 10.0  # ≤ 10% para Overshoot (β)


SWITCHING_PEAK_TOLERANCE = 0.03  # ±3% para Vp
SWITCHING_PEAK_TIME_TOLERANCE = 0.20  # ±20% para Tp
SWITCHING_TAIL_TOLERANCE = 0.60  # ±60% para T2 (ou Td conforme norma)
SWITCHING_TIME_ABOVE_90_MIN = 200.0  # Td ≥ 200 µs
SWITCHING_TIME_TO_ZERO_MIN = (1000.0  # Tz (tempo até primeiro zero após pico) - Verificar definição exata na norma
)


CHOPPED_FRONT_TOLERANCE = 0.30  # ±30% para T1 subjetivo
CHOPPED_PEAK_TOLERANCE = 0.05  # ±5% para Vc (tensão no instante do corte)
CHOPPED_UNDERSHOOT_MAX = 0.20  # ≤ 20% para Undershoot após colapso


# Tabelas BIL/SIL (valores baseados na documentação)
# Padrão NBR/IEC - Impulso Atmosférico (LI/NBI)
BIL_NBR_IEC = {
    1.2: [], # Não especificado na tabela para 1.2 kV
    3.6: [20, 40],
    7.2: [40, 60],
    12: [60, 75, 95],
    17.5: [95, 110],
    24: [95, 125, 145],
    36: [145, 170, 200],
    52: [250],
    72.5: [325, 350],
    145: [450, 550, 650],
    170: [550, 650, 750],
    245: [750, 850, 950, 1050],
    362: [950, 1050, 1175],
    420: [1050, 1175, 1300, 1425],
    525: [1300, 1425, 1550],
    800: [1800, 1950, 2100],
}

# Padrão IEEE - Impulso Atmosférico (BIL)
BIL_IEEE = {
    1.2: [30],
    5.0: [60],
    8.7: [75],
    15: [95, 110],
    25.8: [125, 150],
    34.5: [150, 200],
    46: [200, 250],
    69: [250, 350],
    161: [550, 650, 750],
    230: [650, 750, 825, 900],
    345: [900, 1050, 1175],
    500: [1300, 1425, 1550, 1675, 1800],
    765: [1800, 1925, 2050],
}

# Padrão NBR/IEC - Impulso de Manobra (SI/IM)
SIL_NBR_IEC = {
    245: [650, 750, 850],
    362: [850, 950],
    420: [850, 950, 1050, 1175],
    525: [1050, 1175],
    800: [1425, 1550],
}

# Padrão IEEE - Impulso de Manobra (BSL)
SIL_IEEE = {
    161: [460, 540, 620],
    230: [540, 620, 685, 745],
    345: [745, 870, 975],
    500: [1080, 1180, 1290, 1390, 1500],
    765: [1500, 1600, 1700],
}


# --- Parâmetros Físicos (Exemplo Gerador Haefely & Componentes) ---
# (Estes valores são exemplos e DEVEM ser ajustados para o equipamento real)
L_PER_STAGE_H = 5e-6  # Indutância por estágio (Henry)
C_PER_STAGE_F = 1.5e-6  # Capacitância por estágio (Farad)
C_DIVIDER_HIGH_VOLTAGE_F = 600e-12  # Divisor para Vmax >= 1200kV (Farad)
C_DIVIDER_LOW_VOLTAGE_F = 1200e-12  # Divisor para Vmax < 1200kV (Farad)
C_CHOPPING_GAP_F = 600e-12  # Capacitância parasita do gap de corte (Farad)
R_PARASITIC_OHM = 5.0  # Resistência parasita estimada do circuito (Ohm)

# --- Constantes para Análises Dielétricas ---
# Rigidez dielétrica de diferentes materiais em kV/mm
RIGIDEZ_OLEO_MINERAL = 12.5  # média entre 10-15 kV/mm
RIGIDEZ_PAPEL_IMPREGNADO = 50.0  # média entre 40-60 kV/mm
RIGIDEZ_AR_NIVEL_MAR = 3.0  # kV/mm
RIGIDEZ_SF6 = 7.5  # média entre 7-8 kV/mm
ALTITUDE_CONST = 8150  # metros

# --- Constantes para Tensão Induzida ---
INDICAO_LIMITE = 1.9 # T - Limite físico típico para indução no núcleo

# --- Constantes para Análises de Temperatura ---
SQRT_3 = 1.732050807568877
CALOR_ESPECIFICO_OLEO = 1.880  # kJ/(kg·K)
CALOR_ESPECIFICO_COBRE = 0.385  # kJ/(kg·K)
CALOR_ESPECIFICO_FERRO = 0.450  # kJ/(kg·K)
TEMP_AMBIENTE_REFERENCIA = 20  # °C


# --- Componentes Disponíveis (Para Dropdowns na UI) ---
RESISTORS_LI_FRONT_AVAILABLE = [
    {"value": 15, "label": "15 Ω"},
    {"value": 20, "label": "20 Ω"},
    {"value": 40, "label": "40 Ω"},
    {"value": 60, "label": "60 Ω"},
    {"value": 90, "label": "90 Ω"},
    {"value": 140, "label": "140 Ω"},
    {"value": 300, "label": "300 Ω"},

]
RESISTORS_LI_TAIL_AVAILABLE = [
    {"value": 100, "label": "100 Ω"},
    {"value": 220, "label": "220 Ω"},
    {"value": 300, "label": "300 Ω"},
    {"value": 600, "label": "600 Ω"},
    {"value": 3500, "label": "3.5 kΩ"},
    {"value": 5000, "label": "5.0 kΩ"},
]
RESISTORS_SI_FRONT_AVAILABLE = [
    {"value": 440, "label": "440 Ω"},
    {"value": 900, "label": "900 Ω"},
    {"value": 1000, "label": "1.0 kΩ"},
    {"value": 3000, "label": "3.0 kΩ"},
    {"value": 6000, "label": "6.0 kΩ"},
]
RESISTORS_SI_TAIL_AVAILABLE = [
    {"value": 1600, "label": "1.6 kΩ"},
    {"value": 2200, "label": "2.2 kΩ"},
    {"value": 3600, "label": "3.6 kΩ"},
    {"value": 4500, "label": "4.5 kΩ"},
    {"value": 5000, "label": "5.0 kΩ"},
]
INDUCTORS_OPTIONS = [
    {"value": 0, "label": "Nenhum"},
    {"value": 100e-6, "label": "100 µH"},
    {"value": 200e-6, "label": "200 µH"},
    {"value": 300e-6, "label": "300 µH"},
    {"value": 400e-6, "label": "400 µH"},
]
SHUNT_OPTIONS = [
    {"value": 0.01, "label": "0.01 Ω"},
    {"value": 0.02, "label": "0.02 Ω"},
    {"value": 0.1, "label": "0.1 Ω"},
    {"value": 0.5, "label": "0.5 Ω"},
    {"value": 1.0, "label": "1.0 Ω"},
]
STRAY_CAPACITANCE_OPTIONS_PF = [  # Valores em pF
    {"value": 0, "label": "Nenhuma"},
    {"value": 200, "label": "200 pF"},
    {"value": 400, "label": "400 pF (padrão)"},
    {"value": 600, "label": "600 pF"},
    {"value": 800, "label": "800 pF"},
]

# --- Configurações do Gerador (Exemplo Haefely SGWN 360kJ) ---
GENERATOR_CONFIGURATIONS = [
    # Lista completa movida de impulse.py...
    {
        "value": "1S-1P",
        "label": "1S-1P (200kV / 1.50µF / 30kJ)",
        "stages": 1,
        "parallel": 1,
        "max_voltage_kv": 200,
        "energy_kj": 30,
    },
    {
        "value": "2S-1P",
        "label": "2S-1P (400kV / 0.75µF / 60kJ)",
        "stages": 2,
        "parallel": 1,
        "max_voltage_kv": 400,
        "energy_kj": 60,
    },
    {
        "value": "3S-1P",
        "label": "3S-1P (600kV / 0.50µF / 90kJ)",
        "stages": 3,
        "parallel": 1,
        "max_voltage_kv": 600,
        "energy_kj": 90,
    },
    {
        "value": "4S-1P",
        "label": "4S-1P (800kV / 0.375µF / 120kJ)",
        "stages": 4,
        "parallel": 1,
        "max_voltage_kv": 800,
        "energy_kj": 120,
    },
    {
        "value": "5S-1P",
        "label": "5S-1P (1000kV / 0.30µF / 150kJ)",
        "stages": 5,
        "parallel": 1,
        "max_voltage_kv": 1000,
        "energy_kj": 150,
    },
    {
        "value": "6S-1P",
        "label": "6S-1P (1200kV / 0.25µF / 180kJ)",
        "stages": 6,
        "parallel": 1,
        "max_voltage_kv": 1200,
        "energy_kj": 180,
    },
    {
        "value": "7S-1P",
        "label": "7S-1P (1400kV / 0.214µF / 210kJ)",
        "stages": 7,
        "parallel": 1,
        "max_voltage_kv": 1400,
        "energy_kj": 210,
    },
    {
        "value": "8S-1P",
        "label": "8S-1P (1600kV / 0.188µF / 240kJ)",
        "stages": 8,
        "parallel": 1,
        "max_voltage_kv": 1600,
        "energy_kj": 240,
    },
    {
        "value": "9S-1P",
        "label": "9S-1P (1800kV / 0.167µF / 270kJ)",
        "stages": 9,
        "parallel": 1,
        "max_voltage_kv": 1800,
        "energy_kj": 270,
    },
    {
        "value": "10S-1P",
        "label": "10S-1P (2000kV / 0.15µF / 300kJ)",
        "stages": 10,
        "parallel": 1,
        "max_voltage_kv": 2000,
        "energy_kj": 300,
    },
    {
        "value": "11S-1P",
        "label": "11S-1P (2200kV / 0.136µF / 330kJ)",
        "stages": 11,
        "parallel": 1,
        "max_voltage_kv": 2200,
        "energy_kj": 330,
    },
    {
        "value": "12S-1P",
        "label": "12S-1P (2400kV / 0.125µF / 360kJ)",
        "stages": 12,
        "parallel": 1,
        "max_voltage_kv": 2400,
        "energy_kj": 360,
    },
    {
        "value": "1S-2P",
        "label": "1S-2P (200kV / 3.00µF / 60kJ)",
        "stages": 1,
        "parallel": 2,
        "max_voltage_kv": 200,
        "energy_kj": 60,
    },
    {
        "value": "1S-3P",
        "label": "1S-3P (200kV / 4.50µF / 90kJ)",
        "stages": 1,
        "parallel": 3,
        "max_voltage_kv": 200,
        "energy_kj": 90,
    },
    {
        "value": "1S-4P",
        "label": "1S-4P (200kV / 6.00µF / 120kJ)",
        "stages": 1,
        "parallel": 4,
        "max_voltage_kv": 200,
        "energy_kj": 120,
    },
    {
        "value": "1S-12P",
        "label": "1S-12P (200kV / 18.00µF / 360kJ)",
        "stages": 1,
        "parallel": 12,
        "max_voltage_kv": 200,
        "energy_kj": 360,
    },
    {
        "value": "2S-2P",
        "label": "2S-2P (400kV / 1.50µF / 120kJ)",
        "stages": 2,
        "parallel": 2,
        "max_voltage_kv": 400,
        "energy_kj": 120,
    },
    {
        "value": "2S-6P",
        "label": "2S-6P (400kV / 4.50µF / 360kJ)",
        "stages": 2,
        "parallel": 6,
        "max_voltage_kv": 400,
        "energy_kj": 360,
    },
    {
        "value": "3S-2P",
        "label": "3S-2P (600kV / 1.00µF / 180kJ)",
        "stages": 3,
        "parallel": 2,
        "max_voltage_kv": 600,
        "energy_kj": 180,
    },
    {
        "value": "3S-4P",
        "label": "3S-4P (600kV / 2.00µF / 360kJ)",
        "stages": 3,
        "parallel": 4,
        "max_voltage_kv": 600,
        "energy_kj": 360,
    },
    {
        "value": "4S-2P",
        "label": "4S-2P (800kV / 0.75µF / 240kJ)",
        "stages": 4,
        "parallel": 2,
        "max_voltage_kv": 800,
        "energy_kj": 240,
    },
    {
        "value": "4S-3P",
        "label": "4S-3P (800kV / 1.125µF / 360kJ)",
        "stages": 4,
        "parallel": 3,
        "max_voltage_kv": 800,
        "energy_kj": 360,
    },
    {
        "value": "6S-2P",
        "label": "6S-2P (1200kV / 0.50µF / 360kJ)",
        "stages": 6,
        "parallel": 2,
        "max_voltage_kv": 1200,
        "energy_kj": 360,
    },
]

# --- Dados de Referência para Sugestão de Resistores (Base Haefely) ---
# Formato: (c_load_total_nF, rf_eff_total_ohm)
RF_REFERENCE_DATA_LI = [(0.5, 500), (1, 350), (2, 220), (4, 140), (8, 90), (16, 60), (32, 40)]
RF_REFERENCE_DATA_SI = [
    (0.5, 5000),
    (1, 3500),
    (2, 2200),
    (4, 1400),
    (8, 900),
    (16, 600),
    (32, 400),
]

# --- Valores Padrão de Rt por Coluna (Ohm) ---
RT_DEFAULT_PER_COLUMN = {"lightning": 100, "switching": 2500, "chopped": 120}


# --- Constantes para Cálculo de Elevação de Temperatura ---
TEMP_RISE_CONSTANT = {"cobre": 234.5, "aluminio": 225.0}


# Default values for temperature rise calculations
DEFAULT_AMBIENT_TEMP = 25.0  # °C
DEFAULT_DELTA_THETA_OIL_MAX = 55.0  # °C - Classe A
DEFAULT_WINDING_MATERIAL = "cobre"
DEFAULT_WINDING_RES_COLD = 0.5  # Ω
DEFAULT_WINDING_TEMP_COLD = 20.0  # °C
DEFAULT_WINDING_RES_HOT = 0.6  # Ω
DEFAULT_WINDING_TEMP_TOP_OIL = 75.0  # °C


# --- Tabelas para Tensão Induzida ---
# Tabela de potência magnética (indução, frequência) -> potência
potencia_magnet_data = {
    (0.5, 50): 0.10, (0.5, 60): 0.15, (0.5, 100): 0.35, (0.5, 120): 0.45, (0.5, 150): 0.70, (0.5, 200): 1.00, (0.5, 240): 1.30,
    (0.6, 50): 0.15, (0.6, 60): 0.20, (0.6, 100): 0.45, (0.6, 120): 0.60, (0.6, 150): 0.90, (0.6, 200): 1.40, (0.6, 240): 1.80,
    (0.7, 50): 0.23, (0.7, 60): 0.28, (0.7, 100): 0.60, (0.7, 120): 0.80, (0.7, 150): 1.10, (0.7, 200): 1.70, (0.7, 240): 2.30,
    (0.8, 50): 0.30, (0.8, 60): 0.35, (0.8, 100): 0.80, (0.8, 120): 1.00, (0.8, 150): 1.40, (0.8, 200): 2.20, (0.8, 240): 3.00,
    (0.9, 50): 0.38, (0.9, 60): 0.45, (0.9, 100): 0.95, (0.9, 120): 1.30, (0.9, 150): 1.70, (0.9, 200): 2.80, (0.9, 240): 3.80,
    (1.0, 50): 0.45, (1.0, 60): 0.55, (1.0, 100): 1.10, (1.0, 120): 1.60, (1.0, 150): 2.20, (1.0, 200): 3.50, (1.0, 240): 4.50,
    (1.1, 50): 0.55, (1.1, 60): 0.70, (1.1, 100): 1.50, (1.1, 120): 2.00, (1.1, 150): 2.80, (1.1, 200): 4.10, (1.1, 240): 5.50,
    (1.2, 50): 0.65, (1.2, 60): 0.85, (1.2, 100): 2.00, (1.2, 120): 2.40, (1.2, 150): 3.30, (1.2, 200): 5.00, (1.2, 240): 6.50,
    (1.3, 50): 0.80, (1.3, 60): 1.00, (1.3, 100): 2.20, (1.3, 120): 2.85, (1.3, 150): 3.80, (1.3, 200): 6.00, (1.3, 240): 7.50,
    (1.4, 50): 0.95, (1.4, 60): 1.20, (1.4, 100): 2.50, (1.4, 120): 3.30, (1.4, 150): 4.50, (1.4, 200): 7.00, (1.4, 240): 9.00,
    (1.5, 50): 1.10, (1.5, 60): 1.40, (1.5, 100): 3.00, (1.5, 120): 4.00, (1.5, 150): 5.50, (1.5, 200): 9.00, (1.5, 240): 11.00,
    (1.6, 50): 1.30, (1.6, 60): 1.60, (1.6, 100): 3.50, (1.6, 120): 4.80, (1.6, 150): 6.50, (1.6, 200): 12.00, (1.6, 240): 14.00,
    (1.7, 50): 1.20, (1.7, 60): 1.55, (1.7, 100): 3.50, (1.7, 120): 4.40, (1.7, 150): 6.00, (1.7, 200): 9.00, (1.7, 240): 15.00,
}

# Tabela de perdas do núcleo (indução, frequência) -> perdas
perdas_nucleo_data = {
    (0.5, 50): 0.10, (0.5, 60): 0.13, (0.5, 100): 0.25, (0.5, 120): 0.35, (0.5, 150): 0.50, (0.5, 200): 0.80, (0.5, 240): 1.10,
    (0.6, 50): 0.12, (0.6, 60): 0.18, (0.6, 100): 0.38, (0.6, 120): 0.48, (0.6, 150): 0.70, (0.6, 200): 1.10, (0.6, 240): 1.50,
    (0.7, 50): 0.15, (0.7, 60): 0.23, (0.7, 100): 0.50, (0.7, 120): 0.62, (0.7, 150): 0.95, (0.7, 200): 1.55, (0.7, 240): 2.10,
    (0.8, 50): 0.20, (0.8, 60): 0.30, (0.8, 100): 0.65, (0.8, 120): 0.80, (0.8, 150): 1.20, (0.8, 200): 2.00, (0.8, 240): 2.80,
    (0.9, 50): 0.25, (0.9, 60): 0.37, (0.9, 100): 0.82, (0.9, 120): 1.00, (0.9, 150): 1.50, (0.9, 200): 2.50, (0.9, 240): 3.50,
    (1.0, 50): 0.32, (1.0, 60): 0.46, (1.0, 100): 1.00, (1.0, 120): 1.25, (1.0, 150): 1.85, (1.0, 200): 3.10, (1.0, 240): 4.20,
    (1.1, 50): 0.41, (1.1, 60): 0.55, (1.1, 100): 1.21, (1.1, 120): 1.55, (1.1, 150): 2.20, (1.1, 200): 3.70, (1.1, 240): 5.00,
    (1.2, 50): 0.50, (1.2, 60): 0.65, (1.2, 100): 1.41, (1.2, 120): 1.90, (1.2, 150): 2.70, (1.2, 200): 4.50, (1.2, 240): 6.00,
    (1.3, 50): 0.60, (1.3, 60): 0.80, (1.3, 100): 1.65, (1.3, 120): 2.30, (1.3, 150): 3.20, (1.3, 200): 5.20, (1.3, 240): 7.00,
    (1.4, 50): 0.71, (1.4, 60): 0.95, (1.4, 100): 1.95, (1.4, 120): 2.80, (1.4, 150): 3.80, (1.4, 200): 6.00, (1.4, 240): 8.50,
    (1.5, 50): 0.85, (1.5, 60): 1.10, (1.5, 100): 2.30, (1.5, 120): 3.30, (1.5, 150): 4.50, (1.5, 200): 7.00, (1.5, 240): 10.00,
    (1.6, 50): 1.00, (1.6, 60): 1.30, (1.6, 100): 2.80, (1.6, 120): 3.80, (1.6, 150): 5.30, (1.6, 200): 8.00, (1.6, 240): 12.00,
    (1.7, 50): 1.20, (1.7, 60): 1.55, (1.7, 100): 3.50, (1.7, 120): 4.40, (1.7, 150): 6.00, (1.7, 200): 9.00, (1.7, 240): 15.00,
}

# --- Constantes para Análise Dielétrica ---
# Valores padrão de BIL baseados na classe de tensão (Um)
DEFAULT_BIL_VALUES = {
    24: 125, 36: 170, 72.5: 325, 145: 650, 245: 1050, 420: 1425, 550: 1550
}

# Fatores de correção para aço H110-27 (Seção 3.3.1 da documentação de perdas)
FATOR_CONSTRUCAO_PERDAS_H110_27 = 1.15
FATOR_CONSTRUCAO_POTENCIA_MAG_H110_27 = 1.2

# Fatores de excitação default (Seção 3.3.2 da documentação de perdas)
FATOR_EXCITACAO_DEFAULT_TRIFASICO = 3
FATOR_EXCITACAO_DEFAULT_MONOFASICO = 5

# Parâmetros do SUT (Step-Up Transformer) - Seção 2.2 da documentação de perdas
SUT_BT_VOLTAGE = 480 # V


# Valores padrão de tensão aplicada (ACSD) baseados na classe de tensão
DEFAULT_ACSD_VALUES = {
    1.1: 3, 3.6: 10, 7.2: 20, 12: 28, 24: 50, 36: 70, 52: 95, 72.5: 140,
    100: 185, 123: 230, 145: 275, 170: 325, 245: 460, 300: 570, 362: 680,
    420: 800, 550: 970
}

# Fatores de cálculo para isolamento
NEUTRO_NBI_FACTOR = 0.6  # NBI do neutro = 60% do NBI principal
SIL_NBI_FACTOR = 0.75    # SIL = 75% do NBI
IAC_NBI_FACTOR = 1.1     # IAC = 110% do NBI
TENSAO_INDUZIDA_FACTOR = 2.0  # Tensão induzida = 2x tensão nominal

# Limites para aplicação de SIL e PD
# SIL aplicável para IEEE >= 161 kV e IEC/NBR >= 245 kV
SIL_MIN_VOLTAGE_IEEE = 161.0    # SIL só aplicável para IEEE Um >= 161 kV
SIL_MIN_VOLTAGE_IEC = 245.0     # SIL só aplicável para IEC/NBR Um >= 245 kV
PD_MIN_VOLTAGE = 72.5           # PD requerido para Um >= 72.5 kV

# --- Limites de Variação de Impedância (NBR 5356-5:2007 Tabela 2) ---
# (Chaves devem corresponder aos values do Dropdown 'power-category')
IMPENDANCE_VARIATION_LIMITS = {
    "I": 10.0,  # Categoria I (≤ 2.5 MVA)
    "II": 7.5,  # Categoria II (> 2.5 a 100 MVA)
    "III": 2.0,  # Categoria III (> 100 MVA)
    # Nota: A norma pode ter limites diferentes para enrolamentos com Zcc muito baixo (<3%).
}

# --- Mapeamentos e Outras Constantes Globais ---
MATERIAL_OPTIONS = [
    {"label": "Cobre", "value": "cobre"},
    {"label": "Alumínio", "value": "aluminio"},
    {"label": "Não Aplicável", "value": "na"},
]

POWER_CATEGORY_OPTIONS = [
    {"label": "I (≤ 2.5 MVA)", "value": "I"},
    {"label": "II (> 2.5 a 100 MVA)", "value": "II"},
    {"label": "III (> 100 MVA)", "value": "III"},
]

CONNECTION_OPTIONS = [
    {"label": "Y (Estrela)", "value": "Y"},
    {"label": "YN (Estrela com Neutro)", "value": "YN"},
    {"label": "D (Triângulo/Delta)", "value": "D"},
    {"label": "Z (Zigue-Zague)", "value": "Z"},
    {"label": "ZN (Zigue-Zague com Neutro)", "value": "ZN"},
]

ISOLATION_TYPE_OPTIONS = [
    {"label": "Uniforme", "value": "uniforme"},
    {"label": "Progressivo", "value": "progressivo"},
    {"label": "Não Aplicável", "value": "na"},
]

TRANSFORMER_TYPE_OPTIONS = [
    {"label": "Monofásico", "value": "monofasico"},
    {"label": "Trifásico", "value": "trifasico"},
    {"label": "Trifásico com Terciário", "value": "trifasico_terciario"},
    {"label": "Trifásico com Terciário e Neutro", "value": "trifasico_terciario_neutro"},
    {"label": "Trifásico com Neutro", "value": "trifasico_neutro"},
    {"label": "Trifásico com Neutro e Terciário", "value": "trifasico_neutro_terciario"},
    {"label": "Trifásico com Terciário e Neutro (Zigue-Zague)", "value": "trifasico_terciario_neutro_zigzag"},
    {"label": "Trifásico com Neutro (Zigue-Zigue)", "value": "trifasico_neutro_zigzag"},
    {"label": "Trifásico com Terciário (Zigue-Zague)", "value": "trifasico_terciario_zigzag"},
    {"label": "Trifásico (Zigue-Zague)", "value": "trifasico_zigzag"},
    {"label": "Monofásico (Zigue-Zague)", "value": "monofasico_zigzag"},
    {"label": "Não Aplicável", "value": "na"},




]

# Limites do Sistema Ressonante (Tensão Aplicada)
# Estrutura: { nome: { tensao_max (kV), cap_min (nF), cap_max (nF), corrente (A), potencia (kVA) } }
RESONANT_SYSTEM_CONFIGS = {
    # Configurações do Sistema Ressonante High Volt WRM 1800/1350-900-450
    "Módulos 1+2+3 (Série)": {
        "tensao_max": 1350,
        "cap_min": 0.22,
        "cap_max": 2.6,
        "corrente": 1.33,
        "potencia": 1800,
    },
    "Módulos 1+2 (Série)": {
        "tensao_max": 900,
        "cap_min": 0.3,
        "cap_max": 6.5,
        "corrente": 1.33,
        "potencia": 1200,
    },
    "Módulo 1 (1 em Par.)": {
        "tensao_max": 450,
        "cap_min": 0.7,
        "cap_max": 13.1,
        "corrente": 1.33,
        "potencia": 600,
    },
    "Módulos 1||2||3 (3 Par.) 450kV": {
        "tensao_max": 450,
        "cap_max": 23.6,
        "corrente": 4.0,
        "potencia": 1800,
    },
    "Módulos 1||2||3 (3 Par.) 27": {
        "tensao_max": 270,
        "cap_min": 23.7,
        "cap_max": 39.3,
        "corrente": 4.0,
        "potencia": 1800,
    },
}

# Limites da Fonte de Perdas em Carga (EPS)
EPS_VOLTAGE_LIMIT_KV = 95.6
EPS_CURRENT_LIMIT_A = 2000
EPS_REACTIVE_POWER_LIMIT_MVAR_LOW = 46.8  # Limite inferior para aumento do banco
EPS_REACTIVE_POWER_LIMIT_MVAR_HIGH = 93.6  # Limite superior (impossibilita ensaio)
EPS_ACTIVE_POWER_LIMIT_KW = 1300

# Tolerâncias ABNT NBR 5356-1 (Perdas e Impedância) - Exemplo
LOSSES_TOLERANCE_TOTAL = 0.10  # +10% para perdas totais (Vazio + Carga)
LOSSES_TOLERANCE_INDIVIDUAL = (
    0.15  # +15% para perdas em vazio OU carga (se garantidas separadamente)
)
IMPEDANCE_TOLERANCE = 0.075  # ±7.5% para trafos com 2 enrolamentos
# Nota: A tolerância de impedância pode ser ±10% para 3 enrolamentos ou autotrafos. Ajustar conforme necessário.
# Tensões Nominais do Banco de Capacitores EPS (kV)
EPS_CAP_BANK_VOLTAGES_KV = [13.8, 23.9, 27.6, 41.4, 47.8, 55.2, 71.7, 95.6]
DEFAULT_FREQUENCY = 60

# Configuração do Banco de Capacitores
Q_SWITCH_POWERS = {"generic_cp": [0.1, 0.2, 0.8, 1.2, 1.6]}

# Capacitores disponíveis por tensão
CAPACITORS_BY_VOLTAGE = {
    "13.8": ["CP2A1", "CP2A2", "CP2B1", "CP2B2", "CP2C1", "CP2C2"],
    "23.9": ["CP2A1", "CP2A2", "CP2B1", "CP2B2", "CP2C1", "CP2C2"],
    "27.6": [
        "CP1A1",
        "CP1A2",
        "CP1B1",
        "CP1B2",
        "CP1C1",
        "CP1C2",
        "CP2A1",
        "CP2A2",
        "CP2B1",
        "CP2B2",
        "CP2C1",
        "CP2C2",
        "CP3A1",
        "CP3A2",
        "CP3B1",
        "CP3B2",
        "CP3C1",
        "CP3C2",
        "CP4A1",
        "CP4A2",
        "CP4B1",
        "CP4B2",
        "CP4C1",
        "CP4C2",
    ],
    "41.4": [
        "CP2A1",
        "CP2A2",
        "CP2B1",
        "CP2B2",
        "CP2C1",
        "CP2C2",
        "CP3A1",
        "CP3A2",
        "CP3B1",
        "CP3B2",
        "CP3C1",
        "CP3C2",
        "CP4A1",
        "CP4A2",
        "CP4B1",
        "CP4B2",
        "CP4C1",
        "CP4C2",
    ],
    "47.8": [
        "CP1A1",
        "CP1A2",
        "CP1B1",
        "CP1B2",
        "CP1C1",
        "CP1C2",
        "CP2A1",
        "CP2A2",
        "CP2B1",
        "CP2B2",
        "CP2C1",
        "CP2C2",
        "CP3A1",
        "CP3A2",
        "CP3B1",
        "CP3B2",
        "CP3C1",
        "CP3C2",
        "CP4A1",
        "CP4A2",
        "CP4B1",
        "CP4B2",
        "CP4C1",
        "CP4C2",
    ],
    "55.2": [
        "CP1A1",
        "CP1A2",
        "CP1B1",
        "CP1B2",
        "CP1C1",
        "CP1C2",
        "CP2A1",
        "CP2A2",
        "CP2B1",
        "CP2B2",
        "CP2C1",
        "CP2C2",
        "CP3A1",
        "CP3A2",
        "CP3B1",
        "CP3B2",
        "CP3C1",
        "CP3C2",
        "CP4A1",
        "CP4A2",
        "CP4B1",
        "CP4B2",
        "CP4C1",
        "CP4C2",
    ],
    "71.7": [
        "CP2A1",
        "CP2A2",
        "CP2B1",
        "CP2B2",
        "CP2C1",
        "CP2C2",
        "CP3A1",
        "CP3A2",
        "CP3B1",
        "CP3B2",
        "CP3C1",
        "CP3C2",
        "CP4A1",
        "CP4A2",
        "CP4B1",
        "CP4B2",
        "CP4C1",
        "CP4C2",
    ],
    "95.6": [
        "CP1A1",
        "CP1A2",
        "CP1B1",
        "CP1B2",
        "CP1C1",
        "CP1C2",
        "CP2A1",
        "CP2A2",
        "CP2B1",
        "CP2B2",
        "CP2C1",
        "CP2C2",
        "CP3A1",
        "CP3A2",
        "CP3B1",
        "CP3B2",
        "CP3C1",
        "CP3C2",
        "CP4A1",
        "CP4A2",
        "CP4B1",
        "CP4B2",
        "CP4C1",
        "CP4C2",
    ],
}

# Chaves CS por tensão para transformadores trifásicos
CS_SWITCHES_BY_VOLTAGE_TRI = {
    "13.8": [
        "CSA",
        "CSB",
        "CSC",
        "CS1A1",
        "CS1A2",
        "CS2A1",
        "CS2A2",
        "CS1B1",
        "CS1B2",
        "CS2B1",
        "CS2B2",
        "CS1C1",
        "CS1C2",
        "CS2C1",
        "CS2C2",
        "CS7A",
        "CS7B",
        "CS7C",
    ],
    "23.9": [
        "CSA",
        "CSB",
        "CSC",
        "CS1A1",
        "CS1A2",
        "CS2A1",
        "CS2A2",
        "CS1B1",
        "CS1B2",
        "CS2B1",
        "CS2B2",
        "CS1C1",
        "CS1C2",
        "CS2C1",
        "CS2C2",
        "CS6A",
        "CS6B",
    ],
    "27.6": [
        "CSA",
        "CSB",
        "CSC",
        "CS2A1",
        "CS2A2",
        "CS2B1",
        "CS2B2",
        "CS2C1",
        "CS2C2",
        "CS3A1",
        "CS3A2",
        "CS3B1",
        "CS3B2",
        "CS3C1",
        "CS3C2",
        "CS7A",
        "CS7B",
        "CS7C",
    ],
    "41.4": [
        "CSA",
        "CSB",
        "CSC",
        "CS1A1",
        "CS1A2",
        "CS4A1",
        "CS4A2",
        "CS1B1",
        "CS1B2",
        "CS4B1",
        "CS4B2",
        "CS1C1",
        "CS1C2",
        "CS4C1",
        "CS4C2",
        "CS7A",
        "CS7B",
        "CS7C",
    ],
    "47.8": [
        "CSA",
        "CSB",
        "CSC",
        "CS2A1",
        "CS2A2",
        "CS2B1",
        "CS2B2",
        "CS2C1",
        "CS2C2",
        "CS3A1",
        "CS3A2",
        "CS3B1",
        "CS3B2",
        "CS3C1",
        "CS3C2",
        "CS6A",
        "CS6B",
    ],
    "55.2": [
        "CSA",
        "CSB",
        "CSC",
        "CS4A1",
        "CS4A2",
        "CS4B1",
        "CS4B2",
        "CS4C1",
        "CS4C2",
        "CS7A",
        "CS7B",
        "CS7C",
    ],
    "71.7": [
        "CSA",
        "CSB",
        "CSC",
        "CS1A1",
        "CS1A2",
        "CS4A1",
        "CS4A2",
        "CS1B1",
        "CS1B2",
        "CS4B1",
        "CS4B2",
        "CS1C1",
        "CS1C2",
        "CS4C1",
        "CS4C2",
        "CS6A",
        "CS6B",
    ],
    "95.6": [
        "CSA",
        "CSB",
        "CSC",
        "CS4A1",
        "CS4A2",
        "CS4B1",
        "CS4B2",
        "CS4C1",
        "CS4C2",
        "CS6A",
        "CS6B",
    ],
}

# Chaves CS por tensão para transformadores monofásicos
CS_SWITCHES_BY_VOLTAGE_MONO = {
    "13.8": [
        "CSA",
        "CSB",
        "CSC",
        "CS1A1",
        "CS1A2",
        "CS2A1",
        "CS2A2",
        "CS1B1",
        "CS1B2",
        "CS2B1",
        "CS2B2",
        "CS1C1",
        "CS1C2",
        "CS2C1",
        "CS2C2",
        "CS6A",
        "CS6B",
        "CS6C",
    ],
    "27.6": [
        "CSA",
        "CSB",
        "CSC",
        "CS2A1",
        "CS2A2",
        "CS2B1",
        "CS2B2",
        "CS2C1",
        "CS2C2",
        "CS3A1",
        "CS3A2",
        "CS3B1",
        "CS3B2",
        "CS3C1",
        "CS3C2",
        "CS6A",
        "CS6B",
        "CS6C",
    ],
    "41.4": [
        "CSA",
        "CSB",
        "CSC",
        "CS1A1",
        "CS1A2",
        "CS4A1",
        "CS4A2",
        "CS1B1",
        "CS1B2",
        "CS4B1",
        "CS4B2",
        "CS1C1",
        "CS1C2",
        "CS4C1",
        "CS4C2",
        "CS6A",
        "CS6B",
        "CS6C",
    ],
    "55.2": [
        "CSA",
        "CSB",
        "CSC",
        "CS4A1",
        "CS4A2",
        "CS4B1",
        "CS4B2",
        "CS4C1",
        "CS4C2",
        "CS6A",
        "CS6B",
        "CS6C",
    ],
}

# Constantes para testes SUT/EPS
SUT_BT_VOLTAGE = 480.0 #V
SUT_BT_POWER = 4000.0 #kVA
SUT_AT_POWER = 15000.0 #kVA
SUT_AT_MIN_VOLTAGE = 14000.0 #V
SUT_AT_MAX_VOLTAGE = 140000.0 #V
SUT_AT_STEP_VOLTAGE = 3000.0
EPS_APARENTE_POWER = 1500.0 #kVA
EPS_CURRENT_LIMIT = 1984.0 #A
DUT_POWER_LIMIT = 1350.0 #kw

potencia_magnet_data = {
    (0.5, 50): 0.10,
    (0.5, 60): 0.15,
    (0.5, 100): 0.35,
    (0.5, 120): 0.45,
    (0.5, 150): 0.70,
    (0.5, 200): 1.00,
    (0.5, 240): 1.30,
    (0.5, 250): 1.40,
    (0.5, 300): 1.70,
    (0.5, 350): 2.10,
    (0.5, 400): 3.00,
    (0.5, 500): 4.00,
    (0.6, 50): 0.15,
    (0.6, 60): 0.20,
    (0.6, 100): 0.45,
    (0.6, 120): 0.60,
    (0.6, 150): 0.90,
    (0.6, 200): 1.40,
    (0.6, 240): 1.80,
    (0.6, 250): 1.90,
    (0.6, 300): 2.50,
    (0.6, 350): 3.30,
    (0.6, 400): 4.00,
    (0.6, 500): 5.50,
    (0.7, 50): 0.23,
    (0.7, 60): 0.28,
    (0.7, 100): 0.60,
    (0.7, 120): 0.80,
    (0.7, 150): 1.10,
    (0.7, 200): 1.70,
    (0.7, 240): 2.30,
    (0.7, 250): 2.50,
    (0.7, 300): 3.40,
    (0.7, 350): 4.20,
    (0.7, 400): 5.20,
    (0.7, 500): 7.50,
    (0.8, 50): 0.30,
    (0.8, 60): 0.35,
    (0.8, 100): 0.80,
    (0.8, 120): 1.00,
    (0.8, 150): 1.40,
    (0.8, 200): 2.20,
    (0.8, 240): 3.00,
    (0.8, 250): 3.30,
    (0.8, 300): 4.50,
    (0.8, 350): 5.50,
    (0.8, 400): 7.00,
    (0.8, 500): 9.50,
    (0.9, 50): 0.38,
    (0.9, 60): 0.45,
    (0.9, 100): 0.95,
    (0.9, 120): 1.30,
    (0.9, 150): 1.70,
    (0.9, 200): 2.80,
    (0.9, 240): 3.80,
    (0.9, 250): 4.00,
    (0.9, 300): 5.60,
    (0.9, 350): 7.00,
    (0.9, 400): 8.80,
    (0.9, 500): 12.00,
    (1.0, 50): 0.45,
    (1.0, 60): 0.55,
    (1.0, 100): 1.10,
    (1.0, 120): 1.60,
    (1.0, 150): 2.20,
    (1.0, 200): 3.50,
    (1.0, 240): 4.50,
    (1.0, 250): 4.80,
    (1.0, 300): 6.90,
    (1.0, 350): 8.50,
    (1.0, 400): 11.00,
    (1.0, 500): 15.00,
    (1.1, 50): 0.55,
    (1.1, 60): 0.70,
    (1.1, 100): 1.50,
    (1.1, 120): 2.00,
    (1.1, 150): 2.80,
    (1.1, 200): 4.10,
    (1.1, 240): 5.50,
    (1.1, 250): 5.80,
    (1.1, 300): 8.10,
    (1.1, 350): 10.00,
    (1.1, 400): 13.00,
    (1.1, 500): 18.00,
    (1.2, 50): 0.65,
    (1.2, 60): 0.85,
    (1.2, 100): 2.00,
    (1.2, 120): 2.40,
    (1.2, 150): 3.30,
    (1.2, 200): 5.00,
    (1.2, 240): 6.50,
    (1.2, 250): 7.00,
    (1.2, 300): 9.50,
    (1.2, 350): 12.00,
    (1.2, 400): 15.00,
    (1.2, 500): 22.00,
    (1.3, 50): 0.80,
    (1.3, 60): 1.00,
    (1.3, 100): 2.20,
    (1.3, 120): 2.85,
    (1.3, 150): 3.80,
    (1.3, 200): 6.00,
    (1.3, 240): 7.50,
    (1.3, 250): 8.00,
    (1.3, 300): 11.20,
    (1.3, 350): 13.50,
    (1.3, 400): 17.00,
    (1.3, 500): 26.00,
    (1.4, 50): 0.95,
    (1.4, 60): 1.20,
    (1.4, 100): 2.50,
    (1.4, 120): 3.30,
    (1.4, 150): 4.50,
    (1.4, 200): 7.00,
    (1.4, 240): 9.00,
    (1.4, 250): 9.90,
    (1.4, 300): 13.50,
    (1.4, 350): 16.00,
    (1.4, 400): 20.00,
    (1.4, 500): 30.00,
    (1.5, 50): 1.10,
    (1.5, 60): 1.40,
    (1.5, 100): 3.00,
    (1.5, 120): 4.00,
    (1.5, 150): 5.50,
    (1.5, 200): 9.00,
    (1.5, 240): 11.00,
    (1.5, 250): 12.00,
    (1.5, 300): 15.50,
    (1.5, 350): 18.00,
    (1.5, 400): 24.00,
    (1.5, 500): 37.00,
    (1.6, 50): 1.30,
    (1.6, 60): 1.60,
    (1.6, 100): 3.50,
    (1.6, 120): 4.80,
    (1.6, 150): 6.50,
    (1.6, 200): 12.00,
    (1.6, 240): 14.00,
    (1.6, 250): 15.00,
    (1.6, 300): 18.00,
    (1.6, 350): 22.00,
    (1.6, 400): 30.00,
    (1.6, 500): 45.00,
    (1.7, 50): 1.60,
    (1.7, 60): 2.00,
    (1.7, 100): 4.00,
    (1.7, 120): 5.50,
    (1.7, 150): 7.00,
    (1.7, 200): 15.00,
    (1.7, 240): 17.00,
    (1.7, 250): 18.00,
    (1.7, 300): 22.00,
    (1.7, 350): 28.00,
    (1.7, 400): 38.00,
    (1.7, 500): 55.00,
}

perdas_nucleo_data = {
    (0.5, 50): 0.10,
    (0.5, 60): 0.13,
    (0.5, 100): 0.25,
    (0.5, 120): 0.35,
    (0.5, 150): 0.50,
    (0.5, 200): 0.80,
    (0.5, 240): 1.10,
    (0.5, 250): 1.15,
    (0.5, 300): 1.30,
    (0.5, 350): 1.50,
    (0.5, 400): 1.70,
    (0.5, 500): 2.10,
    (0.6, 50): 0.12,
    (0.6, 60): 0.18,
    (0.6, 100): 0.38,
    (0.6, 120): 0.48,
    (0.6, 150): 0.70,
    (0.6, 200): 1.10,
    (0.6, 240): 1.50,
    (0.6, 250): 1.60,
    (0.6, 300): 2.00,
    (0.6, 350): 2.40,
    (0.6, 400): 2.80,
    (0.6, 500): 3.50,
    (0.7, 50): 0.15,
    (0.7, 60): 0.23,
    (0.7, 100): 0.50,
    (0.7, 120): 0.62,
    (0.7, 150): 0.95,
    (0.7, 200): 1.55,
    (0.7, 240): 2.10,
    (0.7, 250): 2.30,
    (0.7, 300): 3.00,
    (0.7, 350): 3.60,
    (0.7, 400): 4.20,
    (0.7, 500): 5.50,
    (0.8, 50): 0.20,
    (0.8, 60): 0.30,
    (0.8, 100): 0.65,
    (0.8, 120): 0.80,
    (0.8, 150): 1.20,
    (0.8, 200): 2.00,
    (0.8, 240): 2.80,
    (0.8, 250): 3.00,
    (0.8, 300): 3.90,
    (0.8, 350): 4.70,
    (0.8, 400): 5.50,
    (0.8, 500): 7.50,
    (0.9, 50): 0.25,
    (0.9, 60): 0.37,
    (0.9, 100): 0.82,
    (0.9, 120): 1.00,
    (0.9, 150): 1.50,
    (0.9, 200): 2.50,
    (0.9, 240): 3.50,
    (0.9, 250): 3.80,
    (0.9, 300): 4.80,
    (0.9, 350): 5.80,
    (0.9, 400): 6.80,
    (0.9, 500): 9.00,
    (1.0, 50): 0.32,
    (1.0, 60): 0.46,
    (1.0, 100): 1.00,
    (1.0, 120): 1.25,
    (1.0, 150): 1.85,
    (1.0, 200): 3.10,
    (1.0, 240): 4.20,
    (1.0, 250): 4.50,
    (1.0, 300): 5.90,
    (1.0, 350): 7.00,
    (1.0, 400): 8.50,
    (1.0, 500): 11.00,
    (1.1, 50): 0.41,
    (1.1, 60): 0.55,
    (1.1, 100): 1.21,
    (1.1, 120): 1.55,
    (1.1, 150): 2.20,
    (1.1, 200): 3.70,
    (1.1, 240): 5.00,
    (1.1, 250): 5.40,
    (1.1, 300): 6.90,
    (1.1, 350): 8.50,
    (1.1, 400): 10.00,
    (1.1, 500): 14.00,
    (1.2, 50): 0.50,
    (1.2, 60): 0.65,
    (1.2, 100): 1.41,
    (1.2, 120): 1.90,
    (1.2, 150): 2.70,
    (1.2, 200): 4.50,
    (1.2, 240): 6.00,
    (1.2, 250): 6.40,
    (1.2, 300): 8.10,
    (1.2, 350): 10.00,
    (1.2, 400): 12.00,
    (1.2, 500): 17.00,
    (1.3, 50): 0.60,
    (1.3, 60): 0.80,
    (1.3, 100): 1.65,
    (1.3, 120): 2.30,
    (1.3, 150): 3.20,
    (1.3, 200): 5.20,
    (1.3, 240): 7.00,
    (1.3, 250): 7.50,
    (1.3, 300): 9.50,
    (1.3, 350): 11.50,
    (1.3, 400): 14.00,
    (1.3, 500): 20.00,
    (1.4, 50): 0.71,
    (1.4, 60): 0.95,
    (1.4, 100): 1.95,
    (1.4, 120): 2.80,
    (1.4, 150): 3.80,
    (1.4, 200): 6.00,
    (1.4, 240): 8.50,
    (1.4, 250): 9.00,
    (1.4, 300): 11.00,
    (1.4, 350): 13.50,
    (1.4, 400): 16.00,
    (1.4, 500): 24.00,
    (1.5, 50): 0.85,
    (1.5, 60): 1.10,
    (1.5, 100): 2.30,
    (1.5, 120): 3.30,
    (1.5, 150): 4.50,
    (1.5, 200): 7.00,
    (1.5, 240): 10.00,
    (1.5, 250): 10.60,
    (1.5, 300): 13.00,
    (1.5, 350): 15.50,
    (1.5, 400): 19.00,
    (1.5, 500): 29.00,
    (1.6, 50): 1.00,
    (1.6, 60): 1.30,
    (1.6, 100): 2.80,
    (1.6, 120): 3.80,
    (1.6, 150): 5.30,
    (1.6, 200): 8.00,
    (1.6, 240): 12.00,
    (1.6, 250): 12.60,
    (1.6, 300): 15.00,
    (1.6, 350): 18.00,
    (1.6, 400): 23.00,
    (1.6, 500): 35.00,
    (1.7, 50): 1.20,
    (1.7, 60): 1.55,
    (1.7, 100): 3.50,
    (1.7, 120): 4.40,
    (1.7, 150): 6.00,
    (1.7, 200): 9.00,
    (1.7, 240): 15.00,
    (1.7, 250): 15.60,
    (1.7, 300): 18.00,
    (1.7, 350): 22.00,
    (1.7, 400): 28.00,
    (1.7, 500): 42.00,
}

# Dados para Aço H110-27 (Extraídos da Ficha Técnica W/Kg)
perdas_nucleo_data_H110_27 = {
    # Frequência 50 Hz
    (1.9, 50): 2.010, (1.8, 50): 1.398, (1.7, 50): 1.052, (1.6, 50): 0.882,
    (1.5, 50): 0.760, (1.4, 50): 0.658, (1.3, 50): 0.569, (1.2, 50): 0.488,
    (1.1, 50): 0.414, (1.0, 50): 0.346, (0.9, 50): 0.284, (0.8, 50): 0.228,
    (0.7, 50): 0.178, (0.6, 50): 0.135, (0.5, 50): 0.097, (0.4, 50): 0.065,
    (0.3, 50): 0.038, (0.2, 50): 0.018,
    # Frequência 60 Hz
    (1.9, 60): 2.595, (1.8, 60): 1.816, (1.7, 60): 1.383, (1.6, 60): 1.165,
    (1.5, 60): 1.006, (1.4, 60): 0.873, (1.3, 60): 0.755, (1.2, 60): 0.648,
    (1.1, 60): 0.549, (1.0, 60): 0.459, (0.9, 60): 0.377, (0.8, 60): 0.301,
    (0.7, 60): 0.236, (0.6, 60): 0.178, (0.5, 60): 0.128, (0.4, 60): 0.086,
    (0.3, 60): 0.050, (0.2, 60): 0.023,
    # Para outras frequências (100, 120, ... 500 Hz), os dados não estão disponíveis nesta tabela.
    # Estratégia: Omitir por enquanto. O lookup falhará para H110-27 nessas frequências.
}

potencia_magnet_data_H110_27 = { # VA/kg
    # Frequência 50 Hz
    (1.9, 50): 14.434, (1.8, 50): 3.438, (1.7, 50): 1.661, (1.6, 50): 1.188,
    (1.5, 50): 0.962,  (1.4, 50): 0.812, (1.3, 50): 0.698, (1.2, 50): 0.602,
    (1.1, 50): 0.517,  (1.0, 50): 0.441, (0.9, 50): 0.372, (0.8, 50): 0.308,
    (0.7, 50): 0.250,  (0.6, 50): 0.196, (0.5, 50): 0.147, (0.4, 50): 0.103,
    (0.3, 50): 0.064,  (0.2, 50): 0.032,
    # Frequência 60 Hz
    (1.9, 60): 17.589, (1.8, 60): 4.178, (1.7, 60): 2.070, (1.6, 60): 1.507,
    (1.5, 60): 1.230,  (1.4, 60): 1.045, (1.3, 60): 0.900, (1.2, 60): 0.777,
    (1.1, 60): 0.667,  (1.0, 60): 0.568, (0.9, 60): 0.477, (0.8, 60): 0.395,
    (0.7, 60): 0.319,  (0.6, 60): 0.249, (0.5, 60): 0.186, (0.4, 60): 0.130,
    (0.3, 60): 0.081,  (0.2, 60): 0.040,
    # Para outras frequências, os dados não estão disponíveis.
}