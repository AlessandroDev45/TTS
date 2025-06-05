# Guia de Migração: Callbacks para JavaScript

Este documento descreve o processo de migração do sistema baseado em callbacks do Dash para uma solução baseada em JavaScript puro utilizando a API REST do backend.

## 1. Visão Geral da Migração

### Situação Anterior (com Callbacks)
No modelo anterior, o Dash gerenciava grande parte da interatividade e persistência dos dados através de callbacks Python:

- Os componentes HTML tinham IDs específicos para o Dash
- Callbacks Python conectavam entradas e saídas
- O estado era gerenciado pelo Dash usando `dcc.Store`
- As atualizações de UI eram gerenciadas pelo Dash

### Nova Arquitetura (JavaScript + API REST)
No novo modelo, a lógica de persistência e interatividade foi movida para o cliente:

- JavaScript puro gerencia a interatividade na interface
- A persistência é feita através de chamadas à API REST
- O estado é gerenciado pelo sistema apiDataSystem no cliente
- As atualizações de UI são disparadas por listeners de eventos JavaScript

## 2. Componentes Principais da Nova Solução

### 2.1. `api_persistence.js`
Módulo JavaScript responsável pela persistência dos dados através da API REST. Este módulo oferece:

```javascript
// Importação no módulo específico
import { setupApiFormPersistence } from './api_persistence.js';

// Configuração da persistência em formulários
await setupApiFormPersistence('id-do-formulario', 'nome-do-store');
```

### 2.2. `apiDataSystem`
Sistema global gerenciador de estado dos dados:

```javascript
// Acesso ao store
const store = window.apiDataSystem.getStore('nome-do-store');

// Obter dados
const data = await store.getData();

// Atualizar dados
await store.updateData(novosDados);
```

### 2.3. Eventos em JavaScript
Em vez de callbacks, usamos eventos JavaScript para manter a interatividade:

```javascript
// Adicionar listener
document.getElementById('id-do-input').addEventListener('change', async () => {
    // Lógica a ser executada quando o valor mudar
    await atualizarCalculos();
});

// Disparar evento manualmente
element.dispatchEvent(new Event('change', { bubbles: true }));
```

## 3. Migrando um Módulo Existente

### 3.1. Transformar Callbacks em Funções JavaScript

**Callback Original (Python)**:
```python
@app.callback(
    Output('corrente_nominal_at', 'value'),
    [Input('potencia_mva', 'value'),
     Input('tensao_at', 'value'),
     Input('tipo_transformador', 'value')]
)
def calcular_corrente_at(potencia, tensao, tipo):
    if not all([potencia, tensao, tipo]):
        return ''
    fator = 1000 if tipo == 'trifasico' else 1000 / math.sqrt(3)
    corrente = fator * potencia / tensao
    return round(corrente, 2)
```

**Função JavaScript Equivalente**:
```javascript
async function fillNominalCurrentsFromStore() {
    const store = window.apiDataSystem.getStore('transformerInputs');
    const data = await store.getData();
    
    // AT
    const correnteAT = document.getElementById('corrente_nominal_at');
    if (correnteAT) correnteAT.value = data.corrente_nominal_at ?? '';
    // BT
    const correnteBT = document.getElementById('corrente_nominal_bt');
    if (correnteBT) correnteBT.value = data.corrente_nominal_bt ?? '';
}

function setupNominalCurrentAutoUpdate() {
    const ids = [
        'potencia_mva', 'tensao_at', 'tensao_bt', 'tipo_transformador'
    ];
    ids.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('change', async () => {
                // Aguarda persistência automática
                setTimeout(async () => {
                    await fillNominalCurrentsFromStore();
                }, 400);
            });
        }
    });
}
```

### 3.2. Configurando Persistência via API

No início da função de inicialização do módulo:

```javascript
async function initModulo() {
    // Carrega painel de informações do transformador
    await loadAndPopulateTransformerInfo('transformer-info-modulo-page');
    
    // Configura persistência automatica
    setupApiFormPersistence('id-do-formulario', 'nomeDoStore');
    
    // Configura listeners e lógica específica
    setupListeners();
    setupCalculos();
}
```

### 3.3. Atualização para o Ciclo de Vida SPA

```javascript
// SPA routing: executa quando o módulo é carregado
document.addEventListener('moduleContentLoaded', (event) => {
    if (event.detail && event.detail.moduleName === 'nome_do_modulo') {
        console.log('[nome_do_modulo] SPA routing init');
        initModulo();
    }
});

// Fallback para carregamento direto (não-SPA)
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('id-do-formulario')) {
        console.log('[nome_do_modulo] DOMContentLoaded init (fallback)');
        initModulo();
    }
});
```

## 4. Fluxo de Dados na Nova Arquitetura

1. **Entrada de Dados pelo Usuário**:
   - O usuário modifica um campo no formulário
   - O evento 'change' é disparado
   - O sistema `apiDataSystem` detecta a mudança através do `setupApiFormPersistence`
   
2. **Persistência Automática**:
   - Os dados são enviados ao backend via API REST (`PATCH /api/data/stores/{store_id}`)
   - O backend armazena os dados no banco de dados
   
3. **Cálculos no Backend**:
   - O endpoint processa os dados através dos serviços apropriados
   - Os cálculos são realizados no backend
   - Os resultados são salvos no banco e enviados na resposta
   
4. **Atualização da UI**:
   - Os listeners JavaScript são disparados quando campos relevantes mudam
   - A função `fillFromStore()` é chamada para buscar dados atualizados
   - Os campos calculados são preenchidos com os novos valores

## 5. Boas Práticas na Nova Arquitetura

1. **Separação de Responsabilidades**:
   - Frontend (JS): Interação com o usuário, validação básica, exibição de dados
   - Backend (Python): Validação, cálculos complexos, persistência, lógica de negócio

2. **Estrutura do Código JavaScript**:
   - Funções de inicialização claras (ex: `initModulo()`)
   - Funções para configurar listeners (ex: `setupListeners()`)
   - Funções para preencher dados do store (ex: `fillFromStore()`)
   - Funções para cálculos locais quando necessário

3. **Gestão de Estado**:
   - Utilize `window.apiDataSystem` como fonte da verdade
   - Evite estado local quando possível
   - Certifique-se de que alterações relevantes disparem os eventos corretos

## 6. Troubleshooting Comum

### 6.1. Campos Não Estão Sendo Atualizados
- Verifique se o ID do campo no HTML corresponde exatamente ao esperado pelo JavaScript
- Confirme que o listener está sendo adicionado corretamente
- Verifique se o campo está dentro do formulário configurado com `setupApiFormPersistence`
- Verifique o console para erros de JavaScript

### 6.2. Dados Não Persistem
- Confirme que o store foi configurado corretamente no backend
- Verifique se o caminho do API endpoint está correto
- Examine a resposta do servidor usando a aba Network do DevTools
- Verifique se há erros no console do navegador ou nos logs do backend

### 6.3. Cálculos Incorretos
- Verifique se os dados estão sendo enviados corretamente ao backend
- Compare a implementação JavaScript com a lógica original do callback Python
- Examine os dados salvos no banco de dados usando o SQLite Browser

### 6.4. Estrutura de Dados Inconsistente
- Esteja ciente de que alguns dados calculados podem ser armazenados no nível raiz do objeto `data` e não dentro de `formData`
- Ao acessar dados do store, utilize:
  ```javascript
  const data = await store.getData();
  let currentData = data || {};
  if (data && data.formData && Object.keys(data.formData).length > 0) {
      currentData = { ...data, ...data.formData }; // Combina ambas fontes
  }
  ```
- Para dados salvos pelo backend, verifique no nível raiz primeiro e depois em `formData`
