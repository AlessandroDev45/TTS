# Padrão para Persistência de Dados e Uso do MCP no TTS

Este documento define o padrão arquitetural para a persistência de dados e o uso do Model Context Protocol (MCP) no sistema TTS. O objetivo é garantir que os dados inseridos pelo usuário sejam persistidos e armazenados centralmente no MCP, e que qualquer atualização de dados resulte na atualização automática de todas as dependências relacionadas através de um mecanismo de propagação estruturado.

## 1. Princípio Central: A Única Fonte da Verdade

O `MCPDataManager` (`backend/mcp/data_manager.py`) e o banco de dados SQLite (`tts_data.db`) são a **Única Fonte da Verdade** para todos os dados da aplicação.

*   Qualquer alteração de dado deve passar pelo `MCPDataManager` (`set_data` ou `patch_data`).
*   Qualquer leitura de dado deve vir do `MCPDataManager` (`get_data`).

## 2. Fluxo de Dados (Frontend -> Backend -> DB)

O fluxo de dados para persistência segue o seguinte caminho:

*   **Frontend:** Captura dados de formulários (usando `api_persistence.js` ou lógica similar) e envia para endpoints de API específicos no backend (ex: `/api/data/stores/{store_id}`).
*   **Router (Backend):** Recebe os dados da API, valida-os se necessário e chama o `MCPDataManager` para persistir os dados usando `patch_data` ou `set_data` para o `store_id` correspondente.
*   **MCPDataManager:** Atualiza seu estado interno e persiste os dados no banco de dados SQLite (`tts_data.db`). Após a persistência, aciona o mecanismo de propagação de dependências (`_propagate_changes`).

## 3. Definição de Stores (`backend/mcp/data_manager.py`)

Cada store representa um conjunto lógico de dados. A definição de cada store no dicionário `self.store_definitions` dentro da classe `MCPDataManager` deve incluir os seguintes campos:

*   `key`: Identificador único do store (string).
*   `dependencies`: Lista de `store_id`s dos quais este store depende para seus cálculos ou dados (lista de strings).
*   `propagates_to`: (Opcional) Lista de `store_id`s que dependem diretamente deste store. Pode ser redundante se `dependencies` for usado para determinar a propagação reversa, mas pode ser útil para otimização ou clareza.
*   `update_logic_endpoint`: O caminho do endpoint da API (relativo a `/api/data/`) responsável por calcular/atualizar os dados deste store com base em suas dependências (string). Ex: `../transformer/modules/losses/process`.

## 4. Mecanismo de Propagação de Dependências (`backend/mcp/data_manager.py`)

O mecanismo de propagação garante que as atualizações de dados em um store acionem a recalcularão e persistência dos stores dependentes:

*   Quando o `MCPDataManager` persiste dados para um store `A` (via `patch_data` ou `set_data`), o método `_propagate_changes(store_id_A)` é acionado.
*   `_propagate_changes` identifica todos os stores `B` na `self.store_definitions` que listam `store_id_A` em suas `dependencies`.
*   Para cada store dependente `B` encontrado:
    *   O `MCPDataManager` obtém o `update_logic_endpoint` definido para o store `B`.
    *   Ele faz uma chamada interna (backend-to-backend) para este endpoint, passando os dados necessários (obtidos via `get_data` para o store `A` e quaisquer outras dependências de `B`).
    *   O endpoint de `update_logic_endpoint` de `B` executa a lógica de cálculo e chama `mcp_data_manager.patch_data(store_id_B, novo_dados_B)` para persistir os resultados.
    *   Esta chamada a `patch_data` para o store `B` pode, por sua vez, acionar `_propagate_changes(store_id_B)`, criando uma cadeia de atualizações para stores que dependem de `B`.

## 5. Adição de Novos Elementos

Ao adicionar novos campos a módulos existentes ou novos módulos completos, siga as diretrizes do documento [`TTS/docs/instrucoes_persistencia_dados.md`](TTS/docs/instrucoes_persistencia_dados.md:1-176), complementadas pelo padrão definido aqui, especialmente no que diz respeito à definição de novos stores e seus `dependencies` e `update_logic_endpoint`.

## 6. Documentação

Manter o arquivo [`TTS/docs/instrucoes_persistencia_dados.md`](TTS/docs/instrucoes_persistencia_dados.md:1-176) e este documento (`TTS/docs/padrao_persistencia_mcp.md`) atualizados com o padrão formalizado.

## 7. Testes

Continuar seguindo a estratégia de teste contínua descrita no documento [`TTS/docs/instrucoes_persistencia_dados.md`](TTS/docs/instrucoes_persistencia_dados.md:1-176), focando na persistência e na correta propagação das atualizações.

## Diagrama do Fluxo de Dados e Propagação

```mermaid
graph TD
    A[Frontend (HTML/JS)] --> B{API Router (PATCH/POST)};
    B --> C[MCPDataManager];
    C --> D[SQLite DB];
    C -- patch_data/set_data --> D;
    C -- Triggers --> E{_propagate_changes};
    E --> F{Identifica Stores Dependentes};
    F --> G[Para cada Store Dependente B];
    G -- Obtém update_logic_endpoint --> C;
    G --> H{Chama Endpoint de B (Backend-to-Backend)};
    H --> I[Serviço/Router de B];
    I -- get_data (Dependências) --> C;
    I -- patch_data(B, novos_dados) --> C;
    C -- Propagação Recursiva --> E;
    C -- get_data --> A;