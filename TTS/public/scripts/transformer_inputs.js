import { loadAndPopulateTransformerInfo } from './common_module.js';
import { initializeIsolationDropdowns, toggleNeutralFieldsVisibility } from './insulation_levels.js';
// Não precisamos mais importar collectFormData e fillFormWithData daqui,
// pois api_persistence.js já os expõe globalmente e setupFormPersistence os usa.

// --- FUNÇÕES HELPER PARA INPUTS ---
function getNumericValueOrNull(elementId) {
    const el = document.getElementById(elementId);
    if (el) {
        const val = el.value.trim();
        if (val === "") return null;
        const num = parseFloat(val.replace(',', '.'));
        return isNaN(num) ? null : num;
    }
    return null;
}

function getStringValueOrNull(elementId) {
    const el = document.getElementById(elementId);
    if (el) {
        const val = el.value.trim();
        return val === "" ? null : val;
    }
    return null;
}
// --- FIM DAS FUNÇÕES HELPER ---

// Função para configurar persistência (usando sistema global)
async function setupFormPersistence(formId, storeId) {
    try {
        console.log(`[transformer_inputs.js - setupFormPersistence] Iniciando para ${formId} -> ${storeId}`);
        await window.waitForApiSystem();
        const formElement = document.getElementById(formId);
        if (!formElement) {
            console.error(`[transformer_inputs.js - setupFormPersistence] ERRO: Formulário ${formId} não encontrado!`);
            return;
        }
        if (window.setupApiFormPersistence) {
            await window.setupApiFormPersistence(formId, storeId);
            console.log(`[transformer_inputs.js - setupFormPersistence] Persistência configurada por api_persistence.js para ${formId}`);
        } else {
            console.error('[transformer_inputs.js - setupFormPersistence] ERRO: window.setupApiFormPersistence não encontrada!');
        }
    } catch (error) {
        console.error('[transformer_inputs.js - setupFormPersistence] Erro:', error);
    }
}

// Função para enviar os dados básicos do transformador para o backend para cálculo e persistência
async function saveTransformerInputsAndTriggerCalculations() {
    console.log('[transformer_inputs.js - saveTransformerInputsAndTriggerCalculations] Coletando e enviando dados...');

    // Coleta todos os dados do formulário transformer_inputs
    const inputData = {
        potencia_mva: getNumericValueOrNull('potencia_mva'),
        frequencia: getNumericValueOrNull('frequencia'),
        tipo_transformador: getStringValueOrNull('tipo_transformador'),
        grupo_ligacao: getStringValueOrNull('grupo_ligacao'),
        liquido_isolante: getStringValueOrNull('liquido_isolante'),
        tipo_isolamento: getStringValueOrNull('tipo_isolamento'),
        norma_iso: getStringValueOrNull('norma_iso'),
        elevacao_oleo_topo: getNumericValueOrNull('elevacao_oleo_topo'),
        elevacao_enrol: getNumericValueOrNull('elevacao_enrol'),
        peso_parte_ativa: getNumericValueOrNull('peso_parte_ativa'),
        peso_tanque_acessorios: getNumericValueOrNull('peso_tanque_acessorios'),
        peso_oleo: getNumericValueOrNull('peso_oleo'),
        peso_total: getNumericValueOrNull('peso_total'),
        // AT
        tensao_at: getNumericValueOrNull('tensao_at'),
        classe_tensao_at: getNumericValueOrNull('classe_tensao_at'),
        impedancia: getNumericValueOrNull('impedancia'),
        nbi_at: getNumericValueOrNull('nbi_at'),
        sil_at: getNumericValueOrNull('sil_at'),
        sil_at: getNumericValueOrNull('sil_at'),
        conexao_at: getStringValueOrNull('conexao_at'),
        tensao_bucha_neutro_at: getStringValueOrNull('tensao_bucha_neutro_at'), // Alterado para getStringValueOrNull
        nbi_neutro_at: getNumericValueOrNull('nbi_neutro_at'),
        sil_neutro_at: getNumericValueOrNull('sil_neutro_at'),
        tensao_at_tap_maior: getNumericValueOrNull('tensao_at_tap_maior'),
        tensao_at_tap_menor: getNumericValueOrNull('tensao_at_tap_menor'),
        impedancia_tap_maior: getNumericValueOrNull('impedancia_tap_maior'),
        impedancia_tap_menor: getNumericValueOrNull('impedancia_tap_menor'),
        teste_tensao_aplicada_at: getNumericValueOrNull('teste_tensao_aplicada_at'),
        teste_tensao_induzida_at: getNumericValueOrNull('teste_tensao_induzida_at'),
        // BT
        tensao_bt: getNumericValueOrNull('tensao_bt'),
        classe_tensao_bt: getNumericValueOrNull('classe_tensao_bt'),
        nbi_bt: getNumericValueOrNull('nbi_bt'),
        sil_bt: getNumericValueOrNull('sil_bt'),
        conexao_bt: getStringValueOrNull('conexao_bt'),
        tensao_bucha_neutro_bt: getStringValueOrNull('tensao_bucha_neutro_bt'), // Alterado para getStringValueOrNull
        nbi_neutro_bt: getNumericValueOrNull('nbi_neutro_bt'),
        sil_neutro_bt: getNumericValueOrNull('sil_neutro_bt'),
        teste_tensao_aplicada_bt: getNumericValueOrNull('teste_tensao_aplicada_bt'),
        // Terciário
        tensao_terciario: getNumericValueOrNull('tensao_terciario'),
        classe_tensao_terciario: getNumericValueOrNull('classe_tensao_terciario'),
        nbi_terciario: getNumericValueOrNull('nbi_terciario'),
        sil_terciario: getNumericValueOrNull('sil_terciario'),
        conexao_terciario: getStringValueOrNull('conexao_terciario'),
        tensao_bucha_neutro_terciario: getStringValueOrNull('tensao_bucha_neutro_terciario'), // Alterado para getStringValueOrNull
        nbi_neutro_terciario: getNumericValueOrNull('nbi_neutro_terciario'),
        sil_neutro_terciario: getNumericValueOrNull('sil_neutro_terciario'),
        teste_tensao_aplicada_terciario: getNumericValueOrNull('teste_tensao_aplicada_terciario')
    };
    console.log('[transformer_inputs.js - saveTransformerInputsAndTriggerCalculations] Dados coletados (inputData) antes do envio:', inputData);

    try {
        const response = await fetch('/api/transformer/inputs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(inputData),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: "Erro desconhecido ao processar resposta de erro." }));
            console.error('[transformer_inputs.js - saveTransformerInputsAndTriggerCalculations] Falha ao salvar dados básicos:', response.status, errorData);
            throw new Error(`Erro ${response.status} ao salvar dados básicos: ${errorData.detail || response.statusText}`);
        }

        const result = await response.json();
        console.log('[transformer_inputs.js - saveTransformerInputsAndTriggerCalculations] Resposta do backend (result):', result);
        console.log('[transformer_inputs.js - saveTransformerInputsAndTriggerCalculations] Dados atualizados do backend (result.updated_data):', result.updated_data);

        // Após o POST bem-sucedido, os dados calculados (incluindo correntes)
        // estarão no MCP. Disparamos um evento para que o painel e os campos de corrente
        // sejam atualizados lendo do MCP.
        if (window.apiDataSystem) {
            const store = window.apiDataSystem.getStore('transformerInputs');
            // Não precisamos chamar store.getData() aqui, pois o evento já passa os dados atualizados.
            // A chamada a store.getData() dentro de fillNominalCurrentsFromStore já buscará o mais recente.
        }
        document.dispatchEvent(new CustomEvent('transformerDataUpdated', {
            detail: { storeId: 'transformerInputs', formData: result.updated_data }
        }));

    } catch (error) {
        console.error('[transformer_inputs.js - saveTransformerInputsAndTriggerCalculations] Erro durante o POST:', error);
        // Exibir erro para o usuário, se necessário
        const lastSaveOkEl = document.getElementById('last-save-ok');
        if (lastSaveOkEl) {
            lastSaveOkEl.textContent = `Erro ao salvar: ${error.message}`;
            lastSaveOkEl.className = 'col-md-6 offset-md-3 text-center text-danger small';
        }
    }
}

// Função para preencher os campos de corrente nominal a partir do store (que foi atualizado pelo backend)
async function fillNominalCurrentsFromStore() {
    try {
        console.log('[transformer_inputs.js - fillNominalCurrentsFromStore] Iniciando...');
        if (!window.apiDataSystem) {
            console.error('[transformer_inputs.js - fillNominalCurrentsFromStore] apiDataSystem não disponível');
            return;
        }
        const store = window.apiDataSystem.getStore('transformerInputs');
        const data = await store.getData(); // Isso buscará do cache ou do backend

        let formData = {};
        if (data && data.formData) {
            formData = data.formData;
        } else if (data && Object.keys(data).length > 0 && !data.formData) {
            // Se os dados vierem diretamente (sem a estrutura {formData: ...}), como após um GET
            formData = data;
        }

        console.log('[transformer_inputs.js - fillNominalCurrentsFromStore] Dados do formData para preenchimento (do store):', formData);

        const fieldsToUpdate = {
            'corrente_nominal_at': formData.corrente_nominal_at,
            'corrente_nominal_bt': formData.corrente_nominal_bt,
            'corrente_nominal_terciario': formData.corrente_nominal_terciario,
            'corrente_nominal_at_tap_maior': formData.corrente_nominal_at_tap_maior,
            'corrente_nominal_at_tap_menor': formData.corrente_nominal_at_tap_menor
        };

        for (const [id, value] of Object.entries(fieldsToUpdate)) {
            const element = document.getElementById(id);
            if (element) {
                // Verifica se o valor é um número antes de formatar
                if (typeof value === 'number' && !isNaN(value)) {
                    element.value = value.toFixed(2);
                } else {
                    element.value = ''; // Limpa se não for um número válido
                }
                console.log(`[transformer_inputs.js - fillNominalCurrentsFromStore] Campo ${id} atualizado para: ${element.value} (valor original: ${value})`);
            } else {
                console.warn(`[transformer_inputs.js - fillNominalCurrentsFromStore] Elemento ${id} não encontrado.`);
            }
        }
        console.log('[transformer_inputs.js - fillNominalCurrentsFromStore] Concluído.');
    } catch (error) {
        console.error('[transformer_inputs.js - fillNominalCurrentsFromStore] Erro:', error);
    }
}

// Configura listeners para os campos que disparam o recálculo/salvamento
function setupAutoSaveAndRecalculateTrigger() {
    const idsToWatch = [
        'potencia_mva', 'frequencia', 'tipo_transformador', 'grupo_ligacao',
        'liquido_isolante', 'tipo_isolamento', 'norma_iso', 'elevacao_oleo_topo',
        'elevacao_enrol', 'peso_parte_ativa', 'peso_tanque_acessorios',
        'peso_oleo', 'peso_total', 'tensao_at', 'classe_tensao_at',
        'impedancia', 'nbi_at', 'sil_at', 'conexao_at', 'tensao_bucha_neutro_at',
        'nbi_neutro_at', 'sil_neutro_at', 'tensao_at_tap_maior',
        'tensao_at_tap_menor', 'impedancia_tap_maior', 'impedancia_tap_menor',
        'teste_tensao_aplicada_at', 'teste_tensao_induzida_at', 'tensao_bt',
        'classe_tensao_bt', 'nbi_bt', 'sil_bt', 'conexao_bt',
        'tensao_bucha_neutro_bt', 'nbi_neutro_bt', 'sil_neutro_bt',
        'teste_tensao_aplicada_bt', 'tensao_terciario',
        'classe_tensao_terciario', 'nbi_terciario', 'sil_terciario',
        'conexao_terciario', 'tensao_bucha_neutro_terciario',
        'nbi_neutro_terciario', 'sil_neutro_terciario',
        'teste_tensao_aplicada_terciario'
    ];

    let debounceTimeout;

    idsToWatch.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            // Usar 'input' para campos de texto/número para capturar digitação
            // Usar 'change' para selects
            const eventType = (el.tagName === 'SELECT' || el.type === 'number') ? 'change' : 'input';

            el.addEventListener(eventType, () => {
                console.log(`[transformer_inputs.js - setupAutoSaveAndRecalculateTrigger] Campo alterado: ${id}`);
                clearTimeout(debounceTimeout);
                debounceTimeout = setTimeout(async () => {
                    console.log('[transformer_inputs.js - setupAutoSaveAndRecalculateTrigger] Debounce concluído. Salvando e disparando cálculos...');
                    await saveTransformerInputsAndTriggerCalculations();
                    // As correntes serão atualizadas pelo evento 'transformerDataUpdated'
                    // que chama fillNominalCurrentsFromStore.
                }, 750); // Ajuste o delay conforme necessário
            });
        } else {
            console.warn(`[transformer_inputs.js - setupAutoSaveAndRecalculateTrigger] Elemento ${id} não encontrado para adicionar listener.`);
        }
    });
    console.log('[transformer_inputs.js - setupAutoSaveAndRecalculateTrigger] Listeners de auto-save configurados.');
}

async function initTransformerInputs() {
    console.log('[transformer_inputs.js - initTransformerInputs] Iniciando...');

    if (document.readyState === 'loading') {
        await new Promise(resolve => document.addEventListener('DOMContentLoaded', resolve));
    }
    await new Promise(resolve => setTimeout(resolve, 100)); // Pequeno delay adicional

    // 0. O painel de info não deve ser exibido nesta página
    const infoPanel = document.getElementById('transformer-info-transformer_inputs-page');
    if (infoPanel) {
        infoPanel.innerHTML = '';
        infoPanel.classList.add('d-none');
    }

    // 1. Configura persistência automática para o formulário principal (usa api_persistence.js)
    // Esta persistência fará PATCH para /api/data/stores/transformerInputs
    // Não é ela que dispara os cálculos diretamente, mas mantém o estado do formulário.
    await setupFormPersistence('transformer-inputs-form-container', 'transformerInputs');

    // 2. Carrega dados do store PRIMEIRO
    let existingData = null;
    if (window.apiDataSystem) {
        const store = window.apiDataSystem.getStore('transformerInputs');
        existingData = await store.getData(); // Busca do backend/cache
        console.log("[transformer_inputs.js - initTransformerInputs] Dados carregados do store:", existingData);
    }

    // 3. Inicializa os dropdowns de isolamento PRIMEIRO (sem dados)
    console.log("[transformer_inputs.js - initTransformerInputs] Inicializando dropdowns de isolamento...");
    await initializeIsolationDropdowns();

    // 4. DEPOIS preenche o formulário com os dados salvos (incluindo NBI/SIL)
    if (existingData) {
        let dataToFill = existingData.formData || existingData; // Lida com ambas estruturas
        if (Object.keys(dataToFill).length > 0) {
            const formElement = document.getElementById('transformer-inputs-form-container');
            if (formElement) {
                console.log("[transformer_inputs.js - initTransformerInputs] Preenchendo formulário com dados salvos:", dataToFill);
                window.fillFormWithData(formElement, dataToFill); // Usa a função global

                // 5. FORÇA re-população dos dropdowns NBI/SIL e Tensões de Ensaio baseado nos dados carregados
                console.log("[transformer_inputs.js - initTransformerInputs] Forçando re-população dos dropdowns NBI/SIL e Tensões de Ensaio...");
                await forceRepopulateNbiSilDropdowns(dataToFill);
            }
        } else {
            console.log("[transformer_inputs.js - initTransformerInputs] Nenhum dado de formData encontrado no store para preencher o formulário.");
        }
    }

    // 6. Preenche os campos de corrente nominal com base nos dados já calculados (se houver)
    await fillNominalCurrentsFromStore();

    // 6. Configura listeners para que qualquer alteração nos inputs dispare
    //    a função saveTransformerInputsAndTriggerCalculations (que faz o POST).
    setupAutoSaveAndRecalculateTrigger();

    // 7. Configura listeners para a visibilidade dos campos de neutro
    const enrolamentoPrefixos = ['at', 'bt', 'terciario'];
    enrolamentoPrefixos.forEach(prefixo => {
        const conexaoDropdown = document.getElementById(`conexao_${prefixo}`);
        if (conexaoDropdown) {
            conexaoDropdown.addEventListener('change', (event) => {
                toggleNeutralFieldsVisibility(prefixo, event.target.value);
            });
            toggleNeutralFieldsVisibility(prefixo, conexaoDropdown.value); // Estado inicial
        }
    });

    // Listener para atualizar os campos de corrente quando 'transformerDataUpdated' for disparado
    // (geralmente após saveTransformerInputsAndTriggerCalculations ser bem sucedido)
    document.addEventListener('transformerDataUpdated', async (event) => {
        if (event.detail.storeId === 'transformerInputs') {
            console.log('[transformer_inputs.js] Evento transformerDataUpdated recebido. Atualizando campos de corrente.');
            await fillNominalCurrentsFromStore(); // Atualiza os campos de corrente
            // Também garantir que os campos de input normais sejam atualizados se o backend os modificou
            const formElement = document.getElementById('transformer-inputs-form-container');
            if(formElement && event.detail.formData) {
                window.fillFormWithData(formElement, event.detail.formData);
            }
        }
    });

    console.log('[transformer_inputs.js - initTransformerInputs] Concluído.');
}

// Função para forçar re-população dos dropdowns NBI/SIL e Tensões de Ensaio com dados salvos
async function forceRepopulateNbiSilDropdowns(formData) {
    console.log("[transformer_inputs.js - forceRepopulateNbiSilDropdowns] Iniciando com dados:", formData);

    // Lista de campos NBI/SIL que precisam ser re-populados
    const nbiSilFields = [
        { prefix: 'at', nbiField: 'nbi_at', silField: 'sil_at' },
        { prefix: 'at', nbiField: 'nbi_neutro_at', silField: 'sil_neutro_at' },
        { prefix: 'bt', nbiField: 'nbi_bt', silField: 'sil_bt' },
        { prefix: 'bt', nbiField: 'nbi_neutro_bt', silField: 'sil_neutro_bt' },
        { prefix: 'terciario', nbiField: 'nbi_terciario', silField: 'sil_terciario' },
        { prefix: 'terciario', nbiField: 'nbi_neutro_terciario', silField: 'sil_neutro_terciario' }
    ];

    // Lista de campos de tensão de ensaio que precisam ser re-populados
    const testVoltageFields = [
        'teste_tensao_aplicada_at',
        'teste_tensao_induzida_at',
        'teste_tensao_aplicada_bt',
        'teste_tensao_aplicada_terciario'
    ];

    for (const field of nbiSilFields) {
        const nbiValue = formData[field.nbiField];
        const silValue = formData[field.silField];

        if (nbiValue !== undefined && nbiValue !== null) {
            const nbiElement = document.getElementById(field.nbiField);
            if (nbiElement) {
                // Força o valor no dropdown
                nbiElement.value = String(nbiValue);
                console.log(`[forceRepopulateNbiSilDropdowns] Forçando ${field.nbiField} = ${nbiValue}`);

                // Se o valor não existe nas opções, adiciona temporariamente
                if (nbiElement.value !== String(nbiValue)) {
                    const option = document.createElement('option');
                    option.value = String(nbiValue);
                    option.textContent = String(nbiValue);
                    option.setAttribute('data-temp', 'true'); // Marca como temporária
                    nbiElement.appendChild(option);
                    nbiElement.value = String(nbiValue);
                    console.log(`[forceRepopulateNbiSilDropdowns] Adicionada opção temporária para ${field.nbiField}: ${nbiValue}`);
                }
            }
        }

        if (silValue !== undefined && silValue !== null) {
            const silElement = document.getElementById(field.silField);
            if (silElement) {
                // Força o valor no dropdown
                silElement.value = String(silValue);
                console.log(`[forceRepopulateNbiSilDropdowns] Forçando ${field.silField} = ${silValue}`);

                // Se o valor não existe nas opções, adiciona temporariamente
                if (silElement.value !== String(silValue)) {
                    const option = document.createElement('option');
                    option.value = String(silValue);
                    option.textContent = String(silValue);
                    option.setAttribute('data-temp', 'true'); // Marca como temporária
                    silElement.appendChild(option);
                    silElement.value = String(silValue);
                    console.log(`[forceRepopulateNbiSilDropdowns] Adicionada opção temporária para ${field.silField}: ${silValue}`);
                }
            }
        }
    }

    // Processa campos de tensão de ensaio
    for (const fieldId of testVoltageFields) {
        const fieldValue = formData[fieldId];

        if (fieldValue !== undefined && fieldValue !== null) {
            const element = document.getElementById(fieldId);
            if (element) {
                // Força o valor no dropdown
                element.value = String(fieldValue);
                console.log(`[forceRepopulateNbiSilDropdowns] Forçando ${fieldId} = ${fieldValue}`);

                // Se o valor não existe nas opções, adiciona temporariamente
                if (element.value !== String(fieldValue)) {
                    const option = document.createElement('option');
                    option.value = String(fieldValue);
                    option.textContent = String(fieldValue);
                    option.setAttribute('data-temp', 'true'); // Marca como temporária
                    element.appendChild(option);
                    element.value = String(fieldValue);
                    console.log(`[forceRepopulateNbiSilDropdowns] Adicionada opção temporária para ${fieldId}: ${fieldValue}`);
                }
            }
        }
    }

    console.log("[transformer_inputs.js - forceRepopulateNbiSilDropdowns] Concluído.");
}

document.addEventListener('moduleContentLoaded', (event) => {
    if (event.detail && event.detail.moduleName === 'transformer_inputs') {
        initTransformerInputs();
    }
});
