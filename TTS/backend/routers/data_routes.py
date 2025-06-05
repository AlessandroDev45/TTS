# backend/routers/data_routes.py
"""
Rotas da API para gerenciamento de dados dos stores.
Implementa endpoints REST para persistência via MCPDataManager.
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
from datetime import datetime

# Importações com fallback para diferentes estruturas de projeto
try:
    from ..mcp.data_manager import MCPDataManager
except ImportError:
    try:
        from backend.mcp.data_manager import MCPDataManager
    except ImportError:
        from mcp.data_manager import MCPDataManager

# Instância global do data manager (será definida por main.py)
mcp_data_manager = None

router = APIRouter(prefix="/api/data", tags=["data"])

def set_data_manager(data_manager: MCPDataManager):
    """Define a instância do data manager para uso nas rotas."""
    global mcp_data_manager
    mcp_data_manager = data_manager

@router.get("/health")
async def health_check():
    """Verifica se a API de dados está funcionando."""
    return {"status": "ok", "message": "API de dados funcionando"}

@router.get("/stores")
async def list_stores():
    """Lista todos os stores disponíveis."""
    if not mcp_data_manager:
        raise HTTPException(status_code=500, detail="Data manager não inicializado")

    try:
        stores = list(mcp_data_manager.store_definitions.keys())
        return {"stores": stores}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar stores: {str(e)}")

@router.get("/stores/{store_id}")
async def get_store_data(store_id: str):
    """Obtém os dados de um store específico."""
    if not mcp_data_manager:
        raise HTTPException(status_code=500, detail="Data manager não inicializado")

    try:
        data = mcp_data_manager.get_data(store_id)
        return data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter dados: {str(e)}")

@router.put("/stores/{store_id}")
async def set_store_data(store_id: str, data: Dict[str, Any] = Body(...)):
    """Define os dados completos de um store."""
    if not mcp_data_manager:
        raise HTTPException(status_code=500, detail="Data manager não inicializado")

    try:
        success = mcp_data_manager.set_data(store_id, data)
        if success:
            return mcp_data_manager.get_data(store_id)
        else:
            raise HTTPException(status_code=500, detail="Falha ao salvar dados")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao definir dados: {str(e)}")

@router.patch("/stores/{store_id}")
async def update_store_data(store_id: str, partial_data: Dict[str, Any] = Body(...)):
    """Atualiza parcialmente os dados de um store."""
    if not mcp_data_manager:
        raise HTTPException(status_code=500, detail="Data manager não inicializado")

    try:
        success = mcp_data_manager.patch_data(store_id, partial_data)
        if success:
            return mcp_data_manager.get_data(store_id)
        else:
            raise HTTPException(status_code=500, detail="Falha ao atualizar dados")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar dados: {str(e)}")

@router.delete("/stores/{store_id}")
async def clear_store_data(store_id: str):
    """Limpa os dados de um store específico."""
    if not mcp_data_manager:
        raise HTTPException(status_code=500, detail="Data manager não inicializado")

    try:
        success = mcp_data_manager.clear_store(store_id)
        if success:
            return {"message": f"Store {store_id} limpo com sucesso"}
        else:
            raise HTTPException(status_code=500, detail="Falha ao limpar store")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao limpar store: {str(e)}")

@router.delete("/stores")
async def clear_all_stores():
    """Limpa todos os stores."""
    if not mcp_data_manager:
        raise HTTPException(status_code=500, detail="Data manager não inicializado")

    try:
        success = mcp_data_manager.clear_all_stores()
        if success:
            return {"message": "Todos os stores foram limpos com sucesso"}
        else:
            raise HTTPException(status_code=500, detail="Falha ao limpar stores")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao limpar stores: {str(e)}")

@router.get("/stores/{store_id}/export")
async def export_store_data(store_id: str):
    """Exporta os dados de um store em formato JSON."""
    if not mcp_data_manager:
        raise HTTPException(status_code=500, detail="Data manager não inicializado")

    try:
        data = mcp_data_manager.get_data(store_id)
        return {
            "store_id": store_id,
            "data": data,
            "exported_at": datetime.now().isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao exportar dados: {str(e)}")

@router.post("/stores/{store_id}/import")
async def import_store_data(store_id: str, import_data: Dict[str, Any] = Body(...)):
    """Importa dados para um store."""
    if not mcp_data_manager:
        raise HTTPException(status_code=500, detail="Data manager não inicializado")

    try:
        # Extrai apenas os dados, ignorando metadados de exportação
        data_to_import = import_data.get("data", import_data)
        success = mcp_data_manager.set_data(store_id, data_to_import)

        if success:
            return {
                "message": f"Dados importados com sucesso para o store {store_id}",
                "data": mcp_data_manager.get_data(store_id)
            }
        else:
            raise HTTPException(status_code=500, detail="Falha ao importar dados")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao importar dados: {str(e)}")

@router.get("/backup")
async def backup_all_data():
    """Cria um backup completo de todos os stores."""
    if not mcp_data_manager:
        raise HTTPException(status_code=500, detail="Data manager não inicializado")

    try:
        all_stores = mcp_data_manager.get_all_stores()
        return {
            "backup_timestamp": datetime.now().isoformat(),
            "stores": all_stores
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar backup: {str(e)}")

@router.post("/restore")
async def restore_all_data(backup_data: Dict[str, Any] = Body(...)):
    """Restaura dados de um backup completo."""
    if not mcp_data_manager:
        raise HTTPException(status_code=500, detail="Data manager não inicializado")

    try:
        stores_data = backup_data.get("stores", {})
        restored_stores = []

        for store_id, data in stores_data.items():
            if store_id in mcp_data_manager.store_definitions:
                success = mcp_data_manager.set_data(store_id, data)
                if success:
                    restored_stores.append(store_id)

        return {
            "message": f"Backup restaurado com sucesso",
            "restored_stores": restored_stores,
            "total_stores": len(restored_stores)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao restaurar backup: {str(e)}")