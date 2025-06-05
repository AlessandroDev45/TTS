// public/scripts/common_module.js

// Função para aguardar o sistema de persistência estar disponível
// public/scripts/common_module.js

// Importa a função waitForApiSystem do sistema de persistência global
// import { waitForApiSystem } from './api_persistence.js'; // Removido, agora acessa via window

// Store de dados do transformador usando o novo sistema
const transformerDataStore = {
    async getData() {
        console.log('[common_module] transformerDataStore.getData: Iniciando');
        try {
            // Acessa a função globalmente exposta
            const apiSystem = await window.waitForApiSystem();
            if (apiSystem) {
                console.log('[common_module] transformerDataStore.getData: Usando apiDataSystem');
                const store = apiSystem.getStore('transformerInputs');
                const data = await store.getData();
                console.log('[common_module] transformerDataStore.getData: Dados obtidos via apiDataSystem', data);
                return data;
            } else {
                console.log('[common_module] transformerDataStore.getData: Usando fallback localStorage');
                // Fallback para localStorage
                const data = JSON.parse(localStorage.getItem('transformerInputsData')) || {};
                console.log('[common_module] transformerDataStore.getData: Dados obtidos via localStorage', data);
                return data;
            }
        } catch (error) {
            console.error('[common_module] transformerDataStore.getData: Erro ao obter dados:', error);
            return {};
        } finally {
            console.log('[common_module] transformerDataStore.getData: Concluído');
        }
    },

    async setData(newData) {
        console.log('[common_module] transformerDataStore.setData: Iniciando com dados:', newData);
        try {
            // Acessa a função globalmente exposta
            const apiSystem = await window.waitForApiSystem();
            if (apiSystem) {
                console.log('[common_module] transformerDataStore.setData: Usando apiDataSystem');
                const store = apiSystem.getStore('transformerInputs');
                await store.updateData(newData);
                console.log("[common_module] transformerDataStore.setData: Dados atualizados via apiDataSystem");
            } else {
                console.log('[common_module] transformerDataStore.setData: Usando fallback localStorage');
                // Fallback para localStorage
                localStorage.setItem('transformerInputsData', JSON.stringify(newData));
                console.log("[common_module] transformerDataStore.setData: Dados atualizados via localStorage (fallback)");
            }
        } catch (error) {
            console.error('[common_module] transformerDataStore.setData: Erro ao salvar dados:', error);
        } finally {
            console.log('[common_module] transformerDataStore.setData: Concluído');
        }
    }
};

// Funções para preencher o transformer_info_panel
async function loadAndPopulateTransformerInfo(targetElementId) {
    console.log(`[common_module] loadAndPopulateTransformerInfo: Iniciando para ${targetElementId}`);
    const targetElement = document.getElementById(targetElementId);
    if (!targetElement) {
        // Não mostra erro para transformer_inputs pois é esperado não ter o painel
        if (targetElementId.includes('transformer_inputs')) {
            console.log(`[common_module] loadAndPopulateTransformerInfo: Painel não necessário para ${targetElementId}`);
        } else {
            console.error(`[common_module] loadAndPopulateTransformerInfo: Elemento alvo para info do transformador não encontrado: ${targetElementId}`);
        }
        console.log(`[common_module] loadAndPopulateTransformerInfo: Concluído (elemento não encontrado)`);
        return;
    }

    try {
        console.log('[common_module] loadAndPopulateTransformerInfo: Carregando template HTML');
        // Carrega o template HTML do painel de informações
        const response = await fetch('templates/transformer_info_panel.html'); // Caminho relativo ao index.html
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status} ao carregar template.`);
        }
        const templateHtml = await response.text();
        targetElement.innerHTML = templateHtml;
        console.log('[common_module] loadAndPopulateTransformerInfo: Template HTML carregado e inserido');

        console.log('[common_module] loadAndPopulateTransformerInfo: Buscando dados do transformador');
        // Busca os dados básicos do transformador via apiDataSystem
        const transformerData = await transformerDataStore.getData();
        console.log('[common_module] loadAndPopulateTransformerInfo: Dados do transformador obtidos:', transformerData);

        // Extrai dados do formato correto (pode estar em formData ou no nível raiz)
        let basicData = null;
        if (transformerData) {
            // Tenta diferentes estruturas de dados
            if (transformerData.formData) {
                basicData = transformerData.formData;
            } else if (transformerData.inputs && transformerData.inputs.dados_basicos) {
                basicData = transformerData.inputs.dados_basicos;
            } else {
                basicData = transformerData;
            }
        }

        // Função auxiliar para preencher campo com verificação de existência
        const fillField = (elementId, value) => {
            const element = document.getElementById(elementId);
            if (element) {
                element.textContent = value || '-';
            }
        };        // Preenche os campos do template com os dados
        if (basicData && Object.keys(basicData).length > 0) {
            console.log("[common_module] loadAndPopulateTransformerInfo: Preenchendo painel com dados:", basicData);

            // Especificações Gerais
            fillField('info-potencia-mva', basicData.potencia_mva);
            fillField('info-frequencia', basicData.frequencia);
            fillField('info-tipo-transformador', basicData.tipo_transformador);
            fillField('info-grupo-ligacao', basicData.grupo_ligacao);
            fillField('info-liquido-isolante', basicData.liquido_isolante);
            fillField('info-norma-iso', basicData.norma_iso);            // Temperaturas e Pesos
            fillField('info-elevacao-oleo-topo', basicData.elevacao_oleo_topo);
            fillField('info-elevacao-enrol', basicData.elevacao_enrol);
            fillField('info-peso-parte-ativa', basicData.peso_parte_ativa);
            fillField('info-peso-tanque', basicData.peso_tanque_acessorios); // Mapped to peso_tanque_acessorios
            fillField('info-peso-oleo', basicData.peso_oleo);
            fillField('info-peso-total', basicData.peso_total);
            fillField('info-tipo-isolamento', basicData.tipo_isolamento);

            // Dados da Alta Tensão (AT)
            fillField('info-tensao-at', basicData.tensao_at);
            fillField('info-classe-tensao-at', basicData.classe_tensao_at);
            fillField('info-corrente-nominal-at', basicData.corrente_nominal_at);
            fillField('info-impedancia', basicData.impedancia);
            fillField('info-nbi-at', basicData.nbi_at);
            fillField('info-conexao-at', basicData.conexao_at);

            // TAPs AT
            fillField('info-tensao-at-tap-maior', basicData.tensao_at_tap_maior);
            fillField('info-tensao-at-tap-menor', basicData.tensao_at_tap_menor);
            fillField('info-corrente-nominal-at-tap-maior', basicData.corrente_nominal_at_tap_maior);
            fillField('info-corrente-nominal-at-tap-menor', basicData.corrente_nominal_at_tap_menor);
            fillField('info-impedancia-tap-maior', basicData.impedancia_tap_maior);
            fillField('info-impedancia-tap-menor', basicData.impedancia_tap_menor);
            fillField('info-degrau-comutador', basicData.degrau_comutador);
            fillField('info-num-degraus-comutador', basicData.num_degraus_comutador);
            fillField('info-posicao-comutador', basicData.posicao_comutador);
            
            // Dados da Baixa Tensão (BT)
            fillField('info-tensao-bt', basicData.tensao_bt);
            fillField('info-classe-tensao-bt', basicData.classe_tensao_bt);
            fillField('info-corrente-nominal-bt', basicData.corrente_nominal_bt);
            fillField('info-nbi-bt', basicData.nbi_bt);
            fillField('info-conexao-bt', basicData.conexao_bt);

            // Dados do Terciário
            fillField('info-tensao-terciario', basicData.tensao_terciario);
            fillField('info-classe-tensao-terciario', basicData.classe_tensao_terciario);
            fillField('info-corrente-nominal-terciario', basicData.corrente_nominal_terciario);
            fillField('info-nbi-terciario', basicData.nbi_terciario);
            fillField('info-conexao-terciario', basicData.conexao_terciario);
            fillField('info-impedancia-at-terciario', basicData.impedancia_at_terciario);
            fillField('info-impedancia-bt-terciario', basicData.impedancia_bt_terciario);

            // Tensões de Ensaio
            fillField('info-teste-tensao-aplicada-at', basicData.teste_tensao_aplicada_at);
            fillField('info-teste-tensao-induzida-at', basicData.teste_tensao_induzida_at);
            fillField('info-teste-tensao-aplicada-bt', basicData.teste_tensao_aplicada_bt);
            fillField('info-teste-tensao-aplicada-terciario', basicData.teste_tensao_aplicada_terciario);

            // Ensaios e Perdas
            fillField('info-perdas-vazio', basicData.perdas_vazio);
            fillField('info-perdas-curto-circuito', basicData.perdas_curto_circuito);
            fillField('info-corrente-excitacao', basicData.corrente_excitacao);
            fillField('info-fator-k', basicData.fator_k);
            fillField('info-classe-precisao', basicData.classe_precisao);
            fillField('info-frequencia-ressonancia', basicData.frequencia_ressonancia);

        } else {
            console.log("[common_module] loadAndPopulateTransformerInfo: Nenhum dado do transformador encontrado - exibindo campos vazios");
            // Limpa os campos se não houver dados (comportamento normal para formulário vazio)

            // Especificações Gerais
            fillField('info-potencia-mva', '');
            fillField('info-frequencia', '');
            fillField('info-tipo-transformador', '');
            fillField('info-grupo-ligacao', '');
            fillField('info-liquido-isolante', '');
            fillField('info-norma-iso', '');            // Temperaturas e Pesos
            fillField('info-elevacao-oleo-topo', '');
            fillField('info-elevacao-enrol', '');
            fillField('info-peso-parte-ativa', '');
            fillField('info-peso-tanque', '');
            fillField('info-peso-oleo', '');
            fillField('info-peso-total', '');
            fillField('info-tipo-isolamento', '');

            // Dados da Alta Tensão
            fillField('info-tensao-at', '');
            fillField('info-classe-tensao-at', '');
            fillField('info-corrente-nominal-at', '');
            fillField('info-impedancia', '');
            fillField('info-nbi-at', '');
            fillField('info-conexao-at', '');

            // TAPs AT
            fillField('info-tensao-at-tap-maior', '');
            fillField('info-tensao-at-tap-menor', '');
            fillField('info-corrente-nominal-at-tap-maior', '');
            fillField('info-corrente-nominal-at-tap-menor', '');
            fillField('info-impedancia-tap-maior', '');
            fillField('info-impedancia-tap-menor', '');
            fillField('info-degrau-comutador', '');
            fillField('info-num-degraus-comutador', '');
            fillField('info-posicao-comutador', '');

            // Dados da Baixa Tensão
            fillField('info-tensao-bt', '');
            fillField('info-classe-tensao-bt', '');
            fillField('info-corrente-nominal-bt', '');
            fillField('info-corrente-nominal-bt', '');
            fillField('info-nbi-bt', '');
            fillField('info-conexao-bt', '');

            // Dados do Terciário
            fillField('info-tensao-terciario', '');
            fillField('info-classe-tensao-terciario', '');
            fillField('info-corrente-nominal-terciario', '');
            fillField('info-nbi-terciario', '');
            fillField('info-conexao-terciario', '');
            fillField('info-impedancia-at-terciario', '');
            fillField('info-impedancia-bt-terciario', '');

            // Tensões de Ensaio
            fillField('info-teste-tensao-aplicada-at', '');
            fillField('info-teste-tensao-induzida-at', '');
            fillField('info-teste-tensao-aplicada-bt', '');
            fillField('info-teste-tensao-aplicada-terciario', '');

            // Ensaios e Perdas
            fillField('info-perdas-vazio', '');
            fillField('info-perdas-curto-circuito', '');
            fillField('info-corrente-excitacao', '');
            fillField('info-fator-k', '');
            fillField('info-classe-precisao', '');
            fillField('info-frequencia-ressonancia', '');
        }

    } catch (error) {
        console.error('[common_module] loadAndPopulateTransformerInfo: Erro ao carregar ou preencher o painel de informações do transformador:', error);
        targetElement.innerHTML = `
            <div class="alert alert-danger m-0 p-2" style="font-size: 0.75rem;">
                Erro ao carregar informações do transformador.
            </div>
        `;
    } finally {
        console.log(`[common_module] loadAndPopulateTransformerInfo: Concluído para ${targetElementId}`);
    }
}

// Função para atualizar o painel de informações globalmente
async function updateGlobalInfoPanel() {
    console.log('[common_module] updateGlobalInfoPanel: Iniciando');
    // Esta função pode ser chamada quando dados do transformador são atualizados
    // Procura por painéis de informação em todas as páginas e os atualiza
    const infoPanels = document.querySelectorAll('.transformer-info-panel');
    if (infoPanels.length > 0) {
        console.log(`[common_module] updateGlobalInfoPanel: Encontrados ${infoPanels.length} painéis. Atualizando o primeiro.`);
        // Se encontrar painéis, recarrega as informações
        const targetElementId = infoPanels[0].closest('[id]')?.id;
        if (targetElementId) {
            await loadAndPopulateTransformerInfo(targetElementId);
        } else {
             console.warn('[common_module] updateGlobalInfoPanel: Não foi possível encontrar o ID do elemento pai do painel.');
        }
    } else {
        console.log('[common_module] updateGlobalInfoPanel: Nenhum painel de informações encontrado para atualizar.');
    }
    console.log('[common_module] updateGlobalInfoPanel: Concluído');
}

// Configura listener para atualização automática quando dados do transformador mudam
function setupAutoUpdateListener() {
    console.log('[common_module] setupAutoUpdateListener: Configurando listener para transformerDataUpdated');
    document.addEventListener('transformerDataUpdated', async (event) => {
        console.log('[common_module] Evento transformerDataUpdated recebido, atualizando painéis:', event.detail);
        await updateGlobalInfoPanel();
    });
    console.log('[common_module] setupAutoUpdateListener: Listener de atualização automática configurado');
}

// Limpeza automática de cache para módulos específicos
function autoCleanModuleCache(moduleName) {
    console.log(`[common_module] autoCleanModuleCache: Verificando cache para ${moduleName}`);
    const moduleVersion = '1.0.0';
    const versionKey = `${moduleName}_cache_version`;
    const lastVersion = localStorage.getItem(versionKey);

    if (lastVersion !== moduleVersion) {
        console.log(`[common_module] autoCleanModuleCache: Nova versão detectada para ${moduleName}, limpando cache automaticamente...`);

        const keys = Object.keys(localStorage);
        let removedCount = 0;

        keys.forEach(key => {
            if (key.includes(moduleName)) {
                localStorage.removeItem(key);
                removedCount++;
            }
        });

        localStorage.setItem(versionKey, moduleVersion);
        console.log(`[common_module] autoCleanModuleCache: ✅ ${moduleName}: ${removedCount} itens removidos`);
    } else {
        console.log(`[common_module] autoCleanModuleCache: Cache de ${moduleName} já está atualizado`);
    }
    console.log(`[common_module] autoCleanModuleCache: Concluído para ${moduleName}`);
}

// Inicializa o listener quando o DOM estiver pronto
if (document.readyState === 'loading') {
    console.log('[common_module] DOMContentLoaded: Configurando listener para setupAutoUpdateListener');
    document.addEventListener('DOMContentLoaded', setupAutoUpdateListener);
} else {
    console.log('[common_module] DOM já pronto: Executando setupAutoUpdateListener diretamente');
    setupAutoUpdateListener();
}

// Limpa cache automaticamente para módulos problemáticos
autoCleanModuleCache('history');
autoCleanModuleCache('standards');

// Exporta as funções para serem usadas pelos scripts de módulo
export { loadAndPopulateTransformerInfo, transformerDataStore, updateGlobalInfoPanel };