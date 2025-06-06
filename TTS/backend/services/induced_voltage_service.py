"""
Serviço para cálculos de ensaios de tensão induzida
Implementa os algoritmos descritos em docs/instrucoes_induzida.md
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
                SQRT_3 = 1.732050807568877
                INDUCACAO_LIMITE = 1.9 # T
                # Adicionar mocks para as tabelas de dados
                potencia_magnet_data = {} # Mock vazio ou com dados de exemplo
                perdas_nucleo_data = {} # Mock vazio ou com dados de exemplo

            const = MockConstants()

log = logging.getLogger(__name__)

def interpolate_table_data(table_name: str, induction: float, frequency: float) -> float:
    """
    Realiza interpolação bilinear para obter valores das tabelas de referência.
    """
    if table_name == "potencia_magnet":
        table_data = const.potencia_magnet_data
    elif table_name == "perdas_nucleo":
        table_data = const.perdas_nucleo_data
    else:
        log.error(f"Tabela desconhecida para interpolação: {table_name}")
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
         log.warning(f"Indução ({induction} T) ou Frequência ({frequency} Hz) fora do range da tabela {table_name}. Usando valor do ponto mais próximo.")
         # Retorna o valor do ponto mais próximo (i.e., o canto mais próximo da grade)
         # Isso é uma simplificação; interpolação para fora do range exigiria extrapolação.
         # Para simplificar, retornamos o valor do ponto mais próximo dentro do range.
         clamped_induction = max(inductions[0], min(inductions[-1], induction))
         clamped_frequency = max(frequencies[0], min(frequencies[-1], frequency))
         # Encontra o ponto mais próximo na grade
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
        if f0 == f1: return v0 # Should be covered by the point check, but for safety
        return v0 + (v1 - v0) * (frequency - f0) / (f1 - f0)

    # Se a frequência coincidir com um ponto da tabela, interpola linearmente na indução
    if f0 == f1:
        v0 = table_data.get((i0, f0), 0.0)
        v1 = table_data.get((i1, f0), 0.0)
        if i0 == i1: return v0 # Should be covered by the point check, but for safety
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


def calculate_induced_voltage(basic_data: Dict[str, Any], module_inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula os parâmetros do teste de tensão induzida com base nos dados do transformador.

    Args:
        basic_data: Dicionário com os parâmetros de entrada do transformer_inputs
        module_inputs: Dicionário com os parâmetros de entrada do módulo de tensão induzida

    Returns:
        Dicionário com os resultados calculados para o teste de tensão induzida
    """
    # Extrai parâmetros de entrada (conforme Seção 1 da documentação)
    tipo_transformador = basic_data.get("tipo_transformador", "Trifásico")
    tensao_at = basic_data.get("tensao_at", 0)
    tensao_bt = basic_data.get("tensao_bt", 0)
    freq_nominal = basic_data.get("freq_nominal", 60)
    freq_teste = module_inputs.get("freq_teste", 120)
    tensao_prova = basic_data.get("tensao_prova", 0) # Tensão de ensaio induzida informada em dados básicos
    capacitancia = module_inputs.get("capacitancia", 0) # Capacitância AT-GND em pF
    inducao_nominal = basic_data.get("inducao_nominal", 1.7) # T
    peso_nucleo_ton = basic_data.get("peso_nucleo", 0) # Toneladas
    perdas_vazio = basic_data.get("perdas_vazio", 0) # kW

    # Converte peso do núcleo para kg
    peso_nucleo_kg = peso_nucleo_ton * 1000

    # 3. Cálculos Intermediários
    # 3.1. Relações Básicas
    fp_fn = freq_teste / freq_nominal if freq_nominal > 0 else 0

    # up_un = tensao_prova / tensao_nominal_referencia
    # A documentação indica que up_un = tensao_prova (tensão de ensaio induzida informada)
    # e que a tensão nominal de referência depende do tipo de transformador.
    # Vamos usar a tensão de prova diretamente como a tensão de ensaio aplicada no lado AT.
    tensao_ensaio_at = tensao_prova # kV

    # 3.2. Indução no Núcleo na Frequência de Teste
    # Fórmula: inducao_teste = inducao_nominal * (tensao_induzida / tensao_at) * (freq_nominal / freq_teste)
    # A documentação parece ter uma inconsistência aqui, referenciando "tensao_induzida"
    # que não é um parâmetro de entrada claro. Assumindo que "tensao_induzida" na fórmula
    # se refere à tensão de ensaio aplicada no lado AT (tensao_prova).
    inducao_teste = inducao_nominal * (tensao_ensaio_at / tensao_at) * (freq_nominal / freq_teste) if tensao_at > 0 and freq_teste > 0 else 0

    # Limitação da indução
    if inducao_teste > const.INDUCACAO_LIMITE:
        inducao_teste = const.INDUCACAO_LIMITE

    # 3.3. Tensão Aplicada no Lado BT
    # A documentação indica que tensao_aplicada_bt = (tensao_bt / tensao_at) * tensao_prova
    # para ambos monofásico e trifásico.
    tensao_aplicada_bt = (tensao_bt / tensao_at) * tensao_ensaio_at if tensao_at > 0 else 0

    # 3.4. Interpolação de Fatores das Tabelas
    # TODO: Substituir pela lógica real de interpolação
    fator_potencia_mag = interpolate_table_data("potencia_magnet", inducao_teste, freq_teste)
    fator_perdas = interpolate_table_data("perdas_nucleo", inducao_teste, freq_teste)

    results: Dict[str, Any] = {}

    # 4. Cálculos para Transformadores Monofásicos (Seção 4)
    if tipo_transformador.lower() == "monofásico":
        # 4.1. Potência Ativa (Pw)
        pot_ativa = fator_perdas * peso_nucleo_kg / 1000.0 # kW
        
        # 4.2. Potência Magnética (Sm)
        pot_magnetica = fator_potencia_mag * peso_nucleo_kg / 1000.0 # kVA

        # 4.3. Componente Indutiva (Sind)
        pot_induzida = 0.0
        if pot_magnetica**2 >= pot_ativa**2:
             pot_induzida = math.sqrt(pot_magnetica**2 - pot_ativa**2) # kVAr ind
        
        # 4.4. Tensão para Cálculo de Scap (U_calc_scap)
        # A documentação indica u_calc_scap = tensao_prova - (up_un * tensao_bt)
        # Onde up_un = tensao_prova. Isso parece incorreto.
        # Assumindo que up_un deveria ser a relação de transformação ou algo similar.
        # Vou usar uma interpretação mais comum: a tensão no lado BT durante o teste induzido.
        # A tensão induzida no lado BT é proporcional à relação de espiras e à tensão aplicada no lado AT.
        # tensao_induzida_bt = tensao_ensaio_at * (tensao_bt / tensao_at)
        # A documentação em 3.3 já calcula a tensão aplicada no lado BT como:
        # tensao_aplicada_bt = (tensao_bt / tensao_at) * tensao_prova
        # Vamos usar essa como a tensão no lado BT durante o teste.
        # A fórmula u_calc_scap = tensao_prova - (up_un * tensao_bt) na documentação parece confusa.
        # Vou pular este cálculo por enquanto e focar nos outros, ou assumir que u_calc_scap
        # se refere a uma queda de tensão ou algo similar que não está claramente definido.
        # TODO: Clarificar o cálculo de U_calc_scap com a documentação ou requisitos adicionais.
        u_calc_scap = 0 # Placeholder

        # 4.5. Potência Capacitiva (Scap)
        # Fórmula: pcap = -((u_calc_scap * 1000)^2 * 2 * π * freq_teste * capacitancia * 10^-12) / 3 / 1000
        # A fórmula usa u_calc_scap que não está claro.
        # Além disso, a divisão por 3 para transformadores monofásicos parece incorreta.
        # A fórmula para potência reativa capacitiva é Q = V^2 * ω * C
        # Onde V é a tensão RMS, ω = 2 * π * f, e C é a capacitância total.
        # Assumindo que a capacitância fornecida é a total entre AT e terra.
        # A tensão relevante para a potência capacitiva é a tensão de ensaio no lado AT (tensao_ensaio_at).
        # pcap = -((tensao_ensaio_at * 1000)**2 * 2 * math.pi * freq_teste * capacitancia * 1e-12) / 1000 # kVAr cap
        # A documentação original tinha uma divisão por 3 que parece específica para alguma configuração.
        # Vou manter a fórmula original da documentação por enquanto, mas com a tensão de ensaio AT.
        # pcap = -((tensao_ensaio_at * 1000)**2 * 2 * math.pi * freq_teste * capacitancia * 1e-12) / 3 / 1000 # kVAr cap
        # Revertendo para a interpretação mais literal da fórmula da documentação, usando tensao_prova como V:
        pcap = -((tensao_prova * 1000)**2 * 2 * math.pi * freq_teste * capacitancia * 1e-12) / 3 / 1000 # kVAr cap


        # 4.6. Razão Scap/Sind
        scap_sind_ratio = abs(pcap) / pot_induzida if pot_induzida > const.EPSILON else 0

        results["monofasico"] = {
            "pot_ativa": round(pot_ativa, 2),
            "pot_magnetica": round(pot_magnetica, 2),
            "pot_induzida": round(pot_induzida, 2),
            "pcap": round(pcap, 2),
            "scap_sind_ratio": round(scap_sind_ratio, 2)
        }

    # 5. Cálculos para Transformadores Trifásicos (Seção 5)
    elif tipo_transformador.lower() == "trifásico":
        # 5.1. Potência Ativa Total (Pw)
        pot_ativa_total = fator_perdas * peso_nucleo_kg / 1000.0 # kW

        # 5.2. Potência Magnética Total (Sm)
        pot_magnetica_total = fator_potencia_mag * peso_nucleo_kg / 1000.0 # kVA

        # 5.3. Corrente de Excitação (Iexc)
        # Fórmula: corrente_excitacao = pot_magnetica_total / (tensao_aplicada_bt * sqrt(3))
        corrente_excitacao = pot_magnetica_total / (tensao_aplicada_bt * const.SQRT_3) if tensao_aplicada_bt > 0 else 0 # A

        # 5.4. Potência de Teste Total
        # Fórmula: potencia_teste = corrente_excitacao * tensao_aplicada_bt * sqrt(3)
        potencia_teste = corrente_excitacao * tensao_aplicada_bt * const.SQRT_3 # kVA

        results["trifasico"] = {
            "pot_ativa_total": round(pot_ativa_total, 2),
            "pot_magnetica_total": round(pot_magnetica_total, 2),
            "corrente_excitacao": round(corrente_excitacao, 2),
            "potencia_teste": round(potencia_teste, 2)
        }

    # 6. Tabela de Frequências (Seção 6)
    frequencias_tabela = [100, 120, 150, 180, 200, 240]
    tabela_frequencias_resultados = []

    for freq in frequencias_tabela:
        # Recalcular indução, fatores e potências para cada frequência
        inducao_freq = inducao_nominal * (tensao_ensaio_at / tensao_at) * (freq_nominal / freq) if tensao_at > 0 and freq > 0 else 0
        if inducao_freq > const.INDUCACAO_LIMITE:
            inducao_freq = const.INDUCACAO_LIMITE

        fator_potencia_mag_freq = interpolate_table_data("potencia_magnet", inducao_freq, freq)
        fator_perdas_freq = interpolate_table_data("perdas_nucleo", inducao_freq, freq)

        if tipo_transformador.lower() == "monofásico":
            pot_ativa_freq = fator_perdas_freq * peso_nucleo_kg / 1000.0 # kW
            pot_magnetica_freq = fator_potencia_mag_freq * peso_nucleo_kg / 1000.0 # kVA
            pot_induzida_freq = 0.0
            if pot_magnetica_freq**2 >= pot_ativa_freq**2:
                 pot_induzida_freq = math.sqrt(pot_magnetica_freq**2 - pot_ativa_freq**2) # kVAr ind

            # Recalcular pcap para a nova frequência
            pcap_freq = -((tensao_prova * 1000)**2 * 2 * math.pi * freq * capacitancia * 1e-12) / 3 / 1000 # kVAr cap

            tabela_frequencias_resultados.append({
                "frequencia_hz": freq,
                "inducao_teste_t": round(inducao_freq, 4),
                "pot_ativa_kw": round(pot_ativa_freq, 2),
                "pot_magnetica_kVA": round(pot_magnetica_freq, 2),
                "pot_induzida_kVAr_ind": round(pot_induzida_freq, 2),
                "pcap_kVAr_cap": round(pcap_freq, 2),
                "scap_sind_ratio": round(abs(pcap_freq) / pot_induzida_freq, 2) if pot_induzida_freq > const.EPSILON else 0
            })
        elif tipo_transformador.lower() == "trifásico":
            pot_ativa_total_freq = fator_perdas_freq * peso_nucleo_kg / 1000.0 # kW
            pot_magnetica_total_freq = fator_potencia_mag_freq * peso_nucleo_kg / 1000.0 # kVA
            # Para trifásico, a documentação não detalha o cálculo de pcap na tabela de frequências,
            # mas inclui Potência Capacitiva na seção 5. Vamos incluir aqui também se relevante.
            # Assumindo que a fórmula de pcap para monofásico pode ser adaptada, mas a divisão por 3 é questionável.
            # Vou manter a estrutura da documentação que não mostra pcap na tabela para trifásicos.
            # TODO: Clarificar se Potência Capacitiva deve ser incluída na tabela para trifásicos.

            tabela_frequencias_resultados.append({
                "frequencia_hz": freq,
                "inducao_teste_t": round(inducao_freq, 4),
                "pot_ativa_total_kw": round(pot_ativa_total_freq, 2),
                "pot_magnetica_total_kVA": round(pot_magnetica_total_freq, 2),
                # "pcap_kVAr_cap": "Não calculado para Trifásico na tabela" # Placeholder
            })


    results["tabela_frequencias"] = tabela_frequencias_resultados

    # 7. Recomendações para o Teste (Seção 7)
    recomendacoes = {}
    if tipo_transformador.lower() == "monofásico":
        # Usar os resultados calculados para a frequência de teste principal (freq_teste)
        pot_ativa_monofasico = results["monofasico"]["pot_ativa"]
        pot_magnetica_monofasico = results["monofasico"]["pot_magnetica"]
        pot_induzida_monofasico = results["monofasico"]["pot_induzida"]
        pcap_monofasico = results["monofasico"]["pcap"]

        potencia_total_recomendada = max(pot_magnetica_monofasico, pot_ativa_monofasico + pcap_monofasico) * 1.2
        tensao_saida_recomendada = tensao_aplicada_bt * 1.1
        potencia_ativa_minima = pot_ativa_monofasico * 1.2
        potencia_reativa_indutiva = pot_induzida_monofasico * 1.2
        potencia_reativa_capacitiva = pcap_monofasico * 1.2

        recomendacoes["monofasico"] = {
            "potencia_total_recomendada_kVA": round(potencia_total_recomendada, 2),
            "tensao_saida_recomendada_kV": round(tensao_saida_recomendada, 2),
            "potencia_ativa_minima_kW": round(potencia_ativa_minima, 2),
            "potencia_reativa_indutiva_kVAr_ind": round(potencia_reativa_indutiva, 2),
            "potencia_reativa_capacitiva_kVAr_cap": round(potencia_reativa_capacitiva, 2),
        }

    elif tipo_transformador.lower() == "trifásico":
        # Usar os resultados calculados para a frequência de teste principal (freq_teste)
        potencia_teste_trifasico = results["trifasico"]["potencia_teste"]
        corrente_excitacao_trifasico = results["trifasico"]["corrente_excitacao"]
        pot_magnetica_total_trifasico = results["trifasico"]["pot_magnetica_total"]

        potencia_total_recomendada = potencia_teste_trifasico * 1.2
        tensao_saida_recomendada = tensao_aplicada_bt * 1.1
        corrente_nominal_minima = corrente_excitacao_trifasico * 1.5
        potencia_magnetica_recomendada = pot_magnetica_total_trifasico # A documentação repete Sm aqui

        recomendacoes["trifasico"] = {
            "potencia_total_recomendada_kVA": round(potencia_total_recomendada, 2),
            "tensao_saida_recomendada_kV": round(tensao_saida_recomendada, 2),
            "corrente_nominal_minima_A": round(corrente_nominal_minima, 2),
            "potencia_magnetica_recomendada_kVA": round(potencia_magnetica_recomendada, 2),
        }

    results["recomendacoes"] = recomendacoes


    # Adiciona parâmetros de entrada relevantes nos resultados para referência
    results["parametros_entrada"] = {
        "tipo_transformador": tipo_transformador,
        "tensao_at": tensao_at,
        "tensao_bt": tensao_bt,
        "freq_nominal": freq_nominal,
        "freq_teste": freq_teste,
        "tensao_prova": tensao_prova,
        "capacitancia": capacitancia,
        "inducao_nominal": inducao_nominal,
        "peso_nucleo_ton": peso_nucleo_ton,
        "perdas_vazio": perdas_vazio,
        "peso_nucleo_kg": peso_nucleo_kg,
        "tensao_ensaio_at": tensao_ensaio_at,
        "inducao_teste": round(inducao_teste, 4),
        "tensao_aplicada_bt": round(tensao_aplicada_bt, 2),
        "fator_potencia_mag_interpolado": round(fator_potencia_mag, 4),
        "fator_perdas_interpolado": round(fator_perdas, 4)
    }


    return results