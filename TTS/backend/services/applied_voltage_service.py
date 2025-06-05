"""
Serviço para cálculos de ensaios de tensão aplicada
Implementa os algoritmos descritos em docs/instrucoes_aplicada.md
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
                PI = 3.141592653589793
                FREQUENCIA_PADRAO = 60  # Hz
                
            const = MockConstants()


def calculate_applied_voltage_test(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula os parâmetros do teste de tensão aplicada com base nos dados do transformador.
    
    Args:
        data: Dicionário com os parâmetros básicos do transformador
        
    Returns:
        Dicionário com os resultados calculados para o teste de tensão aplicada
    """    # Extrai parâmetros básicos
    tipo_transformador = data.get("tipo_transformador", "Trifásico")
    tensao_at = data.get("tensao_at", 0)
    tensao_bt = data.get("tensao_bt", 0)
    classe_tensao_at = data.get("classe_tensao_at", 0)
    classe_tensao_bt = data.get("classe_tensao_bt", 0)
    classe_tensao_bucha_neutro = data.get("classe_tensao_bucha_neutro", 0)
    conexao_at = data.get("conexao_at", "D")
    conexao_bt = data.get("conexao_bt", "yn")
    conexao_terciario = data.get("conexao_terciario", "")
    classe_tensao_terciario = data.get("classe_tensao_terciario", 0)
    frequencia = data.get("frequencia", 60)  # Hz
      # Determina tensões de teste conforme seção 2.1 da documentação
    # 2.1.1 Para o lado de Alta Tensão (AT)
    if conexao_at and conexao_at.lower().startswith("yn"):
        tensao_teste_at = classe_tensao_bucha_neutro
    else:
        tensao_teste_at = classe_tensao_at
        
    # 2.1.2 Para o lado de Baixa Tensão (BT)
    tensao_teste_bt = classe_tensao_bt
    
    # 2.1.3 Para o Terciário (se existir)
    tensao_teste_terciario = classe_tensao_terciario if conexao_terciario else 0
      # 2.2 Ajustes para Capacitância (valores em pF)
    capacitancia_at = 330 if tensao_teste_at and tensao_teste_at > 450 else 660
    capacitancia_bt = 330 if tensao_teste_bt and tensao_teste_bt > 450 else 660
    capacitancia_terciario = 330 if tensao_teste_terciario and tensao_teste_terciario > 450 else 660 if tensao_teste_terciario and tensao_teste_terciario > 0 else 0
      # 3. Cálculo da Corrente de Teste (I = V * 2πfC)
    corrente_teste_at = tensao_teste_at * 1000 * 2 * const.PI * frequencia * capacitancia_at * 1e-12 if tensao_teste_at else 0
    corrente_teste_bt = tensao_teste_bt * 1000 * 2 * const.PI * frequencia * capacitancia_bt * 1e-12 if tensao_teste_bt else 0
    corrente_teste_terciario = 0
    if tensao_teste_terciario and tensao_teste_terciario > 0:
        corrente_teste_terciario = tensao_teste_terciario * 1000 * 2 * const.PI * frequencia * capacitancia_terciario * 1e-12
    # 3.2. Cálculo da Potência Reativa (Q = V * I)
    potencia_reativa_at = tensao_teste_at * 1000 * corrente_teste_at if tensao_teste_at and corrente_teste_at else 0
    potencia_reativa_bt = tensao_teste_bt * 1000 * corrente_teste_bt if tensao_teste_bt and corrente_teste_bt else 0
    potencia_reativa_terciario = tensao_teste_terciario * 1000 * corrente_teste_terciario if tensao_teste_terciario and corrente_teste_terciario else 0

    # Prepara resultados
    results = {
        # Tensões de teste
        "tensao_teste_at": tensao_teste_at,
        "tensao_teste_bt": tensao_teste_bt,
        "tensao_teste_terciario": tensao_teste_terciario,
        
        # Capacitâncias
        "capacitancia_at": capacitancia_at,
        "capacitancia_bt": capacitancia_bt,
        "capacitancia_terciario": capacitancia_terciario,
        
        # Correntes de teste
        "corrente_teste_at": corrente_teste_at,
        "corrente_teste_bt": corrente_teste_bt,
        "corrente_teste_terciario": corrente_teste_terciario,

        # Potências Reativas (em VAr)
        "potencia_reativa_at": potencia_reativa_at,
        "potencia_reativa_bt": potencia_reativa_bt,
        "potencia_reativa_terciario": potencia_reativa_terciario,
    }

    # 4. Análise de Viabilidade do Sistema Ressonante
    viabilidade_at = "Não analisado"
    if tensao_teste_at > 0:
        if tensao_teste_at <= 270 and capacitancia_at >= 2000 and capacitancia_at <= 39000: # Capacitância em pF
            viabilidade_at = "Viável com Módulos 1||2||3 (3 Par.) 270kV"
        elif tensao_teste_at <= 450 and capacitancia_at >= 2000 and capacitancia_at <= 23400: # Capacitância em pF
             viabilidade_at = "Viável com Módulos 1||2||3 (3 Par.) 450kV"
        else:
            viabilidade_at = "Pode requerer outra configuração ou não viável com sistema ressonante disponível"

    viabilidade_bt = "Não analisado"
    if tensao_teste_bt > 0:
        if tensao_teste_bt <= 270 and capacitancia_bt >= 2000 and capacitancia_bt <= 39000: # Capacitância em pF
            viabilidade_bt = "Viável com Módulos 1||2||3 (3 Par.) 270kV"
        elif tensao_teste_bt <= 450 and capacitancia_bt >= 2000 and capacitancia_bt <= 23400: # Capacitância em pF
             viabilidade_bt = "Viável com Módulos 1||2||3 (3 Par.) 450kV"
        else:
            viabilidade_bt = "Pode requerer outra configuração ou não viável com sistema ressonante disponível"

    viabilidade_terciario = "Não analisado"
    if tensao_teste_terciario > 0:
        if tensao_teste_terciario <= 270 and capacitancia_terciario >= 2000 and capacitancia_terciario <= 39000: # Capacitância em pF
            viabilidade_terciario = "Viável com Módulos 1||2||3 (3 Par.) 270kV"
        elif tensao_teste_terciario <= 450 and capacitancia_terciario >= 2000 and capacitancia_terciario <= 23400: # Capacitância em pF
             viabilidade_terciario = "Viável com Módulos 1||2||3 (3 Par.) 450kV"
        else:
            viabilidade_terciario = "Pode requerer outra configuração ou não viável com sistema ressonante disponível"


    results["analise_viabilidade_ressonante"] = {
        "at": viabilidade_at,
        "bt": viabilidade_bt,
        "terciario": viabilidade_terciario,
    }

    return results