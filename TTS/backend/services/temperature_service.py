"""
Serviço para cálculos de elevação de temperatura
Implementa os algoritmos descritos em docs/instrucoes_temperatura.md
"""

import sys
import pathlib
from typing import Dict, Any, Optional, Union, List
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
                # Constantes para resfriamento
                FATOR_POTENCIA_OLEO = 0.9  # Expoente para modelos de elevação de temperatura
                CALOR_ESPECIFICO_OLEO = 1.880  # kJ/(kg·K)
                CALOR_ESPECIFICO_COBRE = 0.385  # kJ/(kg·K)
                CALOR_ESPECIFICO_FERRO = 0.450  # kJ/(kg·K)
                TEMP_AMBIENTE_REFERENCIA = 20  # °C
                
            const = MockConstants()


def calculate_oil_temperature_rise(data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calcula a elevação de temperatura do óleo conforme seção 3.1 da documentação.
    
    Args:
        data: Dicionário com os parâmetros do transformador
        
    Returns:
        Dicionário com os resultados de elevação de temperatura do óleo
    """
    # Extrai parâmetros relevantes
    perdas_vazio = data.get("perdas_vazio_kw", 0)
    perdas_carga = data.get("perdas_carga_kw_u_nom", 0)
    tipo_resfriamento = data.get("tipo_resfriamento", "ONAN")
    peso_oleo = data.get("peso_oleo", 0)
    carga_percentual = data.get("carga_percentual", 100) / 100
    
    # Determina o expoente n baseado no tipo de resfriamento
    if tipo_resfriamento in ["ONAN", "ONAF"]:
        n = 0.8
    elif tipo_resfriamento in ["OFAF", "OFWF"]:
        n = 0.9
    else:  # ODAF, ODWF e outros
        n = 1.0
    
    # Calcula as perdas totais em condição de carga
    perdas_totais_nominal = perdas_vazio + perdas_carga
    perdas_carga_atual = perdas_carga * (carga_percentual ** 2)
    perdas_totais_atual = perdas_vazio + perdas_carga_atual
    
    # Relação entre perdas em carga e em vazio
    r = perdas_carga / perdas_vazio if perdas_vazio > 0 else 1
    
    # Relação de perdas para condição atual de carga
    r_atual = r * (carga_percentual ** 2)
    
    # Elevação de temperatura do óleo em regime permanente (topo)
    elevacao_nominal = data.get("elevacao_oleo_topo", 55)  # K (valor típico para ONAN)
    elevacao_atual = elevacao_nominal * ((1 + r_atual) / (1 + r)) ** n
    
    # Constante de tempo do óleo (minutos)
    capacidade_termica_oleo = peso_oleo * const.CALOR_ESPECIFICO_OLEO  # kJ/K
    coef_transferencia_oleo = perdas_totais_nominal / elevacao_nominal  # kW/K
    constante_tempo_oleo = capacidade_termica_oleo / (60 * coef_transferencia_oleo)  # minutos
    
    return {
        "elevacao_oleo_nominal": elevacao_nominal,
        "elevacao_oleo_atual": elevacao_atual,
        "constante_tempo_oleo": constante_tempo_oleo,
        "n_expoente": n,
        "r_nominal": r,
        "r_atual": r_atual
    }


def calculate_winding_temperature_rise(data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calcula a elevação de temperatura dos enrolamentos conforme seção 3.2 da documentação.
    
    Args:
        data: Dicionário com os parâmetros do transformador
        
    Returns:
        Dicionário com os resultados de elevação de temperatura dos enrolamentos
    """
    # Extrai parâmetros relevantes
    perdas_carga = data.get("perdas_carga_kw_u_nom", 0)
    tipo_resfriamento = data.get("tipo_resfriamento", "ONAN")
    peso_enrolamentos = data.get("peso_enrolamentos", 0)
    carga_percentual = data.get("carga_percentual", 100) / 100
    
    # Determina o expoente m baseado no tipo de resfriamento
    if tipo_resfriamento in ["ONAN"]:
        m = 0.8
    elif tipo_resfriamento in ["ONAF"]:
        m = 0.9
    else:  # OFAF, OFWF, ODAF, ODWF e outros
        m = 1.0
    
    # Calcula as perdas nos enrolamentos em condição de carga
    perdas_enrol_nominal = perdas_carga
    perdas_enrol_atual = perdas_enrol_nominal * (carga_percentual ** 2)
    
    # Gradiente de temperatura entre enrolamento e óleo
    g_nominal = data.get("elevacao_enrol", 65) - data.get("elevacao_oleo_topo", 55)  # K
    g_atual = g_nominal * (carga_percentual ** (2 * m))
    
    # Elevação de temperatura do óleo (do cálculo anterior)
    elevacao_oleo = calculate_oil_temperature_rise(data)
    elevacao_oleo_atual = elevacao_oleo["elevacao_oleo_atual"]
    
    # Elevação de temperatura dos enrolamentos em relação à ambiente
    elevacao_enrol_atual = elevacao_oleo_atual + g_atual
    
    # Constante de tempo dos enrolamentos (minutos)
    capacidade_termica_enrol = peso_enrolamentos * const.CALOR_ESPECIFICO_COBRE  # kJ/K
    coef_transferencia_enrol = perdas_enrol_nominal / g_nominal  # kW/K
    constante_tempo_enrol = capacidade_termica_enrol / (60 * coef_transferencia_enrol)  # minutos
    
    return {
        "gradiente_nominal": g_nominal,
        "gradiente_atual": g_atual,
        "elevacao_enrol_atual": elevacao_enrol_atual,
        "constante_tempo_enrol": constante_tempo_enrol,
        "m_expoente": m
    }


def calculate_temperature_time_curve(data: Dict[str, Any], tempo_total: float = 480, intervalo: float = 10) -> Dict[str, Any]:
    """
    Calcula a curva de temperatura ao longo do tempo conforme seção 2.2 da documentação.
    
    Args:
        data: Dicionário com os parâmetros do transformador
        tempo_total: Tempo total da simulação em minutos
        intervalo: Intervalo entre pontos em minutos
        
    Returns:
        Dicionário com os arrays de tempo e temperaturas calculadas
    """
    # Extrai parâmetros relevantes
    temp_ambiente = data.get("temp_ambiente", const.TEMP_AMBIENTE_REFERENCIA)
    carga_inicial_pct = data.get("carga_inicial_pct", 0) / 100
    carga_final_pct = data.get("carga_percentual", 100) / 100
    
    # Cria dados temporários para os cálculos iniciais
    data_inicial = data.copy()
    data_inicial["carga_percentual"] = carga_inicial_pct * 100
    
    # Calcula elevações de temperatura para estado inicial e final
    oleo_inicial = calculate_oil_temperature_rise(data_inicial)
    enrol_inicial = calculate_winding_temperature_rise(data_inicial)
    
    data_final = data.copy()
    data_final["carga_percentual"] = carga_final_pct * 100
    
    oleo_final = calculate_oil_temperature_rise(data_final)
    enrol_final = calculate_winding_temperature_rise(data_final)
    
    # Constantes de tempo
    tau_oleo = oleo_final["constante_tempo_oleo"]
    tau_enrol = enrol_final["constante_tempo_enrol"]
    
    # Valores iniciais e finais
    theta_oleo_inicial = oleo_inicial["elevacao_oleo_atual"]
    theta_oleo_final = oleo_final["elevacao_oleo_atual"]
    
    theta_enrol_inicial = enrol_inicial["elevacao_enrol_atual"]
    theta_enrol_final = enrol_final["elevacao_enrol_atual"]
    
    # Gera pontos de tempo
    tempo = np.arange(0, tempo_total + intervalo, intervalo)
    
    # Calcula curvas de temperatura
    # θ(t) = θ_final - (θ_final - θ_inicial) * e^(-t/τ)
    theta_oleo = [theta_oleo_final - (theta_oleo_final - theta_oleo_inicial) * math.exp(-t / tau_oleo) for t in tempo]
    theta_enrol = [theta_enrol_final - (theta_enrol_final - theta_enrol_inicial) * math.exp(-t / tau_enrol) for t in tempo]
    
    # Temperaturas absolutas (°C)
    temp_oleo = [temp_ambiente + theta for theta in theta_oleo]
    temp_enrol = [temp_ambiente + theta for theta in theta_enrol]
    
    return {
        "tempo": tempo.tolist(),
        "elevacao_oleo": theta_oleo,
        "elevacao_enrol": theta_enrol,
        "temp_oleo": temp_oleo,
        "temp_enrol": temp_enrol,
        "temp_ambiente": temp_ambiente
    }


def calculate_temperature_analysis(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Realiza a análise completa de elevação de temperatura para um transformador.
    
    Args:
        data: Dicionário com os parâmetros do transformador
        
    Returns:
        Dicionário com todos os resultados calculados
    """
    # Extrai parâmetros relevantes
    temp_ambiente = data.get("temp_ambiente", const.TEMP_AMBIENTE_REFERENCIA)
    tipo_resfriamento = data.get("tipo_resfriamento", "ONAN") # Extrair tipo_resfriamento aqui

    # Cálculos de elevação de temperatura
    oleo = calculate_oil_temperature_rise(data)
    enrol = calculate_winding_temperature_rise(data)

    # Temperatura ambiente de referência (já extraída acima)
    # temp_ambiente = data.get("temp_ambiente", const.TEMP_AMBIENTE_REFERENCIA)
    
    # Temperaturas absolutas (°C)
    temp_oleo = temp_ambiente + oleo["elevacao_oleo_atual"]
    temp_enrol = temp_ambiente + enrol["elevacao_enrol_atual"]
    
    # Calculando o hot-spot (ponto mais quente)
    fator_hot_spot = data.get("fator_hot_spot", 1.1)
    temp_hot_spot = temp_ambiente + oleo["elevacao_oleo_atual"] + (fator_hot_spot * enrol["gradiente_atual"])
    
    # Calcular curva de temperatura
    curva_temp = calculate_temperature_time_curve(data)
    
    # Consolida os resultados
    results = {
        # Elevações de temperatura
        "elevacao_oleo_nominal": oleo["elevacao_oleo_nominal"],
        "elevacao_oleo_atual": oleo["elevacao_oleo_atual"],
        "gradiente_nominal": enrol["gradiente_nominal"],
        "gradiente_atual": enrol["gradiente_atual"],
        "elevacao_enrol_atual": enrol["elevacao_enrol_atual"],
        
        # Constantes de tempo
        "constante_tempo_oleo": oleo["constante_tempo_oleo"],
        "constante_tempo_enrol": enrol["constante_tempo_enrol"],
        
        # Temperaturas absolutas
        "temp_ambiente": temp_ambiente,
        "temp_oleo": temp_oleo,
        "temp_enrol": temp_enrol,
        "temp_hot_spot": temp_hot_spot,
        
        # Fator de envelhecimento
        "fator_envelhecimento": calculate_aging_factor(temp_hot_spot),
        
        # Curvas de temperatura
        "curva_temperatura": curva_temp
    }

    # 4. Cálculos de Capacidade de Sobrecarga (Seção 4)
    # Definir elevação máxima permitida do óleo (placeholder - precisa ser definido com base em normas/dados específicos)
    delta_theta_oleo_max_permitida = data.get("elevacao_oleo_max_permitida", 65.0) # Exemplo: 65K

    # 4.1. Fator de Carga Máximo em Regime Permanente
    # K_max = √((Δθ_oleo_max / Δθ_oleo_nominal)^(1/n))
    n_expoente = oleo["n_expoente"]
    elevacao_oleo_nominal = oleo["elevacao_oleo_nominal"]
    fator_carga_maximo = 0.0
    if elevacao_oleo_nominal > const.EPSILON and delta_theta_oleo_max_permitida >= elevacao_oleo_nominal:
         fator_carga_maximo = math.sqrt((delta_theta_oleo_max_permitida / elevacao_oleo_nominal)**(1/n_expoente))

    # 4.2. Tempo Máximo de Sobrecarga (requer simulação ou cálculo iterativo, simplificando)
    # A fórmula t_max = -τ_oleo * ln((Δθ_oleo_max - Δθ_oleo_final) / (Δθ_oleo_inicial - Δθ_oleo_final))
    # requer Δθ_oleo_inicial e Δθ_oleo_final sob a condição de sobrecarga.
    # Para simplificar, não calcularemos o tempo máximo de sobrecarga com esta fórmula complexa por enquanto.
    # TODO: Implementar cálculo de tempo máximo de sobrecarga se necessário.
    tempo_max_sobrecarga = "Cálculo complexo pendente" # Placeholder

    # 4.3. Perda de Vida Útil (já calculada pelo fator de envelhecimento)
    # A documentação apresenta a taxa relativa de envelhecimento (V).
    # A perda de vida útil em si é a integração dessa taxa ao longo do tempo.
    # O fator de envelhecimento calculado na função calculate_aging_factor é a taxa V.
    taxa_envelhecimento = calculate_aging_factor(temp_hot_spot)


    # 5. Análise de Resfriamento (Seção 5)
    # 5.1. Capacidade de Dissipação de Calor
    # P_dissipacao = K * Δθ_oleo_topo
    # K = P_total_nominal / Δθ_oleo_nominal
    perdas_vazio = data.get("perdas_vazio_kw", 0)
    perdas_carga = data.get("perdas_carga_kw_u_nom", 0)
    perdas_totais_nominal = perdas_vazio + perdas_carga
    coef_transferencia_calor = perdas_totais_nominal / elevacao_oleo_nominal if elevacao_oleo_nominal > const.EPSILON else 0
    capacidade_dissipacao_calor = coef_transferencia_calor * oleo["elevacao_oleo_atual"] # Usando elevação atual para dissipação atual

    # 5.2. Eficiência do Sistema de Resfriamento
    # η_resfriamento = P_dissipacao / P_total
    # P_total é a potência total de perdas atual
    perdas_totais_atual = data.get("perdas_vazio_kw", 0) + (data.get("perdas_carga_kw_u_nom", 0) * (data.get("carga_percentual", 100) / 100)**2)
    eficiencia_resfriamento = capacidade_dissipacao_calor / perdas_totais_atual if perdas_totais_atual > const.EPSILON else 0


    # 6. Recomendações para Projeto (Seção 6)
    recomendacoes = {}
    # 6.1. Margens de Segurança (Exemplos baseados nos limites típicos da seção 6.1)
    recomendacoes["margens_seguranca"] = {
        "elevacao_temperatura": f"Considerar elevação {oleo['elevacao_oleo_atual']:.2f}K (limite típico 55K/65K)",
        "capacidade_sobrecarga": f"Fator de carga máximo em regime: {fator_carga_maximo:.2f} (limite típico 1.3-1.5)",
        "perda_vida_util": f"Taxa de envelhecimento: {taxa_envelhecimento:.2f} (limite típico 2-3)",
    }
    # 6.2. Considerações Especiais (Baseado na Seção 6.2 e inputs)
    recomendacoes["consideracoes_especiais"] = {
        "altitude": f"Altitude de instalação: {data.get('altitude', 'Não informado')}m. Considerar correção na capacidade de resfriamento.",
        "temperatura_ambiente": f"Temperatura ambiente de referência: {temp_ambiente}°C. Considerar variações.",
        "ciclo_carga": f"Tipo de resfriamento: {tipo_resfriamento}. Otimizar para o ciclo de carga específico.",
    }


    # Consolida os resultados
    results["capacidade_sobrecarga"] = {
        "elevacao_oleo_max_permitida_k": delta_theta_oleo_max_permitida,
        "fator_carga_maximo_regime": round(fator_carga_maximo, 2),
        "tempo_max_sobrecarga": tempo_max_sobrecarga, # Placeholder
        "taxa_envelhecimento": round(taxa_envelhecimento, 4),
    }
    results["analise_resfriamento"] = {
        "coeficiente_transferencia_calor_kw_k": round(coef_transferencia_calor, 4),
        "capacidade_dissipacao_calor_kw": round(capacidade_dissipacao_calor, 2),
        "eficiencia_resfriamento": round(eficiencia_resfriamento, 4),
    }
    results["recomendacoes"] = recomendacoes


    return results


def calculate_aging_factor(temp_hot_spot: float) -> float:
    """
    Calcula o fator de envelhecimento conforme IEC 60076-7.
    
    Args:
        temp_hot_spot: Temperatura do ponto mais quente em °C
        
    Returns:
        Fator de envelhecimento
    """
    # Constantes para papel termoestabilizado
    if temp_hot_spot <= 110:
        return math.exp((15000 / 383) - (15000 / (temp_hot_spot + 273)))
    else:
        return 1.0