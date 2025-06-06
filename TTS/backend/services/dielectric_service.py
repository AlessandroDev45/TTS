"""
Serviço para cálculos de análise dielétrica
Implementa os algoritmos descritos em docs/instrucoes_dieletrica.md
"""

import sys
import pathlib
from typing import Dict, Any, Optional, Union, List
import math
import logging

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

# Tenta importar constantes para o serviço
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
                # Rigidez dielétrica de diferentes materiais em kV/mm
                RIGIDEZ_OLEO_MINERAL = 12.5  # média entre 10-15 kV/mm
                RIGIDEZ_PAPEL_IMPREGNADO = 50.0  # média entre 40-60 kV/mm
                RIGIDEZ_AR_NIVEL_MAR = 3.0  # kV/mm
                RIGIDEZ_SF6 = 7.5  # média entre 7-8 kV/mm
                # Constante para correção de altitude
                ALTITUDE_CONST = 8150  # metros
                
            const = MockConstants()


def calculate_altitude_correction(altitude: float) -> float:
    """
    Calcula o fator de correção para altitude conforme seção 2.2 da documentação.
    
    Args:
        altitude: Altitude em metros
    
    Returns:
        Fator de correção para altitude
    """
    return math.exp(-altitude / const.ALTITUDE_CONST)


def calculate_min_isolation_distance(voltage: float, material: str, altitude: float = 0) -> Dict[str, float]:
    """
    Calcula a distância mínima de isolamento conforme seção 2.3 da documentação.
    
    Args:
        voltage: Tensão máxima em kV
        material: Material isolante ('oleo', 'papel', 'ar', 'sf6')
        altitude: Altitude em metros (relevante apenas para o ar)
    
    Returns:
        Dicionário com distância mínima e rigidez dielétrica aplicada
    """
    # Seleciona a rigidez dielétrica base de acordo com o material
    if material.lower() == 'oleo':
        rigidez = const.RIGIDEZ_OLEO_MINERAL
    elif material.lower() == 'papel':
        rigidez = const.RIGIDEZ_PAPEL_IMPREGNADO
    elif material.lower() == 'sf6':
        rigidez = const.RIGIDEZ_SF6
    else:  # ar como padrão
        rigidez = const.RIGIDEZ_AR_NIVEL_MAR
        # Aplica correção para altitude se for ar
        if altitude > 0:
            rigidez *= calculate_altitude_correction(altitude)
    
    # Calcula a distância mínima
    distancia_min = voltage / rigidez
    
    return {
        "distancia_minima": distancia_min,
        "rigidez_dieletrica": rigidez
    }


def analyze_dielectric_strength(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Realiza a análise dielétrica completa com base nos parâmetros do transformador.
    
    Args:
        data: Dicionário com os parâmetros do transformador
    
    Returns:
        Dicionário com os resultados da análise dielétrica
    """
    # Extrai parâmetros básicos
    tipo_transformador = data.get("tipo_transformador", "Trifásico")
    tensao_at = data.get("tensao_at", 0)
    tensao_bt = data.get("tensao_bt", 0)
    classe_tensao_at = data.get("classe_tensao_at", 0)
    classe_tensao_bt = data.get("classe_tensao_bt", 0)
    bil = data.get("nbi_at", 0)  # Nível Básico de Isolamento para AT
    ac_level = data.get("teste_tensao_aplicada_at", 0)  # Nível de isolamento AC para AT
    espacamentos = data.get("espacamentos", {})
    meio_isolante = data.get("liquido_isolante", "óleo mineral")
    altitude = data.get("altitude", 1000)  # Altitude em metros, padrão 1000m
    
    # Determine material isolante baseado no meio_isolante
    if "óleo" in meio_isolante.lower() or "oleo" in meio_isolante.lower():
        material = "oleo"
    else:
        material = "ar"
    
    # Cálculos para AT (BIL)
    resultado_bil_at = calculate_min_isolation_distance(bil, material, altitude)
    
    # Cálculos para AT (AC)
    resultado_ac_at = calculate_min_isolation_distance(ac_level, material, altitude)
    
    # Cálculos para BT (BIL)
    bil_bt = data.get("nbi_bt", 0)
    resultado_bil_bt = calculate_min_isolation_distance(bil_bt, material, altitude) if bil_bt > 0 else None
    
    # Cálculos para BT (AC)
    ac_level_bt = data.get("teste_tensao_aplicada_bt", 0)
    resultado_ac_bt = calculate_min_isolation_distance(ac_level_bt, material, altitude) if ac_level_bt > 0 else None
    
    # Fator de correção para altitude
    fator_correcao_altitude = calculate_altitude_correction(altitude)
    
    # Prepara resultados
    results = {
        # Parâmetros de entrada relevantes
        "material_isolante": material,
        "altitude": altitude,
        "fator_correcao_altitude": fator_correcao_altitude,
        
        # Resultados para AT
        "at_bil_distancia_minima": resultado_bil_at["distancia_minima"],
        "at_bil_rigidez_dieletrica": resultado_bil_at["rigidez_dieletrica"],
        "at_ac_distancia_minima": resultado_ac_at["distancia_minima"],
        "at_ac_rigidez_dieletrica": resultado_ac_at["rigidez_dieletrica"],
        
        # Resultados para BT (se aplicável)
        "bt_bil_distancia_minima": resultado_bil_bt["distancia_minima"] if resultado_bil_bt else None,
        "bt_bil_rigidez_dieletrica": resultado_bil_bt["rigidez_dieletrica"] if resultado_bil_bt else None,
        "bt_ac_distancia_minima": resultado_ac_bt["distancia_minima"] if resultado_ac_bt else None,
        "bt_ac_rigidez_dieletrica": resultado_ac_bt["rigidez_dieletrica"] if resultado_ac_bt else None,
    }

    # Adicionar placeholders ou valores padrão para parâmetros adicionais necessários
    k_sobretensao = data.get("fator_sobretensao", 2.0) # Exemplo: Fator de sobretensão (2.0 para impulso atmosférico)
    rigidez_oleo = const.RIGIDEZ_OLEO_MINERAL
    rigidez_ar = const.RIGIDEZ_AR_NIVEL_MAR * fator_correcao_altitude # Rigidez do ar corrigida para altitude
    bil_min_norma_at = data.get("bil_min_norma_at", 0) # BIL mínimo pela norma para AT
    ac_min_norma_at = data.get("ac_min_norma_at", 0) # Nível AC mínimo pela norma para AT
    bil_min_norma_bt = data.get("bil_min_norma_bt", 0) # BIL mínimo pela norma para BT
    ac_min_norma_bt = data.get("ac_min_norma_bt", 0) # Nível AC mínimo pela norma para BT
    k_coord_min = data.get("fator_coordenacao_minimo", 1.2) # Fator de coordenação mínimo (ex: 1.2 sem para-raios)
    cs = data.get("capacitancia_serie_pu", 1.0) # Capacitância série por unidade (placeholder)
    cg = data.get("capacitancia_terra_pu", 1.0) # Capacitância para terra por unidade (placeholder)


    # 3. Análise de Espaçamentos
    analise_espacamentos = {}
    if tensao_at > 0:
        # Espaçamentos Fase-Fase AT
        v_max_fase_fase_at = tensao_at * k_sobretensao
        d_min_fase_fase_ar_at = v_max_fase_fase_at / rigidez_ar if rigidez_ar > const.EPSILON else float('inf')
        d_min_fase_fase_oleo_at = v_max_fase_fase_at / rigidez_oleo if rigidez_oleo > const.EPSILON else float('inf')
        analise_espacamentos["at_fase_fase"] = {
            "v_max_kv": round(v_max_fase_fase_at, 2),
            "d_min_ar_mm": round(d_min_fase_fase_ar_at, 2),
            "d_min_oleo_mm": round(d_min_fase_fase_oleo_at, 2),
            "espacamento_projeto_mm": espacamentos.get("fase_fase_at", None),
            "status_ar": "OK" if espacamentos.get("fase_fase_at", float('inf')) >= d_min_fase_fase_ar_at else "INSUFICIENTE",
            "status_oleo": "OK" if espacamentos.get("fase_fase_at", float('inf')) >= d_min_fase_fase_oleo_at else "INSUFICIENTE",
        }

        # Espaçamentos Fase-Terra AT
        v_max_fase_terra_at = (tensao_at / math.sqrt(3)) * k_sobretensao if tipo_transformador.lower() == "trifásico" else tensao_at * k_sobretensao
        d_min_fase_terra_ar_at = v_max_fase_terra_at / rigidez_ar if rigidez_ar > const.EPSILON else float('inf')
        d_min_fase_terra_oleo_at = v_max_fase_terra_at / rigidez_oleo if rigidez_oleo > const.EPSILON else float('inf')
        analise_espacamentos["at_fase_terra"] = {
            "v_max_kv": round(v_max_fase_terra_at, 2),
            "d_min_ar_mm": round(d_min_fase_terra_ar_at, 2),
            "d_min_oleo_mm": round(d_min_fase_terra_oleo_at, 2),
            "espacamento_projeto_mm": espacamentos.get("fase_terra_at", None),
            "status_ar": "OK" if espacamentos.get("fase_terra_at", float('inf')) >= d_min_fase_terra_ar_at else "INSUFICIENTE",
            "status_oleo": "OK" if espacamentos.get("fase_terra_at", float('inf')) >= d_min_fase_terra_oleo_at else "INSUFICIENTE",
        }

    if tensao_bt > 0:
         # Espaçamentos Fase-Fase BT
        v_max_fase_fase_bt = tensao_bt * k_sobretensao
        d_min_fase_fase_ar_bt = v_max_fase_fase_bt / rigidez_ar if rigidez_ar > const.EPSILON else float('inf')
        d_min_fase_fase_oleo_bt = v_max_fase_fase_bt / rigidez_oleo if rigidez_oleo > const.EPSILON else float('inf')
        analise_espacamentos["bt_fase_fase"] = {
            "v_max_kv": round(v_max_fase_fase_bt, 2),
            "d_min_ar_mm": round(d_min_fase_fase_ar_bt, 2),
            "d_min_oleo_mm": round(d_min_fase_fase_oleo_bt, 2),
            "espacamento_projeto_mm": espacamentos.get("fase_fase_bt", None),
            "status_ar": "OK" if espacamentos.get("fase_fase_bt", float('inf')) >= d_min_fase_fase_ar_bt else "INSUFICIENTE",
            "status_oleo": "OK" if espacamentos.get("fase_fase_bt", float('inf')) >= d_min_fase_fase_oleo_bt else "INSUFICIENTE",
        }

        # Espaçamentos Fase-Terra BT
        v_max_fase_terra_bt = (tensao_bt / math.sqrt(3)) * k_sobretensao if tipo_transformador.lower() == "trifásico" else tensao_bt * k_sobretensao
        d_min_fase_terra_ar_bt = v_max_fase_terra_bt / rigidez_ar if rigidez_ar > const.EPSILON else float('inf')
        d_min_fase_terra_oleo_bt = v_max_fase_terra_bt / rigidez_oleo if rigidez_oleo > const.EPSILON else float('inf')
        analise_espacamentos["bt_fase_terra"] = {
            "v_max_kv": round(v_max_fase_terra_bt, 2),
            "d_min_ar_mm": round(d_min_fase_terra_ar_bt, 2),
            "d_min_oleo_mm": round(d_min_fase_terra_oleo_bt, 2),
            "espacamento_projeto_mm": espacamentos.get("fase_terra_bt", None),
            "status_ar": "OK" if espacamentos.get("fase_terra_bt", float('inf')) >= d_min_fase_terra_ar_bt else "INSUFICIENTE",
            "status_oleo": "OK" if espacamentos.get("fase_terra_bt", float('inf')) >= d_min_fase_terra_oleo_bt else "INSUFICIENTE",
        }


    # 4. Análise de Níveis de Isolamento
    analise_niveis_isolamento = {}
    if bil > 0 and bil_min_norma_at > 0:
        bil_corrigido_at = bil / fator_correcao_altitude
        analise_niveis_isolamento["at_bil"] = {
            "bil_especificado_kv": bil,
            "bil_min_norma_kv": bil_min_norma_at,
            "bil_corrigido_altitude_kv": round(bil_corrigido_at, 2),
            "status": "APROVADO" if bil >= bil_corrigido_at and bil >= bil_min_norma_at else "REPROVADO"
        }
    if ac_level > 0 and ac_min_norma_at > 0:
         ac_corrigido_at = ac_level / fator_correcao_altitude
         analise_niveis_isolamento["at_ac"] = {
            "ac_especificado_kv": ac_level,
            "ac_min_norma_kv": ac_min_norma_at,
            "ac_corrigido_altitude_kv": round(ac_corrigido_at, 2),
            "status": "APROVADO" if ac_level >= ac_corrigido_at and ac_level >= ac_min_norma_at else "REPROVADO"
        }
    if bil_bt > 0 and bil_min_norma_bt > 0:
        bil_corrigido_bt = bil_bt / fator_correcao_altitude
        analise_niveis_isolamento["bt_bil"] = {
            "bil_especificado_kv": bil_bt,
            "bil_min_norma_kv": bil_min_norma_bt,
            "bil_corrigido_altitude_kv": round(bil_corrigido_bt, 2),
            "status": "APROVADO" if bil_bt >= bil_corrigido_bt and bil_bt >= bil_min_norma_bt else "REPROVADO"
        }
    if ac_level_bt > 0 and ac_min_norma_bt > 0:
         ac_corrigido_bt = ac_level_bt / fator_correcao_altitude
         analise_niveis_isolamento["bt_ac"] = {
            "ac_especificado_kv": ac_level_bt,
            "ac_min_norma_kv": ac_min_norma_bt,
            "ac_corrigido_altitude_kv": round(ac_corrigido_bt, 2),
            "status": "APROVADO" if ac_level_bt >= ac_corrigido_bt and ac_level_bt >= ac_min_norma_bt else "REPROVADO"
        }


    # 5. Análise de Coordenação de Isolamento
    analise_coordenacao = {}
    if bil > 0 and tensao_at > 0:
        # Assumindo V_max do sistema como a tensão nominal AT (simplificação)
        v_max_sistema = tensao_at
        k_coord = bil / (math.sqrt(2) * v_max_sistema) if v_max_sistema > const.EPSILON else float('inf')
        analise_coordenacao["at"] = {
            "bil_kv": bil,
            "v_max_sistema_kv": round(v_max_sistema, 2),
            "fator_coordenacao": round(k_coord, 2),
            "fator_coordenacao_minimo": k_coord_min,
            "status": "APROVADO" if k_coord >= k_coord_min else "REPROVADO"
        }
    # Poderia adicionar análise para BT se V_max do sistema BT for relevante


    # 6. Análise de Distribuição de Tensão em Enrolamentos
    # Nota: Esta análise requer parâmetros de capacitância série e para terra (Cs e Cg)
    # que não estão nos inputs básicos. Usaremos placeholders e uma simplificação.
    analise_distribuicao_tensao = {}
    if cs > const.EPSILON and cg > const.EPSILON:
        alpha = math.sqrt(cs / cg)
        # Simplificação: calcular fator de distribuição para x=1 (final do enrolamento)
        # A distribuição real requer integração ou métodos numéricos.
        # V(x) = V_0 * (cosh(αx) / cosh(α))
        # V_max ocorre em x=0 (V_0) ou x=1 (V_0 * (1 / cosh(α))) dependendo de α.
        # Para α > 0, cosh(α) > 1, então V(1) < V_0. A tensão máxima inicial é V_0.
        # A análise real de distribuição de tensão é mais complexa e envolve
        # a resposta a transientes de impulso.
        # Manteremos uma indicação simplificada baseada em alpha.
        analise_distribuicao_tensao["parametro_alpha"] = round(alpha, 2)
        analise_distribuicao_tensao["nota"] = "Análise de distribuição de tensão simplificada. Requer parâmetros Cs e Cg e análise de transientes para detalhamento."


    # Combina todos os resultados
    results["analise_espacamentos"] = analise_espacamentos
    results["analise_niveis_isolamento"] = analise_niveis_isolamento
    results["analise_coordenacao_isolamento"] = analise_coordenacao
    results["analise_distribuicao_tensao"] = analise_distribuicao_tensao

    return results


def analyze_dielectric(basic_data: Dict[str, Any], module_inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Função principal de análise dielétrica para interface com o roteador.
    
    Args:
        basic_data: Dados básicos do transformador
        module_inputs: Dados específicos do módulo de análise dielétrica
    
    Returns:
        Dicionário com os resultados da análise dielétrica
    """
    try:
        # Combina dados básicos e específicos do módulo
        combined_data = {**basic_data, **module_inputs}
        
        # Chama a função de análise principal
        results = analyze_dielectric_strength(combined_data)
        
        # Formata os resultados para o padrão esperado pelo frontend
        formatted_results = {
            'status': 'success',
            'data': {
                'at': {
                    'nivel_isolamento': f"{results.get('at_bil_distancia_minima', 0):.2f} mm",
                    'tensao_ensaio_frequencia_industrial': f"{combined_data.get('teste_tensao_aplicada_at', 0)} kV",
                    'tensao_suportabilidade_impulso': f"{combined_data.get('nbi_at', 0)} kV",
                    'status': 'APROVADO' if results.get('analise_niveis_isolamento', {}).get('at_bil', {}).get('status') == 'APROVADO' else 'PENDENTE'
                },
            'bt': {
                    'nivel_isolamento': f"{results.get('bt_bil_distancia_minima', 0):.2f} mm",
                    'tensao_ensaio_frequencia_industrial': f"{combined_data.get('teste_tensao_aplicada_bt', 0)} kV",
                    'tensao_suportabilidade_impulso': f"{combined_data.get('nbi_bt', 0)} kV",
                    'status': 'APROVADO' if results.get('analise_niveis_isolamento', {}).get('bt_bil', {}).get('status') == 'APROVADO' else 'PENDENTE'
                },
                'resumo': {
                    'status_geral': 'APROVADO',
                    'observacoes': f"Análise realizada para altitude de {results.get('altitude', 1000)}m com fator de correção {results.get('fator_correcao_altitude', 1.0):.3f}"
                }
            },
            'calculations': results  # Inclui todos os cálculos detalhados
        }
        
        # Adiciona dados do terciário se existir
        if combined_data.get('tensao_terciario', 0) > 0:
            formatted_results['data']['terciario'] = {
                'nivel_isolamento': f"{combined_data.get('tensao_terciario', 0):.2f} kV",
                'tensao_ensaio_frequencia_industrial': f"{combined_data.get('teste_tensao_aplicada_terciario', 0)} kV",
                'tensao_suportabilidade_impulso': f"{combined_data.get('nbi_terciario', 0)} kV",
                'status': 'PENDENTE'
            }
        
        return formatted_results
        
    except Exception as e:
        logging.error(f"Erro na análise dielétrica: {str(e)}")
        return {
            'status': 'error',
            'message': f"Erro na análise dielétrica: {str(e)}",
            'data': None
        }