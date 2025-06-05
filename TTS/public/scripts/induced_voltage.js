// public/scripts/induced_voltage.js - ATUALIZADO

import { loadAndPopulateTransformerInfo } from './common_module.js';
import { collectFormData, fillFormWithData } from './api_persistence.js';

// Função para carregar dados do store 'inducedVoltage' e preencher o formulário
async function loadInducedVoltageDataAndPopulateForm() {
    try {
        console.log('[induced_voltage] Carregando dados do store "inducedVoltage" e preenchendo formulário...');
        await waitForApiSystem(); // Garante que o sistema de persistência esteja pronto

        const store = window.apiDataSystem.getStore('inducedVoltage');
        const data = await store.getData();

        if (data && data.formData) {
            const formElement = document.getElementById('induced-voltage-form');
            if (formElement) {
                fillFormWithData(formElement, data.formData);
                console.log('[induced_voltage] Formulário de tensão induzida preenchido com dados do store:', data.formData);
            } else {
                console.warn('[induced_voltage] Formulário "induced-voltage-form" não encontrado para preenchimento.');
            }
        } else {
            console.log('[induced_voltage] Nenhum dado de tensão induzida encontrado no store.');
        }
    } catch (error) {
        console.error('[induced_voltage] Erro ao carregar e preencher dados de tensão induzida:', error);
    }
}

// Função para preencher alguns inputs com dados do transformer_inputs
async function fillInputsFromTransformerData() {
    const store = window.apiDataSystem.getStore('transformerInputs');
    const transformerData = await store.getData();
    const formData = transformerData.formData || {};

    // Preenche tipo de transformador
    const tipoTrafoSelect = document.getElementById('tipo-transformador-induced');
    if (tipoTrafoSelect) tipoTrafoSelect.value = formData.tipo_transformador || 'Trifásico';

    // Capacitância (simulada)
    const capInput = document.getElementById('capacitancia');
    if (capInput && !capInput.value) capInput.value = '1500'; // Valor padrão se vazio, pode vir do backend depois

    // Frequência de teste (vem do input ou padrão)
    const freqTesteInput = document.getElementById('frequencia-teste');
    if (freqTesteInput && !freqTesteInput.value) freqTesteInput.value = '120'; // Padrão se vazio

    // Tensões (vêm de Dados Básicos)
    // Aqui você precisaria armazenar esses valores em variáveis locais
    // para que o cálculo possa acessá-los.
    // Para este exemplo, usaremos valores fixos ou dos inputs onde possível.
}

// Função para salvar resultados de cálculo
async function saveCalculationResults(results) {
    const store = window.apiDataSystem.getStore('inducedVoltage');
    await store.updateData({ calculationResults: results });
}

// Lógica para o botão "Calcular"
async function setupCalcButton() {
    const calcBtn = document.getElementById('calc-induced-voltage-btn');
    if (calcBtn) {
        calcBtn.addEventListener('click', async function() {
            console.log('Botão Calcular Tensão Induzida clicado!');
            const tipoTransformador = getInputValue('tipo-transformador-induced');
            const frequenciaTeste = parseFloat(getInputValue('frequencia-teste'));
            const capacitancia = parseFloat(getInputValue('capacitancia'));

            const store = window.apiDataSystem.getStore('transformerInputs');
            const transformerData = await store.getData();
            const formData = transformerData.formData || {};

            const tensaoAt = formData.tensao_at;
            const tensaoBt = formData.tensao_bt;
            const freqNominal = formData.frequencia;
            const testeTensaoInduzidaAt = formData.teste_tensao_induzida_at;

            // Simulação de valores que viriam de 'losses' ou de outros cálculos
            const inducaoNominal = 1.7; // Exemplo
            const pesoNucleo = 5000; // kg, Exemplo (5 Ton)
            const perdasVazio = 10; // kW, Exemplo

            let resultsHtml = '';
            let errorMessage = '';

            if (isNaN(frequenciaTeste) || isNaN(capacitancia) || isNaN(tensaoAt) || isNaN(tensaoBt) || isNaN(freqNominal) || isNaN(testeTensaoInduzidaAt)) {
                errorMessage = "Por favor, preencha todos os parâmetros necessários (incluindo os de Dados Básicos).";
            } else {
                // Simulação de cálculo (muito simplificado, apenas para demonstração)
                const sqrt3 = (tipoTransformador === 'Trifásico') ? Math.sqrt(3) : 1;
                const tensaoProva = testeTensaoInduzidaAt; // Tensão de ensaio induzida

                const inducaoTeste = Math.min(1.9, inducaoNominal * (tensaoProva / tensaoAt) * (freqNominal / frequenciaTeste));

                // Simulação de lookup em tabelas (valores fixos para demo)
                const fatorPerdas = 1.2 + (inducaoTeste - 1.0) * 0.5 + (frequenciaTeste - 60) * 0.01; // W/kg
                const fatorPotenciaMag = 2.0 + (inducaoTeste - 1.0) * 1.0 + (frequenciaTeste - 60) * 0.02; // VAr/kg

                const potAtiva = fatorPerdas * pesoNucleo / 1000; // kW
                const potMagnetica = fatorPotenciaMag * pesoNucleo / 1000; // kVA (reativa)

                if (tipoTransformador === 'Monofásico') {
                    const potInduzida = Math.sqrt(Math.max(0, potMagnetica * potMagnetica - potAtiva * potAtiva)); // kVAr ind
                    const uCalcScap = tensaoProva - ((tensaoBt / tensaoAt) * tensaoProva); // Simplificado
                    const pcap = -((uCalcScap * 1000)**2 * 2 * Math.PI * frequenciaTeste * capacitancia * 1e-12) / (tipoTransformador === 'Monofásico' ? 1 : 3) / 1000; // kVAr cap
                    const scapSindRatio = potInduzida > 0 ? Math.abs(pcap) / potInduzida : 0;

                    resultsHtml = `
                        <h5>Resultados Monofásico:</h5>
                        <p><strong>Potência Ativa (Pw):</strong> ${potAtiva.toFixed(2)} kW</p>
                        <p><strong>Potência Magnética (Sm):</strong> ${potMagnetica.toFixed(2)} kVA</p>
                        <p><strong>Componente Indutiva (Sind):</strong> ${potInduzida.toFixed(2)} kVAr ind</p>
                        <p><strong>Potência Capacitiva (Scap):</strong> ${pcap.toFixed(2)} kVAr cap</p>
                        <p><strong>Razão Scap/Sind:</strong> ${scapSindRatio.toFixed(2)}</p>
                    `;
                } else { // Trifásico
                    const correnteExcitacao = potMagnetica / (tensaoBt * sqrt3); // A
                    const potenciaTeste = correnteExcitacao * tensaoBt * sqrt3; // kVA

                    resultsHtml = `
                        <h5>Resultados Trifásico:</h5>
                        <p><strong>Tensão Aplicada BT:</strong> ${tensaoBt.toFixed(1)} kV</p>
                        <p><strong>Potência Ativa (Pw):</strong> ${potAtiva.toFixed(2)} kW</p>
                        <p><strong>Potência Magnética (Sm):</strong> ${potMagnetica.toFixed(2)} kVA</p>
                        <p><strong>Corrente Excitação:</strong> ${correnteExcitacao.toFixed(2)} A</p>
                        <p><strong>Potência de Teste:</strong> ${potenciaTeste.toFixed(2)} kVA</p>
                    `;
                }
            }

            document.getElementById('resultado-tensao-induzida').innerHTML = resultsHtml;
            document.getElementById('induced-voltage-error-message').textContent = errorMessage;

            // Salvar resultados no store
            const resultsToSave = {
                tipoTransformador,
                frequenciaTeste,
                capacitancia,
                tensaoAt,
                tensaoBt,
                freqNominal,
                testeTensaoInduzidaAt,
                potAtiva,
                potMagnetica,
                resultsHtml
            };
            await saveCalculationResults(resultsToSave);
        });
    }
}

// Lógica para gerar tabela de frequências (muito simplificada)
async function setupFrequencyTableButtons() {
    const generateFreqTableBtn = document.getElementById('generate-frequency-table-button');
    const clearFreqTableBtn = document.getElementById('clear-frequency-table-button');
    const freqTableContainer = document.getElementById('frequency-table-container');

    if (generateFreqTableBtn) {
        generateFreqTableBtn.addEventListener('click', function() {
            console.log('Gerar Tabela de Frequências clicado!');
            let tableHtml = '<h5>Análise de Frequências:</h5><table class="table table-sm table-striped"><thead><tr><th>Frequência (Hz)</th><th>Potência Ativa (kW)</th><th>Potência Magnética (kVA)</th></tr></thead><tbody>';
            const freqs = [100, 120, 150, 180, 200, 240];
            freqs.forEach(f => {
                const potAtivaSim = (10 + (f / 100)).toFixed(2);
                const potMagSim = (25 - (f / 100) * 5).toFixed(2);
                tableHtml += `<tr><td>${f}</td><td>${potAtivaSim}</td><td>${potMagSim}</td></tr>`;
            });
            tableHtml += '</tbody></table>';
            freqTableContainer.innerHTML = tableHtml;
        });
    }

    if (clearFreqTableBtn) {
        clearFreqTableBtn.addEventListener('click', function() {
            freqTableContainer.innerHTML = '';
            console.log('Tabela de frequências limpa.');
        });
    }
}

// Função de inicialização do módulo Tensão Induzida
async function initInducedVoltage() {
    console.log('Módulo Tensão Induzida carregado e pronto para interatividade.');

    // Setup form persistence
    if (window.setupApiFormPersistence) {
        await window.setupApiFormPersistence('induced-voltage-form', 'inducedVoltage');
    } else {
        console.warn('[induced_voltage] Sistema de persistência não disponível');
    }

    // Carregar e preencher os dados do próprio módulo de tensão induzida
    await loadInducedVoltageDataAndPopulateForm();

    // Adicionar listener para o evento transformerDataUpdated
    document.addEventListener('transformerDataUpdated', async (event) => {
        console.log('[induced_voltage] Evento transformerDataUpdated recebido:', event.detail);
        // Recarrega os dados do próprio módulo para garantir consistência
        await loadInducedVoltageDataAndPopulateForm();
        // Atualiza inputs que dependem dos dados básicos do transformador
        await fillInputsFromTransformerData();
    });

    // ID do placeholder para o painel de informações do transformador
    const transformerInfoPlaceholderId = 'transformer-info-induced_voltage-page';
    await loadAndPopulateTransformerInfo(transformerInfoPlaceholderId); // Carrega o painel no topo

    await fillInputsFromTransformerData(); // Preenche inputs ao carregar o módulo
    await setupCalcButton(); // Configura o botão de cálculo
    await setupFrequencyTableButtons(); // Configura os botões da tabela de frequência
}

// SPA routing: executa quando o módulo induced_voltage é carregado
document.addEventListener('moduleContentLoaded', (event) => {
    if (event.detail && event.detail.moduleName === 'induced_voltage') {
        console.log('[induced_voltage] SPA routing init');
        initInducedVoltage();
    }
});

// Fallback para carregamento direto da página (se não for SPA)
document.addEventListener('DOMContentLoaded', () => {
    // Verifica se o elemento principal do módulo está presente para evitar execução em outras páginas
    if (document.getElementById('induced-voltage-form')) { // Assumindo um ID de formulário principal para o módulo
        console.log('[induced_voltage] DOMContentLoaded init (fallback)');
        initInducedVoltage();
    }
});