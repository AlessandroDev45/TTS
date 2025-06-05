# Guia para Manter a Persistência em Novas Implementações do TTS

Este guia detalha as práticas recomendadas para garantir que a persistência de dados do TTS continue funcionando corretamente à medida que novas funcionalidades, módulos ou campos são adicionados.

## 1. Princípio Fundamental: A Única Fonte da Verdade
No coração da persistência do TTS está o MCPDataManager (`backend/mcp/data_manager.py`) e o banco de dados SQLite (`tts_data.db`). Eles são a única fonte da verdade para todos os dados da aplicação.

- Qualquer alteração de dado deve passar pelo MCPDataManager (`set_data` ou `patch_data`)
- Qualquer leitura de dado deve vir do MCPDataManager (`get_data`)

## 2. Checklist para Novas Implementações
Ao adicionar um novo módulo, um novo campo a um módulo existente, ou uma nova funcionalidade que manipule dados, siga este checklist:

### 2.1. Adicionando Novos Campos a Módulos Existentes

Se você está adicionando inputs (text, number, select, radio, checkbox, textarea) a um formulário HTML de um módulo existente que já tem persistência configurada (ex: `transformer_inputs.html`, `losses.html`):
#### HTML:
- Adicione o novo campo ao HTML (ex: `<input type="text" id="novo_campo_id">`)
- Muito importante: Dê ao campo um id único e descritivo. Este id será a chave no JSON dos dados do formulário

#### JavaScript do Módulo (`public/scripts/modulo_existente.js`):
- Nenhuma alteração é necessária na configuração da persistência. O `setupApiFormPersistence` já captura todos os elementos com id dentro do formulário especificado
- Se o novo campo for de select, radio ou checkbox, e seu valor precisar ser predefinido ou gerado por JavaScript (e não apenas o usuário digitando), garanta que o JavaScript do módulo, após carregar os dados persistidos, atualize este campo e, se for o caso, dispare um evento change (`element.dispatchEvent(new Event('change', { bubbles: true }));`) para que a persistência detecte a mudança

#### Backend (`backend/mcp/data_manager.py`):
- Nenhuma alteração é necessária no MCPDataManager para campos dentro de stores já existentes, pois ele armazena o JSON completo
- No entanto, se o novo campo afetar cálculos ou lógica em serviços (ex: um novo peso afeta o cálculo de temperatura), você precisará:
  - Atualizar a assinatura da função/modelo de entrada do serviço para incluir o novo campo
  - Modificar a lógica de cálculo no serviço para usar o novo campo

### 2.2. Adicionando um Novo Módulo Completo

Se você está adicionando um novo módulo com seu próprio formulário e lógica de dados (ex: `analise_oleo.html`, `analise_oleo.js`):

#### HTML (`public/pages/novo_modulo.html`):
- Crie o arquivo HTML para o novo módulo.
- Dê um id único ao formulário principal ou ao container de inputs (ex: `<form id="analise-oleo-form">`).

#### JavaScript (`public/scripts/novo_modulo.js`):
- Crie o arquivo JavaScript para o novo módulo.
- No início do script, adicione:

```javascript
import { loadAndPopulateTransformerInfo } from './common_module.js';
import { setupApiFormPersistence } from './api_persistence.js';
// ... (outras importações específicas do módulo)

async function initNovoModulo() {
    console.log('Módulo Novo Carregado!');

    const transformerInfoPlaceholderId = 'transformer-info-novo_modulo-page';
    await loadAndPopulateTransformerInfo(transformerInfoPlaceholderId);

    // Configure a persistência para o formulário principal do módulo
    await setupApiFormPersistence('analise-oleo-form', 'nome_do_novo_store');

    // ... (restante da lógica de inicialização do seu módulo)
}

// SPA routing: executa quando o módulo é carregado
document.addEventListener('moduleContentLoaded', (event) => {
    if (event.detail && event.detail.moduleName === 'nome_do_modulo_html') {
        console.log('[nome_do_modulo_html] SPA routing init');
        initNovoModulo();
    }
});

// Fallback para carregamento direto da página (se não for SPA)
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('analise-oleo-form')) { // ID do formulário principal
        console.log('[nome_do_modulo_html] DOMContentLoaded init (fallback)');
        initNovoModulo();
    }
});
```

- `nome_do_novo_store`: Escolha um nome único e descritivo para este store (ex: 'oilAnalysis', 'dissolvedGasAnalysis'). Este será o store_id no backend.
- `nome_do_modulo_html`: Este é o nome do arquivo HTML do seu módulo sem a extensão (ex: 'analise_oleo').

#### Adicionar o Novo Módulo ao Roteamento do main.js:
- Abra `public/scripts/main.js`.
- No `navbar-nav`, adicione um novo `<li>` com o data-module apontando para o nome do seu novo módulo.

```html
<li class="nav-item">
    <a class="nav-link" href="#" data-module="nome_do_modulo_html" data-bs-toggle="tooltip" data-bs-placement="bottom" title="Nome do Módulo">
        <i class="fas fa-icon"></i>
        <span>Nome do<br>Módulo</span>
    </a>
</li>
```

#### Backend (`backend/mcp/data_manager.py`):
- Abra `backend/mcp/data_manager.py`.
- No dicionário `self.store_definitions` dentro do `__init__`, adicione uma nova entrada para o seu store:

```python
self.store_definitions = {
    # ... (stores existentes)
    'nome_do_novo_store': { # Deve ser o mesmo nome passado em setupApiFormPersistence
        'key': 'nome_do_novo_store',
        'dependencies': ['transformer_inputs'], # Se depender de dados básicos
        'propagates_to': []
    },
    # ...
}
```

- `dependencies`: Se este novo módulo usar dados do transformer_inputs (ou outros stores), liste-os aqui. Isso é para controle interno do MCP, embora a propagação real precise de lógica explícita.
- `propagates_to`: Se este módulo for uma fonte primária de dados que outros módulos dependem, liste os store_ids aqui.

#### Backend (Opcional - Novo Serviço/Router):
- Se o seu novo módulo realizar cálculos complexos que exigem lógica de backend, você pode criar um novo serviço (ex: `backend/services/analise_oleo_service.py`) e um novo router (ex: `backend/routers/analise_oleo_routes.py`).
- Lembre-se de que esses serviços/routers devem usar a única instância do MCPDataManager importando-a de `backend/routers/data_routes.py`.
- Inclua o novo router no `backend/main.py` (`app.include_router(analise_oleo_routes.router)`).

### 2.3. Modificando Fluxos de Dados e Cálculos

Se você está mudando como os dados são calculados ou como eles se propagam:

#### Serviços (`backend/services/*.py`):
- Ao modificar um serviço, lembre-se que ele recebe dados como entrada e retorna resultados. Ele não deve chamar `mcp_data_manager.set_data()` ou `patch_data()`. Essa responsabilidade é do router.
- Garanta que a lógica de cálculo seja isolada e testável.

#### Rotas da API (`backend/routers/*.py`):
Quando um endpoint recebe dados, ele deve:
- Chamar o serviço relevante para realizar cálculos (passando os dados necessários).
- Chamar `mcp_data_manager.patch_data('store_id', {'campo_no_json': resultado_do_calculo})` para persistir os resultados.
- Considerar chamar `_propagate_changes()` explicitamente se a mudança for fundamental e precisar de propagação imediata (o `patch_data` já chama internamente, mas é bom revisar o fluxo).

#### Propagação (`backend/mcp/data_manager.py`):
- Se um novo tipo de dado precisar acionar a atualização de outros stores, revise o método `_propagate_changes(self, store_id: str)` no MCPDataManager.
- Por exemplo, se o losses agora gerar um valor que o temperature_rise precisa para seu cálculo, losses deve estar na lista de `dependencies` de temperature_rise, e losses talvez precise de uma lógica de `propagates_to` para temperature_rise. A lógica de `_update_global_info()` é um bom exemplo de propagação.

## 3. Ferramentas Essenciais para Manutenção da Persistência

### Ferramentas de Desenvolvedor do Navegador (F12):
- **Network Tab**: Monitore todas as requisições GET, POST, PATCH para `/api/data/stores/...`. Verifique os status codes (200 OK), payloads de requisição e respostas.
- **Console Tab**: Observe os logs do `api_persistence.js` e dos scripts dos módulos, que indicam quando os dados são salvos ou carregados.
- **Application Tab -> Local Storage**: `api_persistence.js` usa um cache em memória, mas o localStorage não é mais a fonte de verdade para a persistência principal. No entanto, é bom estar ciente disso se houver interações legadas.

### DB Browser for SQLite:
- Use esta ferramenta para abrir o arquivo `tts_data.db` e inspecionar diretamente os dados na tabela `data_stores` e `sessions`. Isso é a prova definitiva de que os dados foram persistidos.

### Logs do Backend:
- Habilite o logging no backend (configurado em `backend/main.py` com `logging.basicConfig`). Observe os logs do MCPDataManager para mensagens como "Store 'X' carregado do arquivo." ou "Estado salvo no arquivo.".

## 4. Estrutura de Dados e Acesso
Os dados podem ser armazenados em diferentes níveis da estrutura do store:

- **Dados de Formulário**: São armazenados geralmente em `data.formData` e representam os valores dos inputs do formulário.
- **Dados Calculados pelo Backend**: São frequentemente armazenados no nível raiz de `data` e representam valores calculados pelo backend.

Para garantir acesso correto aos dados, use o seguinte padrão:

```javascript
async function getData() {
    const store = window.apiDataSystem.getStore('storeId');
    const data = await store.getData();
    
    // Combina dados do nível raiz e formData para acesso consistente
    let currentData = data || {};
    if (data && data.formData && Object.keys(data.formData).length > 0) {
        currentData = { ...data, ...data.formData };
    }
    
    return currentData;
}
```

## 5. Estratégia de Teste Contínua
Sempre que fizer uma nova implementação:

- **Testes Manuais Iniciais**: Preencha os dados no novo campo/módulo. Navegue para outro módulo e volte. Feche o navegador e reabra. Reinicie o servidor FastAPI. Verifique se os dados persistem em todas as situações.
- **Limpeza de Dados**: Teste a funcionalidade de "Limpar Campos" para o módulo atual e para todos os módulos.
- **Teste de Regressão**: Verifique se as funcionalidades existentes e seus dados ainda persistem corretamente após a nova implementação.