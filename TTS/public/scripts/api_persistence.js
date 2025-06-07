// public/scripts/api_persistence.js
// Sistema de persistência via API REST para o TTS

// Sistema global de gerenciamento de dados
const apiDataSystem = {
    baseURL: 'http://localhost:8000/api/data',
    stores: new Map(),
    initialized: false,
    useLocalStorageFallback: false, // Adicionado para rastrear o modo de fallback

    // Inicializa o sistema
    async init() {
        console.log('[apiDataSystem] Iniciando apiDataSystem.init');
        if (this.initialized) {
            console.log('[apiDataSystem] apiDataSystem já inicializado');
            return;
        }

        try {
            console.log(`[apiDataSystem] Testando conectividade com backend em ${this.baseURL}/health`);
            const response = await fetch(`${this.baseURL}/health`);
            if (!response.ok) {
                console.warn(`[apiDataSystem] Backend não disponível (Status: ${response.status}), usando fallback localStorage`);
                this.useLocalStorageFallback = true;
            } else {
                console.log('[apiDataSystem] Conectividade com backend OK.');
                this.useLocalStorageFallback = false;
            }
            this.initialized = true;
            console.log('[apiDataSystem] apiDataSystem.init concluído. Fallback ativo:', this.useLocalStorageFallback);
        } catch (error) {
            console.warn('[apiDataSystem] Erro ao conectar com backend:', error);
            this.useLocalStorageFallback = true;
            this.initialized = true;
            console.log('[apiDataSystem] apiDataSystem.init concluído com erro. Fallback ativo:', this.useLocalStorageFallback);
        }
    },

    // Obtém um store específico
    getStore(storeId) {
        console.log(`[apiDataSystem] Obtendo store: ${storeId}`);
        if (!this.stores.has(storeId)) {
            console.log(`[apiDataSystem] Criando novo DataStore para: ${storeId}`);
            this.stores.set(storeId, new DataStore(storeId, this));
        }
        console.log(`[apiDataSystem] Retornando store para: ${storeId}`);
        return this.stores.get(storeId);
    }
};

// Classe para gerenciar um store individual
class DataStore {
    constructor(storeId, apiSystem) {
        this.storeId = storeId;
        this.apiSystem = apiSystem;
        this.cache = null;
        this.lastFetch = 0;
        this.cacheTimeout = 5000; // 5 segundos
        console.log(`[DataStore] Instância criada para store: ${storeId}`);
    }

    // Carrega dados do store
    async getData() {
        console.log(`[DataStore:${this.storeId}] Iniciando getData`);
        await this.apiSystem.init();

        // Verifica cache
        const now = Date.now();
        if (this.cache && (now - this.lastFetch) < this.cacheTimeout) {
            console.log(`[DataStore:${this.storeId}] Usando cache (válido por ${this.cacheTimeout}ms)`);
            return this.cache;
        }
        console.log(`[DataStore:${this.storeId}] Cache expirado ou inexistente. Buscando dados.`);

        try {
            if (this.apiSystem.useLocalStorageFallback) {
                console.log(`[DataStore:${this.storeId}] getData: Usando fallback localStorage`);
                const data = localStorage.getItem(`store_${this.storeId}`);
                this.cache = data ? JSON.parse(data) : {};
                console.log(`[DataStore:${this.storeId}] getData: Dados obtidos via localStorage`, this.cache);
            } else {
                console.log(`[DataStore:${this.storeId}] getData: Buscando do backend em ${this.apiSystem.baseURL}/stores/${this.storeId}`);
                const response = await fetch(`${this.apiSystem.baseURL}/stores/${this.storeId}`);
                if (response.ok) {
                    this.cache = await response.json();
                    console.log(`[DataStore:${this.storeId}] getData: Dados obtidos do backend`, this.cache);
                } else {
                    console.warn(`[DataStore:${this.storeId}] getData: Erro ao carregar store do backend (Status: ${response.status}). Cache definido como vazio.`, response);
                    this.cache = {};
                }
            }

            this.lastFetch = now;
            console.log(`[DataStore:${this.storeId}] getData: Concluído`);
            return this.cache;
        } catch (error) {
            console.error(`[DataStore:${this.storeId}] getData: Erro ao carregar dados:`, error);
            this.cache = {}; // Define cache como vazio em caso de erro
            console.log(`[DataStore:${this.storeId}] getData: Concluído com erro`);
            return {};
        }
    }

    // Atualiza dados do store
    async updateData(newData) {
        console.log(`[DataStore:${this.storeId}] Iniciando updateData com dados:`, newData);
        await this.apiSystem.init();

        try {
            if (this.apiSystem.useLocalStorageFallback) {
                console.log(`[DataStore:${this.storeId}] updateData: Usando fallback localStorage`);
                const currentData = await this.getData(); // Obtém dados atuais (pode vir do cache ou localStorage)
                const updatedData = { ...currentData, ...newData };
                localStorage.setItem(`store_${this.storeId}`, JSON.stringify(updatedData));
                this.cache = updatedData; // Atualiza cache local
                console.log(`[DataStore:${this.storeId}] updateData: Dados salvos no localStorage`, updatedData);
            } else {
                let response;
                if (this.storeId === 'transformerInputs') {
                    // Caso especial para transformerInputs: POST para /api/transformer/inputs
                    console.log(`[DataStore:${this.storeId}] updateData: Enviando POST para /api/transformer/inputs`);
                    response = await fetch(`${this.apiSystem.baseURL.replace('/api/data', '/api/transformer')}/inputs`, {
                        method: 'POST', // Usar POST conforme o fluxo
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(newData.formData) // Enviar apenas formData, pois o backend espera isso
                    });
                } else {
                    // Comportamento padrão: PATCH para /api/data/stores/{storeId}
                    console.log(`[DataStore:${this.storeId}] updateData: Enviando PATCH para backend em ${this.apiSystem.baseURL}/stores/${this.storeId}`);
                    response = await fetch(`${this.apiSystem.baseURL}/stores/${this.storeId}`, {
                        method: 'PATCH',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(newData)
                    });
                }

                if (response.ok) {
                    this.cache = await response.json(); // Atualiza cache com resposta do backend
                    console.log(`[DataStore:${this.storeId}] updateData: Dados atualizados no backend`, this.cache);
                } else {
                    console.error(`[DataStore:${this.storeId}] updateData: Erro ao salvar store no backend (Status: ${response.status}). Tentando localStorage como fallback.`, response);
                    // Fallback automático para localStorage em caso de erro do backend
                    const currentData = JSON.parse(localStorage.getItem(`store_${this.storeId}`) || '{}');
                    const updatedData = { ...currentData, ...newData };
                    localStorage.setItem(`store_${this.storeId}`, JSON.stringify(updatedData));
                    this.cache = updatedData;
                    console.log(`[DataStore:${this.storeId}] updateData: Dados salvos no localStorage como fallback`, updatedData);
                }
            }

            console.log(`[DataStore:${this.storeId}] updateData: Concluído`);
        } catch (error) {
            console.error(`[DataStore:${this.storeId}] updateData: Erro ao atualizar dados:`, error);
            console.log(`[DataStore:${this.storeId}] updateData: Usando localStorage como fallback de emergência`);
            // Fallback de emergência para localStorage em caso de erro geral (rede, etc.)
            try {
                const currentData = JSON.parse(localStorage.getItem(`store_${this.storeId}`) || '{}');
                const updatedData = { ...currentData, ...newData };
                localStorage.setItem(`store_${this.storeId}`, JSON.stringify(updatedData));
                this.cache = updatedData;
                console.log(`[DataStore:${this.storeId}] updateData: Dados salvos no localStorage para ${this.storeId}`);
            } catch (localError) {
                console.error(`[DataStore:${this.storeId}] updateData: Erro crítico - nem backend nem localStorage funcionaram:`, localError);
            }
            console.log(`[DataStore:${this.storeId}] updateData: Concluído com erro`);
        }
    }

    // Define dados completos do store
    async setData(data) {
        console.log(`[DataStore:${this.storeId}] Iniciando setData com dados:`, data);
        await this.apiSystem.init();

        try {
            if (this.apiSystem.useLocalStorageFallback) {
                console.log(`[DataStore:${this.storeId}] setData: Usando fallback localStorage`);
                localStorage.setItem(`store_${this.storeId}`, JSON.stringify(data));
                this.cache = data;
                console.log(`[DataStore:${this.storeId}] setData: Dados definidos no localStorage`, this.cache);
            } else {
                console.log(`[DataStore:${this.storeId}] setData: Enviando para backend em ${this.apiSystem.baseURL}/stores/${this.storeId}`);
                const response = await fetch(`${this.apiSystem.baseURL}/stores/${this.storeId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });

                if (response.ok) {
                    this.cache = await response.json(); // Atualiza cache com resposta do backend
                    console.log(`[DataStore:${this.storeId}] setData: Dados definidos no backend`, this.cache);
                } else {
                    console.error(`[DataStore:${this.storeId}] setData: Erro ao definir store no backend (Status: ${response.status}).`, response);
                    // Não há fallback automático para PUT, pois PUT é para substituir, não mesclar.
                }
            }
            console.log(`[DataStore:${this.storeId}] setData: Concluído`);
        } catch (error) {
            console.error(`[DataStore:${this.storeId}] setData: Erro ao definir dados:`, error);
            console.log(`[DataStore:${this.storeId}] setData: Concluído com erro`);
        }
    }
}

// Função para configurar persistência automática em formulários
async function setupApiFormPersistence(formIdOrElement, storeId) {
    console.log(`[setupApiFormPersistence] *** INICIANDO *** para form: ${typeof formIdOrElement === 'string' ? formIdOrElement : 'Elemento'}, store: ${storeId}`);

    await apiDataSystem.init();
    console.log(`[setupApiFormPersistence] Sistema API inicializado. Fallback ativo: ${apiDataSystem.useLocalStorageFallback}`);

    let formElement;
    if (typeof formIdOrElement === 'string') {
        console.log(`[setupApiFormPersistence] Procurando formulário por ID: ${formIdOrElement}`);
        formElement = document.getElementById(formIdOrElement);
        if (!formElement) {
            console.error(`[setupApiFormPersistence] *** ERRO *** Formulário ${formIdOrElement} não encontrado`);
            console.log(`[setupApiFormPersistence] Elementos disponíveis:`, document.querySelectorAll('form, [id*="form"]'));
            console.log(`[setupApiFormPersistence] *** CONCLUÍDO COM ERRO ***`);
            return;
        }
        console.log(`[setupApiFormPersistence] *** FORMULÁRIO ENCONTRADO *** ${formIdOrElement}`);
    } else if (formIdOrElement instanceof Element) {
        formElement = formIdOrElement;
        console.log(`[setupApiFormPersistence] Usando elemento fornecido diretamente`);
    } else {
        console.warn(`[setupApiFormPersistence] Parâmetro inválido para formIdOrElement:`, formIdOrElement);
        console.log(`[setupApiFormPersistence] *** CONCLUÍDO COM AVISO ***`);
        return;
    }

    const store = apiDataSystem.getStore(storeId);
    console.log(`[setupApiFormPersistence] Store ${storeId} obtido.`);

    console.log(`[setupApiFormPersistence] Carregando dados existentes para preencher formulário`);
    // Carrega dados existentes
    try {
        const existingData = await store.getData();
        if (existingData && existingData.formData) {
            console.log(`[setupApiFormPersistence] Dados encontrados para o store ${storeId}. Preenchendo formulário.`);
            fillFormWithData(formElement, existingData.formData);
            console.log(`[setupApiFormPersistence] Formulário preenchido.`);
        } else {
            console.log(`[setupApiFormPersistence] Nenhum dado existente encontrado para o store ${storeId}.`);
        }
    } catch (error) {
        console.error(`[setupApiFormPersistence] Erro ao carregar dados existentes para preencher formulário:`, error);
    }


    // Configura listeners para auto-save
    const inputs = formElement.querySelectorAll('input, select, textarea');
    console.log(`[setupApiFormPersistence] Configurando listeners para ${inputs.length} inputs no formulário ${formElement.id || formElement.tagName}`);

    inputs.forEach((input, index) => {
        // Evita adicionar múltiplos listeners se a função for chamada mais de uma vez para o mesmo elemento
        if (input._apiPersistenceListener) {
             console.log(`[setupApiFormPersistence] Listener já existe para input ${input.id || input.name}. Pulando.`);
             return;
        }

        console.log(`[setupApiFormPersistence] Configurando listener ${index + 1}: ID=${input.id || 'N/A'}, Name=${input.name || 'N/A'}, Type=${input.type || 'N/A'}`);
        const listener = async () => {
            console.log(`[setupApiFormPersistence] *** MUDANÇA DETECTADA *** em ID=${input.id || 'N/A'}, Name=${input.name || 'N/A'}`);
            const formData = collectFormData(formElement);
            console.log(`[setupApiFormPersistence] Dados coletados:`, formData);

            // Salva dados de forma não-bloqueante
            console.log(`[setupApiFormPersistence] Enviando dados para salvamento no store ${storeId}`);
            store.updateData({ formData }).catch(error => {
                console.error(`[setupApiFormPersistence] Erro ao salvar:`, error);
            });
            console.log(`[setupApiFormPersistence] Dados enviados para salvamento (não-bloqueante)`);

            // Sistema de propagação em background (não-bloqueante)
            // A propagação agora é tratada no backend após a persistência.
            // O frontend apenas dispara eventos para que os componentes reajam à mudança.
            console.log(`[api_persistence] Disparando evento de atualização para ${storeId}`);
            if (storeId === 'transformerInputs') {
                 document.dispatchEvent(new CustomEvent('transformerDataUpdated', {
                     detail: { storeId, formData }
                 }));
                 console.log('[api_persistence] Evento transformerDataUpdated disparado');
            } else {
                 document.dispatchEvent(new CustomEvent('moduleDataUpdated', {
                     detail: { storeId, formData }
                 }));
                 console.log(`[api_persistence] Evento moduleDataUpdated para ${storeId} disparado`);
            }
            console.log(`[api_persistence] Propagação no frontend concluída para ${storeId}`);
        };

        input.addEventListener('change', listener);
        input._apiPersistenceListener = listener; // Marca o input para evitar duplicação
        // Adiciona listener para 'input' também para campos de texto que mudam rapidamente
        if (input.type === 'text' || input.type === 'number') {
             input.addEventListener('input', listener);
        }
    });

    const elementId = formElement.id || formElement.className || 'elemento-sem-id';
    console.log(`[setupApiFormPersistence] Persistência configurada para ${elementId} → ${storeId}. *** CONCLUÍDO ***`);
}

// Coleta dados do formulário
function collectFormData(formElement) {
    console.log('[api_persistence] collectFormData: Iniciando');
    const formData = {};
    const inputs = formElement.querySelectorAll('input, select, textarea');

    inputs.forEach(input => {
        if (input.id) {
            if (input.type === 'checkbox') {
                formData[input.id] = input.checked;
            } else if (input.type === 'radio') {
                if (input.checked) {
                    formData[input.name] = input.value;
                }
            } else {
                // Converte strings vazias para null para campos numéricos
                if (input.type === 'number' && input.value === '') {
                    formData[input.id] = null;
                } else {
                    formData[input.id] = input.value;
                }
            }
        }
    });
    console.log('[api_persistence] collectFormData: Concluído. Dados:', formData);
    return formData;
}

// Preenche formulário com dados
function fillFormWithData(formElement, data) {
    console.log('[api_persistence] fillFormWithData: Iniciando com dados:', data);
    Object.keys(data).forEach(key => {
        const element = formElement.querySelector(`#${key}`);
        if (element) {
            if (element.type === 'checkbox') {
                element.checked = data[key];
                console.log(`[api_persistence] fillFormWithData: Preenchido checkbox ${key} com ${data[key]}`);
            } else if (element.type === 'radio') {
                if (element.value === data[key]) {
                    element.checked = true;
                    console.log(`[api_persistence] fillFormWithData: Preenchido radio ${key} com ${data[key]}`);
                }
            } else if (element.tagName === 'SELECT') {
                // Tratamento especial para dropdowns/select
                const value = data[key];
                if (value !== null && value !== undefined) {
                    element.value = value;
                    // Verifica se o valor foi realmente definido
                    if (element.value === value) {
                        console.log(`[api_persistence] fillFormWithData: Preenchido select ${key} com "${value}"`);
                    } else {
                        console.warn(`[api_persistence] fillFormWithData: Falha ao definir valor "${value}" para select ${key}. Valor atual: "${element.value}"`);
                        // Tenta encontrar a opção correspondente
                        const option = element.querySelector(`option[value="${value}"]`);
                        if (option) {
                            option.selected = true;
                            console.log(`[api_persistence] fillFormWithData: Opção "${value}" selecionada manualmente para ${key}`);
                        } else {
                            console.warn(`[api_persistence] fillFormWithData: Opção "${value}" não encontrada para select ${key}`);
                        }
                    }
                } else {
                    console.log(`[api_persistence] fillFormWithData: Valor null/undefined para select ${key}, mantendo valor atual`);
                }
            } else {
                // Para inputs normais
                const value = data[key];
                if (value !== null && value !== undefined) {
                    // Formatar campos numéricos com 2 casas decimais
                    if (element.type === 'number' && typeof value === 'number' && !isNaN(value)) {
                        element.value = value.toFixed(2);
                        console.log(`[api_persistence] fillFormWithData: Preenchido input numérico ${key} com "${element.value}" (valor original: ${value})`);
                    } else {
                        element.value = value;
                        console.log(`[api_persistence] fillFormWithData: Preenchido input ${key} com "${value}"`);
                    }
                } else {
                    element.value = '';
                    console.log(`[api_persistence] fillFormWithData: Limpo input ${key} (valor era null/undefined)`);
                }
            }
        } else {
             console.warn(`[api_persistence] fillFormWithData: Elemento #${key} não encontrado no formulário.`);
        }
    });
    console.log('[api_persistence] fillFormWithData: Concluído');
}

// A função handleDataPropagation agora é simplificada para apenas disparar eventos no frontend.
// A lógica de propagação e chamada de services é tratada no backend pelo MCPDataManager.
async function handleDataPropagation(storeId, formData) {
    console.log(`[api_persistence] handleDataPropagation (Frontend): Dados para ${storeId} foram atualizados. Disparando evento local.`);

    // Dispara evento específico do módulo ou global
    if (storeId === 'transformerInputs') {
        document.dispatchEvent(new CustomEvent('transformerDataUpdated', {
            detail: { storeId, formData }
        }));
        console.log('[api_persistence] Evento transformerDataUpdated disparado');
    } else {
        document.dispatchEvent(new CustomEvent('moduleDataUpdated', {
            detail: { storeId, formData }
        }));
        console.log(`[api_persistence] Evento moduleDataUpdated para ${storeId} disparado`);
    }
    console.log(`[api_persistence] handleDataPropagation (Frontend): Concluído para ${storeId}`);
}


// Função para aguardar o sistema de persistência estar disponível
async function waitForApiSystem() {
    let attempts = 0;
    const maxAttempts = 50; // 5 segundos máximo

    while (!window.apiDataSystem && attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 100));
        attempts++;
    }

    return window.apiDataSystem || null;
}


// Expõe variáveis e funções essenciais globalmente para acesso por outros scripts
window.apiDataSystem = apiDataSystem;
window.setupApiFormPersistence = setupApiFormPersistence;
window.collectFormData = collectFormData;
window.fillFormWithData = fillFormWithData;
window.handleDataPropagation = handleDataPropagation;
window.waitForApiSystem = waitForApiSystem;

// Exporta funções para módulos ES6 (mantido para compatibilidade ou uso modular)
export { apiDataSystem, setupApiFormPersistence, collectFormData, fillFormWithData, handleDataPropagation, waitForApiSystem };
