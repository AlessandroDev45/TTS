# backend/mcp/session_manager.py
"""
MCP Session Manager - Gerenciador de sessões da aplicação TTS.
"""

from typing import Dict, Any, List
from .data_manager import MCPDataManager


class MCPSessionManager:
    """
    Gerenciador de sessões que trabalha em conjunto com o MCPDataManager.
    Fornece funcionalidades de alto nível para gerenciamento de sessões.
    """
    
    def __init__(self, data_manager: MCPDataManager):
        self.data_manager = data_manager
    
    def create_session(self, name: str, description: str = "") -> bool:
        """Cria uma nova sessão com o estado atual."""
        return self.data_manager.save_session(name, description)
    
    def restore_session(self, session_id: str) -> bool:
        """Restaura uma sessão específica."""
        return self.data_manager.load_session(session_id)
    
    def get_sessions_list(self) -> List[Dict[str, Any]]:
        """Obtém lista de todas as sessões disponíveis."""
        return self.data_manager.list_sessions()
    
    def export_current_state(self) -> Dict[str, Any]:
        """Exporta o estado atual para formato JSON."""
        return {
            'timestamp': self.data_manager.get_data('global_info').get('last_updated'),
            'stores': self.data_manager.get_all_stores()
        }
    
    def import_state(self, state_data: Dict[str, Any]) -> bool:
        """Importa um estado de dados."""
        try:
            stores = state_data.get('stores', {})
            for store_id, data in stores.items():
                if store_id in self.data_manager.store_definitions:
                    self.data_manager.set_data(store_id, data)
            return True
        except Exception as e:
            print(f"Erro ao importar estado: {e}")
            return False
