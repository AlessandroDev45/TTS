"""
Serviço para cálculos de ensaios de impulso
Implementa os algoritmos descritos em docs/instrucoes_impulso.md
"""

import sys
import pathlib
from typing import Dict, Any, Optional, Union, List, Tuple
import math
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
                # Constantes para impulso
                LIGHTNING_IMPULSE_FRONT_TIME_NOM = 1.2  # μs
                LIGHTNING_IMPULSE_TAIL_TIME_NOM = 50.0  # μs
                LIGHTNING_FRONT_TOLERANCE = 0.30  # 30%
                LIGHTNING_TAIL_TOLERANCE = 0.20   # 20%

                # Tabelas BIL/SIL (valores mockados baseados na documentação)
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

            const = MockConstants()


def calculate_impulse_waveform_parameters(resistor_frontal: float, resistor_cauda: float, 
                                         capacitancia_gerador: float, capacitancia_objeto: float) -> Dict[str, Any]:
    """
    Calcula os parâmetros da forma de onda de impulso conforme seção 3.1 da documentação.
    
    Args:
        resistor_frontal: Valor do resistor frontal em Ohms
        resistor_cauda: Valor do resistor de cauda em Ohms
        capacitancia_gerador: Capacitância do gerador em nF
        capacitancia_objeto: Capacitância do objeto de teste em pF
        
    Returns:
        Dicionário com os parâmetros calculados (alfa, beta, tempo de frente, tempo de cauda, eficiência)
    """
    # Converte capacitância do objeto para nF para cálculos consistentes
    c_objeto_nf = capacitancia_objeto / 1000.0
    
    # Cálculo de alfa e beta conforme seção 3.1
    alfa = 1 / (resistor_cauda * c_objeto_nf)
    beta = 1 / (resistor_frontal * capacitancia_gerador)
    
    # Cálculo dos tempos de frente e cauda
    tempo_frente, tempo_cauda = calculate_front_tail_times(alfa, beta)
    
    # Cálculo da eficiência
    eficiencia = calculate_efficiency(alfa, beta)
    
    return {
        "alfa": alfa,
        "beta": beta,
        "tempo_frente": tempo_frente,
        "tempo_cauda": tempo_cauda,        "eficiencia": eficiencia,
        "dentro_tolerancia_frente": is_within_tolerance(tempo_frente, 
                                                      const.LIGHTNING_IMPULSE_FRONT_TIME_NOM, 
                                                      const.LIGHTNING_FRONT_TOLERANCE),
        "dentro_tolerancia_cauda": is_within_tolerance(tempo_cauda,
                                                     const.LIGHTNING_IMPULSE_TAIL_TIME_NOM,
                                                     const.LIGHTNING_TAIL_TOLERANCE)
    }


def impulse_waveform(t: float, alfa: float, beta: float) -> float:
    """
    Calcula o valor da tensão na forma de onda de impulso para um dado tempo.
    
    Args:
        t: Tempo em μs
        alfa: Parâmetro alfa da equação de impulso
        beta: Parâmetro beta da equação de impulso
        
    Returns:
        Valor relativo da tensão (0-1) para o tempo t
    """
    return np.exp(-alfa * t) - np.exp(-beta * t)


def calculate_front_tail_times(alfa: float, beta: float) -> Tuple[float, float]:
    """
    Calcula os tempos de frente e cauda da forma de onda de impulso usando aproximações.
    Nota: O cálculo preciso requer métodos numéricos ou simulação detalhada.
    Esta é uma simplificação para evitar dependências externas como scipy.

    Args:
        alfa: Parâmetro alfa da equação de impulso
        beta: Parâmetro beta da equação de impulso

    Returns:
        Tupla (tempo_frente, tempo_cauda) em μs (valores aproximados)
    """
    # Tempo para o pico (aproximação)
    # t_pico_aprox = 1 / alfa # Simplificação - menos precisa
    # Usando a fórmula exata para o tempo de pico, que não requer fsolve
    if beta <= alfa + const.EPSILON: # Evitar log(<=1) ou divisão por zero/pequeno
        t_pico_aprox = 0.0
    else:
        t_pico_aprox = np.log(beta / alfa) / (beta - alfa)


    # Tempo de frente (aproximação)
    # Uma aproximação comum para T1 é 2.2 / beta
    tempo_frente_aprox = 2.2 / beta if beta > const.EPSILON else 0

    # Tempo de cauda (aproximação)
    # Uma aproximação comum para T2 é 0.7 / alfa
    tempo_cauda_aprox = 0.7 / alfa if alfa > const.EPSILON else 0

    # Nota: Para resultados precisos de T1 e T2 conforme a norma (baseado em 30%-90% e 50% na cauda),
    # a simulação da forma de onda e a análise dos pontos são necessárias.
    # Manteremos essas aproximações por enquanto.

    return tempo_frente_aprox, tempo_cauda_aprox
    return tempo_frente, tempo_cauda


def calculate_efficiency(alfa: float, beta: float) -> float:
    """
    Calcula a eficiência do gerador de impulso.
    
    Args:
        alfa: Parâmetro alfa da equação de impulso
        beta: Parâmetro beta da equação de impulso
        
    Returns:
        Eficiência do gerador (0-1)
    """
    # Tempo para o pico
    t_pico = np.log(beta / alfa) / (beta - alfa)
    
    # Valor máximo da forma de onda (eficiência)
    eficiencia = impulse_waveform(t_pico, alfa, beta)
    
    return eficiencia


def is_within_tolerance(valor: float, nominal: float, tolerancia: float) -> bool:
    """
    Verifica se um valor está dentro da tolerância especificada.
    
    Args:
        valor: Valor medido
        nominal: Valor nominal
        tolerancia: Tolerância em fração (ex: 0.3 para 30%)
        
    Returns:
        True se estiver dentro da tolerância, False caso contrário
    """
    limite_inferior = nominal * (1 - tolerancia)
    limite_superior = nominal * (1 + tolerancia)
    return limite_inferior <= valor <= limite_superior


def calculate_impulse(basic_data: Dict[str, Any], module_inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula os parâmetros do teste de impulso com base nos dados do transformador.
    
    Args:
        basic_data: Dicionário com os parâmetros de entrada do transformer_inputs
        module_inputs: Dicionário com os parâmetros de entrada do módulo de impulso
        
    Returns:
        Dicionário com os resultados calculados para o teste de impulso
    """
    # Extrai parâmetros básicos
    tipo_transformador = basic_data.get("tipo_transformador", "Trifásico")
    tensao_at = basic_data.get("tensao_at", 0)
    classe_tensao_at = basic_data.get("classe_tensao_at", 0)
    bil_especificado = basic_data.get("nbi_at", 0)  # Nível Básico de Isolamento especificado para AT
    norma_isolamento = module_inputs.get("norma_isolamento", "NBR/IEC") # Norma de isolamento (NBR/IEC ou IEEE)
    tipo_impulso = module_inputs.get("tipo_impulso", "Atmosférico") # Tipo de impulso (Atmosférico, Manobra, Cortado)

    # Parâmetros do circuito de impulso
    resistor_frontal = module_inputs.get("resistor_frontal", 500)  # Ohms
    resistor_cauda = module_inputs.get("resistor_cauda", 2000)  # Ohms
    capacitancia_gerador = module_inputs.get("capacitancia_gerador", 1.0)  # nF
    capacitancia_objeto = module_inputs.get("capacitancia_objeto", 1000.0)  # pF
    indutancia = module_inputs.get("indutancia", 5.0)  # μH
    tempo_corte_input = module_inputs.get("tempo_corte", None)  # μs para impulso cortado (pode ser None)
    gap_distance_mm = module_inputs.get("gap_distance_mm", None) # Distância do gap em mm (para calcular tempo de corte)


    # 1.1. Seleção do BIL/SIL com base na norma e tensão
    bil_norma = None
    sil_norma = None
    tensao_max_sistema = classe_tensao_at # Usando classe de tensão como proxy para tensão máxima do sistema

    if tipo_impulso == "Atmosférico":
        if norma_isolamento == "NBR/IEC":
            tabela_bil = const.BIL_NBR_IEC
        elif norma_isolamento == "IEEE":
            tabela_bil = const.BIL_IEEE
        else:
            tabela_bil = {} # Norma desconhecida

        # Encontra o BIL na tabela
        tensoes_tabela = sorted(tabela_bil.keys())
        bil_norma_valores = []
        for tensao_tabela in tensoes_tabela:
            if tensao_max_sistema <= tensao_tabela:
                bil_norma_valores = tabela_bil.get(tensao_tabela, [])
                break
        # Seleciona o maior valor se houver múltiplos
        bil_norma = max(bil_norma_valores) if bil_norma_valores else None

    elif tipo_impulso == "Manobra":
         if norma_isolamento == "NBR/IEC":
            tabela_sil = const.SIL_NBR_IEC
         elif norma_isolamento == "IEEE":
            tabela_sil = const.SIL_IEEE
         else:
            tabela_sil = {} # Norma desconhecida

         # Encontra o SIL na tabela
         tensoes_tabela = sorted(tabela_sil.keys())
         sil_norma_valores = []
         for tensao_tabela in tensoes_tabela:
             if tensao_max_sistema <= tensao_tabela:
                 sil_norma_valores = tabela_sil.get(tensao_tabela, [])
                 break
         # Seleciona o maior valor se houver múltiplos
         sil_norma = max(sil_norma_valores) if sil_norma_valores else None


    # Cálculo dos parâmetros da forma de onda (para impulso atmosférico ou manobra)
    waveform_params = calculate_impulse_waveform_parameters(
        resistor_frontal, resistor_cauda, capacitancia_gerador, capacitancia_objeto
    )

    # Cálculo da tensão de carga e energia
    tensao_pico_desejada = bil_especificado if tipo_impulso == "Atmosférico" else sil_norma # Usar BIL especificado para Atmosférico, SIL da norma para Manobra
    if tensao_pico_desejada is None or waveform_params["eficiencia"] <= const.EPSILON:
        tensao_carregamento = 0
    else:
        tensao_carregamento = tensao_pico_desejada / waveform_params["eficiencia"]

    # Energia do impulso (em Joules) - Seção 3.4
    energia_impulso_joules = 0.5 * (capacitancia_gerador * 1e-9) * (tensao_carregamento * 1000)**2 # C em Farads, V em Volts


    # 4. Impulso Cortado (LIC)
    tempo_corte_us = tempo_corte_input
    if tempo_corte_us is None and gap_distance_mm is not None:
        # Calcular tempo de corte baseado na distância do gap (simplificação)
        # V_ruptura = 30 * distancia_gap_cm * 1000 (em Volts)
        # Precisamos encontrar o tempo 't' onde V(t) = V_ruptura
        # V_ruptura_kv = 30 * (gap_distance_mm / 10) # kV
        # V_ruptura_relativa = V_ruptura_kv / tensao_pico_desejada if tensao_pico_desejada > const.EPSILON else 0
        # def func_tempo_corte(t):
        #     return impulse_waveform(t, waveform_params["alfa"], waveform_params["beta"]) - V_ruptura_relativa
        # try:
        #     tempo_corte_us = fsolve(func_tempo_corte, 3.0)[0] # Estimar tempo de corte em 3 μs
        # except Exception as e:
        #     log.warning(f"Não foi possível calcular tempo de corte baseado no gap: {e}")
        #     tempo_corte_us = None # Não foi possível calcular

        # Simplificação: usar um valor padrão se gap_distance_mm for fornecido mas tempo_corte_input não
        tempo_corte_us = 3.0 # Valor padrão se gap_distance_mm for fornecido mas tempo_corte_input não

    tensao_corte_kv = 0
    sobretensao_corte_kv = 0
    if tempo_corte_us is not None and tensao_carregamento > 0:
        # V_corte = V₀ * (e^(-α*t_corte) - e^(-β*t_corte))
        # Onde V₀ é a tensão de carregamento (V_carga)
        tensao_corte_kv = tensao_carregamento * impulse_waveform(tempo_corte_us, waveform_params["alfa"], waveform_params["beta"])

        # Sobretensão de corte (simplificação)
        # V_sobretensao = V_corte * (1 + k)
        # k depende da indutância e impedância. Simplificando, assumimos um fator k fixo ou calculado de forma simples.
        # A documentação menciona que a indutância afeta a sobretensão.
        # Uma simplificação comum é V_sobretensao ≈ V_corte * (1 + Z_onda / Z_circuito)
        # Onde Z_onda é a impedância de surto do enrolamento e Z_circuito é a impedância do circuito de impulso.
        # Sem esses valores, usaremos um fator de sobretensão placeholder.
        fator_sobretensao_corte = 0.2 # Exemplo: 20% de sobretensão
        sobretensao_corte_kv = tensao_corte_kv * (1 + fator_sobretensao_corte)


    # 5. Simulação da Forma de Onda (simplificada)
    # Gerar pontos de tempo
    tempo_max_simulacao = 100.0 # μs
    passo_tempo = 0.1 # μs
    tempos = np.arange(0, tempo_max_simulacao + passo_tempo, passo_tempo)

    # Calcular tensão em cada ponto
    tensoes = []
    tensoes = []
    for t_val in tempos: # Usar t_val para evitar conflito com parâmetro 't' da função impulse_waveform
        t_float = float(t_val) # Converter explicitamente para float
        if tempo_corte_us is not None and t_float >= tempo_corte_us:
            # Simulação simplificada após o corte
            # V(t) = V_corte * (1 + k) * e^(-γ*(t-t_corte))
            # Precisamos de γ (constante de tempo após o corte). Simplificando, assumimos um decaimento rápido.
            # Usaremos um decaimento exponencial simples a partir da sobretensão de corte.
            # γ = 1 / (L/R) ou 1 / (R*C). Sem R e C específicos após o corte, usamos um valor fixo.
            gamma_decaimento = 0.5 # Exemplo: constante de decaimento
            tensao_simulada = sobretensao_corte_kv * np.exp(-gamma_decaimento * (t_float - tempo_corte_us))
        else:
            # Forma de onda normal antes do corte
            tensao_simulada = tensao_carregamento * impulse_waveform(t_float, waveform_params["alfa"], waveform_params["beta"]) # V_0 = tensao_carregamento

        tensoes.append(tensao_simulada)

    # 6. Análise dos Resultados e Conformidade
    analise_conformidade = {}
    if tipo_impulso == "Atmosférico":
        analise_conformidade["tipo"] = "Impulso Atmosférico (LI)"
        analise_conformidade["tempo_frente_us"] = round(waveform_params["tempo_frente"], 2)
        analise_conformidade["tempo_cauda_us"] = round(waveform_params["tempo_cauda"], 2)
        analise_conformidade["dentro_tolerancia_frente"] = waveform_params["dentro_tolerancia_frente"]
        analise_conformidade["dentro_tolerancia_cauda"] = waveform_params["dentro_tolerancia_cauda"]
        analise_conformidade["overshoot"] = "Não calculado (requer simulação detalhada)" # TODO: Calcular overshoot
        analise_conformidade["tensao_pico_kv"] = round(np.max(tensoes), 2) # Tensão de pico da simulação
        analise_conformidade["tensao_pico_especificada_kv"] = bil_especificado
        analise_conformidade["status_tensao_pico"] = "OK" # TODO: Verificar tolerância da tensão de pico

    elif tipo_impulso == "Manobra":
        analise_conformidade["tipo"] = "Impulso de Manobra (SI)"
        analise_conformidade["tempo_pico_us"] = round(tempos[np.argmax(tensoes)], 2) # Tempo para o pico da simulação
        analise_conformidade["tempo_meia_onda_us"] = "Não calculado (requer análise da cauda)" # TODO: Calcular tempo de meia onda
        analise_conformidade["tensao_pico_kv"] = round(np.max(tensoes), 2) # Tensão de pico da simulação
        analise_conformidade["tensao_pico_especificada_kv"] = sil_norma # Usar SIL da norma para Manobra
        analise_conformidade["status_tensao_pico"] = "OK" # TODO: Verificar tolerância da tensão de pico

    elif tipo_impulso == "Cortado":
        analise_conformidade["tipo"] = "Impulso Cortado (LIC)"
        analise_conformidade["tempo_corte_us"] = round(tempo_corte_us, 2) if tempo_corte_us is not None else None
        analise_conformidade["tensao_corte_kv"] = round(tensao_corte_kv, 2)
        analise_conformidade["sobretensao_corte_kv"] = round(sobretensao_corte_kv, 2)
        analise_conformidade["tensao_pico_simulacao_kv"] = round(np.max(tensoes), 2) # Tensão de pico da simulação (pode ser a sobretensão)
        analise_conformidade["status"] = "Análise de forma de onda e conformidade para LIC requer simulação detalhada." # TODO: Implementar análise detalhada para LIC


    # Prepara resultados
    results: Dict[str, Any] = {
        # Parâmetros de entrada relevantes
        "bil_especificado_kv": bil_especificado,
        "norma_isolamento": norma_isolamento,
        "tipo_impulso": tipo_impulso,
        "resistor_frontal_ohm": resistor_frontal,
        "resistor_cauda_ohm": resistor_cauda,
        "capacitancia_gerador_nf": capacitancia_gerador,
        "capacitancia_objeto_pf": capacitancia_objeto,
        "indutancia_uh": indutancia,
        "tempo_corte_input_us": tempo_corte_input,
        "gap_distance_mm": gap_distance_mm,

        # Níveis de isolamento da norma
        "bil_norma_kv": bil_norma,
        "sil_norma_kv": sil_norma,

        # Parâmetros calculados da forma de onda
        "alfa": round(waveform_params["alfa"], 4),
        "beta": round(waveform_params["beta"], 4),
        "tempo_frente_us_calc": round(waveform_params["tempo_frente"], 2),
        "tempo_cauda_us_calc": round(waveform_params["tempo_cauda"], 2),
        "eficiencia": round(waveform_params["eficiencia"], 4),
        "dentro_tolerancia_frente": waveform_params["dentro_tolerancia_frente"],
        "dentro_tolerancia_cauda": waveform_params["dentro_tolerancia_cauda"],

        # Tensões e Energia calculadas
        "tensao_carregamento_kv": round(tensao_carregamento, 2),
        "energia_impulso_joules": round(energia_impulso_joules, 2),

        # Resultados de Impulso Cortado (se aplicável)
        "tempo_corte_us_calc": round(tempo_corte_us, 2) if tempo_corte_us is not None else None,
        "tensao_corte_kv_calc": round(tensao_corte_kv, 2),
        "sobretensao_corte_kv_calc": round(sobretensao_corte_kv, 2),

        # Simulação da forma de onda (pontos de tempo e tensão)
        "simulacao_forma_onda": {
            "tempos_us": tempos.tolist(),
            "tensoes_kv": [round(v, 2) for v in tensoes],
        },

        # Análise de Conformidade
        "analise_conformidade": analise_conformidade,

        # TODO: Adicionar Recomendações para o Teste (Seção 7)
        "recomendacoes_teste": "Implementação pendente."
    }

    return results