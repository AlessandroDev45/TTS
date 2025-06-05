# backend/mcp/__init__.py
"""
Memory Cache Proxy (MCP) - Sistema central de gerenciamento de dados da aplicação TTS.
"""

from .data_manager import MCPDataManager
from .session_manager import MCPSessionManager

__all__ = ['MCPDataManager', 'MCPSessionManager']
