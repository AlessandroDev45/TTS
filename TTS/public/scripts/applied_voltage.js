// public/scripts/applied_voltage.js

import { loadAndPopulateTransformerInfo, transformerDataStore, updateGlobalInfoPanel } from './common_module.js';
import { waitForApiSystem, collectFormData, fillFormWithData } from './api_persistence.js';

// Função auxiliar para obter valor de input
function getInputValue(id) {
    const element = document.getElementById(id);
    return element ? element.value : null;
}

// Função auxiliar para definir texto em um elemento
function setElementText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

// Função para carregar dados do store 'appliedVoltage' e preencher o formulário
async function loadAppliedVoltageDataAndPopulateForm() {
    try {
        console.log('[applied_voltage] Carregando dados do store "appliedVoltage" e preenchendo formulário...');
        await waitForApiSystem(); // Garante que o sistema de persistência esteja pronto

        const store = window.apiDataSystem.getStore('appliedVoltage');
        const data = await store.getData();

        if (data && data.formData) {
            const formElement = document.getElementById('applied-voltage-form');
            if (formElement) {
                fillFormWithData(formElement, data.formData);
                console.log('[applied_voltage] Formulário de tensão aplicada preenchido com dados do store:', data.formData);
            } else {
                console.warn('[applied_voltage] Formulário "applied-voltage-form" não encontrado para preenchimento.');
            }
        } else {
            console.log('[applied_voltage] Nenhum dado de tensão aplicada encontrado no store.');
        }
    } catch (error) {
        console.error('[applied_voltage] Erro ao carregar e preencher dados de tensão aplicada:', error);
    }
}

// Função para preencher as tensões de ensaio com base nos dados do transformador
async function fillTestVoltages() {
    const store = window.apiDataSystem.getStore('transformerInputs');
    const transformerData = await store.getData();
    const formData = transformerData.formData || {};

    setElementText('tensao-at-display', (formData.teste_tensao_aplicada_at ? `${formData.teste_tensao_aplicada_at} kV` : '-'));
    setElementText('tensao-bt-display', (formData.teste_tensao_aplicada_bt ? `${formData.teste_tensao_aplicada_bt} kV` : '-'));
    setElementText('tensao-terciario-display', (formData.teste_tensao_aplicada_terciario ? `${formData.teste_tensao_aplicada_terciario} kV` : '-'));
    setElementText('frequencia-display', (formData.frequencia ? `${formData.frequencia} Hz` : '60 Hz'));

    // Preenche o campo oculto tipo_transformador, que pode ser usado em cálculos
    const tipoTrafoHidden = document.getElementById('tipo_transformador');
    if (tipoTrafoHidden) {
        tipoTrafoHidden.value = formData.tipo_transformador || 'Trifásico';
    }
}

// Lógica para o botão "Calcular"
async function setupCalcButton() {
    const calcBtn = document.getElementById('calc-applied-voltage-btn');
    if (calcBtn) {
        calcBtn.addEventListener('click', async function() {
            console.log('Botão Calcular Tensão Aplicada clicado!');
            const capAt = parseFloat(getInputValue('cap-at'));
            const capBt = parseFloat(getInputValue('cap-bt'));
            const capTer = parseFloat(getInputValue('cap-ter'));
            const freq = parseFloat(document.getElementById('frequencia-display').textContent.split(' ')[0]);
            const tensaoAt = parseFloat(document.getElementById('tensao-at-display').textContent.split(' ')[0]);
            const tensaoBt = parseFloat(document.getElementById('tensao-bt-display').textContent.split(' ')[0]);
            const tensaoTer = parseFloat(document.getElementById('tensao-terciario-display').textContent.split(' ')[0]);

            let resultsHtml = '<h5>Resultados Calculados:</h5><table class="table table-sm table-striped"><thead><tr><th>Lado</th><th>Tensão Ensaio (kV)</th><th>Cap. Ensaio (pF)</th><th>Corrente (mA)</th><th>Pot. Reativa (kVAr)</th><th>Recomendações</th></tr></thead><tbody>';
            let recommendationText = '';

            const calculateReativePower = (V_kV, C_pF, F_Hz) => {
                if (isNaN(V_kV) || isNaN(C_pF) || isNaN(F_Hz) || C_pF <= 0) return { current: null, reactivePower: null };
                const V_V = V_kV * 1000;
                const C_F = C_pF * 1e-12;
                const I_A = 2 * Math.PI * F_Hz * C_F * V_V;
                const Q_VAr = V_V * I_A;
                return { current: I_A * 1000, reactivePower: Q_VAr / 1000 };
            };

            const atResults = calculateReativePower(tensaoAt, capAt, freq);
            const btResults = calculateReativePower(tensaoBt, capBt, freq);
            const terResults = calculateReativePower(tensaoTer, capTer, freq);

            if (atResults.current !== null) {
                const recommendation = tensaoAt > 450 || atResults.reactivePower > 500 ? 'Sistema Ressonante Recomendado' : 'Fonte Convencional Possível';
                resultsHtml += `<tr><td>AT</td><td>${tensaoAt.toFixed(1)}</td><td>${capAt.toFixed(0)}</td><td>${atResults.current.toFixed(2)}</td><td>${atResults.reactivePower.toFixed(2)}</td><td>${recommendation}</td></tr>`;
                if (recommendation.includes('Ressonante')) recommendationText += `AT: ${recommendation}. `;
            }
            if (btResults.current !== null) {
                const recommendation = tensaoBt > 450 || btResults.reactivePower > 500 ? 'Sistema Ressonante Recomendado' : 'Fonte Convencional Adequada';
                resultsHtml += `<tr><td>BT</td><td>${tensaoBt.toFixed(1)}</td><td>${capBt.toFixed(0)}</td><td>${btResults.current.toFixed(2)}</td><td>${btResults.reactivePower.toFixed(2)}</td><td>${recommendation}</td></tr>`;
                 if (recommendation.includes('Ressonante')) recommendationText += `BT: ${recommendation}. `;
            }
            if (terResults.current !== null) {
                const recommendation = tensaoTer > 450 || terResults.reactivePower > 500 ? 'Sistema Ressonante Recomendado' : 'Fonte Convencional Adequada';
                resultsHtml += `<tr><td>Terciário</td><td>${tensaoTer.toFixed(1)}</td><td>${capTer.toFixed(0)}</td><td>${terResults.current.toFixed(2)}</td><td>${terResults.reactivePower.toFixed(2)}</td><td>${recommendation}</td></tr>`;
                 if (recommendation.includes('Ressonante')) recommendationText += `Terciário: ${recommendation}. `;
            }

            resultsHtml += '</tbody></table>';

            if (!recommendationText) recommendationText = 'Nenhuma recomendação específica. Fontes convencionais parecem adequadas.';

            document.getElementById('applied-voltage-results').innerHTML = resultsHtml;
            document.getElementById('resonant-system-recommendation').textContent = recommendationText;
            document.getElementById('applied-voltage-error-message').textContent = '';

            // Salvar resultados de cálculo
            const appliedVoltageStore = window.apiDataSystem.getStore('appliedVoltage');
            const resultsToSave = {
                at: { tensao: tensaoAt, capacitancia: capAt, corrente: atResults.current, potenciaReativa: atResults.reactivePower },
                bt: { tensao: tensaoBt, capacitancia: capBt, corrente: btResults.current, potenciaReativa: btResults.reactivePower },
                terciario: { tensao: tensaoTer, capacitancia: capTer, corrente: terResults.current, potenciaReativa: terResults.reactivePower }
            };
            await appliedVoltageStore.updateData({ formData: { resultados_calculo: resultsToSave } });
        });
    }
}

// Função de inicialização do módulo Tensão Aplicada
async function initAppliedVoltage() {
    console.log('Módulo Tensão Aplicada carregado e pronto para interatividade.');

    // ID do placeholder para o painel de informações do transformador
    const transformerInfoPlaceholderId = 'transformer-info-applied_voltage-page';
    await loadAndPopulateTransformerInfo(transformerInfoPlaceholderId); // Carrega o painel no topo
    
    // Configurar persistência de dados usando API do backend
    if (window.setupApiFormPersistence) {
        await window.setupApiFormPersistence('applied-voltage-form', 'appliedVoltage');
    } else {
        console.warn('[applied_voltage] Sistema de persistência não disponível');
    }

    // Carregar e preencher os dados do próprio módulo de tensão aplicada
    await loadAppliedVoltageDataAndPopulateForm();

    // Adicionar listener para o evento transformerDataUpdated
    document.addEventListener('transformerDataUpdated', async (event) => {
        console.log('[applied_voltage] Evento transformerDataUpdated recebido:', event.detail);
        // Recarrega os dados do próprio módulo para garantir consistência
        await loadAppliedVoltageDataAndPopulateForm();
        // Atualiza as tensões de ensaio que dependem dos dados básicos
        fillTestVoltages();
    });

    fillTestVoltages(); // Preenche as tensões de ensaio ao carregar o módulo
    setupCalcButton(); // Configura o botão de cálculo
}

// SPA routing: executa quando o módulo applied_voltage é carregado
document.addEventListener('moduleContentLoaded', (event) => {
    if (event.detail && event.detail.moduleName === 'applied_voltage') {
        console.log('[applied_voltage] SPA routing init');
        initAppliedVoltage();
    }
});

// Fallback para carregamento direto da página (se não for SPA)
document.addEventListener('DOMContentLoaded', () => {
    // Verifica se o elemento principal do módulo está presente para evitar execução em outras páginas
    if (document.getElementById('applied-voltage-form')) {
        console.log('[applied_voltage] DOMContentLoaded init (fallback)');
        initAppliedVoltage();
    }
});
