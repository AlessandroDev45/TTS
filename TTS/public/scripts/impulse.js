// public/scripts/impulse.js - ATUALIZADO

import { loadAndPopulateTransformerInfo } from './common_module.js';
import { collectFormData, fillFormWithData, setupApiFormPersistence } from './api_persistence.js'; // Importa setupApiFormPersistence

// Função para carregar dados do store 'impulse' e preencher o formulário
async function loadImpulseDataAndPopulateForm() {
    try {
        console.log('[impulse] Carregando dados do store "impulse" e preenchendo formulário...');
        await waitForApiSystem(); // Garante que o sistema de persistência esteja pronto

        const store = window.apiDataSystem.getStore('impulse');
        const data = await store.getData();

        if (data && data.formData) {
            const formElement = document.querySelector('.card.flex-grow-1.d-flex.flex-column'); // Onde os inputs estão
            if (formElement) {
                fillFormWithData(formElement, data.formData);
                console.log('[impulse] Formulário de impulso preenchido com dados do store:', data.formData);
            } else {
                console.warn('[impulse] Formulário de impulso (card body) não encontrado para preenchimento.');
            }
        } else {
            console.log('[impulse] Nenhum dado de impulso encontrado no store.');
        }
    } catch (error) {
        console.error('[impulse] Erro ao carregar e preencher dados de impulso:', error);
    }
}

// Função de inicialização do módulo Impulso
async function initImpulse() {
    console.log('Módulo Impulso carregado e pronto para interatividade.');

    // ID do placeholder para o painel de informações do transformador
    const transformerInfoPlaceholderId = 'transformer-info-impulse-page';
    await loadAndPopulateTransformerInfo(transformerInfoPlaceholderId); // Carrega o painel no topo
    
    // Configurar persistência automática do formulário
    // Usar o card principal que contém todos os inputs
    const mainFormContainer = document.querySelector('.card.flex-grow-1.d-flex.flex-column');
    if (mainFormContainer) {
        await setupApiFormPersistence(mainFormContainer, 'impulse'); // Usa a função importada
    } else {
        console.warn('[impulse] Contêiner principal do formulário não encontrado para persistência.');
    }

    // Carregar e preencher os dados do próprio módulo de impulso
    await loadImpulseDataAndPopulateForm();

    // Adicionar listener para o evento transformerDataUpdated
    document.addEventListener('transformerDataUpdated', async (event) => {
        console.log('[impulse] Evento transformerDataUpdated recebido:', event.detail);
        // Recarrega os dados do próprio módulo para garantir consistência
        await loadImpulseDataAndPopulateForm();
    });

    // Configurar spinners para campos numéricos
    setupNumericSpinners();
    
    // Configurar botão de simulação
    setupSimulationButton();
}

// Função para configurar spinners dos campos numéricos
function setupNumericSpinners() {
    const spinnerConfigs = [
        { upId: 'voltage-up', downId: 'voltage-down', inputId: 'test-voltage', step: 10 },
        { upId: 'dut-cap-up', downId: 'dut-cap-down', inputId: 'test-object-capacitance', step: 100 },
        { upId: 'stray-cap-up', downId: 'stray-cap-down', inputId: 'stray-capacitance', step: 50 }
    ];

    spinnerConfigs.forEach(config => {
        const upBtn = document.getElementById(config.upId);
        const downBtn = document.getElementById(config.downId);
        const input = document.getElementById(config.inputId);

        if (upBtn && input) {
            upBtn.addEventListener('click', () => {
                const currentValue = parseFloat(input.value) || 0;
                input.value = currentValue + config.step;
                // Dispara evento 'input' para detecção imediata de mudanças
                input.dispatchEvent(new Event('input', { bubbles: true }));
                // Dispara evento 'change' para acionar persistência
                input.dispatchEvent(new Event('change', { bubbles: true }));
                // Fornece feedback visual
                upBtn.classList.add('active');
                setTimeout(() => upBtn.classList.remove('active'), 200);
            });
        }

        if (downBtn && input) {
            downBtn.addEventListener('click', () => {
                const currentValue = parseFloat(input.value) || 0;
                const newValue = Math.max(0, currentValue - config.step);
                input.value = newValue;
                // Dispara evento 'input' para detecção imediata de mudanças
                input.dispatchEvent(new Event('input', { bubbles: true }));
                // Dispara evento 'change' para acionar persistência
                input.dispatchEvent(new Event('change', { bubbles: true }));
                // Fornece feedback visual
                downBtn.classList.add('active');
                setTimeout(() => downBtn.classList.remove('active'), 200);
            });
        }
    });
}

// Função para configurar o botão de simulação
function setupSimulationButton() {
    const simulateButton = document.getElementById('simulate-button');
    const simulateButtonText = document.getElementById('simulate-button-text');
    const simulateSpinner = document.getElementById('simulate-spinner');
    
    if (simulateButton) {
        simulateButton.addEventListener('click', async function() {
            console.log('Botão Simular Impulso clicado!');
            
            // Desabilita o botão durante a simulação
            simulateButton.disabled = true;
            if (simulateButtonText) simulateButtonText.textContent = 'Simulando...';
            if (simulateSpinner) simulateSpinner.classList.remove('d-none');
            
            try {
                // Coleta dados do formulário
                const formData = await getImpulseFormData();
                
                // Simula o processamento
                await simulateImpulseTest(formData);
                
                // Feedback visual de sucesso
                simulateButton.classList.remove('btn-primary');
                simulateButton.classList.add('btn-success');
                if (simulateButtonText) simulateButtonText.textContent = 'Simulação Concluída';
                
                // Retorna ao estado normal após um tempo
                setTimeout(() => {
                    simulateButton.classList.remove('btn-success');
                    simulateButton.classList.add('btn-primary');
                    if (simulateButtonText) simulateButtonText.textContent = 'Simular Forma de Onda';
                }, 2000);
                
            } catch (error) {
                console.error('Erro na simulação:', error);
                simulateButton.classList.remove('btn-primary');
                simulateButton.classList.add('btn-danger');
                if (simulateButtonText) simulateButtonText.textContent = 'Erro na Simulação';
                
                // Retorna ao estado normal após um tempo
                setTimeout(() => {
                    simulateButton.classList.remove('btn-danger');
                    simulateButton.classList.add('btn-primary');
                    if (simulateButtonText) simulateButtonText.textContent = 'Simular Forma de Onda';
                }, 2000);
            } finally {
                // Reabilita o botão
                setTimeout(() => {
                    simulateButton.disabled = false;
                    if (simulateSpinner) simulateSpinner.classList.add('d-none');
                }, 1500);
            }
        });
        
        // Configurar radio buttons para atualizar o título do gráfico
        const radioButtons = document.querySelectorAll('input[name="impulseType"]');
        const waveformTitleDisplay = document.getElementById('waveform-title-display');
        
        radioButtons.forEach(radio => {
            radio.addEventListener('change', function() {
                if (waveformTitleDisplay) {
                    let title = 'Forma de Onda de Tensão e Corrente';
                    
                    switch(this.value) {
                        case 'lightning':
                            title = 'Forma de Onda de Impulso Atmosférico (1.2/50µs)';
                            break;
                        case 'switching':
                            title = 'Forma de Onda de Impulso de Manobra (250/2500µs)';
                            break;
                        case 'chopped':
                            title = 'Forma de Onda de Impulso Cortado';
                            break;
                    }
                    
                    waveformTitleDisplay.textContent = title;
                    
                    // Mostrar ou ocultar elementos específicos por tipo
                    const gapContainer = document.getElementById('gap-distance-container');
                    const capContainer = document.getElementById('capacitor-si-container');
                    const warningAlert = document.getElementById('si-model-warning-alert');
                    
                    if (gapContainer) gapContainer.style.display = this.value === 'chopped' ? 'block' : 'none';
                    if (capContainer) capContainer.style.display = this.value === 'switching' ? 'block' : 'none';
                    if (warningAlert) warningAlert.style.display = this.value === 'switching' ? 'block' : 'none';
                }
            });
        });
    }
}

// Função para coletar dados do formulário de impulso
async function getImpulseFormData() {
    const store = window.apiDataSystem.getStore('impulse');
    const impulseData = await store.getData();
    
    // Coleta dados específicos dos elementos do formulário
    const formData = {
        impulseType: document.querySelector('input[name="impulseType"]:checked')?.value || 'lightning',
        testVoltage: document.getElementById('test-voltage')?.value || 1200,
        generatorConfig: document.getElementById('generator-config')?.value || '6S-1P',
        simulationModel: document.getElementById('simulation-model-type')?.value || 'hybrid',
        dutCapacitance: document.getElementById('test-object-capacitance')?.value || 3000,
        shuntResistor: document.getElementById('shunt-resistor')?.value || 0.01,
        strayCapacitance: document.getElementById('stray-capacitance')?.value || 400,
        ...impulseData.formData
    };
    
    return formData;
}

// Função para simular o teste de impulso
async function simulateImpulseTest(formData) {
    console.log('Simulando teste de impulso com dados:', formData);
    
    // Mostrar spinners durante o carregamento
    document.getElementById('voltage-spinner')?.classList.remove('d-none');
    document.getElementById('current-spinner')?.classList.remove('d-none');
    
    // Simula delay de processamento
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Gera resultados simulados
    const waveformData = generateSimulatedWaveform(formData);
    const results = {
        waveform: waveformData,
        timestamp: new Date().toISOString()
    };
    
    // Salva os resultados
    await saveCalculationResults(results);
    
    // Atualiza a interface com os resultados
    displaySimulationResults(results);
    
    // Atualiza alertas de conformidade com base no tipo de impulso
    updateComplianceAlerts(formData.impulseType, waveformData.parameters);
    
    console.log('Simulação concluída:', results);
}

// Função para atualizar alertas de conformidade
function updateComplianceAlerts(impulseType, parameters) {
    // Limpa alertas anteriores
    document.getElementById('compliance-overall-alert')?.classList.add('d-none');
    document.getElementById('oscillation-warning-alert')?.classList.add('d-none');
    document.getElementById('energy-compliance-alert')?.classList.add('d-none');
    document.getElementById('shunt-voltage-alert')?.classList.add('d-none');
    
    // Mostra alerta de conformidade baseado em regras diferentes para cada tipo de impulso
    let isCompliant = true;
    
    // Verificação simplificada de conformidade
    if (impulseType === 'lightning') {
        // Para impulso atmosférico
        if (parameters.frontTime < 1.0 || parameters.frontTime > 1.5) isCompliant = false;
        if (parameters.tailTime < 40 || parameters.tailTime > 60) isCompliant = false;
        
        // Simulando oscilação com 20% de chance
        if (Math.random() < 0.2) {
            document.getElementById('oscillation-warning-alert')?.classList.remove('d-none');
        }
    } else if (impulseType === 'switching') {
        // Para impulso de manobra
        if (parameters.frontTime < 200 || parameters.frontTime > 300) isCompliant = false;
        if (parameters.tailTime < 2000 || parameters.tailTime > 3000) isCompliant = false;
    } else if (impulseType === 'chopped') {
        // Para impulso cortado
        if (parameters.frontTime < 1.0 || parameters.frontTime > 1.5) isCompliant = false;
    }
    
    // Mostra alerta de conformidade
    if (!isCompliant) {
        document.getElementById('compliance-overall-alert')?.classList.remove('d-none');
    }
    
    // Mostra alerta de energia
    if (parameters.efficiency > 0.8) {
        document.getElementById('energy-compliance-alert')?.classList.remove('d-none');
    }
    
    // Alerta de tensão de shunt (simulação)
    if (parameters.peakVoltage > 1800 && Math.random() > 0.7) {
        document.getElementById('shunt-voltage-alert')?.classList.remove('d-none');
    }
}

// Função para gerar forma de onda simulada
function generateSimulatedWaveform(formData) {
    // Gera pontos de uma forma de onda 1.2/50µs simplificada
    const voltagePoints = [];
    const currentPoints = [];
    const totalTime = 100; // µs
    const dt = 0.1; // µs
    
    const impulseType = formData.impulseType;
    const testVoltage = parseFloat(formData.testVoltage);
    const dutCapacitance = parseFloat(formData.dutCapacitance);
    const shuntResistor = parseFloat(formData.shuntResistor);
    
    // Parâmetros específicos para cada tipo de impulso
    let frontTime, tailTime;
    
    switch(impulseType) {
        case 'lightning':
            frontTime = 1.2;
            tailTime = 50;
            break;
        case 'switching':
            frontTime = 250;
            tailTime = 2500;
            break;
        case 'chopped':
            frontTime = 1.2;
            tailTime = 50;
            break;
        default:
            frontTime = 1.2;
            tailTime = 50;
    }
    
    let timeStep = impulseType === 'switching' ? 1.0 : 0.1; // µs (maior para manobra)
    let simulationTime = impulseType === 'switching' ? 5000 : 100; // µs (maior para manobra)
    
    let times = [];
    let voltageValues = [];
    let currentValues = [];
    
    for (let t = 0; t <= simulationTime; t += timeStep) {
        times.push(t);
        
        let voltage = 0;
        
        if (impulseType === 'chopped' && t >= 4) {
            // Onda de impulso cortada em 4µs
            voltage = t < 4 ? testVoltage * (1 - Math.exp(-t/frontTime)) * Math.exp(-t/tailTime) : 0;
        } else {
            // Fórmula da onda de impulso atmosférico ou manobra
            voltage = testVoltage * (1 - Math.exp(-t/frontTime)) * Math.exp(-t/tailTime);
        }
        
        // Simulação simplificada da corrente baseada na derivada da tensão e capacitância
        const dv = t > 0 ? (voltage - (voltageValues[voltageValues.length - 1] || 0)) / timeStep : 0;
        const current = dutCapacitance * 1e-12 * dv * 1e6; // em Amperes
        
        voltageValues.push(voltage);
        currentValues.push(current);
        
        voltagePoints.push({ time: t, voltage: voltage });
        currentPoints.push({ time: t, current: current });
    }
    
    return {
        voltage: { times, values: voltageValues },
        current: { times, values: currentValues },
        parameters: {
            frontTime,
            tailTime,
            peakVoltage: testVoltage,
            peakCurrent: Math.max(...currentValues),
            efficiency: 0.95 - (0.05 * Math.random()) // Simulação da eficiência
        }
    };
}

// Função para exibir resultados da simulação
function displaySimulationResults(results) {
    // Esconder os spinners e mostrar os gráficos
    document.getElementById('voltage-spinner')?.classList.add('d-none');
    document.getElementById('current-spinner')?.classList.add('d-none');
    
    // Plotar o gráfico de tensão
    const voltageData = results.waveform.voltage;
    
    const voltagePlot = {
        x: voltageData.times,
        y: voltageData.values,
        type: 'scatter',
        mode: 'lines',
        name: 'Tensão (kV)',
        line: {
            color: '#36a2eb',
            width: 2
        }
    };
    
    const voltageLayout = {
        title: {
            text: 'Forma de Onda de Tensão',
            font: {
                size: 14,
                color: '#ffffff'
            }
        },
        xaxis: {
            title: {
                text: 'Tempo (µs)',
                font: {
                    color: '#ffffff'
                }
            },
            color: '#ffffff',
            gridcolor: 'rgba(255, 255, 255, 0.1)'
        },
        yaxis: {
            title: {
                text: 'Tensão (kV)',
                font: {
                    color: '#ffffff'
                }
            },
            color: '#ffffff',
            gridcolor: 'rgba(255, 255, 255, 0.1)'
        },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        margin: {
            l: 50,
            r: 20,
            t: 40,
            b: 40
        },
        autosize: true
    };
    
    // Plotar o gráfico de corrente
    const currentData = results.waveform.current;
    
    const currentPlot = {
        x: currentData.times,
        y: currentData.values,
        type: 'scatter',
        mode: 'lines',
        name: 'Corrente (A)',
        line: {
            color: '#ff6384',
            width: 2
        }
    };
    
    const currentLayout = {
        title: {
            text: 'Forma de Onda de Corrente',
            font: {
                size: 14,
                color: '#ffffff'
            }
        },
        xaxis: {
            title: {
                text: 'Tempo (µs)',
                font: {
                    color: '#ffffff'
                }
            },
            color: '#ffffff',
            gridcolor: 'rgba(255, 255, 255, 0.1)'
        },
        yaxis: {
            title: {
                text: 'Corrente (A)',
                font: {
                    color: '#ffffff'
                }
            },
            color: '#ffffff',
            gridcolor: 'rgba(255, 255, 255, 0.1)'
        },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        margin: {
            l: 50,
            r: 20,
            t: 40,
            b: 40
        },
        autosize: true
    };
    
    // Renderizar os gráficos
    Plotly.newPlot('impulse-waveform', [voltagePlot], voltageLayout, {responsive: true});
    Plotly.newPlot('impulse-current', [currentPlot], currentLayout, {responsive: true});
    
    // Atualizar tabelas de análise
    updateAnalysisTables(results);
}

// Função para atualizar as tabelas de análise com base nos resultados
function updateAnalysisTables(results) {
    const waveformParams = results.waveform.parameters;
    
    // Atualizar a tabela de análise da forma de onda
    const waveformAnalysisTable = document.getElementById('waveform-analysis-table');
    if (waveformAnalysisTable) {
        waveformAnalysisTable.innerHTML = `
            <table class="table table-sm table-bordered">
                <thead>
                    <tr>
                        <th colspan="2" class="text-center">Análise da Forma de Onda</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Tensão de Pico</td>
                        <td class="text-end">${waveformParams.peakVoltage.toFixed(1)} kV</td>
                    </tr>
                    <tr>
                        <td>Corrente de Pico</td>
                        <td class="text-end">${waveformParams.peakCurrent.toFixed(3)} A</td>
                    </tr>
                    <tr>
                        <td>Tempo de Frente (T1)</td>
                        <td class="text-end">${waveformParams.frontTime.toFixed(1)} μs</td>
                    </tr>
                    <tr>
                        <td>Tempo até Meio Valor (T2)</td>
                        <td class="text-end">${waveformParams.tailTime.toFixed(1)} μs</td>
                    </tr>
                    <tr>
                        <td>Eficiência do Gerador</td>
                        <td class="text-end">${(waveformParams.efficiency * 100).toFixed(1)}%</td>
                    </tr>
                </tbody>
            </table>
        `;
    }
    
    // Atualizar a tabela de parâmetros do circuito
    const circuitParamsDisplay = document.getElementById('circuit-parameters-display');
    if (circuitParamsDisplay) {
        // Valores simulados para o circuito
        const stagesTotalCapacitance = 600; // nF
        const stagesPerParallel = parseInt(document.getElementById('generator-config')?.value?.split('-')[0]?.replace('S', '') || '6');
        const numberParallelSets = parseInt(document.getElementById('generator-config')?.value?.split('-')[1]?.replace('P', '') || '1');
        
        circuitParamsDisplay.innerHTML = `
            <table class="table table-sm table-bordered">
                <thead>
                    <tr>
                        <th colspan="2" class="text-center">Parâmetros do Circuito</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Capacitância Total do Gerador</td>
                        <td class="text-end">${stagesTotalCapacitance * numberParallelSets / stagesPerParallel} nF</td>
                    </tr>
                    <tr>
                        <td>Capacitância por Estágio</td>
                        <td class="text-end">${stagesTotalCapacitance / stagesPerParallel} nF</td>
                    </tr>
                    <tr>
                        <td>Resistência de Frente (total)</td>
                        <td class="text-end">${parseFloat(document.getElementById('front-resistor-expression')?.value || '15') * stagesPerParallel / numberParallelSets} Ω</td>
                    </tr>
                    <tr>
                        <td>Resistência de Cauda (total)</td>
                        <td class="text-end">${parseFloat(document.getElementById('tail-resistor-expression')?.value || '100') * stagesPerParallel / numberParallelSets} Ω</td>
                    </tr>
                </tbody>
            </table>
        `;
    }
    
    // Atualizar a tabela de detalhes de energia
    const energyDetailsTable = document.getElementById('energy-details-table');
    if (energyDetailsTable) {
        // Valores simulados para energia
        const maxEnergy = 360; // kJ
        const energyEfficiency = waveformParams.efficiency;
        const usedEnergy = (maxEnergy * energyEfficiency * (waveformParams.peakVoltage / 2400) ** 2).toFixed(1);
        
        energyDetailsTable.innerHTML = `
            <table class="table table-sm table-bordered">
                <thead>
                    <tr>
                        <th colspan="2" class="text-center">Detalhes de Energia</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Energia Máxima do Sistema</td>
                        <td class="text-end">360 kJ</td>
                    </tr>
                    <tr>
                        <td>Energia Utilizada</td>
                        <td class="text-end">${usedEnergy} kJ</td>
                    </tr>
                    <tr>
                        <td>Eficiência da Transferência</td>
                        <td class="text-end">${(energyEfficiency * 100).toFixed(1)}%</td>
                    </tr>
                    <tr>
                        <td>Tensão de Carregamento</td>
                        <td class="text-end">${(waveformParams.peakVoltage / energyEfficiency).toFixed(1)} kV</td>
                    </tr>
                </tbody>
            </table>
        `;
    }
}

async function getTransformerFormData() {
    const store = window.apiDataSystem.getStore('transformerInputs');
    const transformerData = await store.getData();
    return transformerData.formData || {};
}

async function saveCalculationResults(results) {
    const store = window.apiDataSystem.getStore('impulse');
    await store.updateData({ calculationResults: results });
}

// SPA routing: executa quando o módulo impulse é carregado
document.addEventListener('moduleContentLoaded', (event) => {
    if (event.detail && event.detail.moduleName === 'impulse') {
        console.log('[impulse] SPA routing init');
        initImpulse();
    }
});

// Fallback para carregamento direto da página (se não for SPA)
document.addEventListener('DOMContentLoaded', () => {
    // Verifica se o elemento principal do módulo está presente para evitar execução em outras páginas
    if (document.querySelector('.card .card-body')) { // Verifica se há um card body (estrutura do impulse)
        console.log('[impulse] DOMContentLoaded init (fallback)');
        initImpulse();
    }
});