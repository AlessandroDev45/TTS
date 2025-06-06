// public/scripts/losses.js

import { loadAndPopulateTransformerInfo } from './common_module.js';
import { collectFormData, fillFormWithData } from './api_persistence.js';

// Função para aguardar o sistema de persistência estar pronto
async function waitForApiSystem() {
    return new Promise((resolve) => {
        if (window.apiDataSystem) {
            resolve();
        } else {
            const checkInterval = setInterval(() => {
                if (window.apiDataSystem) {
                    clearInterval(checkInterval);
                    resolve();
                }
            }, 100);
            // Timeout após 10 segundos
            setTimeout(() => {
                clearInterval(checkInterval);
                resolve();
            }, 10000);
        }
    });
}

// Função para carregar dados do store 'losses' e preencher o formulário
async function loadLossesDataAndPopulateForm() {
    try {
        console.log('[losses] Carregando dados do store "losses" e preenchendo formulário...');
        await waitForApiSystem(); // Garante que o sistema de persistência esteja pronto

        const store = window.apiDataSystem.getStore('losses');
        const data = await store.getData();

        if (data && data.formData) {
            const formElement = document.getElementById('lossesTabContent');
            if (formElement) {
                fillFormWithData(formElement, data.formData);
                console.log('[losses] Formulário de perdas preenchido com dados do store:', data.formData);
            } else {
                console.warn('[losses] Formulário "lossesTabContent" não encontrado para preenchimento.');
            }
        } else {
            console.log('[losses] Nenhum dado de perdas encontrado no store.');
        }
    } catch (error) {
        console.error('[losses] Erro ao carregar e preencher dados de perdas:', error);
    }
}

// Função de inicialização do módulo de Perdas
async function initLosses() {
    console.log("[losses] losses.js: Initializing interactivity for Losses module.");

    // ID do placeholder para o painel de informações do transformador
    const transformerInfoPlaceholderId = 'transformer-info-losses-page';
    console.log(`[losses] Chamando loadAndPopulateTransformerInfo para ${transformerInfoPlaceholderId}`);
    try {
        await loadAndPopulateTransformerInfo(transformerInfoPlaceholderId);
        console.log(`[losses] loadAndPopulateTransformerInfo concluído para ${transformerInfoPlaceholderId}`);
    } catch (error) {
        console.error(`[losses] Erro em loadAndPopulateTransformerInfo para ${transformerInfoPlaceholderId}:`, error);
        // Continua a execução mesmo com erro no painel de info
    }

    // Configurar persistência automática do formulário para a aba ativa
    const setupActiveTabPersistence = async () => {
        console.log('[losses] Iniciando setupActiveTabPersistence');
        const activeTabContent = document.querySelector('#lossesTabContent .tab-pane.show.active');
        if (activeTabContent && window.setupApiFormPersistence) {
            console.log('[losses] Aba ativa encontrada, configurando persistência...');
            // Passa o elemento da aba ativa para setupApiFormPersistence
            try {
                await window.setupApiFormPersistence(activeTabContent, 'losses');
                console.log('[losses] setupApiFormPersistence concluído.');
            } catch (error) {
                console.error('[losses] Erro em setupApiFormPersistence:', error);
            }
        } else {
            console.warn('[losses] Aba ativa ou sistema de persistência não encontrado para setup inicial.');
        }
        console.log('[losses] setupActiveTabPersistence concluído');
    };

    // Chama a configuração inicial para a aba ativa
    console.log('[losses] Chamando setupActiveTabPersistence inicial');
    await setupActiveTabPersistence();

    // Adiciona listeners para quando as abas são mostradas
    const lossesTab = document.getElementById('lossesTab');
    if (lossesTab) {
        lossesTab.addEventListener('shown.bs.tab', async (event) => {
            console.log(`[losses] Aba "${event.target.id}" mostrada. Reconfigurando persistência.`);
            await setupActiveTabPersistence();
        });
    } else {
        console.warn('[losses] Elemento #lossesTab não encontrado. A persistência pode não funcionar corretamente na troca de abas.');
    }

    // Carregar e preencher os dados do próprio módulo de perdas
    console.log('[losses] Chamando loadLossesDataAndPopulateForm');
    try {
        await loadLossesDataAndPopulateForm();
        console.log('[losses] loadLossesDataAndPopulateForm concluído');
    } catch (error) {
        console.error('[losses] Erro em loadLossesDataAndPopulateForm:', error);
        // Continua a execução mesmo com erro no carregamento de dados
    }

    // Adicionar listener para o evento transformerDataUpdated
    document.addEventListener('transformerDataUpdated', async (event) => {
        console.log('[losses] Evento transformerDataUpdated recebido:', event.detail);
        // Aqui você pode adicionar lógica para atualizar campos específicos do módulo de perdas
        // que dependem dos dados básicos do transformador.
        // Por exemplo, se a potência nominal mudar, recalcular algo.
        // Por enquanto, apenas recarrega os dados do próprio módulo para garantir consistência.
        console.log('[losses] Recarregando dados de perdas após transformerDataUpdated');
        await loadLossesDataAndPopulateForm();
    });

    // --- Helper for safely getting element and attaching listener ---
    // This helper function simplifies attaching event listeners and prevents
    // attaching multiple listeners to the same element if Dash re-renders it.
    function setupListener(elementId, eventType, handler, removeOld = true) {
        const element = document.getElementById(elementId);
        if (element) {
            // If an old listener reference exists, remove it first.
            if (removeOld && element._dash_js_listener) {
                element.removeEventListener(eventType, element._dash_js_listener);
            }
            // Attach the new listener.
            element.addEventListener(eventType, handler);
            // Store a reference to the attached handler for future removal.
            element._dash_js_listener = handler;
            console.log(`[losses] Attached listener for ${elementId}`);
            return true;
        }
        console.warn(`[losses] Element with ID '${elementId}' not found for listener setup.`);
        return false;
    }

    // --- Spinner Setup Function ---
    // This function defines the logic for incrementing/decrementing numeric input fields
    // using associated 'up' and 'down' spinner buttons.
    function setupNumericSpinners() {
        console.log('[losses] Iniciando setupNumericSpinners');
        // Define an object mapping spinner button IDs to their target input ID and step configuration.
        const spinners = {
            // Perdas em Vazio
            'perdas-vazio-kw-up': { id: 'perdas-vazio-kw', step: 0.1, min: 0 },
            'perdas-vazio-kw-down': { id: 'perdas-vazio-kw', step: -0.1, min: 0 },
            'peso-projeto-Ton-up': { id: 'peso-projeto-Ton', step: 0.1, min: 0 },
            'peso-projeto-Ton-down': { id: 'peso-projeto-Ton', step: -0.1, min: 0 },
            'corrente-excitacao-up': { id: 'corrente-excitacao', step: 0.01, min: 0 },
            'corrente-excitacao-down': { id: 'corrente-excitacao', step: -0.01, min: 0 },
            'inducao-nucleo-up': { id: 'inducao-nucleo', step: 0.1, min: 0 },
            'inducao-nucleo-down': { id: 'inducao-nucleo', step: -0.1, min: 0 },
            'corrente-excitacao-1-1-up': { id: 'corrente-excitacao-1-1', step: 0.01, min: 0 },
            'corrente-excitacao-1-1-down': { id: 'corrente-excitacao-1-1', step: -0.01, min: 0 },
            'corrente-excitacao-1-2-up': { id: 'corrente-excitacao-1-2', step: 0.01, min: 0 },
            'corrente-excitacao-1-2-down': { id: 'corrente-excitacao-1-2', step: -0.01, min: 0 },

            // Perdas em Carga
            'perdas-carga-kw_U_min-up': { id: 'perdas-carga-kw_U_min', step: 0.1, min: 0 },
            'perdas-carga-kw_U_min-down': { id: 'perdas-carga-kw_U_min', step: -0.1, min: 0 },
            'perdas-carga-kw_U_nom-up': { id: 'perdas-carga-kw_U_nom', step: 0.1, min: 0 },
            'perdas-carga-kw_U_nom-down': { id: 'perdas-carga-kw_U_nom', step: -0.1, min: 0 },
            'perdas-carga-kw_U_max-up': { id: 'perdas-carga-kw_U_max', step: 0.1, min: 0 },
            'perdas-carga-kw_U_max-down': { id: 'perdas-carga-kw_U_max', step: -0.1, min: 0 },
        };

        // Iterate over the defined spinners to attach event listeners
        Object.keys(spinners).forEach(function(spinnerId) {
            const config = spinners[spinnerId];
            const spinnerHandler = function(e) {
                e.preventDefault(); // Prevent default browser behavior (e.g., text selection)

                const targetInput = document.getElementById(config.id);
                if (!targetInput) return; // Exit if the target input element does not exist

                let currentValue = parseFloat(targetInput.value);
                // If current value is not a valid number, default to min or 0
                if (isNaN(currentValue)) {
                    currentValue = config.min !== undefined ? config.min : 0;
                }

                let newValue = currentValue + config.step;

                // Apply min/max constraints if defined in the config
                if (config.min !== undefined) {
                    newValue = Math.max(newValue, config.min);
                }
                if (config.max !== undefined) {
                    newValue = Math.min(newValue, config.max);
                }

                // Round the new value to avoid floating point inaccuracies.
                // Precision is determined by the number of decimal places in the `step`.
                const stepString = String(config.step);
                const decimalPlaces = stepString.includes('.') ? stepString.split('.')[1].length : 0;
                newValue = parseFloat(newValue.toFixed(decimalPlaces));

                // Only update the input value and dispatch events if the value has actually changed.
                // This prevents unnecessary Dash callback triggers.
                if (targetInput.value !== String(newValue)) {
                    targetInput.value = String(newValue);
                    // Dispatch 'input' event for immediate reactivity (Dash callbacks listening to `Input(id, 'value')`)
                    targetInput.dispatchEvent(new Event('input', { bubbles: true }));
                    // Dispatch 'change' event for when the user "finishes" interaction (Dash callbacks listening to `Input(id, 'n_clicks')` or `Input(id, 'value')` on blur/change)
                    targetInput.dispatchEvent(new Event('change', { bubbles: true }));
                    // console.log(`losses.js: Spinner '${spinnerId}' updated input '${config.id}' to: ${newValue}`);
                }
            };
            // Attach the click listener to the spinner element using the helper function.
            setupListener(spinnerId, 'click', spinnerHandler);
        });
        console.log('[losses] setupNumericSpinners concluído');
    }

    // --- MutationObserver for Dynamic Content ---
    // Dash applications often render content dynamically (e.g., when switching tabs or navigating).
    // The MutationObserver watches for changes in the DOM and re-runs `setupNumericSpinners`
    // to ensure that event listeners are attached to any newly rendered spinner buttons.
    const observer = new MutationObserver(function(mutations) {
        let needsSpinnerSetup = false;
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        // Check if the added node or any of its children contain the spinner elements
                        // or if it's the main content container for a tab (meaning new content was loaded).
                        if (node.querySelector('.fa-chevron-up, .fa-chevron-down') ||
                            // Assuming tab content sections have IDs like 'tab-perdas-vazio-content' or 'tab-perdas-carga-content'
                            // OR, if the tab container itself is replaced, watch its children.
                            node.id === 'tab-perdas-vazio' || node.id === 'tab-perdas-carga' ||
                            node.id === 'losses-tabs-content') { // ID of the container where tab content is rendered
                            needsSpinnerSetup = true;
                        }
                    }
                });
            }
        });

        if (needsSpinnerSetup) {
            console.log("[losses] DOM changed, re-running spinner setup after a short delay.");
            // Adiciona um pequeno atraso para garantir que os elementos estejam no DOM
            setTimeout(() => {
                setupNumericSpinners(); // Re-run the setup for all spinners
                setupCalculateButtons(); // Re-run the setup for calculate buttons
            }, 500); // Atraso aumentado para 500ms
        }
    });

    // --- Initial Setup and Observer Registration ---
    // Run `setupNumericSpinners` once when the script first loads to attach listeners to initial elements.
    console.log('[losses] Chamando setupNumericSpinners inicial');
    setupNumericSpinners();
    
    // Setup Calculate Buttons
    console.log('[losses] Configurando botões de cálculo');
    setupCalculateButtons();    // Start observing the element that contains the tab content.
    // The `losses-tabs` ID is from your `layouts/losses.py` (dbc.Tabs component).
    // This component's children (the `dbc.Tab`s) will have their content updated dynamically.
    const tabContentContainer = document.getElementById('lossesTabContent');
    if (tabContentContainer) {
        console.log('[losses] Observando #lossesTabContent para mutações');
        observer.observe(tabContentContainer, {
            childList: true, // Observe direct children (the tab contents) additions/removals
            subtree: true    // Observe changes within the entire subtree of the tab content
        });
    } else {
        console.warn("[losses] Main tab content container for MutationObserver (ID: 'lossesTabContent') not found. Observing 'document.body' as a fallback.");
        // Fallback: observe the entire document body (less efficient but ensures coverage)
        observer.observe(document.body, { childList: true, subtree: true });
    }
    console.log("[losses] losses.js: Initializing interactivity for Losses module. CONCLUÍDO.");
}

// SPA routing: executa quando o módulo losses é carregado
document.addEventListener('moduleContentLoaded', (event) => {
    if (event.detail && event.detail.moduleName === 'losses') {
        console.log('[losses] SPA routing init');
        initLosses();
    }
});

// Fallback para carregamento direto da página (se não for SPA)
document.addEventListener('DOMContentLoaded', () => {
    // Verifica se o elemento principal do módulo está presente para evitar execução em outras páginas
    if (document.getElementById('lossesTabContent')) {
        console.log('[losses] DOMContentLoaded init (fallback)');
        initLosses();
    }
});

// --- Calculate Button Setup ---
// Implementa os botões "Calcular" para perdas em vazio e perdas em carga
function setupCalculateButtons() {
    console.log('[losses] Configurando botões de cálculo');
    
    // Botão Calcular Perdas em Vazio
    const calcularVazioBtn = document.getElementById('calcular-perdas-vazio');
    if (calcularVazioBtn) {
        calcularVazioBtn.removeEventListener('click', handleCalculateNoLoad);
        calcularVazioBtn.addEventListener('click', handleCalculateNoLoad);
        console.log('[losses] Botão calcular-perdas-vazio configurado');
    }
    
    // Botão Calcular Perdas em Carga
    const calcularCargaBtn = document.getElementById('calcular-perdas-carga');
    if (calcularCargaBtn) {
        calcularCargaBtn.removeEventListener('click', handleCalculateLoad);
        calcularCargaBtn.addEventListener('click', handleCalculateLoad);
        console.log('[losses] Botão calcular-perdas-carga configurado');
    }
}

// Função para lidar com o cálculo de perdas em vazio
async function handleCalculateNoLoad() {
    console.log('[losses] Calculando perdas em vazio...');
    
    try {
        // Exibir indicador de carregamento
        showCalculationLoading('perdas-vazio');
        
        // Coletar dados básicos do transformador
        const basicData = await getBasicTransformerData();
        if (!basicData) {
            throw new Error('Dados básicos do transformador não encontrados');
        }
        
        // Coletar dados do módulo de perdas em vazio
        const noLoadInputs = collectNoLoadInputs();            // Fazer requisição para a API
            const response = await fetch('/api/transformer/modules/losses/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    basicData: basicData,
                    moduleData: noLoadInputs
                })
            });
        
        if (!response.ok) {
            throw new Error(`Erro na API: ${response.status} - ${response.statusText}`);
        }
        
        const results = await response.json();
        
        // Exibir resultados
        displayNoLoadResults(results);
        
        console.log('[losses] Cálculo de perdas em vazio concluído:', results);
        
    } catch (error) {
        console.error('[losses] Erro ao calcular perdas em vazio:', error);
        showCalculationError('perdas-vazio', error.message);
    }
}

// Função para lidar com o cálculo de perdas em carga
async function handleCalculateLoad() {
    console.log('[losses] Calculando perdas em carga...');
    
    try {
        // Exibir indicador de carregamento
        showCalculationLoading('perdas-carga');
        
        // Coletar dados básicos do transformador
        const basicData = await getBasicTransformerData();
        if (!basicData) {
            throw new Error('Dados básicos do transformador não encontrados');
        }
        
        // Coletar dados do módulo de perdas em carga
        const loadInputs = collectLoadInputs();
        
        // Verificar se os campos obrigatórios estão preenchidos
        const requiredFields = ['perdas_carga_kw_U_min', 'perdas_carga_kw_U_nom', 'perdas_carga_kw_U_max'];
        const missingFields = requiredFields.filter(field => !loadInputs[field]);
        
        if (missingFields.length > 0) {
            throw new Error(`Campos obrigatórios não preenchidos: ${missingFields.join(', ')}`);
        }            // Fazer requisição para a API
            const response = await fetch('/api/transformer/modules/losses/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    basicData: basicData,
                    moduleData: { ...collectNoLoadInputs(), ...loadInputs }
                })
            });
        
        if (!response.ok) {
            throw new Error(`Erro na API: ${response.status} - ${response.statusText}`);
        }
        
        const results = await response.json();
        
        // Exibir resultados
        displayLoadResults(results);
        
        console.log('[losses] Cálculo de perdas em carga concluído:', results);
        
    } catch (error) {
        console.error('[losses] Erro ao calcular perdas em carga:', error);
        showCalculationError('perdas-carga', error.message);
    }
}

// Função para coletar dados básicos do transformador
async function getBasicTransformerData() {
    try {
        if (!window.apiDataSystem) {
            throw new Error('Sistema de persistência não disponível');
        }
        
        const store = window.apiDataSystem.getStore('transformerInputs');
        const data = await store.getData();
        
        if (!data || !data.formData) {
            throw new Error('Dados do transformador não encontrados');
        }
        
        return data.formData;
    } catch (error) {
        console.error('[losses] Erro ao obter dados básicos:', error);
        return null;
    }
}

// Função para coletar dados de entrada de perdas em vazio
function collectNoLoadInputs() {
    return {
        perdas_vazio_kw: document.getElementById('perdas-vazio-kw')?.value || '',
        peso_projeto_Ton: document.getElementById('peso-projeto-Ton')?.value || '',
        corrente_excitacao: document.getElementById('corrente-excitacao')?.value || '',
        inducao_nucleo: document.getElementById('inducao-nucleo')?.value || '',
        corrente_excitacao_1_1: document.getElementById('corrente-excitacao-1-1')?.value || '',
        corrente_excitacao_1_2: document.getElementById('corrente-excitacao-1-2')?.value || '',
        tipo_aco: document.getElementById('tipo-aco')?.value || 'M4'
    };
}

// Função para coletar dados de entrada de perdas em carga
function collectLoadInputs() {
    return {
        temperatura_referencia: document.getElementById('temperatura-referencia')?.value || '75',
        perdas_carga_kw_U_min: document.getElementById('perdas-carga-kw_U_min')?.value || '',
        perdas_carga_kw_U_nom: document.getElementById('perdas-carga-kw_U_nom')?.value || '',
        perdas_carga_kw_U_max: document.getElementById('perdas-carga-kw_U_max')?.value || ''
    };
}

// Função para exibir indicador de carregamento
function showCalculationLoading(calculationType) {
    const loadingHtml = `
        <div class="d-flex align-items-center justify-content-center">
            <div class="spinner-border spinner-border-sm text-primary me-2" role="status">
                <span class="visually-hidden">Calculando...</span>
            </div>
            <span class="text-primary">Calculando...</span>
        </div>
    `;
    
    if (calculationType === 'perdas-vazio') {
        const containers = [
            'parametros-gerais-card-body',
            'dut-voltage-level-results-body',
            'sut-analysis-results-area'
        ];
        containers.forEach(id => {
            const element = document.getElementById(id);
            if (element) element.innerHTML = loadingHtml;
        });
    } else if (calculationType === 'perdas-carga') {
        const containers = [
            'condicoes-nominais-card-body',
            'resultados-perdas-carga'
        ];
        containers.forEach(id => {
            const element = document.getElementById(id);
            if (element) element.innerHTML = loadingHtml;
        });
    }
}

// Função para exibir erro de cálculo
function showCalculationError(calculationType, errorMessage) {
    const errorHtml = `
        <div class="alert alert-danger mb-0" role="alert">
            <i class="fas fa-exclamation-triangle me-2"></i>
            <small>Erro: ${errorMessage}</small>
        </div>
    `;
    
    if (calculationType === 'perdas-vazio') {
        const containers = [
            'parametros-gerais-card-body',
            'dut-voltage-level-results-body',
            'sut-analysis-results-area'
        ];
        containers.forEach(id => {
            const element = document.getElementById(id);
            if (element) element.innerHTML = errorHtml;
        });
    } else if (calculationType === 'perdas-carga') {
        const containers = [
            'condicoes-nominais-card-body',
            'resultados-perdas-carga'
        ];
        containers.forEach(id => {
            const element = document.getElementById(id);
            if (element) element.innerHTML = errorHtml;
        });
    }
}

// Função para exibir resultados de perdas em vazio
function displayNoLoadResults(results) {
    console.log('[losses] Exibindo resultados de perdas em vazio:', results);
    
    const noLoadData = results.perdas_vazio || {};
    const analysisData = results.analise_sut_eps_vazio || {};
    
    // Exibir parâmetros gerais
    displayGeneralParameters(noLoadData);
    
    // Exibir resultados por nível de tensão
    displayVoltageResults(noLoadData);
    
    // Exibir análise SUT/EPS
    displaySUTAnalysis(analysisData);
}

// Função para exibir resultados de perdas em carga
function displayLoadResults(results) {
    console.log('[losses] Exibindo resultados de perdas em carga:', results);
    
    const loadData = results.perdas_carga || {};
    const capBankData = results.banco_capacitores || {};
    const sutEpsData = results.analise_sut_eps_carga || {};
    
    // Exibir condições nominais
    displayNominalConditions(loadData);
    
    // Exibir resultados detalhados
    displayDetailedLoadResults(loadData, capBankData, sutEpsData);
}

// Função para exibir parâmetros gerais
function displayGeneralParameters(data) {
    const container = document.getElementById('parametros-gerais-card-body');
    if (!container) return;
    
    const calcData = data.calculos_vazio || {};
    
    const html = `
        <div class="row g-2">
            <div class="col-12">
                <table class="table table-sm table-striped">
                    <tbody>
                        <tr>
                            <td><strong>Peso Núcleo Calc:</strong></td>
                            <td>${calcData.peso_nucleo_calc_ton || 'N/A'} Ton</td>
                        </tr>
                        <tr>
                            <td><strong>Potência Mag. Aço:</strong></td>
                            <td>${calcData.potencia_mag_aco_kvar || 'N/A'} kVAr</td>
                        </tr>
                        <tr>
                            <td><strong>Corrente Excitação:</strong></td>
                            <td>${calcData.corrente_excitacao_calc_a || 'N/A'} A</td>
                        </tr>
                        <tr>
                            <td><strong>Corrente Excitação %:</strong></td>
                            <td>${calcData.corrente_excitacao_percentual_calc || 'N/A'} %</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// Função para exibir resultados por nível de tensão
function displayVoltageResults(data) {
    const container = document.getElementById('dut-voltage-level-results-body');
    if (!container) return;
    
    const calcData = data.calculos_vazio || {};
    
    const html = `
        <div class="row g-2">
            <div class="col-12">
                <table class="table table-sm table-striped">
                    <tbody>
                        <tr>
                            <td><strong>Tensão Teste 1.1pu:</strong></td>
                            <td>${calcData.tensao_teste_1_1_kv || 'N/A'} kV</td>
                        </tr>
                        <tr>
                            <td><strong>Tensão Teste 1.2pu:</strong></td>
                            <td>${calcData.tensao_teste_1_2_kv || 'N/A'} kV</td>
                        </tr>
                        <tr>
                            <td><strong>Corrente 1.1pu:</strong></td>
                            <td>${calcData.corrente_excitacao_1_1_calc_a || 'N/A'} A</td>
                        </tr>
                        <tr>
                            <td><strong>Corrente 1.2pu:</strong></td>
                            <td>${calcData.corrente_excitacao_1_2_calc_a || 'N/A'} A</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// Função para exibir análise SUT/EPS
function displaySUTAnalysis(data) {
    const container = document.getElementById('sut-analysis-results-area');
    if (!container) return;
    
    const html = `
        <div class="row g-2">
            <div class="col-12">
                <table class="table table-sm table-striped">
                    <tbody>
                        <tr>
                            <td><strong>Status:</strong></td>
                            <td><span class="badge bg-info">Análise SUT/EPS implementada</span></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// Função para exibir condições nominais
function displayNominalConditions(data) {
    const container = document.getElementById('condicoes-nominais-card-body');
    if (!container) return;
    
    const html = `
        <div class="row g-2">
            <div class="col-12">
                <table class="table table-sm table-striped">
                    <tbody>
                        <tr>
                            <td><strong>Perdas sem Vazio (Nom):</strong></td>
                            <td>${data.perdas_carga_sem_vazio_nom || 'N/A'} kW</td>
                        </tr>
                        <tr>
                            <td><strong>Tensão CC (Nom):</strong></td>
                            <td>${data.vcc_nom || 'N/A'} kV</td>
                        </tr>
                        <tr>
                            <td><strong>Corrente Teste (Nom):</strong></td>
                            <td>${data.corrente_teste_nom || 'N/A'} A</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// Função para exibir resultados detalhados de perdas em carga
function displayDetailedLoadResults(loadData, capBankData, sutEpsData) {
    const container = document.getElementById('resultados-perdas-carga');
    if (!container) return;
    
    const html = `
        <div class="card">
            <div class="card-header">
                <h6 class="text-center m-0">RESULTADOS DETALHADOS</h6>
            </div>
            <div class="card-body">
                <div class="row g-2">
                    <div class="col-md-6">
                        <h6 class="text-primary">Perdas em Carga</h6>
                        <table class="table table-sm table-striped">
                            <tbody>
                                <tr>
                                    <td>Perdas Tap-:</td>
                                    <td>${loadData.perdas_carga_sem_vazio_min || 'N/A'} kW</td>
                                </tr>
                                <tr>
                                    <td>Perdas Tap Nom:</td>
                                    <td>${loadData.perdas_carga_sem_vazio_nom || 'N/A'} kW</td>
                                </tr>
                                <tr>
                                    <td>Perdas Tap+:</td>
                                    <td>${loadData.perdas_carga_sem_vazio_max || 'N/A'} kW</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <div class="col-md-6">
                        <h6 class="text-success">Banco de Capacitores</h6>
                        <table class="table table-sm table-striped">
                            <tbody>
                                <tr>
                                    <td>Potência Requerida:</td>
                                    <td>${capBankData.potencia_banco_capacitores || 'N/A'} MVAr</td>
                                </tr>
                                <tr>
                                    <td>Status:</td>
                                    <td><span class="badge bg-success">Calculado</span></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
  }