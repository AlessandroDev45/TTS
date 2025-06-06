# backend/services/transformer_service.py

import logging
import sys
import os
import pathlib
import math # Importar math para PI e sqrt
from typing import Dict, Any, Optional

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

# Importa constantes e funções de outros serviços usando importação relativa
try:
    from ..utils import constants as const
    from .short_circuit_service import calculate_nominal_currents # Importar do serviço de curto-circuito
except ImportError as e:
    logging.error(f"Erro ao importar módulos dependentes em transformer_service: {e}")
    # Em caso de falha crítica na importação, re-raise o erro ou defina mocks que falhem explicitamente
    # Para fins de depuração, vamos definir mocks que loggam o uso e retornam None/valores padrão
    class MockConstants:
        IAC_NBI_FACTOR = 3.5
        EPSILON = 1e-6
        SQRT_3 = 1.732050807568877
        PI = 3.141592653589793

    const = MockConstants()

    def calculate_nominal_currents(data: Dict[str, Any]) -> Dict[str, Optional[float]]:
        logging.warning("Usando mock para calculate_nominal_currents devido a falha na importação.")
        return {
            "i_nom_at": None,
            "i_nom_bt": None,
            "i_nom_ter": None,
            "i_nom_at_tap_maior": None,
            "i_nom_at_tap_menor": None,
        }

# Definir extract_and_process_transformer_inputs no escopo principal
def extract_and_process_transformer_inputs(raw_inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrai e processa os dados brutos de entrada do transformador,
    normalizando tipos e tratando valores vazios.
    """
    processed_data = {}

    # Dados Básicos
    processed_data["potencia_mva"] = safe_float_convert(raw_inputs.get("potencia_mva"))
    processed_data["frequencia"] = safe_float_convert(raw_inputs.get("frequencia"))
    processed_data["tipo_transformador"] = raw_inputs.get("tipo_transformador", "Trifásico")
    processed_data["grupo_ligacao"] = raw_inputs.get("grupo_ligacao")
    processed_data["liquido_isolante"] = raw_inputs.get("liquido_isolante")
    processed_data["tipo_isolamento"] = raw_inputs.get("tipo_isolamento")
    processed_data["norma_iso"] = raw_inputs.get("norma_iso")
    processed_data["elevacao_oleo_topo"] = safe_float_convert(raw_inputs.get("elevacao_oleo_topo"))
    processed_data["elevacao_enrol"] = safe_float_convert(raw_inputs.get("elevacao_enrol"))

    # Pesos
    processed_data["peso_total"] = safe_float_convert(raw_inputs.get("peso_total"))
    processed_data["peso_parte_ativa"] = safe_float_convert(raw_inputs.get("peso_parte_ativa"))
    processed_data["peso_oleo"] = safe_float_convert(raw_inputs.get("peso_oleo"))
    processed_data["peso_tanque_acessorios"] = safe_float_convert(raw_inputs.get("peso_tanque_acessorios"))

    # Alta Tensão
    processed_data["tensao_at"] = safe_float_convert(raw_inputs.get("tensao_at"))
    processed_data["classe_tensao_at"] = safe_float_convert(raw_inputs.get("classe_tensao_at"))
    processed_data["impedancia"] = safe_float_convert(raw_inputs.get("impedancia"))
    processed_data["nbi_at"] = safe_float_convert(raw_inputs.get("nbi_at"))
    processed_data["sil_at"] = safe_float_convert(raw_inputs.get("sil_at"))
    processed_data["conexao_at"] = raw_inputs.get("conexao_at")
    processed_data["tensao_bucha_neutro_at"] = safe_float_convert(raw_inputs.get("tensao_bucha_neutro_at"))
    processed_data["nbi_neutro_at"] = safe_float_convert(raw_inputs.get("nbi_neutro_at"))
    processed_data["sil_neutro_at"] = safe_float_convert(raw_inputs.get("sil_neutro_at"))
    processed_data["teste_tensao_aplicada_at"] = safe_float_convert(raw_inputs.get("teste_tensao_aplicada_at"))
    processed_data["teste_tensao_induzida_at"] = safe_float_convert(raw_inputs.get("teste_tensao_induzida_at"))

    # Taps AT
    processed_data["tensao_at_tap_maior"] = safe_float_convert(raw_inputs.get("tensao_at_tap_maior"))
    processed_data["impedancia_tap_maior"] = safe_float_convert(raw_inputs.get("impedancia_tap_maior"))
    processed_data["tensao_at_tap_menor"] = safe_float_convert(raw_inputs.get("tensao_at_tap_menor"))
    processed_data["impedancia_tap_menor"] = safe_float_convert(raw_inputs.get("impedancia_tap_menor"))

    # Baixa Tensão
    processed_data["tensao_bt"] = safe_float_convert(raw_inputs.get("tensao_bt"))
    processed_data["classe_tensao_bt"] = safe_float_convert(raw_inputs.get("classe_tensao_bt"))
    processed_data["nbi_bt"] = safe_float_convert(raw_inputs.get("nbi_bt"))
    processed_data["sil_bt"] = safe_float_convert(raw_inputs.get("sil_bt"))
    processed_data["conexao_bt"] = raw_inputs.get("conexao_bt")
    processed_data["tensao_bucha_neutro_bt"] = safe_float_convert(raw_inputs.get("tensao_bucha_neutro_bt"))
    processed_data["nbi_neutro_bt"] = safe_float_convert(raw_inputs.get("nbi_neutro_bt"))
    processed_data["sil_neutro_bt"] = safe_float_convert(raw_inputs.get("sil_neutro_bt"))
    processed_data["teste_tensao_aplicada_bt"] = safe_float_convert(raw_inputs.get("teste_tensao_aplicada_bt"))

    # Terciário
    processed_data["tensao_terciario"] = safe_float_convert(raw_inputs.get("tensao_terciario"))
    processed_data["classe_tensao_terciario"] = safe_float_convert(raw_inputs.get("classe_tensao_terciario"))
    processed_data["nbi_terciario"] = safe_float_convert(raw_inputs.get("nbi_terciario"))
    processed_data["sil_terciario"] = safe_float_convert(raw_inputs.get("sil_terciario"))
    processed_data["conexao_terciario"] = raw_inputs.get("conexao_terciario")
    processed_data["tensao_bucha_neutro_terciario"] = safe_float_convert(raw_inputs.get("tensao_bucha_neutro_terciario"))
    processed_data["nbi_neutro_terciario"] = safe_float_convert(raw_inputs.get("nbi_neutro_terciario"))
    processed_data["sil_neutro_terciario"] = safe_float_convert(raw_inputs.get("sil_neutro_terciario"))
    processed_data["teste_tensao_aplicada_terciario"] = safe_float_convert(raw_inputs.get("teste_tensao_aplicada_terciario"))

    return processed_data

log = logging.getLogger(__name__)

def safe_float_convert(value: Any) -> Optional[float]:
    """Converte um valor para float, retornando None se a conversão falhar ou o valor for vazio."""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    try:
        if isinstance(value, str):
            value = value.replace(",", ".").strip()
        return float(value)
    except (ValueError, TypeError):
        return None

def calculate_and_process_transformer_data(
    transformer_inputs: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Realiza cálculos de correntes nominais, impedância base, indutância e adiciona dados derivados
    aos inputs do transformador.
    """
    log.info("Iniciando cálculo e processamento de dados do transformador.")

    # 1. Processar e limpar os inputs brutos
    data_to_process = extract_and_process_transformer_inputs(transformer_inputs)

    # LOG: Exibir dados antes do cálculo das correntes
    log.info(f"[DEBUG] Dados para cálculo das correntes: {data_to_process}")

    # 2. Calcular correntes nominais (Seção 2.1 e 2.2)
    currents_input_data = {
        "tipo_transformador": data_to_process.get("tipo_transformador"),
        "potencia_mva": data_to_process.get("potencia_mva"),
        "tensao_at": data_to_process.get("tensao_at"),
        "tensao_at_tap_maior": data_to_process.get("tensao_at_tap_maior"),
        "tensao_at_tap_menor": data_to_process.get("tensao_at_tap_menor"),
        "tensao_bt": data_to_process.get("tensao_bt"),
        "tensao_terciario": data_to_process.get("tensao_terciario"),
    }
    log.info(f"[DEBUG] Dados enviados para calculate_nominal_currents: {currents_input_data}")
    # Usar a função calculate_nominal_currents importada
    calculated_currents = calculate_nominal_currents(currents_input_data)
    log.info(f"[DEBUG] Resultado de calculate_nominal_currents: {calculated_currents}")

    data_to_process["corrente_nominal_at"] = calculated_currents.get("i_nom_at") # Usar chaves corretas do retorno
    data_to_process["corrente_nominal_bt"] = calculated_currents.get("i_nom_bt") # Usar chaves corretas do retorno
    data_to_process["corrente_nominal_terciario"] = calculated_currents.get("i_nom_ter") # Usar chaves corretas do retorno
    data_to_process["corrente_nominal_at_tap_maior"] = calculated_currents.get("i_nom_at_tap_maior")
    data_to_process["corrente_nominal_at_tap_menor"] = calculated_currents.get("i_nom_at_tap_menor")

    # 3. Calcular impedância base e indutância de curto-circuito (Seção 2.3)
    potencia_mva = data_to_process.get("potencia_mva", 0)
    tensao_at = data_to_process.get("tensao_at", 0)
    impedancia_percentual = data_to_process.get("impedancia", 0)
    frequencia = data_to_process.get("frequencia", 60)

    z_base_at = (tensao_at**2 * 1000) / potencia_mva if potencia_mva > const.EPSILON else 0 # Ω
    z_cc_ohm = z_base_at * (impedancia_percentual / 100) if z_base_at > 0 else 0 # Ω
    l_cc_henries = z_cc_ohm / (2 * const.PI * frequencia) if z_cc_ohm > 0 and frequencia > 0 else 0 # H

    data_to_process["z_base_at_ohm"] = round(z_base_at, 4)
    data_to_process["z_cc_ohm"] = round(z_cc_ohm, 4)
    data_to_process["l_cc_henries"] = round(l_cc_henries, 6)
    data_to_process["l_cc_uh"] = round(l_cc_henries * 1e6, 4) # Convertendo para μH

    # 4. Calcular IAC (Impulso Atmosférico Cortado) se a norma for IEC
    norma_para_iac = data_to_process.get("norma_iso")
    if norma_para_iac and "IEC" in norma_para_iac:
        for winding_prefix in ["at", "bt", "terciario"]:
            nbi_key = f"nbi_{winding_prefix}"
            nbi_value = data_to_process.get(nbi_key)

            iac_value = None
            if nbi_value is not None:
                try:
                    # Usar const.IAC_NBI_FACTOR do arquivo constants.py
                    iac_value = round(const.IAC_NBI_FACTOR * float(nbi_value), 2)
                except (ValueError, TypeError, AttributeError):
                    log.warning(f"Não foi possível calcular IAC para {winding_prefix} a partir de {nbi_key}: {nbi_value}")
            data_to_process[f"iac_{winding_prefix}"] = iac_value
    else:
        data_to_process["iac_at"] = None
        data_to_process["iac_bt"] = None
        data_to_process["iac_terciario"] = None

    # 5. Sincronizar elevação de enrolamento
    if data_to_process.get("elevacao_enrol") is not None:
        elevacao = data_to_process["elevacao_enrol"]
        data_to_process["elevacao_enrol_at"] = elevacao
        data_to_process["elevacao_enrol_bt"] = elevacao
        data_to_process["elevacao_enrol_terciario"] = elevacao

    log.info("Cálculo e processamento de dados do transformador concluídos.")
    return data_to_process