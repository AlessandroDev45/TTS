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
except ImportError as e:
    logging.error(f"Erro ao importar módulos dependentes em transformer_service: {e}")
    class MockConstants:
        IAC_NBI_FACTOR = 3.5
        EPSILON = 1e-6
        SQRT_3 = 1.732050807568877
        PI = 3.141592653589793
    const = MockConstants()

# Definir extract_and_process_transformer_inputs no escopo principal
def extract_and_process_transformer_inputs(raw_inputs: Dict[str, Any]) -> Dict[str, Any]:
    processed_data = {}

    # Campos que devem ser tratados como numéricos (float)
    numeric_fields = {
        "potencia_mva", "frequencia", "elevacao_oleo_topo", "elevacao_enrol",
        "peso_parte_ativa", "peso_tanque_acessorios", "peso_oleo", "peso_total", "peso_adicional",
        "tensao_at", "classe_tensao_at", "impedancia", "nbi_at", "sil_at",
        "tensao_bucha_neutro_at", "nbi_neutro_at", "sil_neutro_at", "tensao_at_tap_maior",
        "tensao_at_tap_menor", "impedancia_tap_maior", "impedancia_tap_menor",
        "teste_tensao_aplicada_at", "teste_tensao_induzida_at",
        "tensao_bt", "classe_tensao_bt", "nbi_bt", "sil_bt",
        "tensao_bucha_neutro_bt", "nbi_neutro_bt", "sil_neutro_bt", "teste_tensao_aplicada_bt",
        "tensao_terciario", "classe_tensao_terciario", "nbi_terciario", "sil_terciario",
        "tensao_bucha_neutro_terciario", "nbi_neutro_terciario", "sil_neutro_terciario",
        "teste_tensao_aplicada_terciario"
    }

    # Campos que devem ser tratados como strings
    string_fields = {
        "tipo_transformador", "grupo_ligacao", "liquido_isolante", "tipo_isolamento",
        "norma_iso", "conexao_at", "conexao_bt", "conexao_terciario"
    }

    # Valores padrão para campos string
    string_defaults = {
        "tipo_transformador": "Trifásico",
        "liquido_isolante": "Mineral",
        "tipo_isolamento": "Uniforme",
        "norma_iso": "IEC"
    }

    # Processa todos os campos dos dados de entrada
    for key, raw_value in raw_inputs.items():
        if key in numeric_fields:
            # Trata como numérico
            processed_data[key] = safe_float_convert(raw_value)
        elif key in string_fields:
            # Trata como string
            if raw_value is not None and raw_value != "":
                processed_data[key] = str(raw_value).strip()
            else:
                processed_data[key] = string_defaults.get(key, None)
        else:
            # Para outros campos, mantém o valor original
            processed_data[key] = raw_value

    # Aplica valores padrão para campos string que não foram fornecidos
    for field, default_value in string_defaults.items():
        if field not in processed_data or processed_data[field] is None:
            processed_data[field] = default_value

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
    log.info(f"Dados de entrada recebidos: {transformer_inputs}")

    # 1. Processar e limpar os inputs brutos
    data_to_process = extract_and_process_transformer_inputs(transformer_inputs)
    log.info(f"Dados após processamento: {data_to_process}")

    # Obter potência nominal e tipo de transformador no escopo principal
    potencia_nominal = data_to_process.get("potencia_mva") or 0
    tipo_transformador = data_to_process.get("tipo_transformador", "Trifásico")
    fator = 1.0 if tipo_transformador.lower() == "monofásico" else const.SQRT_3

    log.info(f"Potência nominal: {potencia_nominal} (tipo: {type(potencia_nominal)}), Tipo: {tipo_transformador}, Fator: {fator}")

    # Função interna para calcular correntes nominais
    def _calculate_nominal_currents(data: Dict[str, Any], current_potencia_nominal: float, current_fator: float) -> Dict[str, float]:
        tensao_at = data.get("tensao_at") or 0
        tensao_bt = data.get("tensao_bt") or 0
        tensao_terciario = data.get("tensao_terciario") or 0

        i_nom_at = (current_potencia_nominal * 1000) / (current_fator * tensao_at) if tensao_at and tensao_at > 0 else 0
        i_nom_bt = (current_potencia_nominal * 1000) / (current_fator * tensao_bt) if tensao_bt and tensao_bt > 0 else 0
        i_nom_ter = (current_potencia_nominal * 1000) / (current_fator * tensao_terciario) if tensao_terciario and tensao_terciario > 0 else 0

        return {
            "i_nom_at": i_nom_at,
            "i_nom_bt": i_nom_bt,
            "i_nom_ter": i_nom_ter
        }

    # 2. Calcular correntes nominais (Seção 2.1 e 2.2)
    currents_input_data = {
        "tensao_at": data_to_process.get("tensao_at"),
        "tensao_bt": data_to_process.get("tensao_bt"),
        "tensao_terciario": data_to_process.get("tensao_terciario"),
    }
    log.info(f"Dados para cálculo de correntes: {currents_input_data}")
    calculated_currents = _calculate_nominal_currents(currents_input_data, potencia_nominal, fator)
    log.info(f"Correntes calculadas: {calculated_currents}")

    data_to_process["corrente_nominal_at"] = calculated_currents.get("i_nom_at")
    data_to_process["corrente_nominal_bt"] = calculated_currents.get("i_nom_bt")
    data_to_process["corrente_nominal_terciario"] = calculated_currents.get("i_nom_ter")
    
    # Adicionar cálculo para correntes de tap
    tensao_at_tap_maior = data_to_process.get("tensao_at_tap_maior")
    tensao_at_tap_menor = data_to_process.get("tensao_at_tap_menor")

    if potencia_nominal and potencia_nominal > 0 and fator > 0:
        if tensao_at_tap_maior is not None and tensao_at_tap_maior > 0:
            data_to_process["corrente_nominal_at_tap_maior"] = (potencia_nominal * 1000) / (fator * tensao_at_tap_maior)
        else:
            data_to_process["corrente_nominal_at_tap_maior"] = None

        if tensao_at_tap_menor is not None and tensao_at_tap_menor > 0:
            data_to_process["corrente_nominal_at_tap_menor"] = (potencia_nominal * 1000) / (fator * tensao_at_tap_menor)
        else:
            data_to_process["corrente_nominal_at_tap_menor"] = None
    else:
        data_to_process["corrente_nominal_at_tap_maior"] = None
        data_to_process["corrente_nominal_at_tap_menor"] = None

    # 3. Calcular impedância base e indutância de curto-circuito (Seção 2.3)
    potencia_mva = data_to_process.get("potencia_mva") or 0
    tensao_at = data_to_process.get("tensao_at") or 0
    impedancia_percentual = data_to_process.get("impedancia") or 0
    frequencia = data_to_process.get("frequencia") or 60

    z_base_at = (tensao_at**2 * 1000) / potencia_mva if potencia_mva and potencia_mva > const.EPSILON else 0 # Ω
    z_cc_ohm = z_base_at * (impedancia_percentual / 100) if z_base_at > 0 else 0 # Ω
    l_cc_henries = z_cc_ohm / (2 * const.PI * frequencia) if z_cc_ohm > 0 and frequencia and frequencia > 0 else 0 # H

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