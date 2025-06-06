# backend/services/transformer_service.py

import logging
import sys
import os
import pathlib
import math # Importar math para PI e sqrt
import json # Importar json para ler o arquivo tabela.json
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
    # Em caso de falha crítica na importação, re-raise o erro ou defina mocks que falhem explicitamente
    # Para fins de depuração, vamos definir mocks que loggam o uso e retornam None/valores padrão
    class MockConstants:
        IAC_NBI_FACTOR = 3.5
        EPSILON = 1e-6
        SQRT_3 = 1.732050807568877
        PI = 3.141592653589793

    const = MockConstants()

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

def calculate_nominal_currents(data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calcula as correntes nominais conforme seção 2.1 da documentação,
    incluindo o lado terciário.
    
    Args:
        data: Dicionário com os parâmetros do transformador
    
    Returns:
        Dicionário com as correntes nominais calculadas
    """
    potencia_nominal = data.get("potencia_mva", 0)
    tensao_at = data.get("tensao_at", 0)
    tensao_bt = data.get("tensao_bt", 0)
    tensao_terciario = data.get("tensao_terciario", 0)
    tipo_transformador = data.get("tipo_transformador", "Trifásico")
    
    if potencia_nominal <= 0:
        log.error("Potência nominal (potencia_mva) deve ser maior que zero para calcular correntes nominais.")
        return {}

    fator = 1.0 if tipo_transformador.lower() == "monofásico" else const.SQRT_3
    
    def calculate_current(voltage, voltage_name):
        if voltage is None or voltage <= 0:
            log.warning(f"Tensão {voltage_name} deve ser maior que zero para calcular a corrente nominal.")
            return 0
        return (potencia_nominal * 1000) / (fator * voltage)

    i_nom_at = calculate_current(tensao_at, "AT")
    i_nom_bt = calculate_current(tensao_bt, "BT")
    i_nom_ter = calculate_current(tensao_terciario, "Terciário")

    tensao_at_tap_maior = data.get("tensao_at_tap_maior")
    tensao_at_tap_menor = data.get("tensao_at_tap_menor")

    i_nom_at_tap_maior = calculate_current(tensao_at_tap_maior, "AT Tap Maior") if tensao_at_tap_maior is not None and tensao_at_tap_maior > 0 else 0
    i_nom_at_tap_menor = calculate_current(tensao_at_tap_menor, "AT Tap Menor") if tensao_at_tap_menor is not None and tensao_at_tap_menor > 0 else 0

    return {
        "i_nom_at": i_nom_at,
        "i_nom_bt": i_nom_bt,
        "i_nom_ter": i_nom_ter,
        "i_nom_at_tap_maior": i_nom_at_tap_maior,
        "i_nom_at_tap_menor": i_nom_at_tap_menor
    }

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

    data_to_process["corrente_nominal_at"] = calculated_currents.get("i_nom_at")
    data_to_process["corrente_nominal_bt"] = calculated_currents.get("i_nom_bt")
    data_to_process["corrente_nominal_terciario"] = calculated_currents.get("i_nom_ter")
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

def get_connection_types_info() -> Dict[str, Any]:
    """
    Fornece informações sobre os tipos de conexão e suas implicações (Seção 3).
    Esta função não importa módulos externos.
    """
    return {
        "conexoes_principais": {
            "estrela": {
                "nome": "Estrela (Y)",
                "descricao": "Os enrolamentos são conectados em um ponto comum (neutro). Adequada para alta tensão."
            },
            "estrela_aterrada": {
                "nome": "Estrela Aterrada (Yn)",
                "descricao": "Conexão estrela com o neutro aterrado. Requer bucha de neutro."
            },
            "triangulo": {
                "nome": "Triângulo (D)",
                "descricao": "Os enrolamentos formam um circuito fechado. Adequada para baixa tensão."
            },
            "zigue_zague": {
                "nome": "Zigue-Zague (Z)",
                "descricao": "Conexão especial que oferece melhor distribuição de fluxo magnético."
            }
        },
        "implicacoes_das_conexoes": {
            "estrela": {
                "nome": "Estrela (Y/Yn)",
                "tensao_fase": "Tensão de linha / √3",
                "corrente_fase": "Corrente de linha",
                "observacao": "Requer campos de dados para bucha de neutro quando Yn"
            },
            "triangulo": {
                "nome": "Triângulo (D)",
                "tensao_fase": "Tensão de linha",
                "corrente_fase": "Corrente de linha / √3",
                "observacao": "Não possui neutro acessível"
            }
        },
        "grupo_ligacao": {
            "descricao": "O grupo de ligação (ex: Dyn11, YNd5) indica:",
            "componentes": [
                "Conexão do lado AT (maiúscula: D, Y, YN, Z, ZN)",
                "Conexão do lado BT (minúscula: d, y, yn, z, zn)",
                "Defasamento angular (número: 0, 5, 6, 11, 15)"
            ]
        }
    }

def calculate_impedances(data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calcula as impedâncias de curto-circuito conforme seção 2.2 da documentação.
    """
    potencia_nominal = data.get("potencia_mva", 0)
    tensao_at = data.get("tensao_at", 0)
    tensao_bt = data.get("tensao_bt", 0)
    tensao_terciario = data.get("tensao_terciario", 0)
    imped_percent = data.get("impedancia", 0)
    z_pu = imped_percent / 100
    z_ohm_at = z_pu * (tensao_at**2 * 1000) / potencia_nominal if potencia_nominal > 0 else 0
    z_ohm_bt = z_pu * (tensao_bt**2 * 1000) / potencia_nominal if potencia_nominal > 0 else 0
    z_ohm_ter = z_pu * (tensao_terciario**2 * 1000) / potencia_nominal if potencia_nominal > 0 else 0
    return {"z_pu": z_pu, "z_ohm_at": z_ohm_at, "z_ohm_bt": z_ohm_bt, "z_ohm_ter": z_ohm_ter}

def calculate_symmetric_short_circuit_current(data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calcula a corrente de curto-circuito simétrica conforme seção 2.3.
    """
    potencia_nominal = data.get("potencia_mva", 0)
    potencia_cc_rede = data.get("potencia_cc_rede", 0)
    z_trafo_pu = data.get("impedancia", 0) / 100
    z_rede_pu = potencia_nominal / potencia_cc_rede if potencia_cc_rede > 0 else 0
    z_total_pu = z_trafo_pu + z_rede_pu
    nominal = calculate_nominal_currents(data)
    i_nom_at = nominal.get("i_nom_at", 0)
    i_nom_bt = nominal.get("i_nom_bt", 0)
    i_nom_ter = nominal.get("i_nom_ter", 0)
    i_cc_sim_at = i_nom_at / z_total_pu if z_total_pu > 0 else float('inf')
    i_cc_sim_bt = i_nom_bt / z_total_pu if z_total_pu > 0 else float('inf')
    i_cc_sim_ter = i_nom_ter / z_total_pu if z_total_pu > 0 else float('inf')
    return {"i_cc_sim_at": i_cc_sim_at, "i_cc_sim_bt": i_cc_sim_bt, "i_cc_sim_ter": i_cc_sim_ter,
            "z_trafo_pu": z_trafo_pu, "z_rede_pu": z_rede_pu, "z_total_pu": z_total_pu}

def get_insulation_levels_info() -> Dict[str, Any]:
    """
    Fornece informações sobre os níveis de isolamento (Seção 4), lendo de tabela.json.
    Esta função não importa módulos externos além de json.
    """
    insulation_data = {
        "nbi_bil": {
            "descricao": "O NBI (Nível Básico de Impulso) ou BIL (Basic Impulse Level) é a tensão suportável de impulso atmosférico (1.2/50 μs) que o equipamento deve suportar. Os valores são padronizados conforme a classe de tensão:",
            "valores_iec_nbr": [],
            "valores_ieee": []
        },
        "im_sil": {
            "descricao": "O IM (Impulso de Manobra) ou SIL (Switching Impulse Level) é a tensão suportável de impulso de manobra (250/2500 μs) que o equipamento deve suportar. É relevante principalmente para classes de tensão acima de 170 kV:",
            "valores_iec_nbr": [],
            "valores_ieee": []
        },
        "tensao_aplicada": {
            "descricao": "A tensão aplicada é o valor eficaz da tensão senoidal (60 Hz) aplicada durante o ensaio dielétrico de tensão aplicada. Os valores são padronizados conforme a classe de tensão:",
            "valores_iec_nbr": [],
            "valores_ieee": []
        },
        "tensao_induzida": {
            "descricao": "A tensão induzida é o valor eficaz da tensão aplicada durante o ensaio dielétrico de tensão induzida. Os valores são padronizados conforme a classe de tensão e divididos em dois tipos principais:",
            "acsd": {
                "descricao": "ACSD (Tensão Induzida de Curta Duração) - Aplicada por 60 segundos. Geralmente utilizada para transformadores com Um ≤ 170 kV."
            },
            "acld": {
                "descricao": "ACLD (Tensão Induzida de Longa Duração) - Aplicada por 30 minutos (Um < 300 kV) ou 60 minutos (Um ≥ 300 kV). Obrigatória para transformadores com Um > 170 kV. Realizada com frequência elevada (tipicamente 100-200 Hz). Inclui medição de descargas parciais."
            },
            "valores_iec_nbr": [],
            "valores_ieee": [],
            "formulas_calculo": {
                "acsd_fase_terra_iec_nbr": "U_teste = valor tabelado (acsd_kv_rms)",
                "acsd_fase_fase_iec_nbr": "U_teste = valor tabelado (acsd_kv_rms)",
                "acld_iec_nbr": "U_teste = valor tabelado (acld_kv_rms)",
                "niveis_dp": {
                    "u_pre": "1.1 × Um/√3 (tensão de pré-estresse)",
                    "u2": "1.5 × Um/√3 (tensão de medição)"
                }
            }
        }
    }

    json_file_path = pathlib.Path(__file__).parent.parent.parent / "public" / "assets" / "tabela.json"
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            insulation_levels = data.get("insulation_levels", [])

            for level in insulation_levels:
                um_kv = level.get("um_kv")
                standard = level.get("standard")

                # NBI / BIL
                if level.get("bil_kvp") is not None:
                    entry = {"classe_tensao_kv": um_kv, "nbi_bil_tipico_kvp": level["bil_kvp"]}
                    if standard == "IEC/NBR":
                        insulation_data["nbi_bil"]["valores_iec_nbr"].append(entry)
                    elif standard == "IEEE":
                        insulation_data["nbi_bil"]["valores_ieee"].append(entry)

                # IM / SIL
                if level.get("sil_kvp") is not None:
                    entry = {"classe_tensao_kv": um_kv, "im_sil_tipico_kvp": level["sil_kvp"]}
                    if standard == "IEC/NBR":
                        insulation_data["im_sil"]["valores_iec_nbr"].append(entry)
                    elif standard == "IEEE":
                        # IEEE usa BSL para Switching Impulse Level
                        if level.get("bsl_kvp") is not None:
                            entry = {"classe_tensao_kv": um_kv, "im_sil_tipico_kvp": level["bsl_kvp"]}
                            insulation_data["im_sil"]["valores_ieee"].append(entry)

                # Tensão Aplicada
                if level.get("acsd_kv_rms") is not None:
                    entry = {"classe_tensao_kv": um_kv, "tensao_aplicada_tipica_kv_rms": level["acsd_kv_rms"]}
                    if standard == "IEC/NBR":
                        insulation_data["tensao_aplicada"]["valores_iec_nbr"].append(entry)
                    elif standard == "IEEE":
                        insulation_data["tensao_aplicada"]["valores_ieee"].append(entry)

                # Tensão Induzida
                # ACSD
                if level.get("acsd_kv_rms") is not None:
                    entry = {"classe_tensao_kv": um_kv, "tensao_induzida_acsd_kv_rms": level["acsd_kv_rms"]}
                    if standard == "IEC/NBR":
                        insulation_data["tensao_induzida"]["valores_iec_nbr"].append(entry)
                    elif standard == "IEEE":
                        insulation_data["tensao_induzida"]["valores_ieee"].append(entry)
                # ACLD
                if level.get("acld_kv_rms") is not None:
                    entry = {"classe_tensao_kv": um_kv, "tensao_induzida_acld_kv_rms": level["acld_kv_rms"]}
                    if standard == "IEC/NBR":
                        # Adiciona apenas se já não tiver sido adicionado pelo ACSD para a mesma classe
                        if not any(d.get("classe_tensao_kv") == um_kv and "tensao_induzida_acld_kv_rms" in d for d in insulation_data["tensao_induzida"]["valores_iec_nbr"]):
                            insulation_data["tensao_induzida"]["valores_iec_nbr"].append(entry)
                        else: # Atualiza o existente
                            for d in insulation_data["tensao_induzida"]["valores_iec_nbr"]:
                                if d.get("classe_tensao_kv") == um_kv:
                                    d["tensao_induzida_acld_kv_rms"] = level["acld_kv_rms"]
                    elif standard == "IEEE":
                        if not any(d.get("classe_tensao_kv") == um_kv and "tensao_induzida_acld_kv_rms" in d for d in insulation_data["tensao_induzida"]["valores_ieee"]):
                            insulation_data["tensao_induzida"]["valores_ieee"].append(entry)
                        else: # Atualiza o existente
                            for d in insulation_data["tensao_induzida"]["valores_ieee"]:
                                if d.get("classe_tensao_kv") == um_kv:
                                    d["tensao_induzida_acld_kv_rms"] = level["acld_kv_rms"]

    except FileNotFoundError:
        log.error(f"Arquivo tabela.json não encontrado em {json_file_path}")
    except json.JSONDecodeError:
        log.error(f"Erro ao decodificar JSON do arquivo {json_file_path}")
    except Exception as e:
        log.error(f"Erro inesperado ao ler tabela.json: {e}")

    return insulation_data

def calculate_asymmetric_short_circuit_current(data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calcula a corrente de curto-circuito assimétrica conforme seção 2.4.
    """
    fator_xr = data.get("fator_xr", 10)
    k_asym = math.sqrt(1 + 2 * math.exp(-math.pi / fator_xr))
    sym = calculate_symmetric_short_circuit_current(data)
    i_cc_sim_at = sym.get("i_cc_sim_at", 0)
    i_cc_sim_bt = sym.get("i_cc_sim_bt", 0)
    i_cc_sim_ter = sym.get("i_cc_sim_ter", 0)
    i_cc_asym_at = k_asym * math.sqrt(2) * i_cc_sim_at
    i_cc_asym_bt = k_asym * math.sqrt(2) * i_cc_sim_bt
    i_cc_asym_ter = k_asym * math.sqrt(2) * i_cc_sim_ter
    return {"k_asym": k_asym, "i_cc_asym_at": i_cc_asym_at,
            "i_cc_asym_bt": i_cc_asym_bt, "i_cc_asym_ter": i_cc_asym_ter}

def calculate_thermal_effects(data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calcula efeitos térmicos do curto-circuito conforme seção 2.5.
    """
    duracao_cc = data.get("duracao_cc", 1.0)
    sym = calculate_symmetric_short_circuit_current(data)
    i_cc_sim_at = sym.get("i_cc_sim_at", 0)
    i_cc_sim_bt = sym.get("i_cc_sim_bt", 0)
    i_cc_sim_ter = sym.get("i_cc_sim_ter", 0)
    i2t_at = (i_cc_sim_at**2) * duracao_cc
    i2t_bt = (i_cc_sim_bt**2) * duracao_cc
    i2t_ter = (i_cc_sim_ter**2) * duracao_cc
    r_at = data.get("resistencia_at", 0.1)
    r_bt = data.get("resistencia_bt", 0.01)
    r_ter = data.get("resistencia_ter", 0.005)
    Wth_at = r_at * i2t_at / 1000
    Wth_bt = r_bt * i2t_bt / 1000
    Wth_ter = r_ter * i2t_ter / 1000
    return {"duracao_cc": duracao_cc, "i_squared_t_at": i2t_at,
            "i_squared_t_bt": i2t_bt, "i_squared_t_ter": i2t_ter,
            "energia_termica_at": Wth_at, "energia_termica_bt": Wth_bt,
            "energia_termica_ter": Wth_ter}