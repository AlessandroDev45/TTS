# backend/routers/transformer_routes.py
import sys
import pathlib
from datetime import datetime
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional, Union
from pydantic import BaseModel, field_validator

# Ajusta o path para permitir importações corretas
current_file = pathlib.Path(__file__).absolute()
current_dir = current_file.parent
backend_dir = current_dir.parent
root_dir = backend_dir.parent

if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    from ..mcp import MCPDataManager
    from ..services import transformer_service
    from ..services import losses_service
    from ..services import impulse_service
    from ..services import applied_voltage_service
    from ..services import induced_voltage_service
    from ..services import short_circuit_service
    from ..services import temperature_service
    from ..services import dielectric_service
except ImportError as e:
    print(f"Erro ao importar módulos em transformer_routes: {e}")
    sys.exit(1) # Saia se as importações essenciais falharem
# Placeholder para a instância do MCP (será definida por main.py)
mcp_data_manager = None

router = APIRouter(prefix="/api/transformer", tags=["transformer"])

class TransformerInputsData(BaseModel):
    # Campos do formulário transformer_inputs.html
    potencia_mva: Optional[Union[float, str]] = None
    frequencia: Optional[Union[float, str]] = None
    tipo_transformador: Optional[str] = None
    grupo_ligacao: Optional[str] = None
    liquido_isolante: Optional[str] = None
    tipo_isolamento: Optional[str] = None
    norma_iso: Optional[str] = None
    elevacao_oleo_topo: Optional[Union[float, str]] = None
    elevacao_enrol: Optional[Union[float, str]] = None
    peso_parte_ativa: Optional[Union[float, str]] = None
    peso_tanque_acessorios: Optional[Union[float, str]] = None
    peso_oleo: Optional[Union[float, str]] = None
    peso_total: Optional[Union[float, str]] = None
    peso_adicional: Optional[Union[float, str]] = None
    tensao_at: Optional[Union[float, str]] = None
    classe_tensao_at: Optional[Union[float, str]] = None
    impedancia: Optional[Union[float, str]] = None
    nbi_at: Optional[Union[float, str]] = None
    sil_at: Optional[Union[float, str]] = None
    conexao_at: Optional[str] = None
    tensao_bucha_neutro_at: Optional[Union[float, str]] = None
    nbi_neutro_at: Optional[Union[float, str]] = None
    sil_neutro_at: Optional[Union[float, str]] = None
    tensao_at_tap_maior: Optional[Union[float, str]] = None
    tensao_at_tap_menor: Optional[Union[float, str]] = None
    impedancia_tap_maior: Optional[Union[float, str]] = None
    impedancia_tap_menor: Optional[Union[float, str]] = None
    teste_tensao_aplicada_at: Optional[Union[float, str]] = None
    teste_tensao_induzida_at: Optional[Union[float, str]] = None
    tensao_bt: Optional[Union[float, str]] = None
    classe_tensao_bt: Optional[Union[float, str]] = None
    nbi_bt: Optional[Union[float, str]] = None
    sil_bt: Optional[Union[float, str]] = None
    conexao_bt: Optional[str] = None
    tensao_bucha_neutro_bt: Optional[Union[float, str]] = None
    nbi_neutro_bt: Optional[Union[float, str]] = None
    sil_neutro_bt: Optional[Union[float, str]] = None
    teste_tensao_aplicada_bt: Optional[Union[float, str]] = None
    tensao_terciario: Optional[Union[float, str]] = None
    classe_tensao_terciario: Optional[Union[float, str]] = None
    nbi_terciario: Optional[Union[float, str]] = None
    sil_terciario: Optional[Union[float, str]] = None
    conexao_terciario: Optional[str] = None
    tensao_bucha_neutro_terciario: Optional[Union[float, str]] = None
    nbi_neutro_terciario: Optional[Union[float, str]] = None
    sil_neutro_terciario: Optional[Union[float, str]] = None
    teste_tensao_aplicada_terciario: Optional[Union[float, str]] = None

@router.post("/inputs")
async def update_transformer_inputs(data: TransformerInputsData = Body(...)):
    """
    Recebe os dados de entrada do formulário do transformador,
    calcula os valores derivados e os persiste no store 'transformer_inputs'.
    """
    try:
        # Converte o Pydantic Model para um dicionário
        input_data_dict = data.model_dump(exclude_unset=True)
        print(f"[DEBUG] Dados recebidos: {input_data_dict}")

        # Calcula os dados derivados (correntes nominais, etc.)
        calculated_data = transformer_service.calculate_and_process_transformer_data(input_data_dict)

        # Combina os dados de entrada com os dados calculados
        final_data = {**input_data_dict, **calculated_data}

        # Persiste os dados combinados no store 'transformer_inputs'
        if mcp_data_manager is None:
            raise HTTPException(status_code=500, detail="Sistema de dados não inicializado")

        success = mcp_data_manager.patch_data('transformerInputs', {"formData": final_data})

        if success:
            return {
                "status": "success",
                "message": "Dados do transformador atualizados e calculados com sucesso.",
                "updated_data": final_data
            }
        else:
            raise HTTPException(status_code=500, detail="Falha ao persistir dados do transformador.")
    except Exception as e:
        import traceback
        print(f"[ERROR] Erro completo: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar dados do transformador: {str(e)}")

@router.post("/propagate")
async def trigger_propagation():
    """
    Dispara propagação manual para todos os módulos dependentes
    """
    try:
        if mcp_data_manager is None:
            raise HTTPException(status_code=500, detail="Sistema de dados não inicializado")

        # Habilita propagação temporariamente
        mcp_data_manager.enable_auto_propagation()

        # Dispara propagação manual para transformerInputs
        mcp_data_manager._propagate_changes('transformerInputs')

        # Desabilita novamente
        mcp_data_manager.disable_auto_propagation()

        return {"status": "success", "message": "Propagação executada com sucesso"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao executar propagação: {str(e)}")

@router.post("/propagation/enable")
async def enable_propagation():
    """Habilita propagação automática"""
    if mcp_data_manager is None:
        raise HTTPException(status_code=500, detail="Sistema de dados não inicializado")

    mcp_data_manager.enable_auto_propagation()
    return {"status": "success", "message": "Propagação automática habilitada"}

@router.post("/propagation/disable")
async def disable_propagation():
    """Desabilita propagação automática"""
    if mcp_data_manager is None:
        raise HTTPException(status_code=500, detail="Sistema de dados não inicializado")

    mcp_data_manager.disable_auto_propagation()
    return {"status": "success", "message": "Propagação automática desabilitada"}

# Rotas para processamento de módulos específicos conforme arquitetura TTS
@router.post("/modules/{module_id}/process")
async def process_module_data(module_id: str, data: Dict[str, Any] = Body(...)):
    """
    Processa dados específicos de um módulo.
    Arquitetura TTS: Dados Básicos + Inputs Específicos → Services → MCP
    """
    try:
        # Valida módulos ativos conforme especificação
        valid_modules = ['losses', 'impulse', 'appliedVoltage', 'inducedVoltage',
                        'shortCircuit', 'temperatureRise', 'dielectricAnalysis']

        if module_id not in valid_modules:
            raise HTTPException(status_code=404, detail=f"Módulo '{module_id}' não encontrado")

        # Extrai dados básicos e dados específicos do módulo
        basic_data = data.get('basicData', {})
        module_data = data.get('moduleData', {})

        # Chama service específico com base no module_id
        processed_data = {}
        if module_id == 'losses':
            # Verificar se há uma operação específica
            operation = data.get('operation')
            if operation == 'no_load_losses':
                input_data = data.get('data', {})
                processed_data = losses_service.calculate_no_load_losses(input_data)
                # Salvar apenas os inputs no MCP
                if mcp_data_manager:
                    mcp_data_manager.patch_data(f"{module_id}-inputs", {
                        "no_load_inputs": input_data,
                        "timestamp": datetime.now().isoformat()
                    })
            elif operation == 'load_losses':
                input_data = data.get('data', {})
                processed_data = losses_service.calculate_load_losses(input_data)
                # Salvar apenas os inputs no MCP - SOMENTE INPUTS
                load_inputs_only = {
                    "temperatura_referencia": input_data.get("temperatura_referencia"),
                    "perdas_carga_kw_u_min": input_data.get("perdas_carga_kw_u_min"),
                    "perdas_carga_kw_u_nom": input_data.get("perdas_carga_kw_u_nom"),
                    "perdas_carga_kw_u_max": input_data.get("perdas_carga_kw_u_max")
                }
                if mcp_data_manager:
                    mcp_data_manager.patch_data(f"{module_id}-inputs", {
                        "load_inputs": load_inputs_only,
                        "timestamp": datetime.now().isoformat()
                    })
            else:
                raise HTTPException(status_code=400, detail="Operação inválida para perdas")
        elif module_id == 'impulse':
            # Função correta baseada no código do impulse_service
            combined_data = {**basic_data, **module_data}
            processed_data = impulse_service.calculate_impulse_test(combined_data)
        elif module_id == 'appliedVoltage':
            # Função correta baseada no código do applied_voltage_service
            combined_data = {**basic_data, **module_data}
            processed_data = applied_voltage_service.calculate_applied_voltage_test(combined_data)
        elif module_id == 'inducedVoltage':
            # Função correta baseada no código do induced_voltage_service
            combined_data = {**basic_data, **module_data}
            processed_data = induced_voltage_service.calculate_induced_voltage_test(combined_data)
        elif module_id == 'shortCircuit':
            # Função correta baseada no código do short_circuit_service
            combined_data = {**basic_data, **module_data}
            processed_data = short_circuit_service.calculate_short_circuit_analysis(combined_data)
        elif module_id == 'temperatureRise':
            # Função correta baseada no código do temperature_service
            combined_data = {**basic_data, **module_data}
            processed_data = temperature_service.calculate_temperature_analysis(combined_data)
        elif module_id == 'dielectricAnalysis':
            # Função correta baseada no código do dielectric_service
            processed_data = dielectric_service.analyze_dielectric(basic_data, module_data)
        else:
            # Isso não deve acontecer devido à validação de valid_modules, mas é um fallback
            raise HTTPException(status_code=500, detail=f"Serviço para o módulo '{module_id}' não implementado.")

        # Armazena no MCP
        if mcp_data_manager is None:
            raise HTTPException(status_code=500, detail="Sistema de dados não inicializado")

        store_data = {
            'inputs': module_data,
            'basicData': basic_data,
            'results': processed_data,
            'lastUpdated': str(pathlib.Path(__file__).stat().st_mtime)  # timestamp simples
        }

        success = mcp_data_manager.patch_data(module_id, store_data)

        if not success:
            raise HTTPException(status_code=500, detail=f"Erro ao armazenar dados do módulo {module_id}")

        return {
            'success': True,
            'module': module_id,
            'results': processed_data,
            'message': f'Dados do módulo {module_id} processados com sucesso'
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/global-update")
async def trigger_global_update(data: Dict[str, Any] = Body(...)):
    """
    Dispara atualização global do MCP em ciclo estruturado.
    Arquitetura TTS: Dados Básicos → Propagam para todos os módulos → MCP atualizado
    """
    try:
        if mcp_data_manager is None:
            raise HTTPException(status_code=500, detail="Sistema de dados não inicializado")

        triggered_by = data.get('triggeredBy', 'unknown')

        # 1. Obtém dados básicos (fonte da verdade)
        basic_data = mcp_data_manager.get_data('transformerInputs')
        if not basic_data:
            basic_data = {}

        basic_form_data = basic_data.get('formData', {})

        # 2. Módulos ativos conforme especificação
        active_modules = ['losses', 'impulse', 'appliedVoltage', 'inducedVoltage',
                         'shortCircuit', 'temperatureRise', 'dielectricAnalysis']

        # 3. Ciclo estruturado de atualização
        update_results = {}

        for module_id in active_modules:
            try:
                # Obtém dados específicos do módulo
                module_data = mcp_data_manager.get_data(module_id)
                module_inputs = module_data.get('inputs', {}) if module_data else {}

                # Atualiza store do módulo com dados básicos propagados
                updated_store_data = {
                    'inputs': module_inputs,
                    'basicData': basic_form_data,  # Propagação dos dados básicos
                    'results': module_data.get('results', {}) if module_data else {},
                    'lastGlobalUpdate': str(pathlib.Path(__file__).stat().st_mtime)
                }

                success = mcp_data_manager.patch_data(module_id, updated_store_data)

                update_results[module_id] = {
                    'status': 'updated' if success else 'error',
                    'message': 'Dados básicos propagados' if success else 'Erro ao atualizar'
                }

            except Exception as e:
                update_results[module_id] = {
                    'status': 'error',
                    'message': f'Erro: {str(e)}'
                }

        return {
            'success': True,
            'triggeredBy': triggered_by,
            'modulesUpdated': len([r for r in update_results.values() if r['status'] == 'updated']),
            'results': update_results,
            'message': 'Atualização global concluída'
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na atualização global: {str(e)}")
