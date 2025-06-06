"""
Serviço para cálculos de perdas em transformadores
"""
import sys
import pathlib
import math
from pydantic import BaseModel
from typing import Dict, List, Optional, Union, Any
import logging
import numpy as np

# Ajusta o path para permitir importações corretas
current_file = pathlib.Path(__file__).absolute()
current_dir = current_file.parent
backend_dir = current_dir.parent
root_dir = backend_dir.parent

# Adiciona os diretórios ao path se ainda não estiverem lá
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Adiciona importação de constantes e logger
try:
    from ..utils import constants as const
except ImportError:
    try:
        from backend.utils import constants as const
    except ImportError:
        try:
            from utils import constants as const
        except ImportError:
            logging.warning("Não foi possível importar 'constants'. Usando mock para constantes.")
            class MockConstants:
                EPSILON = 1e-6
                SQRT_3 = 1.732050807568877
                # Adicionar mocks para as tabelas de dados de perdas e potência magnetizante
                potencia_magnet_data = {}
                perdas_nucleo_data = {}
                potencia_magnet_data_H110_27 = {}
                perdas_nucleo_data_H110_27 = {}
                # Adicionar mocks para fatores de correção H110-27
                FATOR_CONSTRUCAO_PERDAS_H110_27 = 1.15
                FATOR_CONSTRUCAO_POTENCIA_MAG_H110_27 = 1.2
                # Adicionar mock para fator de excitação default
                FATOR_EXCITACAO_DEFAULT_TRIFASICO = 3
                FATOR_EXCITACAO_DEFAULT_MONOFASICO = 5
                # Adicionar mocks para constantes do sistema SUT/EPS
                SUT_BT_VOLTAGE = 480
                EPS_CURRENT_LIMIT = 2000
                DUT_POWER_LIMIT = 1350


            const = MockConstants()

log = logging.getLogger(__name__)


class NoLoadLossesInput(BaseModel):
    """Modelo para os dados de entrada de perdas em vazio"""
    perdas_vazio_ui: float # Perdas em vazio (no-load) de projeto (kW)
    peso_nucleo_ui: float # Peso do núcleo de projeto (Ton)
    corrente_excitacao_ui: float # Corrente de excitação nominal de projeto (%)
    inducao_ui: float # Indução magnética nominal de projeto no núcleo (T)
    corrente_exc_1_1_ui: Optional[float] = None # Corrente de excitação de projeto a 110% V nominal (%)
    corrente_exc_1_2_ui: Optional[float] = None # Corrente de excitação de projeto a 120% V nominal (%)
    frequencia: float # Frequência nominal do DUT (Hz)
    tensao_bt_kv: float # Tensão nominal BT do DUT (kV)
    corrente_nominal_bt: float # Corrente nominal BT do DUT (A)
    tipo_transformador: str = "Trifásico" # Monofásico ou Trifásico
    steel_type: str = "M4" # Tipo de aço do núcleo (M4 ou H110-27)
    potencia_mva: float # Potência nominal do DUT (MVA) - Adicionado para consistência, embora não usado diretamente nos cálculos de perdas em vazio baseados em aço/projeto


class LoadLossesInput(BaseModel):
    """Modelo para os dados de entrada de perdas em carga"""
    temperatura_referencia: int
    perdas_carga_kw_u_min: float
    perdas_carga_kw_u_nom: float
    perdas_carga_kw_u_max: float
    potencia_mva: float
    impedancia: float


def interpolate_losses_table_data(table_name: str, induction: float, frequency: float, steel_type: str = "M4") -> float:
    """
    Realiza interpolação bilinear para obter valores das tabelas de perdas ou potência magnetizante.
    """
    if steel_type == "M4":
        if table_name == "potencia_magnet":
            table_data = const.potencia_magnet_data
        elif table_name == "perdas_nucleo":
            table_data = const.perdas_nucleo_data
        else:
            log.error(f"Tabela desconhecida para interpolação ({steel_type}): {table_name}")
            return 0.0
    elif steel_type == "H110-27":
         if table_name == "potencia_magnet":
            table_data = const.potencia_magnet_data_H110_27
         elif table_name == "perdas_nucleo":
            table_data = const.perdas_nucleo_data_H110_27
         else:
            log.error(f"Tabela desconhecida para interpolação ({steel_type}): {table_name}")
            return 0.0
    else:
        log.error(f"Tipo de aço desconhecido para interpolação: {steel_type}")
        return 0.0


    # Extrai pontos de indução e frequência disponíveis na tabela
    inductions = sorted(list(set([k[0] for k in table_data.keys()])))
    frequencies = sorted(list(set([k[1] for k in table_data.keys()])))

    # Encontra os pontos mais próximos para interpolação
    # Encontra os dois valores de indução que envolvem a indução de teste
    i0 = max([i for i in inductions if i <= induction], default=inductions[0])
    i1 = min([i for i in inductions if i >= induction], default=inductions[-1])

    # Encontra os dois valores de frequência que envolvem a frequência de teste
    f0 = max([f for f in frequencies if f <= frequency], default=frequencies[0])
    f1 = min([f for f in frequencies if f >= frequency], default=frequencies[-1])

    # Se a indução ou frequência de teste estiverem fora do range da tabela, retorna o valor do ponto mais próximo
    if induction < inductions[0] or induction > inductions[-1] or frequency < frequencies[0] or frequency > frequencies[-1]:
         log.warning(f"Indução ({induction} T) ou Frequência ({frequency} Hz) fora do range da tabela {table_name} para aço {steel_type}. Usando valor do ponto mais próximo.")
         # Retorna o valor do ponto mais próximo (i.e., o canto mais próximo da grade)
         clamped_induction = max(inductions[0], min(inductions[-1], induction))
         clamped_frequency = max(frequencies[0], min(frequencies[-1], frequency))
         closest_i = min(inductions, key=lambda x: abs(x - clamped_induction))
         closest_f = min(frequencies, key=lambda x: abs(x - clamped_frequency))
         return table_data.get((closest_i, closest_f), 0.0)


    # Se a indução ou frequência de teste coincidir com um ponto da tabela
    if i0 == i1 and f0 == f1:
        return table_data.get((i0, f0), 0.0)

    # Se a indução coincidir com um ponto da tabela, interpola linearmente na frequência
    if i0 == i1:
        v0 = table_data.get((i0, f0), 0.0)
        v1 = table_data.get((i0, f1), 0.0)
        if f0 == f1: return v0
        return v0 + (v1 - v0) * (frequency - f0) / (f1 - f0)

    # Se a frequência coincidir com um ponto da tabela, interpola linearmente na indução
    if f0 == f1:
        v0 = table_data.get((i0, f0), 0.0)
        v1 = table_data.get((i1, f0), 0.0)
        if i0 == i1: return v0
        return v0 + (v1 - v0) * (induction - i0) / (i1 - i0)

    # Interpolação bilinear
    q11 = table_data.get((i0, f0), 0.0)
    q12 = table_data.get((i0, f1), 0.0)
    q21 = table_data.get((i1, f0), 0.0)
    q22 = table_data.get((i1, f1), 0.0)

    # Interpolação na direção da indução
    r1 = q11 * (i1 - induction) / (i1 - i0) + q21 * (induction - i0) / (i1 - i0)
    r2 = q12 * (i1 - induction) / (i1 - i0) + q22 * (induction - i0) / (i1 - i0)

    # Interpolação na direção da frequência
    p = r1 * (f1 - frequency) / (f1 - f0) + r2 * (frequency - f0) / (f1 - f0)

    return p


def calculate_no_load_losses(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula os resultados de perdas em vazio com base nos parâmetros de entrada,
    incluindo cálculos baseados em tabelas de aço e dados de projeto.
    """
    # Converter dicionário para modelo de dados
    data = NoLoadLossesInput(**input_data)

    # Constante: sqrt_3 = math.sqrt(3) (para trifásicos, 1.0 para monofásicos)
    sqrt_3_factor = const.SQRT_3 if data.tipo_transformador.lower() == "trifásico" else 1.0

    # Peso do núcleo em kg
    peso_nucleo_kg = data.peso_nucleo_ui * 1000

    # --- Cálculos Baseados em Aço (Estimativa) - Seção 3.3.2 (primeira parte) ---
    # Arredonda indução e frequência para lookup na tabela
    # A documentação menciona arredondar indução para 1 casa decimal, mas as tabelas têm 2.
    # Vou usar a indução de projeto diretamente para a interpolação.
    inducao_arredondada = data.inducao_ui # Usar indução de projeto diretamente
    frequencia_arredondada = data.frequencia # Usar frequência de projeto diretamente

    # Interpolação dos fatores das tabelas de aço
    fator_perdas_aco = interpolate_losses_table_data("perdas_nucleo", inducao_arredondada, frequencia_arredondada, data.steel_type)
    fator_potencia_mag_aco = interpolate_losses_table_data("potencia_magnet", inducao_arredondada, frequencia_arredondada, data.steel_type)

    # Aplicar fatores construtivos para aço H110-27 (Seção 3.3.1)
    if data.steel_type == "H110-27":
        fator_perdas_aco *= const.FATOR_CONSTRUCAO_PERDAS_H110_27
        fator_potencia_mag_aco *= const.FATOR_CONSTRUCAO_POTENCIA_MAG_H110_27

    # Cálculo do peso do núcleo baseado nas perdas de projeto e fator de perdas do aço
    # perdas_vazio_ui (kW) / fator_perdas_aco (W/kg) -> (kW) / (W/kg) = (1000 W) / (W/kg) = 1000 kg
    # Para converter para Ton: (perdas_vazio_ui * 1000) / fator_perdas_aco / 1000 = perdas_vazio_ui / fator_perdas_aco
    # A documentação menciona que a fórmula peso_nucleo_calc = perdas_vazio / fator_perdas resulta em kTon
    # se perdas_vazio é kW e fator_perdas é W/kg. Isso parece uma interpretação incorreta das unidades.
    # kW / (W/kg) = (1000 W) / (W/kg) = 1000 kg. Para Ton, divide por 1000.
    # Portanto, peso_nucleo_calc (kg) = (data.perdas_vazio_ui * 1000) / fator_perdas_aco
    # peso_nucleo_calc (Ton) = peso_nucleo_calc_kg / 1000
    # Vou seguir a fórmula da documentação que parece resultar em Ton diretamente se perdas_vazio_ui for em kW e fator_perdas_aco em W/kg.
    # peso_nucleo_calc (Ton) = data.perdas_vazio_ui / fator_perdas_aco if fator_perdas_aco > const.EPSILON else 0
    # A documentação no exemplo numérico usa 10 kW / 1.30 W/kg = 7692.31 kg = 7.692 Ton.
    # Isso implica que fator_perdas_aco é W/kg e perdas_vazio_ui é kW.
    peso_nucleo_calc_kg = (data.perdas_vazio_ui * 1000) / fator_perdas_aco if fator_perdas_aco > const.EPSILON else 0
    peso_nucleo_calc_ton = peso_nucleo_calc_kg / 1000

    # Potência magnética baseada no fator do aço
    # potencia_mag_aco (kVAR) = fator_potencia_mag_aco (VAR/kg) * peso_nucleo_calc_kg (kg) / 1000 (VAR/kVAR)
    potencia_mag_aco_kvar = (fator_potencia_mag_aco * peso_nucleo_calc_kg) / 1000 if peso_nucleo_calc_kg > 0 else 0

    # Corrente de excitação calculada a partir da potência magnética do aço
    # corrente_excitacao_calc (A) = potencia_mag_aco_kvar (kVAR) / (tensao_bt_kv (kV) * sqrt_3_factor)
    corrente_excitacao_calc_a = potencia_mag_aco_kvar / (data.tensao_bt_kv * sqrt_3_factor) if data.tensao_bt_kv > 0 and sqrt_3_factor > 0 else 0

    # Corrente de excitação percentual calculada
    corrente_excitacao_percentual_calc = (corrente_excitacao_calc_a / data.corrente_nominal_bt) * 100 if data.corrente_nominal_bt > 0 else 0

    # Tensões de teste a 1.1 pu e 1.2 pu
    tensao_teste_1_1_kv = data.tensao_bt_kv * 1.1
    tensao_teste_1_2_kv = data.tensao_bt_kv * 1.2

    # Correntes de excitação estimadas a 1.1 pu e 1.2 pu (baseado na estimativa P ~ V^2, I ~ V^n)
    # A documentação sugere I ~ V^1 para 1.1 pu e I ~ V^2 para 1.2 pu no exemplo numérico, o que é uma simplificação.
    # Vou manter a simplificação do exemplo numérico por enquanto.
    corrente_excitacao_1_1_calc_a = 2 * corrente_excitacao_calc_a # Simplificação do exemplo
    corrente_excitacao_1_2_calc_a = 4 * corrente_excitacao_calc_a # Simplificação do exemplo

    # Potências de ensaio calculadas (kVA)
    potencia_ensaio_1pu_calc_kva = data.tensao_bt_kv * corrente_excitacao_calc_a * sqrt_3_factor
    potencia_ensaio_1_1pu_calc_kva = tensao_teste_1_1_kv * corrente_excitacao_1_1_calc_a * sqrt_3_factor
    potencia_ensaio_1_2pu_calc_kva = tensao_teste_1_2_kv * corrente_excitacao_1_2_calc_a * sqrt_3_factor


    # --- Cálculos Baseados em Dados de Projeto - Seção 3.3.2 (segunda parte) ---
    # Fator de perdas de projeto (kW/Ton e W/kg)
    fator_perdas_projeto_kw_ton = data.perdas_vazio_ui / data.peso_nucleo_ui if data.peso_nucleo_ui > 0 else 0
    fator_perdas_projeto_w_kg = (data.perdas_vazio_ui * 1000) / (data.peso_nucleo_ui * 1000) if data.peso_nucleo_ui > 0 else 0

    # Corrente de excitação de projeto (A)
    corrente_excitacao_projeto_a = data.corrente_nominal_bt * (data.corrente_excitacao_ui / 100.0) if data.corrente_nominal_bt > 0 else 0

    # Potência de ensaio a 1 pu (Projeto) (kVA)
    potencia_ensaio_1pu_projeto_kva = data.tensao_bt_kv * corrente_excitacao_projeto_a * sqrt_3_factor

    # Potência magnética de projeto (kVAR) - Assumindo que é igual à potência de ensaio a 1 pu
    potencia_mag_projeto_kvar = potencia_ensaio_1pu_projeto_kva

    # Fator de potência magnética de projeto (VAR/kg)
    # (potencia_mag_projeto_kvar * 1000) / (peso_nucleo_ui * 1000)
    fator_potencia_mag_projeto_var_kg = (potencia_mag_projeto_kvar * 1000) / (data.peso_nucleo_ui * 1000) if data.peso_nucleo_ui > 0 else 0

    # Fator de excitação default
    fator_excitacao_default = const.FATOR_EXCITACAO_DEFAULT_TRIFASICO if data.tipo_transformador.lower() == "trifásico" else const.FATOR_EXCITACAO_DEFAULT_MONOFASICO

    # Corrente de excitação a 1.1 pu (Projeto) (A)
    # Se corrente_exc_1_1_ui não nulo, usar valor de projeto. Senão, usar fator default * corrente_excitacao_projeto.
    corrente_excitacao_1_1_projeto_a = None
    if data.corrente_exc_1_1_ui is not None:
        corrente_excitacao_1_1_projeto_a = data.corrente_nominal_bt * (data.corrente_exc_1_1_ui / 100.0) if data.corrente_nominal_bt > 0 else 0
    else:
        corrente_excitacao_1_1_projeto_a = fator_excitacao_default * corrente_excitacao_projeto_a

    # Corrente de excitação a 1.2 pu (Projeto) (A)
    # Se corrente_exc_1_2_ui não nulo, usar valor de projeto. Senão, None.
    corrente_excitacao_1_2_projeto_a = None
    if data.corrente_exc_1_2_ui is not None:
        corrente_excitacao_1_2_projeto_a = data.corrente_nominal_bt * (data.corrente_exc_1_2_ui / 100.0) if data.corrente_nominal_bt > 0 else 0

    # Potência de ensaio a 1.1 pu (Projeto) (kVA)
    potencia_ensaio_1_1pu_projeto_kva = tensao_teste_1_1_kv * corrente_excitacao_1_1_projeto_a * sqrt_3_factor if corrente_excitacao_1_1_projeto_a is not None else None

    # Potência de ensaio a 1.2 pu (Projeto) (kVA)
    potencia_ensaio_1_2pu_projeto_kva = tensao_teste_1_2_kv * corrente_excitacao_1_2_projeto_a * sqrt_3_factor if corrente_excitacao_1_2_projeto_a is not None else None


    # Prepara resultados
    results = {
        "parametros_entrada": {
            "perdas_vazio_ui": data.perdas_vazio_ui,
            "peso_nucleo_ui": data.peso_nucleo_ui,
            "corrente_excitacao_ui": data.corrente_excitacao_ui,
            "inducao_ui": data.inducao_ui,
            "corrente_exc_1_1_ui": data.corrente_exc_1_1_ui,
            "corrente_exc_1_2_ui": data.corrente_exc_1_2_ui,
            "frequencia": data.frequencia,
            "tensao_bt_kv": data.tensao_bt_kv,
            "corrente_nominal_bt": data.corrente_nominal_bt,
            "tipo_transformador": data.tipo_transformador,
            "steel_type": data.steel_type,
            "potencia_mva": data.potencia_mva,
            "peso_nucleo_kg": peso_nucleo_kg,
        },
        "calculos_baseados_aço": {
            "inducao_arredondada": round(inducao_arredondada, 4),
            "frequencia_arredondada": round(frequencia_arredondada, 2),
            "fator_perdas_aco_w_kg": round(fator_perdas_aco, 4),
            "fator_potencia_mag_aco_var_kg": round(fator_potencia_mag_aco, 4),
            "peso_nucleo_calc_kg": round(peso_nucleo_calc_kg, 2),
            "peso_nucleo_calc_ton": round(peso_nucleo_calc_ton, 2),
            "potencia_mag_aco_kvar": round(potencia_mag_aco_kvar, 2),
            "corrente_excitacao_calc_a": round(corrente_excitacao_calc_a, 2),
            "corrente_excitacao_percentual_calc": round(corrente_excitacao_percentual_calc, 2),
            "tensao_teste_1_1_kv": round(tensao_teste_1_1_kv, 2),
            "tensao_teste_1_2_kv": round(tensao_teste_1_2_kv, 2),
            "corrente_excitacao_1_1_calc_a": round(corrente_excitacao_1_1_calc_a, 2),
            "corrente_excitacao_1_2_calc_a": round(corrente_excitacao_1_2_calc_a, 2),
            "potencia_ensaio_1pu_calc_kva": round(potencia_ensaio_1pu_calc_kva, 2),
            "potencia_ensaio_1_1pu_calc_kva": round(potencia_ensaio_1_1pu_calc_kva, 2) if potencia_ensaio_1_1pu_calc_kva is not None else None,
            "potencia_ensaio_1_2pu_calc_kva": round(potencia_ensaio_1_2pu_calc_kva, 2) if potencia_ensaio_1_2pu_calc_kva is not None else None,
        },
        "calculos_baseados_projeto": {
            "fator_perdas_projeto_kw_ton": round(fator_perdas_projeto_kw_ton, 4),
            "fator_perdas_projeto_w_kg": round(fator_perdas_projeto_w_kg, 4),
            "corrente_excitacao_projeto_a": round(corrente_excitacao_projeto_a, 2),
            "potencia_ensaio_1pu_projeto_kva": round(potencia_ensaio_1pu_projeto_kva, 2),
            "potencia_mag_projeto_kvar": round(potencia_mag_projeto_kvar, 2),
            "fator_potencia_mag_projeto_var_kg": round(fator_potencia_mag_projeto_var_kg, 4),
            "fator_excitacao_default": fator_excitacao_default,
            "corrente_excitacao_1_1_projeto_a": round(corrente_excitacao_1_1_projeto_a, 2) if corrente_excitacao_1_1_projeto_a is not None else None,
            "corrente_excitacao_1_2_projeto_a": round(corrente_excitacao_1_2_projeto_a, 2) if corrente_excitacao_1_2_projeto_a is not None else None,
            "potencia_ensaio_1_1pu_projeto_kva": round(potencia_ensaio_1_1pu_projeto_kva, 2) if potencia_ensaio_1_1pu_projeto_kva is not None else None,
            "potencia_ensaio_1_2pu_projeto_kva": round(potencia_ensaio_1_2pu_projeto_kva, 2) if potencia_ensaio_1_2pu_projeto_kva is not None else None,
        },
        "analise_taps": {
            "message": "Análise de taps e SUT/EPS para perdas em vazio pendente."
        }
    }

    return results


def calculate_load_losses(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula os resultados de perdas em carga com base nos parâmetros de entrada.
    """
    # Converter dicionário para modelo de dados
    data = LoadLossesInput(**input_data)

    # Realizar cálculos básicos
    temperatura_ref = data.temperatura_referencia

    # Correção de temperatura para cálculo de perdas
    fator_correcao = (235 + 75) / (235 + temperatura_ref)  # Para referência a 75°C

    # Perdas corrigidas
    perdas_corrigidas_min = data.perdas_carga_kw_u_min * fator_correcao
    perdas_corrigidas_nom = data.perdas_carga_kw_u_nom * fator_correcao
    perdas_corrigidas_max = data.perdas_carga_kw_u_max * fator_correcao

    # Perdas por unidade (base de 10 kW/MVA)
    perdas_pu_nominal = perdas_corrigidas_nom / (data.potencia_mva * 10)

    # Perdas I²R e adicionais (estimativas)
    i2r_perdas = perdas_corrigidas_nom * 0.85  # ~85% são perdas I²R
    perdas_adicionais = perdas_corrigidas_nom - i2r_perdas

    return {
        "condicoes_nominais": {
            "temperatura_referencia": temperatura_ref,
            "perdas_tap_menos": round(perdas_corrigidas_min, 2),
            "perdas_tap_nominal": round(perdas_corrigidas_nom, 2),
            "perdas_tap_mais": round(perdas_corrigidas_max, 2),
            "perdas_por_unidade": round(perdas_pu_nominal * 100, 2),  # Em percentual
            "i2r_perdas": round(i2r_perdas, 2),
            "perdas_adicionais": round(perdas_adicionais, 2),
            "impedancia": data.impedancia
        }
    }


def calculate_cap_bank(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula o banco de capacitores requerido para compensação de potência reativa.
    """
    # Extrair potência de referência e fator de potência desejado
    potencia_ativa = input_data.get("potencia_ativa", 0)  # kW
    fp_atual = input_data.get("fator_potencia_atual", 0.7)
    fp_desejado = input_data.get("fator_potencia_desejado", 0.95)

    # Evitar divisão por zero e outros valores inválidos
    if potencia_ativa <= 0 or fp_atual <= 0 or fp_atual >= 1 or fp_desejado <= 0 or fp_desejado >= 1:
        return {
            "potencia_reativa_atual": 0,
            "potencia_reativa_desejada": 0,
            "potencia_banco_capacitores": 0,
            "status": "Valores de entrada inválidos."
        }

    # Cálculo de potências reativas
    tg_phi_atual = math.sqrt(1 - fp_atual**2) / fp_atual
    tg_phi_desejado = math.sqrt(1 - fp_desejado**2) / fp_desejado

    potencia_reativa_atual = potencia_ativa * tg_phi_atual  # kVAR
    potencia_reativa_desejada = potencia_ativa * tg_phi_desejado  # kVAR

    # Potência do banco de capacitores
    potencia_banco_capacitores = potencia_reativa_atual - potencia_reativa_desejada  # kVAR

    return {
        "potencia_reativa_atual": round(potencia_reativa_atual, 2),
        "potencia_reativa_desejada": round(potencia_reativa_desejada, 2),
        "potencia_banco_capacitores": round(potencia_banco_capacitores, 2),
        "status": "OK"
    }


def calculate_sut_eps_current_compensated(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula a corrente compensada para o sistema SUT/EPS com banco de capacitores.
    """
    # Extrair dados da análise básica
    potencia_ativa = input_data.get("potencia_ativa", 0)  # kW
    tensao_teste = input_data.get("tensao_teste", 0)  # kV
    fator_potencia = input_data.get("fator_potencia", 0.7)
    potencia_banco_cap = input_data.get("potencia_banco_cap", 0)  # kVAR

    # Constantes do sistema
    sut_bt_voltage = 480  # V (SUT_BT_VOLTAGE)
    eps_current_limit = 2000  # A (EPS_CURRENT_LIMIT)

    # Evitar divisão por zero
    if tensao_teste <= 0:
        return {
            "corrente_sem_compensacao": 0,
            "corrente_compensada": 0,
            "percentual_limite": 0,
            "status": "Tensão de teste inválida."
        }

    # Cálculo da potência aparente sem compensação
    potencia_reativa = potencia_ativa * math.sqrt(1 - fator_potencia**2) / fator_potencia  # kVAR
    potencia_aparente = math.sqrt(potencia_ativa**2 + potencia_reativa**2)  # kVA

    # Cálculo da potência reativa compensada
    potencia_reativa_compensada = potencia_reativa - potencia_banco_cap  # kVAR
    potencia_aparente_compensada = math.sqrt(potencia_ativa**2 + potencia_reativa_compensada**2)  # kVA

    # Fator de potência compensado
    fp_compensado = potencia_ativa / potencia_aparente_compensada if potencia_aparente_compensada > 0 else 1.0

    # Cálculos de corrente no lado primário (BT) do SUT
    # A documentação em 4.6 usa tensao_ref_dut_kv e corrente_ref_dut_a.
    # Assumindo que tensao_teste é a tensao_ref_dut_kv e a corrente total do DUT no ensaio
    # precisa ser calculada ou fornecida. Por enquanto, usarei a potencia_aparente_compens