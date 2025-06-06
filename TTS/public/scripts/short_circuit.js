// public/scripts/short_circuit.js - ATUALIZADO

import { loadAndPopulateTransformerInfo } from './common_module.js';
import { collectFormData, fillFormWithData } from './api_persistence.js';

// Função para carregar dados do store 'shortCircuit' e preencher o formulário
async function loadShortCircuitDataAndPopulateForm() {
    try {
        console.log('[short_circuit] Carregando dados do store "shortCircuit" e preenchendo formulário...');
        await waitForApiSystem(); // Garante que o sistema de persistência esteja pronto

        const store = window.apiDataSystem.getStore('shortCircuit');
        const data = await store.getData();

        if (data && data.formData) {
            const formElement = document.getElementById('short-circuit-form');
            if (formElement) {
                fillFormWithData(formElement, data.formData);
                console.log('[short_circuit] Formulário de curto-circuito preenchido com dados do store:', data.formData);
            } else {
                console.warn('[short_circuit] Formulário "short-circuit-form" não encontrado para preenchimento.');
            }
        } else {
            console.log('[short_circuit] Nenhum dado de curto-circuito encontrado no store.');
        }
    } catch (error) {
        console.error('[short_circuit] Erro ao carregar e preencher dados de curto-circuito:', error);
    }
}

// Função auxiliar para obter valor de input
function getInputValue(id) {
    const element = document.getElementById(id);
    return element ? element.value : null;
}

async function getTransformerFormData() {
    const store = window.apiDataSystem.getStore('transformerInputs');
    const transformerData = await store.getData();
    return transformerData.formData || {};
}

async function saveCalculationResults(results) {
    const store = window.apiDataSystem.getStore('shortCircuit');
    await store.updateData({ calculationResults: results });
}

function updateImpedanceGraph(Z_before, Z_after, limitZ, currentDeltaZ) {
    const graphDiv = document.getElementById('impedance-variation-graph');
    if (!graphDiv) return;

    graphDiv.innerHTML = '';
    graphDiv.classList.remove('plotly-graph-placeholder');

    let graphHtml = `
        <div style="width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 0.8rem; position: relative;">
            <div style="width: 90%; height: 80%; display: flex; align-items: flex-end; justify-content: space-around; position: relative; border-left: 1px solid var(--border-color); border-bottom: 1px solid var(--border-color);">
                <div style="position: absolute; top: ${100 - limitZ * 2}%; width: 100%; border-top: 1px dashed var(--fail-color); font-size: 0.7em; text-align: right; padding-right: 5px; color: var(--fail-color);">+${limitZ}%</div>
                <div style="position: absolute; top: ${100 - (-limitZ) * 2}%; width: 100%; border-top: 1px dashed var(--fail-color); font-size: 0.7em; text-align: right; padding-right: 5px; color: var(--fail-color); transform: translateY(-100%);">-${limitZ}%</div>

                <div style="display: flex; flex-direction: column; align-items: center; margin: 0 5px;">
                    <div style="height: ${Math.min(100, Math.abs(currentDeltaZ) * 2)}%; width: 50px; background-color: var(--primary-color); position: relative;">
                        <span style="position: absolute; bottom: -20px; width: 100%; text-align: center; color: var(--text-light);">${currentDeltaZ.toFixed(2)}%</span>
                    </div>
                    <div style="margin-top: 5px; color: var(--text-light);">ΔZ Medido</div>
                </div>
                <div style="display: flex; flex-direction: column; align-items: center; margin: 0 5px;">
                    <div style="height: ${Math.min(100, Math.abs(limitZ) * 2)}%; width: 50px; background-color: var(--fail-color); position: relative;">
                        <span style="position: absolute; bottom: -20px; width: 100%; text-align: center; color: var(--text-light);">±${limitZ}%</span>
                    </div>
                    <div style="margin-top: 5px; color: var(--text-light);">Limite Normativo</div>
                </div>
            </div>
        </div>
    `;
    graphDiv.innerHTML = graphHtml;
}

// Lógica para o botão "Calcular / Verificar"
async function setupCalcButton() {
    const calcBtn = document.getElementById('calc-short-circuit-btn');
    if (calcBtn) {
        calcBtn.addEventListener('click', async function() {
            console.log('Botão Calcular / Verificar Curto-Circuito clicado!');

            const impedanceBefore = parseFloat(getInputValue('impedance-before'));
            const impedanceAfter = parseFloat(getInputValue('impedance-after'));
            const peakFactor = parseFloat(getInputValue('peak-factor'));
            const iscSide = getInputValue('isc-side');
            const powerCategory = getInputValue('power-category');

            const transformerData = await getTransformerFormData();
            const basicData = transformerData || {}; // formData já é o objeto de dados básicos
            const atData = transformerData || {}; // Os dados de AT estão no mesmo objeto
            const btData = transformerData || {}; // Os dados de BT estão no mesmo objeto
            const terciarioData = transformerData || {}; // Os dados de Terciário estão no mesmo objeto

            let errorMessage = '';
            let iscSym = '-';
            let iscPeak = '-';
            let deltaZ = '-';
            let checkStatus = '-';

            try {
                if (isNaN(impedanceBefore) || isNaN(impedanceAfter) || isNaN(peakFactor)) {
                    throw new Error("Preencha todos os campos de impedância e fator de pico.");
                }

                if (!basicData.potencia_mva || !basicData.frequencia || !atData.tensao_at || !btData.tensao_bt) {
                    throw new Error("Dados básicos do transformador (potência, tensões) são necessários. Verifique a página 'Dados Básicos'.");
                }

                let limitDeltaZ = 0;
                switch (powerCategory) {
                    case 'I':
                        limitDeltaZ = 7.5;
                        break;
                    case 'II':
                        limitDeltaZ = 5.0;
                        break;
                    case 'III':
                        limitDeltaZ = 2.0;
                        break;
                    default:
                        errorMessage = "Selecione uma categoria de potência.";
                        break; // Adicionado break para evitar que o código continue executando
                }

                if (errorMessage) {
                    document.getElementById('short-circuit-error-message').textContent = errorMessage;
                    return; // Aborta a execução se houver um erro
                }

                const diffZ = Math.abs(impedanceAfter - impedanceBefore);
                const percentDeltaZ = (diffZ / impedanceBefore) * 100;
                deltaZ = percentDeltaZ.toFixed(2) + ' %';

                if (percentDeltaZ <= limitDeltaZ) {
                    checkStatus = '<span style="color: var(--success-color); font-weight: bold;"><i class="fas fa-check-circle me-1"></i>APROVADO</span>';
                } else {
                    checkStatus = `<span style="color: var(--danger-color); font-weight: bold;"><i class="fas fa-times-circle me-1"></i>REPROVADO (Limite: ±${limitDeltaZ}%)</span>`;
                }

                const Sn_MVA = basicData.potencia_mva;
                const Zn_percent = atData.impedancia;

                if (isNaN(Sn_MVA) || isNaN(Zn_percent) || Zn_percent === 0) {
                     throw new Error("Potência nominal e impedância nominal do transformador são inválidas. Verifique 'Dados Básicos'.");
                }

                let nominalVoltagekV = 0;
                let nominalCurrentA = 0;
                if (iscSide === 'AT') {
                    nominalVoltagekV = atData.tensao_at;
                    nominalCurrentA = Sn_MVA * 1000 / (basicData.tipo_transformador === 'Trifásico' ? Math.sqrt(3) : 1) / nominalVoltagekV;
                } else if (iscSide === 'BT') {
                    nominalVoltagekV = btData.tensao_bt;
                    nominalCurrentA = Sn_MVA * 1000 / (basicData.tipo_transformador === 'Trifásico' ? Math.sqrt(3) : 1) / nominalVoltagekV;
                } else if (iscSide === 'TERCIARIO') {
                    nominalVoltagekV = terciarioData.tensao_terciario;
                    nominalCurrentA = Sn_MVA * 1000 / (basicData.tipo_transformador === 'Trifásico' ? Math.sqrt(3) : 1) / nominalVoltagekV;
                }
                if (isNaN(nominalVoltagekV) || nominalVoltagekV === 0) {
                    throw new Error(`Tensão nominal para o lado ${iscSide} inválida.`);
                }

                const Isc = nominalCurrentA / (Zn_percent / 100);
                iscSym = (Isc / 1000).toFixed(2);
                iscPeak = (Isc / 1000 * peakFactor).toFixed(2);

            } catch (error) {
                errorMessage = error.message;
            }

            document.getElementById('isc-sym-result').value = iscSym;
            document.getElementById('isc-peak-result').value = iscPeak;
            document.getElementById('delta-impedance-result').value = deltaZ;
            document.getElementById('impedance-check-status').innerHTML = checkStatus;
            document.getElementById('short-circuit-error-message').textContent = errorMessage;

            await saveCalculationResults({ iscSym, iscPeak, deltaZ, checkStatus, errorMessage });
            updateImpedanceGraph(impedanceBefore, impedanceAfter, limitDeltaZ, percentDeltaZ);
        });
    }
}

// Função de inicialização do módulo Curto-Circuito
async function initShortCircuit() {
    console.log('Módulo Curto-Circuito carregado e pronto para interatividade.');

    if (window.setupApiFormPersistence) {
        await window.setupApiFormPersistence('short-circuit-form', 'shortCircuit');
    } else {
        console.warn('[short_circuit] Sistema de persistência não disponível');
    }

    // Carregar e preencher os dados do próprio módulo de curto-circuito
    await loadShortCircuitDataAndPopulateForm();

    // Adicionar listener para o evento transformerDataUpdated
    document.addEventListener('transformerDataUpdated', async (event) => {
        console.log('[short_circuit] Evento transformerDataUpdated recebido:', event.detail);
        // Recarrega os dados do próprio módulo para garantir consistência
        await loadShortCircuitDataAndPopulateForm();
        // Se houver campos que dependem diretamente dos dados básicos do transformador,
        // eles podem ser atualizados aqui.
    });

    const transformerInfoPlaceholderId = 'transformer-info-short_circuit-page';
    await loadAndPopulateTransformerInfo(transformerInfoPlaceholderId);

    setupCalcButton();
}

// SPA routing: executa quando o módulo short_circuit é carregado
document.addEventListener('moduleContentLoaded', (event) => {
    if (event.detail && event.detail.moduleName === 'short_circuit') {
        console.log('[short_circuit] SPA routing init');
        initShortCircuit();
    }
});

// Fallback para carregamento direto da página (se não for SPA)
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('short-circuit-form')) { // Assumindo um ID de formulário principal para o módulo
        console.log('[short_circuit] DOMContentLoaded init (fallback)');
        initShortCircuit();
    }
});