// public/scripts/temperature_rise.js - ATUALIZADO

import { loadAndPopulateTransformerInfo } from './common_module.js';
import { collectFormData, fillFormWithData } from './api_persistence.js';

// Função para carregar dados do store 'temperatureRise' e preencher o formulário
async function loadTemperatureRiseDataAndPopulateForm() {
    try {
        console.log('[temperature_rise] Carregando dados do store "temperatureRise" e preenchendo formulário...');
        await waitForApiSystem(); // Garante que o sistema de persistência esteja pronto

        const store = window.apiDataSystem.getStore('temperatureRise');
        const data = await store.getData();

        if (data && data.formData) {
            const formElement = document.getElementById('temperature-rise-form');
            if (formElement) {
                fillFormWithData(formElement, data.formData);
                console.log('[temperature_rise] Formulário de elevação de temperatura preenchido com dados do store:', data.formData);
            } else {
                console.warn('[temperature_rise] Formulário "temperature-rise-form" não encontrado para preenchimento.');
            }
        } else {
            console.log('[temperature_rise] Nenhum dado de elevação de temperatura encontrado no store.');
        }
    } catch (error) {
        console.error('[temperature_rise] Erro ao carregar e preencher dados de elevação de temperatura:', error);
    }
}

// Função auxiliar para obter valor de input
function getInputValue(id) {
    const element = document.getElementById(id);
    return element ? element.value : null;
}

// Função auxiliar para definir valor de output
function setOutputValue(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.value = value;
    }
}

async function getTransformerFormData() {
    const store = window.apiDataSystem.getStore('transformerInputs');
    const transformerData = await store.getData();
    return transformerData.formData || {};
}

async function saveCalculationResults(results) {
    const store = window.apiDataSystem.getStore('temperatureRise');
    await store.updateData({ calculationResults: results });
}

// Lógica para o botão "Calcular Elevação"
async function setupCalcButton() {
    const calcBtn = document.getElementById('limpar-temp-rise'); // ID original é "limpar-temp-rise"
    if (calcBtn) {
        calcBtn.addEventListener('click', async function() {
            console.log('Botão Calcular Elevação clicado!');

            const tempAmb = parseFloat(getInputValue('temp-amb'));
            const windingMaterial = getInputValue('winding-material');
            const resCold = parseFloat(getInputValue('res-cold'));
            const tempCold = parseFloat(getInputValue('temp-cold'));
            const resHot = parseFloat(getInputValue('res-hot'));
            const tempTopOil = parseFloat(getInputValue('temp-top-oil'));
            const deltaThetaOilMax = parseFloat(getInputValue('delta-theta-oil-max'));

            const transformerData = await getTransformerFormData();
            const basicData = transformerData || {}; // formData já é o objeto de dados básicos
            const pesosData = transformerData || {}; // Pesos também estão no formData

            // Em um sistema real, lossesData viria de losses-store
            // const lossesData = {/* fetch from losses store */};
            const perdasVazio = 10; // kW, Exemplo
            const perdasCargaNominal = 85; // kW, Exemplo
            const perdasTotais = perdasVazio + perdasCargaNominal; // Simplificado

            let errorMessage = '';

            try {
                if (isNaN(tempAmb) || isNaN(resCold) || isNaN(tempCold) || isNaN(resHot) || isNaN(tempTopOil)) {
                    throw new Error("Preencha todos os campos de medição e ambiente.");
                }

                const C_material = (windingMaterial === 'cobre') ? 234.5 : 225;

                const thetaW = tempAmb + ((resHot / resCold) * (C_material + tempCold) - C_material);
                setOutputValue('avg-winding-temp', thetaW.toFixed(2));

                const deltaThetaW = thetaW - tempAmb;
                setOutputValue('avg-winding-rise', deltaThetaW.toFixed(2));

                const deltaThetaOil = tempTopOil - tempAmb;
                setOutputValue('top-oil-rise', deltaThetaOil.toFixed(2));

                setOutputValue('ptot-used', perdasTotais.toFixed(2));

                let tau0 = '';
                if (!isNaN(deltaThetaOilMax) && pesosData.peso_total && pesosData.peso_oleo && perdasTotais > 0) {
                     const mT_ton = pesosData.peso_total;
                     const mO_ton = pesosData.peso_oleo;
                     tau0 = (0.132 * (mT_ton - 0.5 * mO_ton) * deltaThetaOilMax) / perdasTotais;
                    setOutputValue('tau0-result', tau0.toFixed(2));
                } else {
                    tau0 = 'N/A';
                    setOutputValue('tau0-result', tau0);
                }

            } catch (error) {
                errorMessage = error.message;
            }

            document.getElementById('temp-rise-error-message').textContent = errorMessage;
        });
    }
}

// Função de inicialização do módulo Elevação de Temperatura
async function initTemperatureRise() {
    console.log('Módulo Elevação de Temperatura carregado e pronto para interatividade.');

    if (window.setupApiFormPersistence) {
        await window.setupApiFormPersistence('temperature-rise-form', 'temperatureRise');
    } else {
        console.warn('[temperature_rise] Sistema de persistência não disponível');
    }

    // Carregar e preencher os dados do próprio módulo de elevação de temperatura
    await loadTemperatureRiseDataAndPopulateForm();

    // Adicionar listener para o evento transformerDataUpdated
    document.addEventListener('transformerDataUpdated', async (event) => {
        console.log('[temperature_rise] Evento transformerDataUpdated recebido:', event.detail);
        // Recarrega os dados do próprio módulo para garantir consistência
        await loadTemperatureRiseDataAndPopulateForm();
        // Se houver campos que dependem diretamente dos dados básicos do transformador,
        // eles podem ser atualizados aqui.
    });

    const transformerInfoPlaceholderId = 'transformer-info-temperature_rise-page';
    await loadAndPopulateTransformerInfo(transformerInfoPlaceholderId);

    setupCalcButton();
}

// SPA routing: executa quando o módulo temperature_rise é carregado
document.addEventListener('moduleContentLoaded', (event) => {
    if (event.detail && event.detail.moduleName === 'temperature_rise') {
        console.log('[temperature_rise] SPA routing init');
        initTemperatureRise();
    }
});

// Fallback para carregamento direto da página (se não for SPA)
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('temperature-rise-form')) { // Assumindo um ID de formulário principal para o módulo
        console.log('[temperature_rise] DOMContentLoaded init (fallback)');
        initTemperatureRise();
    }
});