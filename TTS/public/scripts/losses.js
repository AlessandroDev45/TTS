// public/scripts/losses.js

import { loadAndPopulateTransformerInfo } from './common_module.js';
import { collectFormData, fillFormWithData, setupApiFormPersistence } from './api_persistence.js'; // Assuming setupApiFormPersistence is available

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
            setTimeout(() => { // Timeout after 10 seconds
                clearInterval(checkInterval);
                console.warn('[losses] Timeout waiting for apiDataSystem.');
                resolve(); // Resolve anyway to avoid blocking
            }, 10000);
        }
    });
}

// Função para carregar dados do store 'losses' e preencher o formulário de perdas
async function loadLossesDataAndPopulateForm() {
    try {
        console.log('[losses] Carregando dados do store "losses" e preenchendo formulário...');
        await waitForApiSystem();

        const store = window.apiDataSystem.getStore('losses');
        const data = await store.getData();

        if (data && data.formData) {
            const formElement = document.getElementById('lossesTabContent'); // Main container for both tabs
            if (formElement) {
                fillFormWithData(formElement, data.formData);
                console.log('[losses] Formulário de perdas preenchido com dados do store:', data.formData);

                // After filling, if results are also in store, display them
                if (data.resultsNoLoad) {
                    displayNoLoadResults(data.resultsNoLoad);
                }
                if (data.resultsLoad) {
                    displayLoadResults(data.resultsLoad.condicoes_nominais, data.resultsLoad.cenarios_detalhados, data.resultsLoad.sugestao_geral_banco);
                }

            } else {
                console.warn('[losses] Formulário "lossesTabContent" não encontrado para preenchimento.');
            }
        } else {
            console.log('[losses] Nenhum dado de perdas encontrado no store para preenchimento inicial.');
        }
    } catch (error) {
        console.error('[losses] Erro ao carregar e preencher dados de perdas:', error);
    }
}


// Função de inicialização do módulo de Perdas
async function initLosses() {
    console.log("[losses] losses.js: Initializing interactivity for Losses module.");

    const transformerInfoPlaceholderId = 'transformer-info-losses-page';
    await loadAndPopulateTransformerInfo(transformerInfoPlaceholderId);

    // Setup persistence for the entire lossesTabContent (covers both forms)
    // The store key 'losses' will store formData for both no-load and load losses inputs.
    const lossesFormContainer = document.getElementById('lossesTabContent');
    if (lossesFormContainer && window.setupApiFormPersistence) {
        try {
            // Using a single store 'losses' for all inputs in the losses module
            await setupApiFormPersistence(lossesFormContainer, 'losses');
            console.log('[losses] Persistência configurada para o container de abas de perdas.');
        } catch (error) {
            console.error('[losses] Erro ao configurar persistência para perdas:', error);
        }
    } else {
        console.warn('[losses] Container de abas "lossesTabContent" ou setupApiFormPersistence não encontrado.');
    }
    
    // Load stored data and populate forms and results if available
    await loadLossesDataAndPopulateForm();


    // Event listeners for tab changes
    const tabButtons = document.querySelectorAll('#lossesTab .nav-link');
    tabButtons.forEach(tabButton => {
        tabButton.addEventListener('shown.bs.tab', async (event) => {
            console.log(`[losses] Aba "${event.target.textContent.trim()}" mostrada.`);
            // Data is already loaded by persistence, but can re-trigger display if needed
            // For now, assume persistence handles initial population.
        });
    });

    document.addEventListener('transformerDataUpdated', async (event) => {
        console.log('[losses] Evento transformerDataUpdated recebido:', event.detail);
        await updateDependentFieldsFromTransformerData();
    });

    setupCalculateButtons();
    // Initial setup for spinners (if any defined later)
    // setupNumericSpinners(); 

    console.log("[losses] losses.js: Initialization complete.");
}


// --- Calculate Button Setup ---
function setupCalculateButtons() {
    console.log('[losses] Configurando botões de cálculo');
    
    const calcularVazioBtn = document.getElementById('calcular-perdas-vazio');
    if (calcularVazioBtn) {
        calcularVazioBtn.addEventListener('click', handleCalculateNoLoad);
        console.log('[losses] Botão calcular-perdas-vazio configurado');
    }
    
    const calcularCargaBtn = document.getElementById('calcular-perdas-carga');
    if (calcularCargaBtn) {
        calcularCargaBtn.addEventListener('click', handleCalculateLoad);
        console.log('[losses] Botão calcular-perdas-carga configurado');
    }
}

// --- Data Collection and API Calls ---
async function getBasicTransformerData() {
    try {
        await waitForApiSystem();
        if (!window.apiDataSystem) throw new Error('Sistema de persistência não disponível');
        
        const store = window.apiDataSystem.getStore('transformerInputs');
        const data = await store.getData();
        
        if (!data || !data.formData) throw new Error('Dados do transformador não encontrados no store transformerInputs');
        
        console.log('[losses] Dados básicos carregados para cálculos:', data.formData);
        return data.formData;
    } catch (error) {
        console.error('[losses] Erro ao obter dados básicos:', error);
        return null;
    }
}

function collectNoLoadInputs() {
    return {
        perdas_vazio_ui: parseFloat(document.getElementById('perdas-vazio-kw')?.value) || 0,
        peso_nucleo_ui: parseFloat(document.getElementById('peso-projeto-Ton')?.value) || 0,
        corrente_excitacao_ui: parseFloat(document.getElementById('corrente-excitacao')?.value) || 0,
        inducao_ui: parseFloat(document.getElementById('inducao-nucleo')?.value) || 0,
        corrente_exc_1_1_ui: parseFloat(document.getElementById('corrente-excitacao-1-1')?.value) || null,
        corrente_exc_1_2_ui: parseFloat(document.getElementById('corrente-excitacao-1-2')?.value) || null,
        steel_type: document.getElementById('tipo-aco')?.value || 'M4'
        // frequencia, tensao_bt_kv, corrente_nominal_bt, tipo_transformador, potencia_mva will come from basicData
    };
}

function collectLoadInputs() {
    return {
        temperatura_referencia: parseInt(document.getElementById('temperatura-referencia')?.value) || 75,
        perdas_carga_kw_u_min: parseFloat(document.getElementById('perdas-carga-kw_U_min')?.value) || 0,
        perdas_carga_kw_u_nom: parseFloat(document.getElementById('perdas-carga-kw_U_nom')?.value) || 0,
        perdas_carga_kw_u_max: parseFloat(document.getElementById('perdas-carga-kw_U_max')?.value) || 0
        // potencia_mva, impedancia, etc., will come from basicData
    };
}

async function handleCalculateNoLoad() {
    console.log('[losses] Calculando perdas em vazio...');
    showCalculationLoading('perdas-vazio');
    
    try {
        const basicData = await getBasicTransformerData();
        if (!basicData) throw new Error('Dados básicos do transformador não encontrados para cálculo de perdas em vazio.');
        
        const noLoadInputs = collectNoLoadInputs();

        const payload = {
            operation: 'no_load_losses',
            data: { // Data expected by NoLoadLossesInput Pydantic model
                ...noLoadInputs,
                frequencia: basicData.frequencia,
                tensao_bt_kv: basicData.tensao_bt ? basicData.tensao_bt / 1000 : 0, // Convert V to kV
                corrente_nominal_bt: basicData.corrente_nominal_bt,
                tipo_transformador: basicData.tipo_transformador,
                potencia_mva: basicData.potencia_mva
            }
        };
        
        const response = await fetch('/api/transformer/modules/losses/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`Erro na API (${response.status}): ${errorData.detail || response.statusText}`);
        }
        
        const results = await response.json();
        console.log('[losses] Resultados de perdas em vazio:', results);
        displayNoLoadResults(results.results); // Assuming results are in results.results from the route

        // Persist results in the 'losses' store
        await waitForApiSystem();
        const store = window.apiDataSystem.getStore('losses');
        const currentStoreData = await store.getData() || {};
        await store.updateData({ resultsNoLoad: results.results, formData: currentStoreData.formData || collectFormData(document.getElementById('lossesTabContent')) });


    } catch (error) {
        console.error('[losses] Erro ao calcular perdas em vazio:', error);
        showCalculationError('perdas-vazio', error.message);
    }
}

async function handleCalculateLoad() {
    console.log('[losses] Calculando perdas em carga...');
    showCalculationLoading('perdas-carga');
    
    try {
        const basicData = await getBasicTransformerData();
        if (!basicData) throw new Error('Dados básicos do transformador não encontrados para cálculo de perdas em carga.');
        
        // Ensure perdas_vazio_kw_calculada is available from no-load inputs (not results)
        await waitForApiSystem();
        const lossesStore = window.apiDataSystem.getStore('losses');
        const storedLossesData = await lossesStore.getData();

        // Try to get from stored form data first (the input value)
        let perdasVazioCalculada = storedLossesData?.formData?.['perdas-vazio-kw'];

        // If not found in form data, try basic transformer data
        if (perdasVazioCalculada === undefined || perdasVazioCalculada === null || perdasVazioCalculada === '') {
            perdasVazioCalculada = basicData.perdas_vazio_kw;
        }

        // Convert to number if it's a string
        if (typeof perdasVazioCalculada === 'string') {
            perdasVazioCalculada = parseFloat(perdasVazioCalculada);
        }

        if (perdasVazioCalculada === undefined || perdasVazioCalculada === null || isNaN(perdasVazioCalculada)) {
            throw new Error('Perdas em vazio não encontradas. Preencha o campo "Perdas em Vazio (kW)" ou calcule as perdas em vazio primeiro.');
        }


        const loadInputs = collectLoadInputs();
         const requiredFields = ['perdas_carga_kw_u_min', 'perdas_carga_kw_u_nom', 'perdas_carga_kw_u_max'];
        const missingFields = requiredFields.filter(field => loadInputs[field] === 0 || loadInputs[field] === null || loadInputs[field] === undefined );

        if (missingFields.length > 0) {
            throw new Error(`Campos obrigatórios de perdas em carga não preenchidos ou zerados: ${missingFields.join(', ')}`);
        }


        const payload = {
            operation: 'load_losses',
            data: { // Data expected by LoadLossesInput Pydantic model
                ...loadInputs,
                potencia_mva: basicData.potencia_mva,
                impedancia: basicData.impedancia,
                tensao_at_kv: basicData.tensao_at ? basicData.tensao_at / 1000 : 0, // Convert V to kV
                tensao_at_tap_maior_kv: basicData.tensao_at_tap_maior ? basicData.tensao_at_tap_maior / 1000 : 0,
                tensao_at_tap_menor_kv: basicData.tensao_at_tap_menor ? basicData.tensao_at_tap_menor / 1000 : 0,
                impedancia_tap_maior: basicData.impedancia_tap_maior,
                impedancia_tap_menor: basicData.impedancia_tap_menor,
                corrente_nominal_at_a: basicData.corrente_nominal_at,
                corrente_nominal_at_tap_maior_a: basicData.corrente_nominal_at_tap_maior,
                corrente_nominal_at_tap_menor_a: basicData.corrente_nominal_at_tap_menor,
                tipo_transformador: basicData.tipo_transformador,
                perdas_vazio_kw_calculada: perdasVazioCalculada
            }
        };
        
        const response = await fetch('/api/transformer/modules/losses/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`Erro na API (${response.status}): ${errorData.detail || response.statusText}`);
        }
        
        const results = await response.json();
        console.log('[losses] Resultados de perdas em carga:', results);
        // The service returns a structure like: {"condicoes_nominais": {}, "cenarios_detalhados_por_tap": [], "sugestao_geral_banco": {}}
        // Corrigir nome do campo: cenarios_detalhados_por_tap em vez de cenarios_detalhados
        displayLoadResults(results.results.condicoes_nominais, results.results.cenarios_detalhados_por_tap, results.results.sugestao_geral_banco);

        // Persist results in the 'losses' store
        await waitForApiSystem();
        const store = window.apiDataSystem.getStore('losses');
        const currentStoreData = await store.getData() || {};
        await store.updateData({ resultsLoad: results.results, formData: currentStoreData.formData || collectFormData(document.getElementById('lossesTabContent')) });

    } catch (error) {
        console.error('[losses] Erro ao calcular perdas em carga:', error);
        showCalculationError('perdas-carga', error.message);
    }
}


// --- DOM Manipulation for Displaying Results ---
function showCalculationLoading(calculationType) {
    const loadingHtml = `
        <div class="d-flex align-items-center justify-content-center p-3">
            <div class="spinner-border spinner-border-sm text-primary me-2" role="status">
                <span class="visually-hidden">Calculando...</span>
            </div>
            <span class="text-primary small">Calculando...</span>
        </div>`;
    
    const areas = calculationType === 'perdas-vazio' 
        ? ['parametros-gerais-card-body', 'dut-voltage-level-results-body', 'sut-analysis-results-area']
        : ['condicoes-nominais-card-body', 'resultados-perdas-carga'];
    
    areas.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = loadingHtml;
    });
}

function showCalculationError(calculationType, errorMessage) {
    const errorHtml = `
        <div class="alert alert-danger alert-sm mb-0 small p-2" role="alert">
            <i class="fas fa-exclamation-triangle me-1"></i> Erro: ${errorMessage}
        </div>`;
        
    const areas = calculationType === 'perdas-vazio' 
        ? ['parametros-gerais-card-body', 'dut-voltage-level-results-body', 'sut-analysis-results-area']
        : ['condicoes-nominais-card-body', 'resultados-perdas-carga'];

    areas.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = errorHtml;
    });
}

function displayNoLoadResults(results) {
    console.log('[losses] Exibindo resultados de perdas em vazio:', results);
    const { calculos_baseados_aco, calculos_vazio, analise_sut_eps_vazio } = results;

    // Parâmetros Gerais e de Material
    const geraisContainer = document.getElementById('parametros-gerais-card-body');
    if (geraisContainer) {
        geraisContainer.innerHTML = `
            <table class="table table-sm table-striped table-hover small">
                <tbody>
                    <tr><td>Peso Núcleo Calc. (Ton):</td><td class="text-end fw-bold">${calculos_baseados_aco?.peso_nucleo_calc_ton ?? 'N/A'}</td></tr>
                    <tr><td>Potência Mag. Aço (kVAr):</td><td class="text-end fw-bold">${calculos_baseados_aco?.potencia_mag_aco_kvar ?? 'N/A'}</td></tr>
                    <tr><td>Corrente Exc. Calc. (A):</td><td class="text-end fw-bold">${calculos_baseados_aco?.corrente_excitacao_calc_a ?? 'N/A'}</td></tr>
                    <tr><td>Corrente Exc. Calc. (%):</td><td class="text-end fw-bold">${calculos_baseados_aco?.corrente_excitacao_percentual_calc ?? 'N/A'}</td></tr>
                    <tr><td>Fator Perdas Projeto (W/kg):</td><td class="text-end fw-bold">${calculos_vazio?.fator_perdas_projeto_w_kg ?? 'N/A'}</td></tr>
                    <tr><td>Fator Pot.Mag. Projeto (VAR/kg):</td><td class="text-end fw-bold">${calculos_vazio?.fator_pot_mag_projeto_var_kg ?? 'N/A'}</td></tr>
                </tbody>
            </table>`;
    }

    // Resultados por Nível de Tensão (DUT)
    const dutContainer = document.getElementById('dut-voltage-level-results-body');
    if (dutContainer) {
        dutContainer.innerHTML = `
            <table class="table table-sm table-striped table-hover small">
                <tbody>
                    <tr><td>Tensão Teste 1.1pu (kV):</td><td class="text-end fw-bold">${calculos_vazio?.tensao_teste_1_1_kv ?? 'N/A'}</td></tr>
                    <tr><td>Corrente Exc. 1.1pu (A):</td><td class="text-end fw-bold">${calculos_vazio?.corrente_excitacao_1_1_calc_a ?? 'N/A'}</td></tr>
                    <tr><td>Tensão Teste 1.2pu (kV):</td><td class="text-end fw-bold">${calculos_vazio?.tensao_teste_1_2_kv ?? 'N/A'}</td></tr>
                    <tr><td>Corrente Exc. 1.2pu (A):</td><td class="text-end fw-bold">${calculos_vazio?.corrente_excitacao_1_2_calc_a ?? 'N/A'}</td></tr>
                </tbody>
            </table>`;
    }

    // Análise TAPS SUT / Corrente EPS
    const sutContainer = document.getElementById('sut-analysis-results-area');
    if (sutContainer && analise_sut_eps_vazio) {
        let sutHtml = '<div class="row g-2">';
        for (const puLevel of ['1.0pu', '1.1pu', '1.2pu']) {
            const analysis = analise_sut_eps_vazio[puLevel];
            sutHtml += `
                <div class="col-md-4">
                    <div class="card card-sm">
                        <div class="card-header card-header-sm text-center small fw-bold">${puLevel.toUpperCase()}</div>
                        <div class="card-body p-1">`;
            if (analysis && analysis.status === "OK" && analysis.taps_info.length > 0) {
                sutHtml += `<table class="table table-sm table-striped table-hover small mb-0">
                                <thead><tr><th>Tap SUT (kV)</th><th class="text-end">I_EPS (A)</th><th class="text-end">% Limite</th></tr></thead>
                                <tbody>`;
                analysis.taps_info.forEach(tap => {
                    const dòng_style = tap.percent_limite_eps > 100 ? 'table-danger' : (tap.percent_limite_eps > 85 ? 'table-warning' : '');
                    sutHtml += `<tr class="${dòng_style}">
                                    <td>${tap.sut_tap_kv}</td>
                                    <td class="text-end">${tap.corrente_eps_a}</td>
                                    <td class="text-end">${tap.percent_limite_eps}%</td>
                                </tr>`;
                });
                sutHtml += `</tbody></table>`;
            } else {
                sutHtml += `<p class="text-muted text-center small m-1">${analysis?.status || 'N/A'}</p>`;
            }
            sutHtml += `</div></div></div>`;
        }
        sutHtml += '</div>';
        sutContainer.innerHTML = sutHtml;
    }
}

function displayLoadResults(condicoesNominais, cenariosDetalhados, sugestaoGeralBanco) {
    console.log('[losses] Exibindo resultados de perdas em carga:', { condicoesNominais, cenariosDetalhados, sugestaoGeralBanco });

    // Condições Nominais - Implementação mais robusta baseada nos arquivos de referência
    const nominaisContainer = document.getElementById('condicoes-nominais-card-body');
    if (nominaisContainer && condicoesNominais) {
        // Formatação com 2 casas decimais para valores numéricos
        const formatValue = (value, decimals = 2) => {
            if (value === null || value === undefined || value === '') return 'N/A';
            if (typeof value === 'number') return value.toFixed(decimals);
            return value;
        };

        nominaisContainer.innerHTML = `
            <table class="table table-sm table-striped table-hover small">
                <tbody>
                    <tr><td>Temperatura Referência (°C):</td><td class="text-end fw-bold">${formatValue(condicoesNominais.temperatura_referencia, 0)}</td></tr>
                    <tr><td>Perdas Tap Nominal (kW):</td><td class="text-end fw-bold">${formatValue(condicoesNominais.perdas_tap_nominal)}</td></tr>
                    <tr><td>Perdas por Unidade (%):</td><td class="text-end fw-bold">${formatValue(condicoesNominais.perdas_por_unidade, 4)}</td></tr>
                    <tr><td>Impedância (%):</td><td class="text-end fw-bold">${formatValue(condicoesNominais.impedancia_entrada, 4)}</td></tr>
                    <tr><td>Resistência (%):</td><td class="text-end fw-bold">${formatValue(condicoesNominais.resistencia_percentual, 4)}</td></tr>
                    <tr><td>Reatância (%):</td><td class="text-end fw-bold">${formatValue(condicoesNominais.reatancia_percentual, 4)}</td></tr>
                    <tr><td>Fator Potência CC:</td><td class="text-end fw-bold">${formatValue(condicoesNominais.fator_potencia_curto_circuito, 4)}</td></tr>
                    <tr><td>Fator Correção Temp.:</td><td class="text-end fw-bold">${formatValue(condicoesNominais.fator_correcao_temperatura, 4)}</td></tr>
                    <tr><td>I²R Perdas (kW):</td><td class="text-end fw-bold">${formatValue(condicoesNominais.i2r_perdas)}</td></tr>
                    <tr><td>Perdas Adicionais (kW):</td><td class="text-end fw-bold">${formatValue(condicoesNominais.perdas_adicionais)}</td></tr>
                </tbody>
            </table>`;
    }

    // Resultados Detalhados e Análise SUT/EPS - Implementação mais robusta
    const detalhadosContainer = document.getElementById('resultados-perdas-carga');
    if (detalhadosContainer) {
        let htmlContent = '';

        // Verificar se há dados para exibir
        if (!cenariosDetalhados || !Array.isArray(cenariosDetalhados) || cenariosDetalhados.length === 0) {
            htmlContent = `
                <div class="alert alert-warning text-center">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Nenhum cenário detalhado encontrado. Verifique se os dados básicos do transformador estão preenchidos.
                </div>`;
            detalhadosContainer.innerHTML = htmlContent;
            return;
        }

        // Função auxiliar para formatação
        const formatValue = (value, decimals = 2) => {
            if (value === null || value === undefined || value === '') return 'N/A';
            if (typeof value === 'number') return value.toFixed(decimals);
            return value;
        };

        // Sugestão Geral do Banco de Capacitores
        if (sugestaoGeralBanco) {
            htmlContent += `
            <div class="card card-sm mb-3">
                <div class="card-header card-header-sm text-center fw-bold">Sugestão Geral do Banco de Capacitores</div>
                <div class="card-body p-2 small">
                    <div class="row">
                        <div class="col"><strong>Config. CS:</strong> ${sugestaoGeralBanco.cs_config || 'N/A'}</div>
                        <div class="col"><strong>Config. Q:</strong> ${sugestaoGeralBanco.q_config || 'N/A'}</div>
                        <div class="col text-end"><strong>Q Prov. (MVAr):</strong> ${formatValue(sugestaoGeralBanco.q_provided_mvar, 3)}</div>
                    </div>
                    <div class="row">
                        <div class="col"><i>Baseado em Vmax: ${formatValue(sugestaoGeralBanco.max_v_overall_kv)} kV, Qmax_req: ${formatValue(sugestaoGeralBanco.max_q_overall_mvar_req, 3)} MVAr</i></div>
                    </div>
                </div>
            </div>`;
        }
        
        // Iterar sobre cada TAP (Nominal, Menor, Maior) - Implementação mais robusta
        cenariosDetalhados.forEach((tapData, tapIndex) => {
            console.log(`[losses] Processando Tap ${tapIndex}:`, tapData);

            const tapNome = tapData.nome_tap || `Tap ${tapIndex + 1}`;
            htmlContent += `<h5 class="mt-3 mb-2 small text-primary fw-bold">Resultados para ${tapNome}</h5>`;

            // Verificar se há cenários para este TAP
            const cenarios = tapData.cenarios_do_tap || [];
            if (cenarios.length === 0) {
                htmlContent += `<div class="alert alert-warning small">Nenhum cenário encontrado para ${tapNome}</div>`;
                return;
            }

            // Tabela de Testes e Banco de Capacitores
            htmlContent += `<div class="table-responsive mb-2">
                            <table class="table table-sm table-bordered table-hover small caption-top">
                            <caption class="small text-muted">Parâmetros de Teste e Banco de Capacitores (${tapNome})</caption>
                            <thead>
                                <tr class="table-light">
                                    <th>Cenário Teste</th>
                                    <th>Vtest (kV)</th>
                                    <th>Itest (A)</th>
                                    <th>P_ativa (kW)</th>
                                    <th>P_teste (MVA)</th>
                                    <th>Q_req (MVAr)</th>
                                    <th>Banco V_disp SF/CF (kV)</th>
                                    <th>Banco Q_prov SF/CF (MVAr)</th>
                                    <th>CS Conf SF/CF</th>
                                    <th>Q Conf SF/CF</th>
                                </tr>
                            </thead><tbody>`;

            cenarios.forEach((cenario, cenarioIndex) => {
                console.log(`[losses] Processando Cenário ${cenarioIndex}:`, cenario);

                // Corrigir nome do campo: test_params_cenario em vez de test_params
                const testParams = cenario.test_params_cenario || {};
                const capBankSf = cenario.cap_bank_sf || {};
                const capBankCf = cenario.cap_bank_cf || {};

                htmlContent += `<tr>
                    <td>${cenario.nome_cenario_teste || `Cenário ${cenarioIndex + 1}`}</td>
                    <td>${formatValue(testParams.tensao_kv)}</td>
                    <td>${formatValue(testParams.corrente_a)}</td>
                    <td>${formatValue(testParams.pativa_kw)}</td>
                    <td>${formatValue(testParams.pteste_mva, 3)}</td>
                    <td>${formatValue(testParams.pteste_mvar_req, 3)}</td>
                    <td>${formatValue(capBankSf.tensao_disp_kv) || '-'}/${formatValue(capBankCf.tensao_disp_kv) || '-'}</td>
                    <td>${formatValue(capBankSf.q_provided_mvar, 3) || '-'}/${formatValue(capBankCf.q_provided_mvar, 3) || '-'}</td>
                    <td>${capBankSf.cs_config || 'N/A'}/${capBankCf.cs_config || 'N/A'}</td>
                    <td>${capBankSf.q_config || 'N/A'}/${capBankCf.q_config || 'N/A'}</td>
                </tr>`;
            });
            htmlContent += `</tbody></table></div>`;

            // Tabela de Análise SUT/EPS - Implementação mais robusta
            htmlContent += `<div class="table-responsive">
                            <table class="table table-sm table-bordered table-hover small caption-top">
                            <caption class="small text-muted">Análise SUT/EPS Compensada (${tapNome})</caption>
                            <thead>
                                <tr class="table-light">
                                    <th>Cenário Teste</th>
                                    <th>Tap SUT (kV)</th>
                                    <th>I_EPS SF (A)</th>
                                    <th>% Limite SF</th>
                                    <th>I_EPS CF (A)</th>
                                    <th>% Limite CF</th>
                                </tr>
                            </thead><tbody>`;

            cenarios.forEach((cenario, cenarioIndex) => {
                const sutEpsAnalysis = cenario.sut_eps_analysis || [];
                const cenarioNome = cenario.nome_cenario_teste || `Cenário ${cenarioIndex + 1}`;

                if (sutEpsAnalysis.length > 0) {
                    sutEpsAnalysis.forEach((sut_tap, index) => {
                        const sf_style = (sut_tap.percent_limite_sf > 100) ? 'table-danger' :
                                        (sut_tap.percent_limite_sf > 85) ? 'table-warning' : '';
                        const cf_style = (sut_tap.percent_limite_cf > 100) ? 'table-danger' :
                                        (sut_tap.percent_limite_cf > 85) ? 'table-warning' : '';

                        htmlContent += `<tr>
                            ${index === 0 ? `<td rowspan="${sutEpsAnalysis.length}">${cenarioNome}</td>` : ''}
                            <td>${formatValue(sut_tap.sut_tap_kv)}</td>
                            <td class="${sf_style}">${formatValue(sut_tap.corrente_eps_sf_a)}</td>
                            <td class="${sf_style}">${formatValue(sut_tap.percent_limite_sf, 1)}%</td>
                            <td class="${cf_style}">${formatValue(sut_tap.corrente_eps_cf_a)}</td>
                            <td class="${cf_style}">${formatValue(sut_tap.percent_limite_cf, 1)}%</td>
                        </tr>`;
                    });
                } else {
                     htmlContent += `<tr><td>${cenarioNome}</td><td colspan="5" class="text-muted text-center">Sem dados SUT/EPS</td></tr>`;
                }
            });
            htmlContent += `</tbody></table></div>`;
        });

        detalhadosContainer.innerHTML = htmlContent;
        console.log('[losses] Resultados de perdas em carga exibidos com sucesso');
    } else {
        console.warn('[losses] Container de resultados detalhados não encontrado');
    }
}

// --- Helper for updating fields from transformer data ---
async function updateDependentFieldsFromTransformerData() {
    console.log('[losses] updateDependentFieldsFromTransformerData: Chamado.');
    // Currently, losses module inputs are mostly independent or specific to losses.
    // If there were fields in the losses form that should auto-populate from basic transformer data
    // (e.g., a read-only display of Potencia MVA), this is where that logic would go.
    // For now, just showing a notification that basic data is available for calculations.
    const basicData = await getBasicTransformerData();
    if (basicData) {
        const inheritedDataSummary = {
            potencia_mva: basicData.potencia_mva,
            frequencia: basicData.frequencia,
            impedancia: basicData.impedancia,
            tensao_bt_kv: basicData.tensao_bt ? basicData.tensao_bt / 1000 : 0,
            corrente_nominal_bt: basicData.corrente_nominal_bt
        };
        showInheritanceNotification(inheritedDataSummary, "Dados básicos do transformador carregados e disponíveis para os cálculos de perdas.");
    }
}

function showInheritanceNotification(summary, message) {
    const existingNotification = document.querySelector('.inheritance-notification-losses');
    if (existingNotification) existingNotification.remove();

    const count = Object.values(summary).filter(v => v !== null && v !== undefined && v !== '').length;
    if (count === 0) return;

    const notification = document.createElement('div');
    notification.className = 'alert alert-info alert-dismissible fade show inheritance-notification-losses small';
    notification.style.cssText = 'position: fixed; top: 70px; right: 20px; z-index: 1055; max-width: 380px; font-size: 0.8rem;';
    notification.innerHTML = `
        <i class="fas fa-info-circle me-2"></i>
        <strong>${message}</strong>
        <ul class="mb-0 ps-3 small">
            ${Object.entries(summary).map(([key, value]) => `<li>${key.replace(/_/g, ' ')}: ${value ?? 'N/A'}</li>`).join('')}
        </ul>
        <button type="button" class="btn-close btn-sm" data-bs-dismiss="alert" aria-label="Close"></button>`;
    document.body.appendChild(notification);
    setTimeout(() => { if (notification.parentNode) notification.remove(); }, 7000);
}


// --- SPA Routing and DOMContentLoaded ---
document.addEventListener('moduleContentLoaded', (event) => {
    if (event.detail && event.detail.moduleName === 'losses') {
        console.log('[losses] Módulo losses carregado via SPA routing.');
        initLosses();
    }
});

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('lossesTabContent')) { // Check if on losses page
        console.log('[losses] DOMContentLoaded (fallback para perdas).');
        initLosses();
    }
});