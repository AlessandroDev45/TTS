# backend/mcp/data_manager.py
"""
MCP Data Manager - Gerenciador central de dados da aplicação TTS.
Implementa o padrão Single Source of Truth com persistência e propagação de dados.
"""

import json
import os
import sqlite3
from typing import Dict, Any, Optional
from datetime import datetime
import threading
import requests


class MCPDataManager:
    """
    Memory Cache Proxy - Gerenciador central de dados da aplicação.
    
    Responsabilidades:
    - Manter estado da aplicação em memória
    - Gerenciar persistência no banco de dados
    - Propagar mudanças entre módulos relacionados
    - Fornecer API para leitura/escrita de dados
    """
    
    def __init__(self, db_path: str = "tts_data.db"):
        self.db_path = db_path
        self._memory_store: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        
        # Stores definidos na aplicação
        self.store_definitions = {
            'transformerInputs': {  # Nome usado no frontend
                'key': 'transformerInputs',
                'dependencies': [],
                'propagates_to': ['losses', 'impulse', 'appliedVoltage', 'inducedVoltage', 'shortCircuit', 'temperatureRise', 'dielectricAnalysis', 'globalInfo'],
                'update_logic_endpoint': None
            },
            'losses': {
                'key': 'losses',
                'dependencies': ['transformerInputs'],
                'propagates_to': ['temperatureRise'],
                'update_logic_endpoint': 'losses/process'
            },
            'impulse': {
                'key': 'impulse',
                'dependencies': ['transformerInputs'],
                'propagates_to': [],
                'update_logic_endpoint': 'impulse/process'
            },
            'appliedVoltage': {
                'key': 'appliedVoltage',
                'dependencies': ['transformerInputs'],
                'propagates_to': [],
                'update_logic_endpoint': 'appliedVoltage/process'
            },
            'inducedVoltage': {
                'key': 'inducedVoltage',
                'dependencies': ['transformerInputs'],
                'propagates_to': [],
                'update_logic_endpoint': 'inducedVoltage/process'
            },
            'shortCircuit': {
                'key': 'shortCircuit',
                'dependencies': ['transformerInputs'],
                'propagates_to': [],
                'update_logic_endpoint': 'shortCircuit/process'
            },
            'temperatureRise': {
                'key': 'temperatureRise',
                'dependencies': ['transformerInputs', 'losses'],
                'propagates_to': [],
                'update_logic_endpoint': 'temperatureRise/process'
            },
            'dielectricAnalysis': {
                'key': 'dielectricAnalysis',
                'dependencies': ['transformerInputs'],
                'propagates_to': [],
                'update_logic_endpoint': 'dielectricAnalysis/process'
            },
            'standards': {
                'key': 'standards',
                'dependencies': [],
                'propagates_to': [],
                'update_logic_endpoint': None
            },
            'sessions': {
                'key': 'sessions',
                'dependencies': [],
                'propagates_to': [],
                'update_logic_endpoint': None
            },
            'globalInfo': {
                'key': 'globalInfo',
                'dependencies': ['transformerInputs'],
                'propagates_to': [],
                'update_logic_endpoint': 'global-update'
            }
        }
        
        self._init_database()
        self._load_all_stores()
    
    def _init_database(self):
        """Inicializa o banco de dados SQLite com as tabelas necessárias."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabela principal para armazenar os dados dos stores
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_stores (
                    store_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    version INTEGER DEFAULT 1
                )
            ''')
            
            # Tabela para histórico de sessões
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    session_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            ''')
            
            conn.commit()
    
    def _load_all_stores(self):
        """Carrega todos os stores do banco de dados para a memória."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT store_id, data FROM data_stores')
            
            for store_id, data_json in cursor.fetchall():
                try:
                    self._memory_store[store_id] = json.loads(data_json)
                except json.JSONDecodeError:
                    print(f"Erro ao carregar dados do store '{store_id}'. Inicializando vazio.")
                    self._memory_store[store_id] = {}
            
            # Inicializa stores vazios para os que não existem no DB
            for store_id in self.store_definitions:
                if store_id not in self._memory_store:
                    self._memory_store[store_id] = {}
    
    def get_data(self, store_id: str) -> Dict[str, Any]:
        """
        Obtém os dados de um store específico.
        
        Args:
            store_id: Identificador do store
            
        Returns:
            Dicionário com os dados do store
        """
        with self._lock:
            if store_id not in self.store_definitions:
                raise ValueError(f"Store '{store_id}' não existe.")
            
            return self._memory_store.get(store_id, {}).copy()
    
    def set_data(self, store_id: str, data: Dict[str, Any]) -> bool:
        """
        Define os dados completos de um store e persiste no banco.
        
        Args:
            store_id: Identificador do store
            data: Dados a serem armazenados
            
        Returns:
            True se a operação foi bem-sucedida
        """
        with self._lock:
            if store_id not in self.store_definitions:
                raise ValueError(f"Store '{store_id}' não existe.")
            
            # Atualiza na memória
            self._memory_store[store_id] = data.copy()
            
            # Persiste no banco
            self._persist_store(store_id)
            
            # Propaga mudanças se necessário
            self._propagate_changes(store_id)
            
            return True
    
    def patch_data(self, store_id: str, partial_data: Dict[str, Any]) -> bool:
        """
        Atualiza parcialmente os dados de um store.
        
        Args:
            store_id: Identificador do store
            partial_data: Dados parciais para atualização
            
        Returns:
            True se a operação foi bem-sucedida
        """
        with self._lock:
            if store_id not in self.store_definitions:
                raise ValueError(f"Store '{store_id}' não existe.")
            
            # Obtém dados atuais
            current_data = self._memory_store.get(store_id, {})
            
            # Atualiza com os novos dados
            current_data.update(partial_data)
            
            # Salva os dados atualizados
            return self.set_data(store_id, current_data)
    
    def _persist_store(self, store_id: str):
        """Persiste um store específico no banco de dados."""
        data_json = json.dumps(self._memory_store.get(store_id, {}))
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO data_stores (store_id, data, last_updated, version)
                VALUES (?, ?, CURRENT_TIMESTAMP, 
                    COALESCE((SELECT version + 1 FROM data_stores WHERE store_id = ?), 1))
            ''', (store_id, data_json, store_id))
            conn.commit()
    
    def _propagate_changes(self, store_id: str):
        """
        Propaga mudanças para stores dependentes, acionando seus endpoints de atualização.
        Chamado automaticamente quando dados fundamentais são alterados.
        """
        print(f"Iniciando propagação de mudanças a partir de '{store_id}'")

        # Iterar por todas as definições de store para encontrar dependentes
        for dependent_store_id, dependent_store_def in self.store_definitions.items():
            # Verificar se o store_id atualizado está nas dependências do store dependente atual
            if store_id in dependent_store_def.get('dependencies', []):
                update_endpoint_path = dependent_store_def.get('update_logic_endpoint')

                if update_endpoint_path:
                    print(f"Store '{dependent_store_id}' depende de '{store_id}'. Acionando endpoint: {update_endpoint_path}")
                    try:
                        payload_data = {}
                        # Dados básicos de transformerInputs (se for uma dependência)
                        # Todos os módulos dependem de transformerInputs, então basicData é crucial.
                        transformer_inputs_data = self.get_data('transformerInputs')
                        payload_data['basicData'] = transformer_inputs_data.get('formData', {})

                        # Dados de input do módulo dependente
                        dependent_module_current_data = self.get_data(dependent_store_id)
                        payload_data['moduleData'] = dependent_module_current_data.get('inputs', {}) # O que está em 'inputs' do store do módulo

                        # Determinar a URL base correta
                        # Os endpoints dos módulos estão em /api/transformer/modules/
                        # O endpoint global-update está em /api/transformer/
                        if update_endpoint_path == 'global-update':
                            base_url_prop = "http://localhost:8000/api/transformer"
                        else:
                            base_url_prop = "http://localhost:8000/api/transformer/modules"
                        
                        full_url = f"{base_url_prop}/{update_endpoint_path.lstrip('/')}"

                        print(f"Chamando endpoint interno: POST {full_url} com payload: {json.dumps(payload_data, indent=2)}")
                        
                        response = requests.post(full_url, json=payload_data, timeout=10) # Adicionado timeout
                        response.raise_for_status() 

                        print(f"Endpoint '{update_endpoint_path}' para '{dependent_store_id}' acionado com sucesso. Status: {response.status_code}")
                        # O backend já salva os resultados no MCP através do endpoint chamado.
                        # Não precisamos fazer store.updateData aqui no _propagate_changes.

                    except requests.exceptions.RequestException as e:
                        print(f"Erro de requisição ao acionar endpoint '{update_endpoint_path}' para '{dependent_store_id}': {e}")
                        if e.response is not None:
                            print(f"Detalhes do erro: {e.response.text}")
                    except Exception as e:
                        print(f"Erro inesperado ao processar propagação para '{dependent_store_id}': {e}")
                else:
                    print(f"Store '{dependent_store_id}' depende de '{store_id}', mas não tem 'update_logic_endpoint' definido.")

    # Remove the _update_global_info method as its logic will be handled by the endpoint call
    # def _update_global_info(self):
    #     """Atualiza o store globalInfo baseado nos dados do transformerInputs."""
    #     # ... (rest of the method)
    #     pass # Remove the entire method


    def get_all_stores(self) -> Dict[str, Dict[str, Any]]:
        """Retorna todos os stores em um único dicionário."""
        with self._lock:
            return {store_id: data.copy() for store_id, data in self._memory_store.items()}
    
    def clear_store(self, store_id: str) -> bool:
        """Limpa os dados de um store específico."""
        with self._lock:
            if store_id not in self.store_definitions:
                raise ValueError(f"Store '{store_id}' não existe.")
            
            self._memory_store[store_id] = {}
            self._persist_store(store_id)
            return True
    
    def clear_all_stores(self) -> bool:
        """Limpa todos os stores."""
        with self._lock:
            for store_id in self.store_definitions:
                self._memory_store[store_id] = {}
                self._persist_store(store_id)
            return True
    
    def save_session(self, session_id: str, description: str = "") -> bool:
        """Salva o estado atual como uma sessão nomeada."""
        session_data = {
            'stores': self.get_all_stores(),
            'timestamp': datetime.now().isoformat()
        }
        
        session_json = json.dumps(session_data)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO sessions (session_id, session_data, created_at, description)
                VALUES (?, ?, CURRENT_TIMESTAMP, ?)
            ''', (session_id, session_json, description))
            conn.commit()
        
        return True
    
    def load_session(self, session_id: str) -> bool:
        """Carrega uma sessão específica."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT session_data FROM sessions WHERE session_id = ?', (session_id,))
            result = cursor.fetchone()
            
            if not result:
                return False
            
            try:
                session_data = json.loads(result[0])
                stores = session_data.get('stores', {})
                
                # Carrega todos os stores da sessão
                for store_id, data in stores.items():
                    if store_id in self.store_definitions:
                        self.set_data(store_id, data)
                
                return True
            except json.JSONDecodeError:
                return False
    
    def list_sessions(self) -> list:
        """Lista todas as sessões salvas."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT session_id, created_at, description 
                FROM sessions 
                ORDER BY created_at DESC
            ''')
            
            return [
                {
                    'session_id': row[0],
                    'created_at': row[1],
                    'description': row[2]
                }
                for row in cursor.fetchall()
            ]
