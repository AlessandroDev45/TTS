# Instruções para Transformer Input

Este documento descreve o funcionamento do módulo de entrada de dados do transformador (Transformer Input), incluindo a estrutura de dados, persistência via API e funcionamento dos dropdowns de níveis de isolamento.

## Estrutura do Transformer Input

O módulo de entrada de dados do transformador é responsável por coletar todas as informações básicas necessárias para os cálculos do sistema, incluindo:

1. **Dados gerais do transformador**: potência, frequência, tipo, grupo de ligação, líquido isolante, tipo de isolamento, norma
2. **Dados de temperatura**: elevação do óleo, elevação dos enrolamentos  
3. **Dados de pesos**: parte ativa, tanque, óleo, peso total, peso adicional
4. **Dados dos enrolamentos**: tensão, corrente, conexão, classe de tensão para AT/BT/Terciário
5. **Níveis de isolamento**: NBI, SIL, TA, TI para cada enrolamento
6. **Dados de TAPs**: tensões e impedâncias para TAP maior e menor
7. **Dados de neutros**: buchas de neutro quando aplicável
8. **Tensões de ensaio**: tensões aplicadas e induzidas

Todos esses dados são armazenados via sistema de persistência API backend e servem como fonte única de verdade para o sistema.

## Dropdowns de Níveis de Isolamento (NBI, SIL, TA, TI)

### Tabela JSON

Os valores disponíveis para os dropdowns de níveis de isolamento são carregados da tabela JSON localizada em `assets/tabela.json`. Esta tabela contém todos os níveis de isolamento padronizados de acordo com as normas IEC/NBR e IEEE.

#### Estrutura da Tabela JSON

A tabela JSON tem a seguinte estrutura:

```json
{
  "insulation_levels": [
    {
      "id": "1",
      "standard": "IEC/NBR",
      "um_kv": "3.6",
      "bil_kvp": [40, 60],
      "sil_kvp": ["NA_SIL"],
      "acsd_kv_rms": [10],
      "acld_kv_rms": []
    },
    {
      "id": "2",
      "standard": "IEC/NBR",
      "um_kv": "7.2",
      "bil_kvp": [60, 75],
      "sil_kvp": ["NA_SIL"],
      "acsd_kv_rms": [20],
      "acld_kv_rms": []
    },
    // ... mais níveis de isolamento
  ]
}
```

Onde:

- `standard`: Norma aplicável (IEC/NBR ou IEEE)
- `um_kv`: Classe de tensão (kV)
- `bil_kvp`: Valores de NBI disponíveis (kVp)
- `sil_kvp`: Valores de SIL disponíveis (kVp)
- `acsd_kv_rms`: Valores de TA disponíveis (kVrms)
- `acld_kv_rms`: Valores de TI disponíveis (kVrms)

#### Tabela Completa de Níveis de Isolamento (Estilo Excel)

A tabela abaixo apresenta os níveis de isolamento padronizados de acordo com as normas IEC/NBR e IEEE:

##### Norma IEC/NBR

| ID | Um (kV) | NBI (kVp) | SIL (kVp) | TA (kVrms) | TI (kVrms) | Classificação |
|----|---------|-----------|-----------|------------|------------|---------------|
| 1  | 3.6     | 40, 60    | NA_SIL    | 10         | -          | Rotina        |
| 2  | 7.2     | 60, 75    | NA_SIL    | 20         | -          | Rotina        |
| 3  | 12      | 75, 95    | NA_SIL    | 28         | -          | Rotina        |
| 4  | 17.5    | 95, 125   | NA_SIL    | 38         | -          | Rotina        |
| 5  | 24      | 125, 145  | NA_SIL    | 50         | -          | Rotina        |
| 6  | 36      | 145, 170  | NA_SIL    | 70         | -          | Rotina        |
| 7  | 52      | 250       | NA_SIL    | 95         | -          | Rotina        |
| 8  | 72.5    | 325, 450  | NA_SIL    | 140        | 140        | Rotina        |
| 9  | 123     | 450, 550  | NA_SIL    | 230        | 230        | Rotina        |
| 10 | 145     | 550, 650  | NA_SIL    | 275        | 275        | Rotina        |
| 11 | 170     | 650, 750  | NA_SIL    | 325        | 325        | Rotina        |
| 12 | 245     | 850, 950, 1050 | NA_SIL | 395, 460  | 395, 460   | Rotina        |
| 13 | 300     | 950, 1050, 1175 | 750, 850 | 460, 510 | 460, 510 | Rotina        |
| 14 | 362     | 1050, 1175, 1300, 1425 | 850, 950, 1050 | 510, 570 | 510, 570 | Rotina |
| 15 | 420     | 1300, 1425, 1550 | 1050, 1175 | 570, 630, 680 | 570, 630, 680 | Rotina |
| 16 | 550     | 1425, 1550, 1675, 1800 | 1175, 1300, 1425 | 680, 800 | 680, 800 | Rotina |
| 17 | 800     | 1800, 1950, 2100 | 1300, 1425, 1550 | 975, 1100 | 975, 1100 | Rotina |

##### Norma IEEE

| ID | Um (kV) | NBI (kVp) | SIL/BSL (kVp) | TA (kVrms) | TI (kVrms) | Classificação |
|----|---------|-----------|---------------|------------|------------|---------------|
| 18 | 1.2     | 30        | NA_SIL        | 10         | -          | Rotina        |
| 19 | 2.5     | 45        | NA_SIL        | 15         | -          | Rotina        |
| 20 | 5.0     | 60        | NA_SIL        | 19         | -          | Rotina        |
| 21 | 8.7     | 75        | NA_SIL        | 26         | -          | Rotina        |
| 22 | 15.0    | 95, 110   | NA_SIL        | 34, 40     | -          | Rotina        |
| 23 | 25.0    | 150       | NA_SIL        | 50         | -          | Rotina        |
| 24 | 34.5    | 200       | NA_SIL        | 70         | -          | Rotina        |
| 25 | 46.0    | 250       | NA_SIL        | 95         | -          | Rotina        |
| 26 | 69.0    | 350       | NA_SIL        | 140        | 140        | Rotina        |
| 27 | 115.0   | 450, 550  | NA_SIL        | 230        | 230        | Rotina        |
| 28 | 138.0   | 550, 650  | NA_SIL        | 275        | 275        | Rotina        |
| 29 | 161.0   | 650, 750  | NA_SIL        | 325        | 325        | Rotina        |
| 30 | 230.0   | 825, 900, 1050 | NA_SIL   | 395, 460   | 395, 460   | Rotina        |
| 31 | 345.0   | 1050, 1175, 1300 | 825, 900, 975 | 555 | 555 | Rotina |
| 32 | 500.0   | 1425, 1550, 1675, 1800 | 1050, 1175, 1300 | 860 | 860 | Rotina |
| 33 | 765.0   | 1800, 1950, 2050, 2100 | 1300, 1425, 1550 | 970 | 970 | Rotina |

Notas:

1. Para classes de tensão até 72.5 kV (IEC/NBR) ou 69.0 kV (IEEE), o SIL não é aplicável (NA_SIL).
2. Para classes de tensão até 52 kV (IEC/NBR) ou 46.0 kV (IEEE), a Tensão Induzida (TI) não é aplicável.
3. Quando múltiplos valores são listados (separados por vírgula), todos são opções válidas para aquela classe de tensão.
4. A classificação "Rotina" indica que estes são os níveis de isolamento padrão para uso rotineiro.

### Comportamento Esperado

Os dropdowns de níveis de isolamento (NBI, SIL, TA, TI) são populados automaticamente via JavaScript com dados da tabela JSON (`assets/tabela.json`). O comportamento esperado é:

1. **Carregamento automático de opções**: Os dropdowns são populados com todas as opções disponíveis da tabela JSON quando a página carrega
2. **Filtragem por classe de tensão**: Quando uma classe de tensão é selecionada, as opções relevantes são priorizadas
3. **Persistência automática**: Os valores selecionados são automaticamente salvos no backend via API
4. **Carregamento de valores salvos**: Quando a página é recarregada, os valores são automaticamente restaurados do backend

### Arquitetura do Sistema

#### Frontend (JavaScript)
- **`transformer_inputs.js`**: Script principal que gerencia a inicialização do módulo
- **`api_persistence.js`**: Sistema de persistência automática via backend API  
- **`common_module.js`**: Funções comuns para carregamento de informações

#### Backend (Python)
- **`transformer_service.py`**: Serviço para processamento e validação dos dados
- **`data_routes.py`**: Rotas da API para persistência de dados
- **`data_store.py`**: Gerenciamento do armazenamento de dados

#### Dados
- **`assets/tabela.json`**: Tabela JSON com todos os níveis de isolamento padronizados

### Fluxo de Funcionamento

#### Inicialização do Módulo

1. **Carregamento da página**: Quando `transformer_inputs.html` é carregada via SPA routing
2. **Evento `moduleContentLoaded`**: Dispara a função `initTransformerInputs()` 
3. **Carregamento de informações**: `loadAndPopulateTransformerInfo()` popula o painel de informações
4. **Configuração de persistência**: `setupApiFormPersistence()` configura salvamento automático via API
5. **Carregamento de correntes**: `fillNominalCurrentsFromStore()` carrega correntes nominais calculadas
6. **Auto-atualização**: `setupNominalCurrentAutoUpdate()` configura listeners para recálculo automático

#### Persistência de Dados

1. **Salvamento automático**: Todos os campos do formulário são automaticamente salvos no backend via API quando alterados
2. **Sistema MCP**: O backend utiliza um Memory Control Panel (MCP) para gerenciar dados na sessão
3. **Cache local**: O frontend mantém cache local para melhor performance
4. **Sincronização**: Dados são sincronizados entre frontend e backend automaticamente

#### Cálculos Automáticos  

1. **Correntes nominais**: Calculadas automaticamente no backend baseadas em potência, tensão e tipo de transformador
2. **Atualização em tempo real**: Quando campos relevantes mudam, as correntes são recalculadas automaticamente
3. **Timeout de debounce**: Aguarda 400ms após mudança para permitir a persistência automática

### Implementação Técnica

#### Sistema de Persistência API

O sistema utiliza o arquivo `api_persistence.js` que implementa:

```javascript
// Sistema de persistência via backend API
const apiDataSystem = {
    baseURL: 'http://localhost:8000/api/data',
    
    // Inicializa conexão com backend
    async init() {
        // Verifica conectividade com backend
        // Configura stores disponíveis
    },
    
    // Carrega dados do store
    async loadStore(storeName) {
        // Carrega dados do backend ou cache local
    },
    
    // Salva dados no store  
    async saveStore(storeName, data) {
        // Salva dados no backend via API
    }
}
```

#### Carregamento de Dados

No `transformer_inputs.js`, os dados são carregados via:

```javascript
async function fillNominalCurrentsFromStore() {
    const store = window.apiDataSystem.getStore('transformerInputs');
    const data = await store.getData();
    
    // Verifica se os dados estão no nível raiz ou em formData
    let currentData = data || {};
    if (data && data.formData && Object.keys(data.formData).length > 0) {
        // Combina dados do nível raiz com formData
        currentData = { ...data, ...data.formData };
    }
    
    // Preenche campos com dados salvos
    const correnteAT = document.getElementById('corrente_nominal_at');
    if (correnteAT) {
        correnteAT.value = currentData.corrente_nominal_at ?? '';
    }
    // ... outros campos
}
```

#### Auto-atualização de Cálculos

```javascript
function setupNominalCurrentAutoUpdate() {
    const ids = [
        'potencia_mva', 'tensao_at', 'tensao_bt', 'tensao_terciario', 'tipo_transformador',
        'tensao_at_tap_maior', 'tensao_at_tap_menor'
    ];
    
    let updateTimeout;
    
    ids.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('change', async () => {
                // Cancela timeout anterior se existir
                if (updateTimeout) {
                    clearTimeout(updateTimeout);
                }
                
                // Aguarda persistência automática (400ms por padrão)
                updateTimeout = setTimeout(async () => {
                    await fillNominalCurrentsFromStore();
                }, 400);
            });
        }
    });
}
```

#### Backend - Processamento de Dados

No `transformer_service.py`:

```python
def extract_and_process_transformer_inputs(raw_inputs: Dict[str, Any]) -> Dict[str, Any]:
    # Processa e valida dados de entrada
    processed_data = {}
    
    # Converte valores para tipos apropriados
    processed_data["potencia_mva"] = safe_float_convert(raw_inputs.get("potencia_mva"))
    processed_data["tensao_at"] = safe_float_convert(raw_inputs.get("tensao_at"))
    processed_data["nbi_at"] = safe_float_convert(raw_inputs.get("nbi_at"))
    
    return processed_data
```

### Troubleshooting

#### Dados não são salvos

Se os dados não estiverem sendo salvos:

1. Verifique se o backend está rodando na porta 8000
2. Verifique o console do navegador para erros de conectividade
3. Confirme se `setupApiFormPersistence()` foi chamado corretamente
4. Verifique se os IDs dos campos HTML estão corretos

#### Correntes nominais não são calculadas

Se as correntes nominais não estiverem sendo calculadas automaticamente:

1. Verifique se os campos de potência e tensão estão preenchidos
2. Confirme se `setupNominalCurrentAutoUpdate()` está configurado
3. Verifique se o backend está processando os cálculos corretamente
4. Observe o console para logs de `fillNominalCurrentsFromStore()`

#### Dropdowns de isolamento não funcionam

Se os dropdowns de níveis de isolamento não estiverem funcionando:

1. Verifique se o arquivo `assets/tabela.json` está acessível
2. Confirme se o JavaScript está carregando as opções corretamente  
3. Verifique se há erros no console relacionados ao carregamento da tabela
4. Confirme se os IDs dos dropdowns estão corretos no HTML

#### Backend offline

Se o backend estiver offline:

1. O sistema automaticamente funciona em modo cache local
2. Dados não serão persistidos entre sessões
3. Mensagem de aviso será exibida no console
4. Reinicie o backend para restaurar funcionalidade completa

## Referências

### Arquivos Frontend
- **`public/pages/transformer_inputs.html`**: Interface HTML do módulo
- **`public/scripts/transformer_inputs.js`**: Script principal do módulo  
- **`public/scripts/api_persistence.js`**: Sistema de persistência via API
- **`public/scripts/common_module.js`**: Funções comuns compartilhadas
- **`public/assets/tabela.json`**: Tabela com níveis de isolamento padronizados

### Arquivos Backend  
- **`backend/services/transformer_service.py`**: Serviço para processamento de dados
- **`backend/routers/data_routes.py`**: Rotas da API para persistência
- **`backend/data_store.py`**: Gerenciamento do armazenamento de dados
- **`backend/mcp/data_manager.py`**: Memory Control Panel para sessões

### Documentação
- **`docs/instrucoes_gerais.md`**: Instruções gerais do sistema
- **`docs/help_docs/formulas_transformer_inputs.html`**: Fórmulas e cálculos detalhados
