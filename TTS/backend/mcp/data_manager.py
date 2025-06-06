# backend/mcp/data_manager.py
import json
import os
import sqlite3
from typing import Dict, Any, Optional
from datetime import datetime
import threading
import requests # Importação crucial

class MCPDataManager:
    def __init__(self, db_path: str = "tts_data.db"):
        self.db_path = db_path
        self._memory_store: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        
        # Definições dos stores, incluindo dependências e endpoints de atualização
        self.store_definitions = {
            'transformerInputs': {
                'key': 'transformerInputs',
                'dependencies': [],
                'propagates_to': ['losses', 'impulse', 'appliedVoltage', 'inducedVoltage', 'shortCircuit', 'temperatureRise', 'dielectricAnalysis', 'globalInfo'],
                'update_logic_endpoint': None 
            },
            'losses': {
                'key': 'losses',
                'dependencies': ['transformerInputs'],
                'propagates_to': ['temperatureRise'], # temperatureRise depende de losses
                'update_logic_endpoint': 'api/transformer/modules/losses/process' 
            },
            'impulse': {
                'key': 'impulse',
                'dependencies': ['transformerInputs'],
                'propagates_to': [],
                'update_logic_endpoint': 'api/transformer/modules/impulse/process'
            },
            'appliedVoltage': {
                'key': 'appliedVoltage',
                'dependencies': ['transformerInputs'],
                'propagates_to': [],
                'update_logic_endpoint': 'api/transformer/modules/appliedVoltage/process'
            },
            'inducedVoltage': {
                'key': 'inducedVoltage',
                'dependencies': ['transformerInputs'],
                'propagates_to': [],
                'update_logic_endpoint': 'api/transformer/modules/inducedVoltage/process'
            },
            'shortCircuit': {
                'key': 'shortCircuit',
                'dependencies': ['transformerInputs'],
                'propagates_to': [],
                'update_logic_endpoint': 'api/transformer/modules/shortCircuit/process'
            },
            'temperatureRise': {
                'key': 'temperatureRise',
                'dependencies': ['transformerInputs', 'losses'], 
                'propagates_to': [],
                'update_logic_endpoint': 'api/transformer/modules/temperatureRise/process'
            },
            'dielectricAnalysis': {
                'key': 'dielectricAnalysis',
                'dependencies': ['transformerInputs'],
                'propagates_to': [],
                'update_logic_endpoint': 'api/transformer/modules/dielectricAnalysis/process'
            },
            'standards': {
                'key': 'standards', 'dependencies': [], 'propagates_to': [], 'update_logic_endpoint': None
            },
            'sessions': {
                'key': 'sessions', 'dependencies': [], 'propagates_to': [], 'update_logic_endpoint': None
            },
            'globalInfo': {
                'key': 'globalInfo',
                'dependencies': ['transformerInputs'],
                'propagates_to': [],
                'update_logic_endpoint': 'api/transformer/global-update'
            }
        }
        
        self._init_database()
        self._load_all_stores()
    
    def _init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_stores (
                    store_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    version INTEGER DEFAULT 1
                )
            ''')
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
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT store_id, data FROM data_stores')
            for store_id, data_json in cursor.fetchall():
                try:
                    self._memory_store[store_id] = json.loads(data_json)
                except json.JSONDecodeError:
                    print(f"Erro ao carregar dados do store '{store_id}'. Inicializando vazio.")
                    self._memory_store[store_id] = {}
            for store_id_def in self.store_definitions:
                if store_id_def not in self._memory_store:
                    self._memory_store[store_id_def] = {} # Inicializa stores vazios
    
    def get_data(self, store_id: str) -> Dict[str, Any]:
        with self._lock:
            if store_id not in self.store_definitions:
                # Se não está definido, não deve existir. Mas para flexibilidade, podemos retornar vazio
                # raise ValueError(f"Store '{store_id}' não existe.")
                print(f"Aviso: Tentativa de obter store não definido '{store_id}'. Retornando vazio.")
                return {}
            return self._memory_store.get(store_id, {}).copy()
    
    def set_data(self, store_id: str, data: Dict[str, Any]) -> bool:
        with self._lock:
            if store_id not in self.store_definitions:
                # Poderia adicionar dinamicamente, mas por ora vamos manter os stores definidos
                print(f"Aviso: Tentativa de definir store não definido '{store_id}'. Ignorando.")
                return False # Ou raise ValueError
            
            self._memory_store[store_id] = data.copy() # Substitui completamente
            self._persist_store(store_id)
            print(f"[MCPDataManager - set_data] Store '{store_id}' definido. Disparando propagação.")
            self._propagate_changes(store_id) 
            return True
    
    def patch_data(self, store_id: str, partial_data: Dict[str, Any]) -> bool:
        with self._lock:
            if store_id not in self.store_definitions:
                print(f"Aviso: Tentativa de aplicar patch em store não definido '{store_id}'. Ignorando.")
                return False # Ou raise ValueError

            current_store_data = self._memory_store.get(store_id, {})
            
            # Lógica de merge inteligente para 'formData'
            if 'formData' in partial_data and isinstance(partial_data['formData'], dict):
                if 'formData' not in current_store_data or not isinstance(current_store_data.get('formData'), dict):
                    current_store_data['formData'] = {} 
                
                current_store_data['formData'].update(partial_data['formData'])
                
                # Remove 'formData' de partial_data para o update geral abaixo, se houver outras chaves
                # Isso evita que current_store_data['formData'] seja sobrescrito se partial_data = {'formData': ..., 'outraChave': ...}
                # No entanto, se partial_data é APENAS {'formData': ...}, o update abaixo não fará nada.
                # É mais seguro fazer uma cópia e remover.
                other_partial_updates = {k: v for k, v in partial_data.items() if k != 'formData'}
                current_store_data.update(other_partial_updates)
            else:
                current_store_data.update(partial_data) # Merge simples se não houver 'formData' em partial_data
            
            self._memory_store[store_id] = current_store_data
            self._persist_store(store_id)
            print(f"[MCPDataManager - patch_data] Store '{store_id}' atualizado. Disparando propagação.")
            self._propagate_changes(store_id)
            return True
    
    def _persist_store(self, store_id: str):
        data_json = json.dumps(self._memory_store.get(store_id, {}))
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO data_stores (store_id, data, last_updated, version)
                VALUES (?, ?, CURRENT_TIMESTAMP, 
                    COALESCE((SELECT version + 1 FROM data_stores WHERE store_id = ?), 1))
            ''', (store_id, data_json, store_id))
            conn.commit()

    def _propagate_changes(self, updated_store_id: str):
        print(f"[MCPDataManager] Iniciando propagação a partir de '{updated_store_id}'")
        
        # Encontra todos os stores que dependem DIRETAMENTE do store atualizado
        # e que têm um endpoint de atualização.
        dependent_calls_info = []
        for store_key, store_def in self.store_definitions.items():
            if updated_store_id in store_def.get('dependencies', []) and store_def.get('update_logic_endpoint'):
                dependent_calls_info.append({
                    "dependent_store_id": store_key,
                    "endpoint": store_def['update_logic_endpoint'],
                    "all_dependencies_ids": store_def.get('dependencies', []) # Todas as dependências do store alvo
                })

        if not dependent_calls_info:
            print(f"[MCPDataManager] '{updated_store_id}' não tem dependentes diretos com endpoints para propagar.")
            return

        base_url = "http://localhost:8000" # Assume que o servidor FastAPI está rodando aqui

        for call_info in dependent_calls_info:
            dependent_store_id = call_info["dependent_store_id"]
            update_endpoint_path = call_info["endpoint"]
            all_deps_ids_for_target = call_info["all_dependencies_ids"]
            
            print(f"[MCPDataManager] Store '{dependent_store_id}' (dependente de '{updated_store_id}') precisa ser recalculado. Endpoint: {update_endpoint_path}")
            
            payload_for_dependent_module = {}
            # 1. Adicionar os 'inputs' do próprio módulo dependente ao payload
            dependent_module_current_data = self.get_data(dependent_store_id) # Dados atuais do store dependente
            payload_for_dependent_module['moduleData'] = dependent_module_current_data.get('inputs', {})

            # 2. Adicionar dados de TODAS as suas dependências
            for dep_id in all_deps_ids_for_target:
                dependency_data_content = self.get_data(dep_id) # Pega do cache em memória
                if dep_id == 'transformerInputs':
                    payload_for_dependent_module['basicData'] = dependency_data_content.get('formData', {})
                elif dep_id == 'losses': # Específico para temperatureRise
                    # O service de temperatureRise precisa dos 'results' de 'losses'
                    payload_for_dependent_module['lossesData'] = dependency_data_content.get('results', {})
                else:
                    # Para outras dependências, pode ser necessário enviar 'results' ou o dado completo
                    # Esta parte pode precisar de ajuste fino dependendo do que cada service espera
                    payload_for_dependent_module[dep_id] = dependency_data_content.get('results', dependency_data_content)
            
            full_url = f"{base_url}/{update_endpoint_path.lstrip('/')}"
            print(f"[MCPDataManager] Chamando: POST {full_url}")
            # print(f"[MCPDataManager] Payload para {dependent_store_id}: {json.dumps(payload_for_dependent_module, indent=2)}") # Cuidado com payloads grandes

            try:
                response = requests.post(full_url, json=payload_for_dependent_module, timeout=15)
                response.raise_for_status()
                print(f"[MCPDataManager] Sucesso ao chamar {full_url} para '{dependent_store_id}'. Status: {response.status_code}")
                # O endpoint do módulo (ex: /api/transformer/modules/losses/process)
                # fará o mcp_data_manager.patch_data(...), o que pode disparar mais propagações.
            except requests.exceptions.RequestException as e:
                print(f"[MCPDataManager] ERRO HTTP ao chamar {full_url} para '{dependent_store_id}': {e}")
            except Exception as e:
                print(f"[MCPDataManager] ERRO INESPERADO ao processar propagação para '{dependent_store_id}' via {full_url}: {e}")
        
        print(f"[MCPDataManager] Fim da propagação de mudanças para '{updated_store_id}'")

    def get_all_stores(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return {store_id: data.copy() for store_id, data in self._memory_store.items()}

    def clear_store(self, store_id: str) -> bool:
        with self._lock:
            if store_id not in self.store_definitions:
                return False
            self._memory_store[store_id] = {}
            self._persist_store(store_id)
            # Propagar a limpeza? Geralmente não, a menos que seja um reset.
            # self._propagate_changes(store_id) # Descomentar se necessário
            return True

    def clear_all_stores(self) -> bool:
        with self._lock:
            all_cleared = True
            for store_id in self.store_definitions:
                if not self.clear_store(store_id): # clear_store já persiste e pode propagar
                    all_cleared = False
            return all_cleared

    # Métodos de sessão (save_session, load_session, list_sessions) permanecem iguais
    def save_session(self, session_id: str, description: str = "") -> bool:
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
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT session_data FROM sessions WHERE session_id = ?', (session_id,))
            result = cursor.fetchone()
            if not result: return False
            try:
                session_data = json.loads(result[0])
                stores_to_load = session_data.get('stores', {})
                with self._lock: # Garantir que o carregamento seja atômico em relação a outras operações
                    self._memory_store.clear() # Limpa o estado atual da memória
                    self._memory_store.update(stores_to_load) # Carrega todos os stores da sessão
                    # Persiste cada store individualmente e dispara propagações
                    for store_id_loaded, data_loaded in stores_to_load.items():
                        if store_id_loaded in self.store_definitions: # Apenas se o store ainda é definido
                            self._persist_store(store_id_loaded) # Persiste
                            # Dispara propagação para cada store principal carregado
                            # TransformerInputs é o mais importante para disparar primeiro
                    if 'transformerInputs' in stores_to_load:
                        print(f"[MCPDataManager - load_session] Disparando propagação para 'transformerInputs' após carregar sessão.")
                        self._propagate_changes('transformerInputs')
                    else: # Se não houver transformerInputs, propaga para outros que possam ter sido carregados
                        for store_id_loaded in stores_to_load:
                             if store_id_loaded in self.store_definitions:
                                print(f"[MCPDataManager - load_session] Disparando propagação para '{store_id_loaded}' após carregar sessão.")
                                self._propagate_changes(store_id_loaded)

                return True
            except json.JSONDecodeError:
                return False
    
    def list_sessions(self) -> list:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT session_id, created_at, description FROM sessions ORDER BY created_at DESC')
            return [{'session_id': row[0], 'created_at': row[1], 'description': row[2]} for row in cursor.fetchall()]