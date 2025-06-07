// public/scripts/losses.js

import { loadAndPopulateTransformerInfo } from './common_module.js';
import { collectFormData, fillFormWithData, setupApiFormPersistence } from './api_persistence.js';

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
            setTimeout(() => {
                clearInterval(checkInterval);
                console.warn('[losses] Timeout waiting for apiDataSystem.');
                resolve(); 
            }, 10000);
        }
    });
}

async function loadLossesDataAndPopulateForm() {
    try {
        console.log('[losses] Carregando dados do store "losses" e preenchendo formulário...');
        await waitForApiSystem();

        const store = window.apiDataSystem.getStore('losses');
        const data = await store.getData();

        if (data && data.formData) {
            const formElement = document.getElementById('lossesTabContent');
            if (formElement) {
                fillFormWithData(formElement, data.formData);
                console.log('[losses] Formulário de perdas preenchido com dados do store:', data.formData);

                if (data.resultsNoLoad) {
                    displayNoLoadResults(data.resultsNoLoad);
                }
                if (data.resultsLoad) {
                    displayLoadResults(data.resultsLoad.condicoes_nominais, data.resultsLoad.cenarios_detalhados_por_tap, data.resultsLoad.sugestao_geral_banco);
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

async function initLosses() {
    console.log("[losses] losses.js: Initializing interactivity for Losses module.");

    const transformerInfoPlaceholderId = 'transformer-info-losses-page';
    await loadAndPopulateTransformerInfo(transformerInfoPlaceholderId);

    const lossesFormContainer = document.getElementById('lossesTabContent');
    if (lossesFormContainer && window.setupApiFormPersistence) {
        try {
            await setupApiFormPersistence(lossesFormContainer, 'losses');
            console.log('[losses] Persistência configurada para o container de abas de perdas.');
        } catch (error) {
            console.error('[losses] Erro ao configurar persistência para perdas:', error);
        }
    } else {
        console.warn('[losses] Container de abas "lossesTabContent" ou setupApiFormPersistence não encontrado.');
    }
    
    await loadLossesDataAndPopulateForm();

    document.addEventListener('transformerDataUpdated', async (event) => {
        console.log('[losses] Evento transformerDataUpdated recebido:', event.detail);
        await updateDependentFieldsFromTransformerData();
    });

    setupCalculateButtons();
    console.log("[losses] losses.js: Initialization complete.");
}

function setupCalculateButtons() {
    console.log('[losses] Configurando botões de cálculo');
    const calcularVazioBtn = document.getElementById('calcular-perdas-vazio');
    if (calcularVazioBtn) {
        calcularVazioBtn.addEventListener('click', handleCalculateNoLoad);
    }
    const calcularCargaBtn = document.getElementById('calcular-perdas-carga');
    if (calcularCargaBtn) {
        calcularCargaBtn.addEventListener('click', handleCalculateLoad);
    }
}

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
    };
}

function collectLoadInputs() {
    return {
        temperatura_referencia: parseInt(document.getElementById('temperatura-referencia')?.value) || 75,
        perdas_carga_kw_u_min: parseFloat(document.getElementById('perdas-carga-kw_U_min')?.value) || 0,
        perdas_carga_kw_u_nom: parseFloat(document.getElementById('perdas-carga-kw_U_nom')?.value) || 0,
        perdas_carga_kw_u_max: parseFloat(document.getElementById('perdas-carga-kw_U_max')?.value) || 0
    };
}

async function handleCalculateNoLoad() {
    console.log('[losses] Calculando perdas em vazio...');
    showCalculationLoading('perdas-vazio');
    
    try {
        const basicData = await getBasicTransformerData();
        if (!basicData) throw new Error('Dados básicos do transformador não encontrados.');
        
        const noLoadInputs = collectNoLoadInputs();
        const requiredNoLoadFields = ['perdas_vazio_ui', 'peso_nucleo_ui', 'corrente_excitacao_ui', 'inducao_ui'];
        const missingNoLoad = requiredNoLoadFields.filter(field => !noLoadInputs[field] || noLoadInputs[field] <= 0);
        if (missingNoLoad.length > 0) {
            throw new Error(`Campos obrigatórios de perdas em vazio não preenchidos ou inválidos: ${missingNoLoad.join(', ')}`);
        }

        const payload = {
            operation: 'no_load_losses',
            data: {
                ...noLoadInputs,
                frequencia: basicData.frequencia,
                tensao_bt_kv: basicData.tensao_bt ? basicData.tensao_bt / 1000 : 0,
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
        displayNoLoadResults(results.results);

        await waitForApiSystem();
        const store = window.apiDataSystem.getStore('losses');
        const currentStoreData = await store.getData() || {};
        const newFormData = collectFormData(document.getElementById('lossesTabContent'));
        await store.updateData({ 
            resultsNoLoad: results.results, 
            formData: { ...(currentStoreData.formData || {}), ...newFormData } 
        });

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
        if (!basicData) throw new Error('Dados básicos do transformador não encontrados.');
        
        await waitForApiSystem();
        const lossesStore = window.apiDataSystem.getStore('losses');
        const storedLossesData = await lossesStore.getData();

        let perdasVazioCalculada;
        if (storedLossesData?.formData?.['perdas-vazio-kw']) {
            perdasVazioCalculada = parseFloat(storedLossesData.formData['perdas-vazio-kw']);
        } else if (basicData.perdas_vazio_kw) { // Fallback to basic data if entered there
             perdasVazioCalculada = parseFloat(basicData.perdas_vazio_kw);
        }

        if (perdasVazioCalculada === undefined || perdasVazioCalculada === null || isNaN(perdasVazioCalculada) || perdasVazioCalculada <=0) {
            throw new Error('Perdas em Vazio (kW) não encontradas, inválidas ou não calculadas. Preencha e calcule na aba "Perdas em Vazio" primeiro.');
        }

        const loadInputs = collectLoadInputs();
        const requiredLoadFields = ['perdas_carga_kw_u_min', 'perdas_carga_kw_u_nom', 'perdas_carga_kw_u_max'];
        const missingLoad = requiredLoadFields.filter(field => !loadInputs[field] || loadInputs[field] <= 0);
        if (missingLoad.length > 0) {
            throw new Error(`Campos obrigatórios de perdas em carga não preenchidos ou inválidos: ${missingLoad.join(', ')}`);
        }

        const payload = {
            operation: 'load_losses',
            data: {
                ...loadInputs,
                potencia_mva: basicData.potencia_mva,
                impedancia: basicData.impedancia,
                tensao_at_kv: basicData.tensao_at ? basicData.tensao_at / 1000 : 0,
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
        displayLoadResults(results.results.condicoes_nominais, results.results.cenarios_detalhados_por_tap, results.results.sugestao_geral_banco);

        const store = window.apiDataSystem.getStore('losses');
        const currentStoreData = await store.getData() || {};
        const newFormData = collectFormData(document.getElementById('lossesTabContent'));
        await store.updateData({ 
            resultsLoad: results.results, 
            formData: { ...(currentStoreData.formData || {}), ...newFormData }
        });

    } catch (error) {
        console.error('[losses] Erro ao calcular perdas em carga:', error);
        showCalculationError('perdas-carga', error.message);
    }
}

function showCalculationLoading(calculationType) {
    const loadingHtml = `
        <div class="d-flex align-items-center justify-content-center p-3">
            <div class="spinner-border spinner-border-sm text-primary me-2" role="status">
                <span class="visually-hidden">Calculando...</span>
            </div>
            <span class="text-primary small">Calculando...</span>
        </div>`;
    
    const areas = calculationType === 'perdas-vazio' 
        ? ['parametros-gerais-card-body', 'dut-voltage-level-results-body', 'sut-analysis-results-area', 'legend-observations-no-load-area']
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
        ? ['parametros-gerais-card-body', 'dut-voltage-level-results-body', 'sut-analysis-results-area', 'legend-observations-no-load-area']
        : ['condicoes-nominais-card-body', 'resultados-perdas-carga'];

    areas.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = errorHtml;
    });
}

function displayNoLoadResults(results) {
    console.log('[losses] Exibindo resultados de perdas em vazio:', results);
    const { calculos_baseados_aco, calculos_vazio, analise_sut_eps_vazio } = results;

    const geraisContainer = document.getElementById('parametros-gerais-card-body');
    if (geraisContainer) {
        geraisContainer.innerHTML = `
            <table class="table table-sm table-striped table-hover small caption-top">
                <caption class="small text-muted">Baseado em Aço M4 (Calculado) vs. Projeto (Input)</caption>
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

    const dutContainer = document.getElementById('dut-voltage-level-results-body');
    if (dutContainer) {
        dutContainer.innerHTML = `
            <table class="table table-sm table-striped table-hover small caption-top">
                 <caption class="small text-muted">Valores de Teste DUT (Baseado em Entradas de Projeto)</caption>
                <tbody>
                    <tr><td>Tensão Teste 1.1pu (kV):</td><td class="text-end fw-bold">${calculos_vazio?.tensao_teste_1_1_kv ?? 'N/A'}</td></tr>
                    <tr><td>Corrente Exc. 1.1pu (A):</td><td class="text-end fw-bold">${calculos_vazio?.corrente_excitacao_1_1_calc_a ?? 'N/A'}</td></tr>
                    <tr><td>Tensão Teste 1.2pu (kV):</td><td class="text-end fw-bold">${calculos_vazio?.tensao_teste_1_2_kv ?? 'N/A'}</td></tr>
                    <tr><td>Corrente Exc. 1.2pu (A):</td><td class="text-end fw-bold">${calculos_vazio?.corrente_excitacao_1_2_calc_a ?? 'N/A'}</td></tr>
                </tbody>
            </table>`;
    }

    const sutContainer = document.getElementById('sut-analysis-results-area');
    if (sutContainer && analise_sut_eps_vazio) {
        let sutHtml = '<div class="row g-2">';
        const puLevels = Object.keys(analise_sut_eps_vazio).sort(); // Sort to ensure order

        puLevels.forEach(puLevel => {
            const analysis = analise_sut_eps_vazio[puLevel];
            sutHtml += `
                <div class="col-md-4">
                    <div class="card card-sm">
                        <div class="card-header card-header-sm text-center small fw-bold">${puLevel.toUpperCase()}</div>
                        <div class="card-body p-1 table-responsive">`;
            if (analysis && analysis.status === "OK" && analysis.taps_info && analysis.taps_info.length > 0) {
                sutHtml += `<table class="table table-sm table-striped table-hover small mb-0">
                                <thead><tr><th>Tap SUT (kV)</th><th class="text-end">I_EPS (A)</th><th class="text-end">% Limite</th></tr></thead>
                                <tbody>`;
                analysis.taps_info.forEach(tap => {
                    const row_style = tap.percent_limite_eps > 100 ? 'table-danger' : (tap.percent_limite_eps > 85 ? 'table-warning' : '');
                    sutHtml += `<tr class="${row_style}">
                                    <td>${tap.sut_tap_kv}</td>
                                    <td class="text-end">${tap.corrente_eps_a}</td>
                                    <td class="text-end">${tap.percent_limite_eps}%</td>
                                </tr>`;
                });
                sutHtml += `</tbody></table>`;
            } else {
                sutHtml += `<p class="text-muted text-center small m-1 p-2">${analysis?.status || 'N/A'}</p>`;
            }
            sutHtml += `</div></div></div>`;
        });
        sutHtml += '</div>';
        sutContainer.innerHTML = sutHtml;
    }
     // Placeholder for legend/observations area for no-load losses
    const legendNoLoadContainer = document.getElementById('legend-observations-no-load-area');
    if (legendNoLoadContainer) {
        // Basic legend example, can be expanded based on Dash app's `create_legend_section` for no-load
        legendNoLoadContainer.innerHTML = `
            <div class="card mt-2">
                <div class="card-header card-header-sm"><h6 class="m-0 text-center small fw-bold">LEGENDA SUT/EPS (VAZIO)</h6></div>
                <div class="card-body p-2 small">
                    <span class="badge bg-light text-dark border me-1">Normal (<85%)</span>
                    <span class="badge bg-warning text-dark border me-1">Alerta (85-100%)</span>
                    <span class="badge bg-danger border me-1">Crítico (>100%)</span>
                </div>
            </div>
        `;
    }
}


function displayLoadResults(condicoesNominais, cenariosDetalhadosPorTap, sugestaoGeralBanco) {
    console.log('[losses] Exibindo resultados de perdas em carga:', { condicoesNominais, cenariosDetalhadosPorTap, sugestaoGeralBanco });

    const formatValue = (value, decimals = 2, unit = '') => {
        if (value === null || value === undefined || value === '' || Number.isNaN(value)) return 'N/A';
        if (typeof value === 'number') {
            const num = parseFloat(value.toFixed(decimals)); // Avoid -0.00
            return num.toLocaleString(undefined, {minimumFractionDigits: decimals, maximumFractionDigits: decimals}) + unit;
        }
        return value + unit;
    };
    
    const nominaisContainer = document.getElementById('condicoes-nominais-card-body');
    if (nominaisContainer && condicoesNominais) {
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

    const detalhadosContainer = document.getElementById('resultados-perdas-carga');
    if (detalhadosContainer) {
        let htmlContent = '';

        if (!cenariosDetalhadosPorTap || !Array.isArray(cenariosDetalhadosPorTap) || cenariosDetalhadosPorTap.length === 0) {
            htmlContent = `<div class="alert alert-warning text-center small p-2"><i class="fas fa-exclamation-triangle me-2"></i>Nenhum cenário detalhado encontrado.</div>`;
            detalhadosContainer.innerHTML = htmlContent;
            return;
        }

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
                     <p class="text-muted small mt-1 mb-0">Nota: Configurações S/F e C/F individuais para cada cenário de teste são detalhadas abaixo.</p>
                </div>
            </div>`;
        }
        
        cenariosDetalhadosPorTap.forEach((tapData) => {
            const tapNome = tapData.nome_tap || `Tap Desconhecido`;
            htmlContent += `<h5 class="mt-3 mb-2 small text-primary fw-bold">Resultados para Tap ${tapNome}</h5>`;

            const cenariosDoTap = tapData.cenarios_do_tap || [];
            if (cenariosDoTap.length === 0) {
                htmlContent += `<div class="alert alert-info small p-1">Nenhum cenário de teste encontrado para ${tapNome}.</div>`;
                return; // next tapData
            }

            // Tabela de Parâmetros de Teste e Banco de Capacitores
            htmlContent += `<div class="table-responsive mb-2">
                            <table class="table table-sm table-bordered table-hover small caption-top">
                            <caption class="small text-muted">Parâmetros de Teste e Banco de Capacitores (${tapNome})</caption>
                            <thead>
                                <tr class="table-light">
                                    <th rowspan="2" style="vertical-align: middle;">Cenário Teste</th>
                                    <th rowspan="2" style="vertical-align: middle;">Vtest (kV)</th>
                                    <th rowspan="2" style="vertical-align: middle;">Itest (A)</th>
                                    <th rowspan="2" style="vertical-align: middle;">P_ativa (kW)</th>
                                    <th rowspan="2" style="vertical-align: middle;">P_teste (MVA)</th>
                                    <th rowspan="2" style="vertical-align: middle;">Q_req (MVAr)</th>
                                    <th colspan="2" class="text-center">Banco S/F (V_teste ≤ V_banco)</th>
                                    <th colspan="2" class="text-center">Banco C/F (V_teste > V_banco*1.1)</th>
                                    <th rowspan="2" style="vertical-align: middle;">Status</th>
                                </tr>
                                <tr class="table-light">
                                    <th class="text-center small">V_disp (kV) / CS / Q / Q_prov (MVAr)</th>
                                    <th class="text-center small">I_EPS (A) / % Limite</th>
                                    <th class="text-center small">V_disp (kV) / CS / Q / Q_prov (MVAr)</th>
                                    <th class="text-center small">I_EPS (A) / % Limite</th>
                                </tr>
                            </thead><tbody>`;

            cenariosDoTap.forEach((cenario) => {
                const testParams = cenario.test_params_cenario || {};
                const capBankSf = cenario.cap_bank_sf || {};
                const capBankCf = cenario.cap_bank_cf || {};
                const sutEpsAnalysis = cenario.sut_eps_analysis || [];

                // Find the SUT Tap analysis closest to 100% or lowest if all over.
                // This is a simplified version of Dash's "most critical" selection for brevity here.
                let bestSutTapSf = sutEpsAnalysis.length > 0 ? sutEpsAnalysis[0] : {}; // Default to first if available
                let bestSutTapCf = sutEpsAnalysis.length > 0 ? sutEpsAnalysis[0] : {};
                if (sutEpsAnalysis.length > 0) {
                    bestSutTapSf = sutEpsAnalysis.reduce((prev, curr) => (Math.abs(100 - parseFloat(curr.percent_limite_sf)) < Math.abs(100 - parseFloat(prev.percent_limite_sf)) ? curr : prev), sutEpsAnalysis[0]);
                    bestSutTapCf = sutEpsAnalysis.reduce((prev, curr) => (Math.abs(100 - parseFloat(curr.percent_limite_cf)) < Math.abs(100 - parseFloat(prev.percent_limite_cf)) ? curr : prev), sutEpsAnalysis[0]);
                }


                const sf_bank_info = `${formatValue(capBankSf.tensao_disp_kv,1)} / ${capBankSf.cs_config || '-'} / ${capBankSf.q_config || '-'} / ${formatValue(capBankSf.q_provided_mvar,3)}`;
                const cf_bank_info = `${formatValue(capBankCf.tensao_disp_kv,1)} / ${capBankCf.cs_config || '-'} / ${capBankCf.q_config || '-'} / ${formatValue(capBankCf.q_provided_mvar,3)}`;
                
                const sf_eps_info = sutEpsAnalysis.length > 0 ? `${formatValue(bestSutTapSf.corrente_eps_sf_a,1)} / ${formatValue(bestSutTapSf.percent_limite_sf,1,'%')}` : '- / -';
                const cf_eps_info = sutEpsAnalysis.length > 0 ? `${formatValue(bestSutTapCf.corrente_eps_cf_a,1)} / ${formatValue(bestSutTapCf.percent_limite_cf,1,'%')}` : '- / -';

                const statusStyle = getStatusStyle(cenario.status_cenario);

                htmlContent += `<tr>
                    <td>${cenario.nome_cenario_teste || '-'}</td>
                    <td>${formatValue(testParams.tensao_kv)}</td>
                    <td>${formatValue(testParams.corrente_a)}</td>
                    <td>${formatValue(testParams.pativa_kw)}</td>
                    <td>${formatValue(testParams.pteste_mva, 3)}</td>
                    <td>${formatValue(testParams.pteste_mvar_req, 3)}</td>
                    <td class="small">${capBankSf.tensao_disp_kv ? sf_bank_info : 'N/A'}</td>
                    <td class="small" style="${getSutEpsStyle(bestSutTapSf.percent_limite_sf)}">${capBankSf.tensao_disp_kv ? sf_eps_info : 'N/A'}</td>
                    <td class="small">${capBankCf.tensao_disp_kv ? cf_bank_info : 'N/A'}</td>
                    <td class="small" style="${getSutEpsStyle(bestSutTapCf.percent_limite_cf)}">${capBankCf.tensao_disp_kv ? cf_eps_info : 'N/A'}</td>
                    <td style="${statusStyle.cssText}" class="small">${cenario.status_cenario || 'N/A'}</td>
                </tr>`;
            });
            htmlContent += `</tbody></table></div>`;

            // Optional: Detailed SUT/EPS table per scenario (can be verbose)
            // For brevity, the main SUT/EPS info is now integrated above.
            // If you need the full SUT/EPS table for each scenario, you'd add another loop here.
        });

        // Add Legend
        htmlContent += `
        <div class="card mt-3">
            <div class="card-header card-header-sm"><h6 class="m-0 text-center small fw-bold">LEGENDA DE STATUS E SUT/EPS (CARGA)</h6></div>
            <div class="card-body p-2 small">
                <p class="mb-1"><strong>Status do Cenário:</strong> Indica alertas sobre Tensão de Teste (V), Corrente de Teste (A), Potência Ativa (P), ou Q Requerido do Banco.</p>
                <ul class="list-unstyled d-flex flex-wrap">
                    <li class="me-3"><span style="${getStatusStyle('OK').cssText}">OK</span>: Sem alertas.</li>
                    <li class="me-3"><span style="${getStatusStyle('(V) > Limite').cssText}">(V) > Limite</span>: Tensão de teste excede limite do banco C/F.</li>
                    <li class="me-3"><span style="${getStatusStyle('(A) > Limite').cssText}">(A) > Limite</span>: Corrente de teste excede limite EPS.</li>
                    <li class="me-3"><span style="${getStatusStyle('(P) > Limite').cssText}">(P) > Limite</span>: Potência ativa excede limite DUT.</li>
                    <li class="me-3"><span style="${getStatusStyle('CapBank Q_req ↑ (46.8+ MVAr)').cssText}">Q_req ↑ (46.8+ MVAr)</span>: Potência reativa alta.</li>
                    <li class="me-3"><span style="${getStatusStyle('CapBank Q_req ↑ (93.6+ MVAr)').cssText}">Q_req ↑ (93.6+ MVAr)</span>: Potência reativa crítica.</li>
                </ul>
                <p class="mb-1 mt-2"><strong>Corrente I_EPS SUT (% Limite):</strong> Corrente refletida na BT do SUT, considerando compensação do banco (S/F ou C/F).</p>
                 <ul class="list-unstyled d-flex flex-wrap">
                    <li class="me-2 p-1 small" style="${getSutEpsStyle(-10)}">Compens. Excessiva</li>
                    <li class="me-2 p-1 small" style="${getSutEpsStyle(25)}">Normal (<50%)</li>
                    <li class="me-2 p-1 small" style="${getSutEpsStyle(70)}">Alerta (50-85%)</li>
                    <li class="me-2 p-1 small" style="${getSutEpsStyle(95)}">Alto (85-100%)</li>
                    <li class="me-2 p-1 small" style="${getSutEpsStyle(110)}">Crítico (>100%)</li>
                </ul>
                <p class="small text-muted mt-1 mb-0">S/F: V_teste ≤ V_banco_nominal. C/F: V_teste > V_banco_nominal * 1.1. Valores de I_EPS mostrados são para o tap SUT mais próximo do limite de 100%.</p>
            </div>
        </div>`;


        detalhadosContainer.innerHTML = htmlContent;
    } else {
        console.warn('[losses] Container de resultados detalhados "resultados-perdas-carga" não encontrado.');
    }
}

function getStatusStyle(statusText) {
    // Simplified version of Dash's StatusStyler for JS
    const style = { cssText: "font-weight: normal; padding: 0.1rem 0.2rem;" };
    if (!statusText) return style;

    if (statusText.includes("(V)") || statusText.includes("(A)") || statusText.includes("(P)") || statusText.includes("93.6+ MVAr")) {
        style.cssText += "color: #B00020; font-weight: bold;"; // Material Design Error Color
    } else if (statusText.includes("46.8+ MVAr")) {
        style.cssText += "color: #FF6F00; font-weight: bold;"; // Material Design Warning Color (Orange)
    } else if (statusText === "OK") {
        style.cssText += "color: #388E3C;"; // Material Design Success Color (Green)
    } else {
         style.cssText += "color: #5f5f5f;"; // Default muted
    }
    return style;
}

function getSutEpsStyle(percent_limite) {
    let cssText = "padding: 0.1rem 0.2rem; border-radius: 3px; color: black;"; // Default black text
    if (percent_limite === null || percent_limite === undefined || isNaN(percent_limite)) return `background-color: #f8f9fa; ${cssText}`; // Light grey for N/A

    if (percent_limite < 0) { // Overcompensated
        cssText += "background-color: #e3f2fd; color: #0d47a1;"; // Light blue background, dark blue text
    } else if (percent_limite < 50) {
        cssText += "background-color: #e8f5e9;"; // Light green
    } else if (percent_limite < 85) {
        cssText += "background-color: #fff9c4;"; // Light yellow
    } else if (percent_limite <= 100) {
        cssText += "background-color: #ffe0b2;"; // Light orange
    } else { // > 100
        cssText += "background-color: #ffcdd2; color: #c62828; font-weight: bold;"; // Light red background, dark red text
    }
    return cssText;
}


async function updateDependentFieldsFromTransformerData() {
    console.log('[losses] updateDependentFieldsFromTransformerData: Chamado.');
    const basicData = await getBasicTransformerData();
    if (basicData) {
        const summary = {
            potencia_mva: basicData.potencia_mva,
            frequencia: basicData.frequencia,
            impedancia: basicData.impedancia,
            tipo_transformador: basicData.tipo_transformador,
            tensao_at_kv: basicData.tensao_at ? basicData.tensao_at / 1000 : 'N/A',
            tensao_bt_kv: basicData.tensao_bt ? basicData.tensao_bt / 1000 : 'N/A',
        };
        showInheritanceNotification(summary, "Dados básicos do transformador carregados e disponíveis para os cálculos de perdas.");
    }
}

function showInheritanceNotification(summary, message) {
    const existingNotification = document.querySelector('.inheritance-notification-losses');
    if (existingNotification) existingNotification.remove();

    const count = Object.values(summary).filter(v => v !== null && v !== undefined && v !== '' && v !== 'N/A').length;
    if (count === 0) return;

    const notification = document.createElement('div');
    notification.className = 'alert alert-info alert-dismissible fade show inheritance-notification-losses small shadow-sm';
    notification.style.cssText = 'position: fixed; top: 70px; right: 20px; z-index: 1055; max-width: 380px; font-size: 0.8rem;';
    notification.innerHTML = `
        <i class="fas fa-info-circle me-2"></i>
        <strong>${message}</strong>
        <ul class="mb-0 ps-3 small mt-1" style="font-size: 0.75rem;">
            ${Object.entries(summary).map(([key, value]) => `<li>${key.replace(/_/g, ' ')}: ${value ?? 'N/A'}</li>`).join('')}
        </ul>
        <button type="button" class="btn-close btn-sm" data-bs-dismiss="alert" aria-label="Close" style="font-size:0.6rem;"></button>`;
    document.body.appendChild(notification);
    setTimeout(() => { if (notification.parentNode) notification.remove(); }, 7000);
}

document.addEventListener('moduleContentLoaded', (event) => {
    if (event.detail && event.detail.moduleName === 'losses') {
        initLosses();
    }
});

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('lossesTabContent')) {
        initLosses();
    }
});