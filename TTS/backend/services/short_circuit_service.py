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
                SQRT_3 = 1.732050807568877
                
            const = MockConstants()


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
    tensao_terciario = data.get("tensao_terciario", 0) # Adicionado terciário
    tipo_transformador = data.get("tipo_transformador", "Trifásico")
    
    # Determina o fator conforme o tipo de transformador (seção 2.1.1 e 2.1.2)
    fator = 1.0 if tipo_transformador.lower() == "monofásico" else const.SQRT_3
    
    # Calcula as correntes nominais
    i_nom_at = (potencia_nominal * 1000) / (fator * tensao_at) if tensao_at > 0 else 0
    i_nom_bt = (potencia_nominal * 1000) / (fator * tensao_bt) if tensao_bt > 0 else 0
    # Cálculo para o lado terciário
    i_nom_ter = (potencia_nominal * 1000) / (fator * tensao_terciario) if tensao_terciario > 0 else 0

    # Cálculo para taps AT (tap+ e tap-)
    tensao_at_tap_maior = data.get("tensao_at_tap_maior", 0)
    tensao_at_tap_menor = data.get("tensao_at_tap_menor", 0)
    i_nom_at_tap_maior = (potencia_nominal * 1000) / (fator * tensao_at_tap_maior) if tensao_at_tap_maior > 0 else 0
    i_nom_at_tap_menor = (potencia_nominal * 1000) / (fator * tensao_at_tap_menor) if tensao_at_tap_menor > 0 else 0

    return {
        "i_nom_at": i_nom_at,
        "i_nom_bt": i_nom_bt,
        "i_nom_ter": i_nom_ter,
        "i_nom_at_tap_maior": i_nom_at_tap_maior,
        "i_nom_at_tap_menor": i_nom_at_tap_menor
    }


def calculate_impedances(data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calcula as impedâncias de curto-circuito conforme seção 2.2 da documentação,
    incluindo o lado terciário.
    
    Args:
        data: Dicionário com os parâmetros do transformador
    
    Returns:
        Dicionário com as impedâncias calculadas
    """
    potencia_nominal = data.get("potencia_mva", 0)
    tensao_at = data.get("tensao_at", 0)
    tensao_bt = data.get("tensao_bt", 0)
    tensao_terciario = data.get("tensao_terciario", 0) # Adicionado terciário
    impedancia_percentual = data.get("impedancia", 0)
    
    # Converte a impedância para p.u.
    z_pu = impedancia_percentual / 100
    
    # Calcula as impedâncias em ohms referidas aos lados AT, BT e Terciário
    # Nota: Para transformadores de 3 enrolamentos, a modelagem de impedância é mais complexa,
    # envolvendo impedâncias entre pares de enrolamentos (Z_AT-BT, Z_AT-Terciário, Z_BT-Terciário).
    # Esta implementação assume que a 'impedancia_percentual' é um valor único e se aplica
    # proporcionalmente a cada lado para o cálculo da impedância base, o que é uma simplificação.
    z_ohm_at = z_pu * ((tensao_at ** 2) * 1000) / potencia_nominal if potencia_nominal > 0 else 0
    z_ohm_bt = z_pu * ((tensao_bt ** 2) * 1000) / potencia_nominal if potencia_nominal > 0 else 0
    z_ohm_ter = z_pu * ((tensao_terciario ** 2) * 1000) / potencia_nominal if potencia_nominal > 0 else 0 # Adicionado terciário
    
    return {
        "z_pu": z_pu,
        "z_ohm_at": z_ohm_at,
        "z_ohm_bt": z_ohm_bt,
        "z_ohm_ter": z_ohm_ter # Corrigido e adicionado terciário
    }


def calculate_symmetric_short_circuit_current(data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calcula a corrente de curto-circuito simétrica conforme seção 2.3 da documentação,
    incluindo o lado terciário.
    
    Args:
        data: Dicionário com os parâmetros do transformador e da rede
    
    Returns:
        Dicionário com as correntes de curto-circuito simétricas calculadas
    """
    potencia_nominal = data.get("potencia_mva", 0)
    potencia_cc_rede = data.get("potencia_cc_rede", 0)
    impedancia_percentual = data.get("impedancia", 0)
    
    # Impedâncias equivalentes
    z_trafo_pu = impedancia_percentual / 100
    z_rede_pu = potencia_nominal / potencia_cc_rede if potencia_cc_rede > 0 else 0
    z_total_pu = z_trafo_pu + z_rede_pu
    
    # Correntes nominais calculadas previamente
    nom_currents = calculate_nominal_currents(data)
    i_nom_at = nom_currents["i_nom_at"]
    i_nom_bt = nom_currents["i_nom_bt"]
    i_nom_ter = nom_currents["i_nom_ter"] # Adicionado terciário
    
    # Correntes de curto-circuito simétricas
    # Nota: Para transformadores de 3 enrolamentos, a corrente de curto-circuito
    # em um terminal depende das impedâncias mútuas. Esta é uma simplificação
    # que usa a impedância total de curto-circuito em p.u. (Z_trafo + Z_rede)
    # como a impedância vista de qualquer terminal para calcular a corrente de curto.
    i_cc_sim_at = i_nom_at / z_total_pu if z_total_pu > 0 else float('inf')
    i_cc_sim_bt = i_nom_bt / z_total_pu if z_total_pu > 0 else float('inf')
    i_cc_sim_ter = i_nom_ter / z_total_pu if z_total_pu > 0 else float('inf') # Adicionado terciário
    
    return {
        "i_cc_sim_at": i_cc_sim_at,
        "i_cc_sim_bt": i_cc_sim_bt,
        "i_cc_sim_ter": i_cc_sim_ter, # Adicionado terciário
        "z_trafo_pu": z_trafo_pu,
        "z_rede_pu": z_rede_pu,
        "z_total_pu": z_total_pu
    }


def calculate_asymmetric_short_circuit_current(data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calcula a corrente de curto-circuito assimétrica conforme seção 2.4 da documentação,
    incluindo o lado terciário.
    
    Args:
        data: Dicionário com os parâmetros do transformador e da rede
    
    Returns:
        Dicionário com as correntes de curto-circuito assimétricas calculadas
    """
    fator_xr = data.get("fator_xr", 10)  # Relação X/R padrão = 10
    
    # Fator de assimetria
    k_asym = math.sqrt(1 + 2 * math.exp(-math.pi / fator_xr))
    
    # Correntes de curto-circuito simétricas calculadas previamente
    sym_currents = calculate_symmetric_short_circuit_current(data)
    i_cc_sim_at = sym_currents["i_cc_sim_at"]
    i_cc_sim_bt = sym_currents["i_cc_sim_bt"]
    i_cc_sim_ter = sym_currents["i_cc_sim_ter"] # Adicionado terciário
    
    # Correntes de curto-circuito assimétricas (pico)
    i_cc_asym_at = k_asym * math.sqrt(2) * i_cc_sim_at
    i_cc_asym_bt = k_asym * math.sqrt(2) * i_cc_sim_bt
    i_cc_asym_ter = k_asym * math.sqrt(2) * i_cc_sim_ter # Adicionado terciário
    
    return {
        "k_asym": k_asym,
        "i_cc_asym_at": i_cc_asym_at,
        "i_cc_asym_bt": i_cc_asym_bt,
        "i_cc_asym_ter": i_cc_asym_ter # Adicionado terciário
    }


def calculate_thermal_effects(data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calcula os efeitos térmicos do curto-circuito conforme seção 2.5 da documentação,
    incluindo o lado terciário.
    
    Args:
        data: Dicionário com os parâmetros do transformador e da rede
    
    Returns:
        Dicionário com os resultados dos efeitos térmicos calculados
    """
    duracao_cc = data.get("duracao_cc", 1.0)  # segundos
    
    # Correntes de curto-circuito simétricas calculadas previamente
    sym_currents = calculate_symmetric_short_circuit_current(data)
    i_cc_sim_at = sym_currents["i_cc_sim_at"]
    i_cc_sim_bt = sym_currents["i_cc_sim_bt"]
    i_cc_sim_ter = sym_currents["i_cc_sim_ter"] # Adicionado terciário
    
    # Integral de Joule (I²t)
    i_squared_t_at = (i_cc_sim_at ** 2) * duracao_cc
    i_squared_t_bt = (i_cc_sim_bt ** 2) * duracao_cc
    i_squared_t_ter = (i_cc_sim_ter ** 2) * duracao_cc # Adicionado terciário
    
    # Energia térmica dissipada (kWs)
    r_at = data.get("resistencia_at", 0.1)  # ohm (valor assumido)
    r_bt = data.get("resistencia_bt", 0.01)  # ohm (valor assumido)
    r_ter = data.get("resistencia_ter", 0.005) # ohm (valor assumido para terciário)
    
    energia_termica_at = r_at * i_squared_t_at / 1000
    energia_termica_bt = r_bt * i_squared_t_bt / 1000
    energia_termica_ter = r_ter * i_squared_t_ter / 1000 # Adicionado terciário
    
    return {
        "duracao_cc": duracao_cc,
        "i_squared_t_at": i_squared_t_at,
        "i_squared_t_bt": i_squared_t_bt,
        "i_squared_t_ter": i_squared_t_ter, # Adicionado terciário
        "energia_termica_at": energia_termica_at,
        "energia_termica_bt": energia_termica_bt,
        "energia_termica_ter": energia_termica_ter # Adicionado terciário
    }


def calculate_dynamic_forces(data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calcula as forças dinâmicas de curto-circuito conforme seção 2.6 da documentação.
    As fórmulas aqui são mais genéricas para um sistema de dois enrolamentos.
    Para um transformador com terciário, as forças internas seriam mais complexas
    e exigiriam a geometria e as correntes entre os três enrolamentos.
    Esta função mantém o modelo original para forças axiais e radiais.
    
    Args:
        data: Dicionário com os parâmetros do transformador
    
    Returns:
        Dicionário com as forças dinâmicas calculadas
    """
    # Correntes de curto-circuito assimétricas calculadas previamente
    asym_currents = calculate_asymmetric_short_circuit_current(data)
    i_cc_asym_at = asym_currents["i_cc_asym_at"]
    i_cc_asym_bt = asym_currents["i_cc_asym_bt"]
    # i_cc_asym_ter = asym_currents["i_cc_asym_ter"] # Não utilizado diretamente no modelo atual de forças dinâmicas genéricas
    
    # Constante para força eletromagnética entre condutores
    k_forca = 2e-7  # N/A² (µ₀/2π)
    
    # Comprimento efetivo dos condutores (assumido)
    l_efetivo = data.get("comprimento_enrolamento", 1.0)  # metros
    
    # Distância entre condutores (assumido)
    d_condutores = data.get("distancia_condutores", 0.1)  # metros
    
    # Forças eletromagnéticas (N)
    # Assumimos que as forças axiais e radiais são dominadas pela interação entre AT e BT
    forca_axial = k_forca * (i_cc_asym_at ** 2) * l_efetivo / d_condutores
    forca_radial = k_forca * (i_cc_asym_bt ** 2) * l_efetivo / d_condutores
    
    return {
        "forca_axial": forca_axial,
        "forca_radial": forca_radial
    }


def calculate_mechanical_forces(data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calcula os esforços mecânicos do curto-circuito conforme seção 3 da documentação.
    Assim como as forças dinâmicas, o cálculo preciso para um transformador de 3 enrolamentos
    seria mais complexo e específico para o design do enrolamento (ex: enrolamentos concêntricos).
    Esta função mantém o modelo original.
    
    Args:
        data: Dicionário com os parâmetros do transformador e do curto-circuito
    
    Returns:
        Dicionário com os resultados dos esforços mecânicos calculados
    """
    # Parâmetros necessários
    raio_medio = data.get("raio_medio", 0.3)  # metros
    altura_enrolamento = data.get("altura_enrolamento", 1.0)  # metros
    espessura_enrolamento = data.get("espessura_enrolamento", 0.05)  # metros
    numero_espiras = data.get("numero_espiras", 100)
    
    # Correntes de curto-circuito assimétrica calculadas previamente
    asym_currents = calculate_asymmetric_short_circuit_current(data)
    i_cc_asym_at = asym_currents["i_cc_asym_at"]
    i_cc_asym_bt = asym_currents["i_cc_asym_bt"]
    # i_cc_asym_ter = asym_currents["i_cc_asym_ter"] # Não utilizado no modelo original
    
    # Permeabilidade do vácuo (H/m)
    mu_0 = 4 * math.pi * 1e-7
    
    # Força axial - usando uma estimativa simplificada com correntes iguais
    # Esta é uma simplificação para interação entre dois enrolamentos.
    comprimento_axial = altura_enrolamento
    forca_axial = (mu_0 * i_cc_asym_at * i_cc_asym_bt) / (2 * math.pi * raio_medio) * comprimento_axial
    
    # Força radial
    # Também simplificado para dois enrolamentos.
    forca_radial_por_area = (mu_0 * (i_cc_asym_at ** 2) * (numero_espiras ** 2)) / (2 * math.pi * raio_medio * altura_enrolamento)
    
    # Tensão de compressão radial
    tensao_compressao_radial = forca_radial_por_area * raio_medio / espessura_enrolamento
    
    # Tensão de tração circunferencial
    tensao_tracao_circunferencial = forca_radial_por_area * raio_medio
    
    return {
        "forca_axial": forca_axial,
        "forca_radial_por_area": forca_radial_por_area,
        "tensao_compressao_radial": tensao_compressao_radial,
        "tensao_tracao_circunferencial": tensao_tracao_circunferencial
    }


def calculate_short_circuit_analysis(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Realiza a análise completa de curto-circuito para um transformador,
    incluindo o lado terciário onde aplicável e com as simplificações notadas.
    
    Args:
        data: Dicionário com os parâmetros do transformador e da rede
    
    Returns:
        Dicionário com todos os resultados calculados
    """
    # Cálculos básicos
    nom_currents = calculate_nominal_currents(data)
    impedances = calculate_impedances(data)
    
    # Cálculos de correntes de curto
    sym_currents = calculate_symmetric_short_circuit_current(data)
    asym_currents = calculate_asymmetric_short_circuit_current(data)
    
    # Cálculos de efeitos
    thermal = calculate_thermal_effects(data)
    dynamic = calculate_dynamic_forces(data)
    mechanical = calculate_mechanical_forces(data)
    
    # Consolida os resultados
    # Consolida os resultados
    results: Dict[str, Any] = {
        # Correntes nominais
        "i_nom_at": nom_currents["i_nom_at"],
        "i_nom_bt": nom_currents["i_nom_bt"],
        "i_nom_ter": nom_currents["i_nom_ter"], # Adicionado terciário

        # Impedâncias
        "z_pu": impedances["z_pu"],
        "z_ohm_at": impedances["z_ohm_at"],
        "z_ohm_bt": impedances["z_ohm_bt"],
        "z_ohm_ter": impedances["z_ohm_ter"], # Adicionado terciário

        # Correntes simétricas
        "z_trafo_pu": sym_currents["z_trafo_pu"],
        "z_rede_pu": sym_currents["z_rede_pu"],
        "z_total_pu": sym_currents["z_total_pu"],
        "i_cc_sim_at": sym_currents["i_cc_sim_at"],
        "i_cc_sim_bt": sym_currents["i_cc_sim_bt"],
        "i_cc_sim_ter": sym_currents["i_cc_sim_ter"], # Adicionado terciário

        # Correntes assimétricas
        "k_asym": asym_currents["k_asym"],
        "i_cc_asym_at": asym_currents["i_cc_asym_at"],
        "i_cc_asym_bt": asym_currents["i_cc_asym_bt"],
        "i_cc_asym_ter": asym_currents["i_cc_asym_ter"], # Adicionado terciário

        # Efeitos térmicos
        "duracao_cc": thermal["duracao_cc"],
        "i_squared_t_at": thermal["i_squared_t_at"],
        "i_squared_t_bt": thermal["i_squared_t_bt"],
        "i_squared_t_ter": thermal["i_squared_t_ter"], # Adicionado terciário
        "energia_termica_at": thermal["energia_termica_at"],
        "energia_termica_bt": thermal["energia_termica_bt"],
        "energia_termica_ter": thermal["energia_termica_ter"], # Adicionado terciário

        # Forças dinâmicas
        "forca_axial": dynamic["forca_axial"],
        "forca_radial": dynamic["forca_radial"],

        # Esforços mecânicos
        "forca_axial_mecanica": mechanical["forca_axial"],
        "forca_radial_por_area": mechanical["forca_radial_por_area"],
        "tensao_compressao_radial": mechanical["tensao_compressao_radial"],
        "tensao_tracao_circunferencial": mechanical["tensao_tracao_circunferencial"]
    }

    # 5. Análise de Suportabilidade
    # Definir limites máximos admissíveis (valores placeholder - precisam ser definidos com base em normas/dados específicos)
    sigma_radial_max = 100e6 # Exemplo: 100 MPa
    sigma_circ_max = 150e6 # Exemplo: 150 MPa
    delta_t_max = 250 # Exemplo: 250 °C (para cobre)
    i_squared_t_max_at = 100e6 # Exemplo: 100 MA²s (para AT)
    i_squared_t_max_bt = 200e6 # Exemplo: 200 MA²s (para BT)
    i_squared_t_max_ter = 150e6 # Exemplo: 150 MA²s (para Terciário)


    # 5.1. Verificação Mecânica
    verificacao_mecanica_radial = mechanical["tensao_compressao_radial"] <= sigma_radial_max
    verificacao_mecanica_circunferencial = mechanical["tensao_tracao_circunferencial"] <= sigma_circ_max

    # 5.2. Verificação Térmica
    # Nota: A elevação de temperatura (Delta T) não foi calculada explicitamente,
    # mas a Integral de Joule (I²t) é um indicador comum de estresse térmico.
    # Usaremos I²t para a verificação térmica por enquanto.
    verificacao_termica_at = thermal["i_squared_t_at"] <= i_squared_t_max_at
    verificacao_termica_bt = thermal["i_squared_t_bt"] <= i_squared_t_max_bt
    verificacao_termica_ter = thermal["i_squared_t_ter"] <= i_squared_t_max_ter


    # Status geral de suportabilidade
    status_suportabilidade = "APROVADO"
    if not (verificacao_mecanica_radial and verificacao_mecanica_circunferencial and
            verificacao_termica_at and verificacao_termica_bt and verificacao_termica_ter):
        status_suportabilidade = "REPROVADO"

    results["analise_suportabilidade"] = {
        "limites_maximos_admissiveis": {
            "sigma_radial_max_pa": sigma_radial_max,
            "sigma_circ_max_pa": sigma_circ_max,
            "delta_t_max_c": delta_t_max,
            "i_squared_t_max_at_a2s": i_squared_t_max_at,
            "i_squared_t_max_bt_a2s": i_squared_t_max_bt,
            "i_squared_t_max_ter_a2s": i_squared_t_max_ter,
            "nota": "Estes limites são placeholders e precisam ser definidos com base em normas e dados específicos do material e design."
        },
        "verificacao_mecanica": {
            "radial": verificacao_mecanica_radial,
            "circunferencial": verificacao_mecanica_circunferencial,
        },
        "verificacao_termica": {
            "at": verificacao_termica_at,
            "bt": verificacao_termica_bt,
            "terciario": verificacao_termica_ter,
        },
        "status_geral": status_suportabilidade
    }

    return results