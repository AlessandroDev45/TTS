// public/scripts/transformer_inputs.js - Simplificado
// Importações do módulo comum

import { loadAndPopulateTransformerInfo } from './common_module.js';
import { initializeIsolationDropdowns, populateIsolationDropdowns, toggleNeutralFieldsVisibility } from './insulation_levels.js';

// public/scripts/transformer_inputs.js - Simplificado

// Função para configurar persistência (usando sistema global)
async function setupFormPersistence(formId, storeId) {
    try {
        console.log(`[setupFormPersistence] Iniciando configuração para ${formId} → ${storeId}`);
        // Usa a função globalmente exposta
        await window.waitForApiSystem();

        // Verificar se o formulário existe
        const formElement = document.getElementById(formId);
        if (!formElement) {
            console.error(`[setupFormPersistence] ERRO: Formulário ${formId} não encontrado!`);
            return;
        }
        console.log(`[setupFormPersistence] Formulário ${formId} encontrado`);

        // Usa a função globalmente exposta
        if (window.setupApiFormPersistence) {
            console.log('[setupFormPersistence] Usando função global setupApiFormPersistence');
            await window.setupApiFormPersistence(formId, storeId);
        } else {
            console.error('[setupFormPersistence] ERRO: Função global setupApiFormPersistence não encontrada!');
            // Não há fallback local, pois a função global é a fonte de verdade
        }
        console.log(`[setupFormPersistence] Configuração concluída para ${formId}`);

    // Teste adicional - verificar se listeners estão funcionando
    setTimeout(() => {
        const formElement = document.getElementById(formId);
        if (formElement) {
            const inputs = formElement.querySelectorAll('input, select, textarea');
            console.log(`[setupFormPersistence] VERIFICAÇÃO: ${inputs.length} inputs encontrados no formulário`);

            // Testa o primeiro input
            if (inputs.length > 0) {
                const firstInput = inputs[0];
                console.log(`[setupFormPersistence] TESTE: Primeiro input é ${firstInput.id || firstInput.name} (${firstInput.type})`);
            }
        }
    }, 1000);
    } catch (error) {
        console.error('[setupFormPersistence] Erro:', error);
    }
}

// Função para preencher os campos de corrente nominal a partir do backend
async function fillNominalCurrentsFromStore() {
    try {
        console.log('[fillNominalCurrentsFromStore] Iniciando...');

        // Usa a variável globalmente exposta
        if (!window.apiDataSystem) {
            console.error('[fillNominalCurrentsFromStore] apiDataSystem não disponível');
            return;
        }

        const store = window.apiDataSystem.getStore('transformerInputs');
        if (!store) {
            console.error('[fillNominalCurrentsFromStore] Store não encontrado');
            return;
        }

        const data = await store.getData();
        console.log('[fillNominalCurrentsFromStore] Dados recebidos:', data);

        // Verifica se os dados estão no nível raiz ou em formData
        let currentData = data || {};
        if (data && data.formData && Object.keys(data.formData).length > 0) {
            console.log('[fillNominalCurrentsFromStore] Usando dados de formData');
            currentData = { ...data, ...data.formData };
        }

        console.log('[fillNominalCurrentsFromStore] Dados processados:', currentData);

        // AT
        const correnteAT = document.getElementById('corrente_nominal_at');
        if (correnteAT) {
            const valor = currentData.corrente_nominal_at ?? '';
            correnteAT.value = valor;
            console.log('[fillNominalCurrentsFromStore] AT:', valor);
        }

        // BT
        const correnteBT = document.getElementById('corrente_nominal_bt');
        if (correnteBT) {
            const valor = currentData.corrente_nominal_bt ?? '';
            correnteBT.value = valor;
            console.log('[fillNominalCurrentsFromStore] BT:', valor);
        }

        // Terciário
        const correnteTer = document.getElementById('corrente_nominal_terciario');
        if (correnteTer) {
            const valor = currentData.corrente_nominal_terciario ?? '';
            correnteTer.value = valor;
            console.log('[fillNominalCurrentsFromStore] Terciário:', valor);
        }

        // Taps AT
        const correnteATTapMaior = document.getElementById('corrente_nominal_at_tap_maior');
        if (correnteATTapMaior) {
            const valor = currentData.corrente_nominal_at_tap_maior ?? '';
            correnteATTapMaior.value = valor;
            console.log('[fillNominalCurrentsFromStore] Tap Maior:', valor);
        }

        const correnteATTapMenor = document.getElementById('corrente_nominal_at_tap_menor');
        if (correnteATTapMenor) {
            const valor = currentData.corrente_nominal_at_tap_menor ?? '';
            correnteATTapMenor.value = valor;
            console.log('[fillNominalCurrentsFromStore] Tap Menor:', valor);
        }

        console.log('[fillNominalCurrentsFromStore] Concluído');

    } catch (error) {
        console.error('[fillNominalCurrentsFromStore] Erro:', error);
    }
}

// Atualiza correntes nominais sempre que campos relevantes mudam
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
                console.log(`[setupNominalCurrentAutoUpdate] Campo alterado: ${id}`);
                
                // Cancela timeout anterior se existir
                if (updateTimeout) {
                    clearTimeout(updateTimeout);
                }
                
                // Aguarda um tempo para a persistência automática e cálculo do backend
                updateTimeout = setTimeout(async () => {
                    console.log('[setupNominalCurrentAutoUpdate] Atualizando correntes...');
                    await fillNominalCurrentsFromStore();
                }, 1000); // Aumentei para 1 segundo
            });
        }
    });
}

// Função de inicialização do módulo Dados Básicos
async function initTransformerInputs() {
    console.log('[initTransformerInputs] Iniciando...');

    // Verificar se o DOM está pronto
    if (document.readyState === 'loading') {
        console.log('[initTransformerInputs] DOM ainda carregando, aguardando...');
        await new Promise(resolve => document.addEventListener('DOMContentLoaded', resolve));
    }
    console.log('[initTransformerInputs] DOM pronto');

    // Adiciona um pequeno atraso para garantir que o DOM esteja totalmente renderizado
    await new Promise(resolve => setTimeout(resolve, 200));
    console.log('[initTransformerInputs] Atraso de 200ms concluído.');


    // Preenche o painel de informações do transformador
    await loadAndPopulateTransformerInfo('transformer-info-transformer_inputs-page');

    // Configura persistência via backend e localStorage
    console.log('[initTransformerInputs] Configurando persistência...');
    await setupFormPersistence('transformer-inputs-form-container', 'transformerInputs');

    // Preenche as correntes nominais calculadas
    await fillNominalCurrentsFromStore();

    // Configura atualização automática das correntes nominais
    setupNominalCurrentAutoUpdate();

    // Dispara evento inicial para atualizar templates com dados existentes
    const store = window.apiDataSystem?.getStore('transformerInputs');
    if (store) {
        const existingData = await store.getData();
        if (existingData && existingData.formData && Object.keys(existingData.formData).length > 0) {
            document.dispatchEvent(new CustomEvent('transformerDataUpdated', {
                detail: { storeId: 'transformerInputs', formData: existingData.formData }
            }));
            console.log('[initTransformerInputs] Evento inicial transformerDataUpdated disparado');
        }
    }


    // Inicializa e configura os dropdowns de níveis de isolamento
    await initializeIsolationDropdowns();

    // Configura listeners para a visibilidade dos campos de neutro
    const enrolamentoPrefixos = ['at', 'bt', 'terciario'];
    enrolamentoPrefixos.forEach(prefixo => {
        const conexaoDropdown = document.getElementById(`conexao_${prefixo}`);
        if (conexaoDropdown) {
            conexaoDropdown.addEventListener('change', (event) => {
                toggleNeutralFieldsVisibility(prefixo, event.target.value);
            });
            // Garante que a visibilidade inicial seja correta ao carregar a página
            toggleNeutralFieldsVisibility(prefixo, conexaoDropdown.value);
        }
    });
}

// Garante que o painel de informações do transformador nunca seja exibido nesta página
window.addEventListener('DOMContentLoaded', () => {
    const infoPanel = document.getElementById('transformer-info-transformer_inputs-page');
    if (infoPanel) {
        infoPanel.innerHTML = '';
        infoPanel.classList.add('d-none');
        infoPanel.style.display = 'none';
    }
});

// SPA routing: executa quando o módulo transformer_inputs é carregado
document.addEventListener('moduleContentLoaded', (event) => {
    if (event.detail && event.detail.moduleName === 'transformer_inputs') {
        console.log('[transformer_inputs] SPA routing init');
        initTransformerInputs();
    }
});
