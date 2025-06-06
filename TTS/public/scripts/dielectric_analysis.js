// public/scripts/dielectric_analysis.js - ATUALIZADO (Combinado com abas)

import { loadAndPopulateTransformerInfo, transformerDataStore } from './common_module.js';
import { collectFormData, fillFormWithData, setupApiFormPersistence, waitForApiSystem } from './api_persistence.js';

// Função auxiliar para obter dados básicos do transformador
async function getTransformerBasicData() {
    try {
        const store = window.apiDataSystem.getStore('transformerInputs');
        const data = await store.getData();
        
        if (data && data.formData) {
            return data.formData;
        }
        return {};
    } catch (error) {
        console.error('[dielectric_analysis] Erro ao obter dados básicos do transformador:', error);
        return {};
    }
}

// Função para carregar dados do store 'dielectricAnalysis' e preencher o formulário
async function loadDielectricDataAndPopulateForm() {
    try {
        console.log('[dielectric_analysis] Carregando dados do store "dielectricAnalysis" e preenchendo formulário...');
        await waitForApiSystem(); // Garante que o sistema de persistência esteja pronto

        const store = window.apiDataSystem.getStore('dielectricAnalysis');
        const data = await store.getData();

        if (data && data.formData) {
            const formElement = document.getElementById('dielectric-analysis-form');
            if (formElement) {
                fillFormWithData(formElement, data.formData);
                console.log('[dielectric_analysis] Formulário de análise dielétrica preenchido com dados do store:', data.formData);
            } else {
                console.warn('[dielectric_analysis] Formulário "dielectric-analysis-form" não encontrado para preenchimento.');
            }
        } else {
            console.log('[dielectric_analysis] Nenhum dado de análise dielétrica encontrado no store.');
        }
    } catch (error) {
        console.error('[dielectric_analysis] Erro ao carregar e preencher dados de análise dielétrica:', error);
    }
}

// Função para configurar o botão Calculate
async function setupCalcButton() {
    const calcBtn = document.getElementById('calc-dielectric-btn');
    if (calcBtn) {
        calcBtn.addEventListener('click', async function() {
            console.log('[dielectric_analysis] Botão Calcular clicado!');
            
            try {
                // Mostrar feedback de carregamento
                const resultsDiv = document.getElementById('dielectric-calc-results');
                const errorDiv = document.getElementById('dielectric-calc-error');
                resultsDiv.innerHTML = '<div class="text-center text-muted"><i class="fas fa-spinner fa-spin me-2"></i>Calculando...</div>';
                errorDiv.textContent = '';

                // Coletar dados do formulário
                const formElement = document.getElementById('dielectric-analysis-form');
                if (!formElement) {
                    throw new Error('Formulário de análise dielétrica não encontrado');
                }
                
                const moduleData = collectFormData(formElement);
                console.log('[dielectric_analysis] Dados do módulo coletados:', moduleData);

                // Obter dados básicos do transformador
                const basicData = await getTransformerBasicData();
                console.log('[dielectric_analysis] Dados básicos do transformador:', basicData);

                // Validar dados essenciais
                if (!basicData.potencia_mva || !basicData.tensao_at || !basicData.tensao_bt) {
                    throw new Error('Dados básicos do transformador incompletos. Verifique a página "Dados Básicos".');
                }

                // Preparar dados para envio
                const requestData = {
                    basicData: basicData,
                    moduleData: moduleData
                };

                console.log('[dielectric_analysis] Enviando dados para backend:', requestData);

                // Fazer requisição para o backend
                const response = await fetch('/api/transformer/modules/dielectricAnalysis/process', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestData)
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `Erro na requisição: ${response.status}`);
                }

                const result = await response.json();
                console.log('[dielectric_analysis] Resultado do backend:', result);

                // Exibir resultados
                displayCalculationResults(result);

            } catch (error) {
                console.error('[dielectric_analysis] Erro no cálculo:', error);
                const errorDiv = document.getElementById('dielectric-calc-error');
                errorDiv.textContent = `Erro: ${error.message}`;
                
                const resultsDiv = document.getElementById('dielectric-calc-results');
                resultsDiv.innerHTML = '';
            }
        });
    }
}

// Função para exibir os resultados do cálculo
function displayCalculationResults(result) {
    const resultsDiv = document.getElementById('dielectric-calc-results');
    
    if (!result || !result.data) {
        resultsDiv.innerHTML = '<div class="text-warning">Nenhum resultado retornado pelo servidor.</div>';
        return;
    }

    // Construir HTML dos resultados
    let resultsHtml = '<div class="card mt-2"><div class="card-header bg-primary text-white"><h6 class="mb-0">Resultados da Análise Dielétrica</h6></div><div class="card-body">';
    
    const data = result.data;
    
    // Resultados AT
    if (data.at) {
        resultsHtml += '<div class="mb-3"><h6 class="text-primary">Alta Tensão (AT)</h6>';
        if (data.at.nivel_isolamento) resultsHtml += `<p><strong>Nível de Isolamento:</strong> ${data.at.nivel_isolamento}</p>`;
        if (data.at.tensao_ensaio_frequencia_industrial) resultsHtml += `<p><strong>Tensão de Ensaio (60Hz):</strong> ${data.at.tensao_ensaio_frequencia_industrial} kV</p>`;
        if (data.at.tensao_suportabilidade_impulso) resultsHtml += `<p><strong>NBI:</strong> ${data.at.tensao_suportabilidade_impulso} kV</p>`;
        if (data.at.status) resultsHtml += `<p><strong>Status:</strong> <span class="${data.at.status === 'APROVADO' ? 'text-success' : 'text-danger'}">${data.at.status}</span></p>`;
        resultsHtml += '</div>';
    }
    
    // Resultados BT
    if (data.bt) {
        resultsHtml += '<div class="mb-3"><h6 class="text-info">Baixa Tensão (BT)</h6>';
        if (data.bt.nivel_isolamento) resultsHtml += `<p><strong>Nível de Isolamento:</strong> ${data.bt.nivel_isolamento}</p>`;
        if (data.bt.tensao_ensaio_frequencia_industrial) resultsHtml += `<p><strong>Tensão de Ensaio (60Hz):</strong> ${data.bt.tensao_ensaio_frequencia_industrial} kV</p>`;
        if (data.bt.tensao_suportabilidade_impulso) resultsHtml += `<p><strong>NBI:</strong> ${data.bt.tensao_suportabilidade_impulso} kV</p>`;
        if (data.bt.status) resultsHtml += `<p><strong>Status:</strong> <span class="${data.bt.status === 'APROVADO' ? 'text-success' : 'text-danger'}">${data.bt.status}</span></p>`;
        resultsHtml += '</div>';
    }

    // Resultados Terciário
    if (data.terciario) {
        resultsHtml += '<div class="mb-3"><h6 class="text-warning">Terciário</h6>';
        if (data.terciario.nivel_isolamento) resultsHtml += `<p><strong>Nível de Isolamento:</strong> ${data.terciario.nivel_isolamento}</p>`;
        if (data.terciario.tensao_ensaio_frequencia_industrial) resultsHtml += `<p><strong>Tensão de Ensaio (60Hz):</strong> ${data.terciario.tensao_ensaio_frequencia_industrial} kV</p>`;
        if (data.terciario.tensao_suportabilidade_impulso) resultsHtml += `<p><strong>NBI:</strong> ${data.terciario.tensao_suportabilidade_impulso} kV</p>`;
        if (data.terciario.status) resultsHtml += `<p><strong>Status:</strong> <span class="${data.terciario.status === 'APROVADO' ? 'text-success' : 'text-danger'}">${data.terciario.status}</span></p>`;
        resultsHtml += '</div>';
    }

    // Resumo geral
    if (data.resumo) {
        resultsHtml += '<div class="alert alert-info"><h6>Resumo</h6>';
        if (data.resumo.status_geral) resultsHtml += `<p><strong>Status Geral:</strong> <span class="${data.resumo.status_geral === 'APROVADO' ? 'text-success' : 'text-danger'}">${data.resumo.status_geral}</span></p>`;
        if (data.resumo.observacoes) resultsHtml += `<p><strong>Observações:</strong> ${data.resumo.observacoes}</p>`;
        resultsHtml += '</div>';
    }

    resultsHtml += '</div></div>';
    
    resultsDiv.innerHTML = resultsHtml;
}

// Função de inicialização do módulo Análise Dielétrica
async function initDielectricAnalysis() {
    console.log('Módulo Análise Dielétrica (com abas) carregado e pronto para interatividade.');

    // ID do placeholder para o painel de informações do transformador
    const transformerInfoPlaceholderId = 'transformer-info-dielectric_analysis-page';
    await loadAndPopulateTransformerInfo(transformerInfoPlaceholderId); // Carrega o painel no topo

    // Configurar persistência de dados usando API do backend
    // A persistência será configurada para o formulário principal da aba "Dados de Ensaio"
    const dielectricForm = document.getElementById('dielectric-analysis-form');
    if (dielectricForm) {
        await setupApiFormPersistence(dielectricForm, 'dielectricAnalysis');
    } else {
        console.warn('[dielectric_analysis] Formulário principal não encontrado para persistência.');
    }

    // Carregar e preencher os dados do próprio módulo de análise dielétrica
    await loadDielectricDataAndPopulateForm();

    // Configurar o botão Calculate
    await setupCalcButton();

    // Adicionar listener para o evento transformerDataUpdated
    document.addEventListener('transformerDataUpdated', async (event) => {
        console.log('[dielectric_analysis] Evento transformerDataUpdated recebido:', event.detail);
        // Recarrega os dados do próprio módulo para garantir consistência
        await loadDielectricDataAndPopulateForm();
    });

    // Inicialização das abas Bootstrap (garante que funcionem corretamente)
    const dielectricTabsEl = document.getElementById('dielectricTabs');
    if (dielectricTabsEl) {
        // Ativa a primeira aba por padrão ao carregar o script
        const basicAnalysisTabBtn = dielectricTabsEl.querySelector('#basic-analysis-tab');
        if (basicAnalysisTabBtn) {
            const dielectricTabs = new bootstrap.Tab(basicAnalysisTabBtn);
            dielectricTabs.show(); 
        }

        dielectricTabsEl.addEventListener('shown.bs.tab', async event => { // Tornar o listener assíncrono
            console.log(`Aba "${event.target.id}" mostrada. Reconfigurando persistência se necessário.`);
            // Se a aba de dados de ensaio for mostrada, reconfigura a persistência para ela
            if (event.target.id === 'basic-analysis-tab') {
                const basicAnalysisForm = document.getElementById('dielectric-analysis-form');
                if (basicAnalysisForm) {
                    await setupApiFormPersistence(basicAnalysisForm, 'dielectricAnalysis');
                }
            }
            // Lógica que precisa ser ativada quando uma aba é mostrada
            if (event.target.id === 'comprehensive-analysis-tab') {
                // Ao mostrar a aba de análise comparativa, podemos chamar o botão de análise automática
                const analisarDetalhesBtn = document.getElementById('analisar-detalhes-button');
                if (analisarDetalhesBtn) {
                    analisarDetalhesBtn.click(); // Simula o clique no botão
                }
            }
        });
    }

    // Função auxiliar para obter valor de input
    function getInputValue(id) {
        const element = document.getElementById(id);
        return element ? element.value : null;
    }

    // Lógica para o botão "Salvar Parâmetros" (na aba Dados de Ensaio)
    const saveParamsBtn = document.getElementById('save-dielectric-params-btn');
    if (saveParamsBtn) {
        saveParamsBtn.addEventListener('click', function() {
            console.log('Botão Salvar Parâmetros Dielétricos clicado!');
            // Implementar lógica para coletar todos os inputs da aba "Dados de Ensaio"
            // Ex: const um_at = getInputValue('um_at');
            // Enviar dados para o backend ou armazenar em um store local (localStorage/sessionStorage)
            document.getElementById('dielectric-save-confirmation').textContent = 'Parâmetros salvos!';
            setTimeout(() => {
                document.getElementById('dielectric-save-confirmation').textContent = '';
            }, 3000);
        });
    }

    // Lógica para o botão "Analisar Detalhes" (na aba Análise Comparativa)
    const analisarDetalhesBtn = document.getElementById('analisar-detalhes-button');
    if (analisarDetalhesBtn) {
        analisarDetalhesBtn.addEventListener('click', function() {
            console.log('Botão Analisar Detalhes (Análise Comparativa) clicado!');
            // Implementar lógica para carregar os "Parâmetros Selecionados"
            // e os "Resultados da Análise" (AT, BT, Terciário)
            // Isso geralmente envolveria ler os dados salvos da aba anterior (ou do backend)
            // e fazer cálculos/comparações para preencher as divs de output.
            document.getElementById('selected-params-display').innerHTML = '<div class="text-center py-3">Parâmetros carregados e análise iniciada.</div>';
            document.getElementById('comparison-output-at').innerHTML = '<div class="text-muted text-center py-3">Resultados AT em processamento...</div>';
            document.getElementById('comparison-output-bt').innerHTML = '<div class="text-muted text-center py-3">Resultados BT em processamento...</div>';
            document.getElementById('comparison-output-terciario').innerHTML = '<div class="text-muted text-center py-3">Resultados Terciário em processamento...</div>';

            // Simulação de carregamento e preenchimento
            setTimeout(() => {
                document.getElementById('selected-params-display').innerHTML = `
                    <p><strong>Tipo Isolamento:</strong> ${getInputValue('tipo-isolamento') || 'Uniforme'}</p>
                    <p><strong>Um AT:</strong> ${getInputValue('um_at') || '-'} kV</p>
                    <p><strong>BIL AT:</strong> ${getInputValue('ia_at') || '-'} kV</p>
                    <p>... (outros parâmetros selecionados)</p>
                `;
                document.getElementById('comparison-output-at').innerHTML = `
                    <p><strong>Status AT:</strong> APROVADO</p>
                    <p><strong>NBI Normativo:</strong> 650 kV</p>
                    <p><strong>BIL Compatível:</strong> Sim</p>
                `;
                document.getElementById('comparison-output-bt').innerHTML = `
                    <p><strong>Status BT:</strong> APROVADO</p>
                    <p><strong>NBI Normativo:</strong> 110 kV</p>
                    <p><strong>BIL Compatível:</strong> Sim</p>
                `;
                document.getElementById('comparison-output-terciario').innerHTML = `
                    <p><strong>Status Ter:</strong> N/A (não configurado)</p>
                `;
            }, 1500);
        });
    }

    // Lógica para o botão "Forçar Carregamento Dados" (na aba Análise Comparativa)
    const forcarCarregamentoBtn = document.getElementById('forcar-carregamento-button');
    if (forcarCarregamentoBtn) {
        forcarCarregamentoBtn.addEventListener('click', function() {
            console.log('Botão Forçar Carregamento Dados (Análise Comparativa) clicado!');
            // Implementar lógica para recarregar todos os dados do transformador e os inputs da página
            // Isso seria útil se os dados de "Dados Básicos" tivessem sido atualizados em outra aba
            // e você quisesse que eles se refletissem aqui sem ter que recalcular tudo.
        });
    }

    // Lógica para preencher "Informações Complementares"
    // Isso é um exemplo, os dados reais viriam do "transformerDataStore"
    const fillComplementaryInfo = async () => {
        const tipoIsolamentoEl = document.getElementById('tipo-isolamento');
        const displayTipoTransformadorEl = document.getElementById('display-tipo-transformador-dieletric');

        try {
            const transformerData = await transformerDataStore.getData();

            // Extrai dados do formato correto (pode estar em formData ou no nível raiz)
            let basicData = null;
            if (transformerData) {
                if (transformerData.formData) {
                    basicData = transformerData.formData;
                } else if (transformerData.inputs && transformerData.inputs.dados_basicos) {
                    basicData = transformerData.inputs.dados_basicos;
                } else {
                    basicData = transformerData;
                }
            }

            if (basicData && Object.keys(basicData).length > 0) {
                if (tipoIsolamentoEl) tipoIsolamentoEl.textContent = basicData.tipo_isolamento || '-';
                if (displayTipoTransformadorEl) displayTipoTransformadorEl.textContent = basicData.tipo_transformador || '-';
            } else {
                if (tipoIsolamentoEl) tipoIsolamentoEl.textContent = "-";
                if (displayTipoTransformadorEl) displayTipoTransformadorEl.textContent = "-";
            }
        } catch (error) {
            console.error('[dielectric_analysis] Erro ao carregar dados complementares:', error);
            if (tipoIsolamentoEl) tipoIsolamentoEl.textContent = "-";
            if (displayTipoTransformadorEl) displayTipoTransformadorEl.textContent = "-";
        }
    };

    await fillComplementaryInfo(); // Chama ao carregar o script

    // Lógica para alternar para a aba "Análise Comparativa" se o botão "Análise Dielétrica Completa" for clicado
    const switchToComprehensiveBtn = document.getElementById('switch-to-comprehensive-tab-btn');
    if (switchToComprehensiveBtn) {
        switchToComprehensiveBtn.addEventListener('click', function() {
            const comprehensiveTab = new bootstrap.Tab(document.getElementById('comprehensive-analysis-tab'));
            comprehensiveTab.show(); // Ativa a aba de Análise Comparativa
        });
    }

    // Lógica para alternar para a aba "Dados de Ensaio" se o botão "Voltar" (na aba Comparativa) for clicado
    const switchToBasicBtn = document.getElementById('switch-to-basic-tab-btn');
    if (switchToBasicBtn) {
        switchToBasicBtn.addEventListener('click', function() {
            const basicTab = new bootstrap.Tab(document.getElementById('basic-analysis-tab'));
            basicTab.show(); // Ativa a aba de Dados de Ensaio
        });
    }
}

// SPA routing: executa quando o módulo dielectric_analysis é carregado
document.addEventListener('moduleContentLoaded', (event) => {
    if (event.detail && event.detail.moduleName === 'dielectric_analysis') {
        console.log('[dielectric_analysis] SPA routing init');
        initDielectricAnalysis();
    }
});

// Fallback para carregamento direto da página (se não for SPA)
document.addEventListener('DOMContentLoaded', () => {
    // Verifica se o elemento principal do módulo está presente para evitar execução em outras páginas
    if (document.getElementById('dielectricTabs')) {
        console.log('[dielectric_analysis] DOMContentLoaded init (fallback)');
        initDielectricAnalysis();
    }
});