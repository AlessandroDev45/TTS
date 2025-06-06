# backend/routers/transformer_routes.py
import sys
import pathlib
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional
from pydantic import BaseModel

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
    potencia_mva: Optional[float] = None
    frequencia: Optional[float] = None
    tipo_transformador: Optional[str] = None
    grupo_ligacao: Optional[str] = None
    liquido_isolante: Optional[str] = None
    tipo_isolamento: Optional[str] = None
    norma_iso: Optional[str] = None
    elevacao_oleo_topo: Optional[float] = None
    elevacao_enrol: Optional[float] = None
    peso_parte_ativa: Optional[float] = None
    peso_tanque_acessorios: Optional[float] = None
    peso_oleo: Optional[float] = None
    peso_total: Optional[float] = None
    peso_adicional: Optional[float] = None
    tensao_at: Optional[float] = None
    classe_tensao_at: Optional[float] = None
    impedancia: Optional[float] = None
    nbi_at: Optional[float] = None
    sil_at: Optional[float] = None
    conexao_at: Optional[str] = None
    tensao_bucha_neutro_at: Optional[float] = None
    nbi_neutro_at: Optional[float] = None
    sil_neutro_at: Optional[float] = None
    teste_tensao_aplicada_at: Optional[float] = None
    teste_tensao_induzida_at: Optional[float] = None
    tensao_bt: Optional[float] = None
    classe_tensao_bt: Optional[float] = None
    nbi_bt: Optional[float] = None
    sil_bt: Optional[float] = None
    conexao_bt: Optional[str] = None
    tensao_bucha_neutro_bt: Optional[float] = None
    nbi_neutro_bt: Optional[float] = None
    sil_neutro_bt: Optional[float] = None
    teste_tensao_aplicada_bt: Optional[float] = None
    tensao_terciario: Optional[float] = None
    classe_tensao_terciario: Optional[float] = None
    nbi_terciario: Optional[float] = None
    sil_terciario: Optional[float] = None
    conexao_terciario: Optional[str] = None
    tensao_bucha_neutro_terciario: Optional[float] = None
    nbi_neutro_terciario: Optional[float] = None
    sil_neutro_terciario: Optional[float] = None
    teste_tensao_aplicada_terciario: Optional[float] = None

@router.post("/inputs")
async def update_transformer_inputs(data: TransformerInputsData = Body(...)):
    """
    Recebe os dados de entrada do formulário do transformador,
    calcula os valores derivados e os persiste no store 'transformer_inputs'.
    """
    try:
        # Converte o Pydantic Model para um dicionário
        input_data_dict = data.model_dump(exclude_unset=True)
        
        # Calcula os dados derivados (correntes nominais, etc.)
        try:
            calculated_data = transformer_service.calculate_and_process_transformer_data(input_data_dict)
        except Exception as e:
            log.error(f"Erro ao calcular correntes nominais: {e}")
            raise HTTPException(status_code=500, detail=f"Erro ao calcular correntes nominais: {str(e)}")
        
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
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro ao processar dados do transformador: {str(e)}")

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
        if mcp_data_manager is None:
            raise HTTPException(status_code=500, detail="Sistema de dados não inicializado")

        processed_results = {}
        if module_id == 'losses':
            # A função calculate_losses espera basic_data e module_inputs
            processed_results = losses_service.calculate_losses(basic_data, module_data)
        elif module_id == 'impulse':
            processed_results = impulse_service.calculate_impulse(basic_data, module_data)
        elif module_id == 'appliedVoltage':
            # Renomear a função no service para aceitar basic_data e module_inputs
            processed_results = applied_voltage_service.calculate_applied_voltage(basic_data, module_data)
        elif module_id == 'inducedVoltage':
            processed_results = induced_voltage_service.calculate_induced_voltage(basic_data, module_data)
        elif module_id == 'shortCircuit':
            processed_results = short_circuit_service.calculate_short_circuit_analysis(basic_data) # short_circuit_service parece usar só basic_data
            # Se precisar de module_inputs para short_circuit, adapte o service e passe module_inputs aqui
        elif module_id == 'temperatureRise':
            # temperatureRise precisa de 'losses' results. Se 'losses' é uma dependência,
            # o _propagate_changes deveria garantir que 'losses' é processado primeiro.
            # Aqui, assumimos que os resultados de 'losses' estão no MCP ou são passados.
            # Para simplificar, o service de temperatureRise deve buscar 'losses' do mcp_data_manager internamente ou tê-los passados.
            losses_data_from_mcp = mcp_data_manager.get_data('losses') # Pega os dados completos de losses
            losses_results = losses_data_from_mcp.get('results', {}).get('perdas_carga', {}) # Exemplo de como pegar perdas em carga
            
            # Crie um combined_data ou passe os dados separadamente para o service de temperature
            temperature_service_input = {**basic_data, **module_data, **losses_results} # Simplificação
            processed_results = temperature_service.calculate_temperature_analysis(temperature_service_input)

        elif module_id == 'dielectricAnalysis':
             # dielectric_service.analyze_dielectric_strength já espera um 'data' combinado
             # Podemos combinar basic_data e module_inputs aqui
             combined_dielectric_data = {**basic_data, **module_data}
             processed_results = dielectric_service.analyze_dielectric_strength(combined_dielectric_data)


        # Armazena no MCP a estrutura completa: inputs, basicData (snapshot), e results
        store_data_to_save = {
            'inputs': module_data, # Os inputs que vieram do formulário do módulo
            'basicData': basic_data,   # Um snapshot dos dados básicos usados para este cálculo
            'results': processed_results,
            'lastUpdated': datetime.now().isoformat()
        }

        success = mcp_data_manager.set_data(module_id, store_data_to_save) # Usar set_data para sobrescrever completamente

        if not success:
            raise HTTPException(status_code=500, detail=f"Erro ao armazenar dados do módulo {module_id}")

        return {
            'success': True,
            'module': module_id,
            'message': f'Dados do módulo {module_id} processados e salvos com sucesso',
            'saved_data': store_data_to_save # Retorna os dados salvos para o cliente (propagação)
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro interno no processamento do módulo {module_id}: {str(e)}")

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
