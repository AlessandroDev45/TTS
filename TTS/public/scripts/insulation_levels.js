// public/scripts/insulation_levels.js
// Script para gerenciar níveis de isolamento e popular dropdowns

// Cache para dados de tabela.json
let isolationLevelsCache = null;

// Função para carregar dados de isolamento da tabela.json
async function loadIsolationLevelData() {
    if (isolationLevelsCache) {
        console.log('[insulation_levels] Usando cache de níveis de isolamento');
        return isolationLevelsCache;
    }

    try {
        console.log('[insulation_levels] Carregando tabela.json...');
        const response = await fetch('/assets/tabela.json');
        if (!response.ok) {
            throw new Error(`Erro HTTP ${response.status} ao carregar tabela.json`);
        }
        
        const data = await response.json();
        isolationLevelsCache = data;
        console.log('[insulation_levels] tabela.json carregada com sucesso');
        return data;
    } catch (error) {
        console.error('[insulation_levels] Erro ao carregar tabela.json:', error);
        return null;
    }
}

// Obter valores distintos para uma norma específica
function getDistinctValuesForNorma(standard, key) {
    if (!isolationLevelsCache || !isolationLevelsCache.insulation_levels) {
        console.error('[insulation_levels] Cache não disponível');
        return [];
    }

    const values = isolationLevelsCache.insulation_levels
        .filter(item => item.standard.startsWith(standard))
        .flatMap(item => item[key] || [])
        .filter(val => val !== null && val !== "NA_SIL");

    return [...new Set(values)].sort((a, b) => Number(a) - Number(b));
}

// Criar opções para um dropdown
function createOptionsForKey(standard, key, suffix) {
    const distinctValues = getDistinctValuesForNorma(standard, key);
    return distinctValues.map(val => ({
        label: `${val}${suffix}`,
        value: String(val)
    }));
}

// Filtrar níveis de isolamento por classe de tensão
function getIsolationLevels(umKvValue, windingPrefix, standard) {
    if (!isolationLevelsCache || !isolationLevelsCache.insulation_levels) {
        console.error('[insulation_levels] Cache não disponível');
        return { nbi_list: [], sil_list: [], ta_list: [], ti_list: [] };
    }

    // Encontrar o item correspondente à classe de tensão
    const matchingItem = isolationLevelsCache.insulation_levels.find(item => 
        item.standard.startsWith(standard) && 
        Number(item.um_kv) === Number(umKvValue)
    );

    if (!matchingItem) {
        console.warn(`[insulation_levels] Nenhum dado encontrado para ${standard} ${umKvValue}kV`);
        return { nbi_list: [], sil_list: [], ta_list: [], ti_list: [] };
    }

    return {
        nbi_list: matchingItem.bil_kvp || [],
        sil_list: matchingItem.sil_kvp || [],
        ta_list: matchingItem.acsd_kv_rms || [],
        ti_list: (windingPrefix === "at") ? (matchingItem.acld_kv_rms || []) : []
    };
}

// Popula os dropdowns baseados na classe de tensão
async function populateIsolationDropdowns(enrolamentoPrefixo, classeTensaoValue) {
    // Certifica que os dados estão carregados
    await loadIsolationLevelData();
    
    // Mapeia prefixos para nomes legíveis
    const prefixToName = {
        'at': 'AT',
        'bt': 'BT',
        'terciario': 'Terciário'
    };
    const enrolamentoName = prefixToName[enrolamentoPrefixo] || enrolamentoPrefixo;
    
    // Obtém o valor da norma selecionada
    const normaSelect = document.getElementById('norma_iso');
    const selectedNorma = normaSelect ? normaSelect.value : 'IEC';
    
    console.log(`[insulation_levels] Populando dropdowns para ${enrolamentoName} com classe ${classeTensaoValue}kV, norma ${selectedNorma}`);
    console.log(`[insulation_levels] Classe de Tensão para ${enrolamentoName}: ${classeTensaoValue}`);
    console.log(`[insulation_levels] Norma Selecionada: ${selectedNorma}`);
    
    // Obtém os dropdowns
    const nbiDropdown = document.getElementById(`nbi_${enrolamentoPrefixo}`);
    const silDropdown = document.getElementById(`sil_${enrolamentoPrefixo}`);
    const taDropdown = document.getElementById(`teste_tensao_aplicada_${enrolamentoPrefixo}`);
    const tiDropdown = document.getElementById(`teste_tensao_induzida_${enrolamentoPrefixo}`);
    
    // Carrega todas as opções disponíveis
    const optionsNbi = createOptionsForKey(selectedNorma, "bil_kvp", " kVp");
    
    // Para SIL, tratamento especial devido ao NA_SIL
    let optionsSil = [];
    const silDistinctRaw = getDistinctValuesForNorma(selectedNorma, "sil_kvp");
    if (silDistinctRaw.length > 0) {
        optionsSil = silDistinctRaw.map(val => ({
            label: `${val} kVp`,
            value: String(val)
        }));
    }
    
    // Para Tensão Aplicada
    const optionsTa = createOptionsForKey(selectedNorma, "acsd_kv_rms", " kVrms");
    
    // Para Tensão Induzida
    let optionsTi = [];
    if (enrolamentoPrefixo === "at") {
        const acldDistinct = getDistinctValuesForNorma(selectedNorma, "acld_kv_rms");
        const acsdDistinct = getDistinctValuesForNorma(selectedNorma, "acsd_kv_rms");
        const combinedTiRaw = [...new Set([...acldDistinct, ...acsdDistinct])].sort((a, b) => Number(a) - Number(b));
        optionsTi = combinedTiRaw.map(val => ({
            label: `${val} kVrms`,
            value: String(val)
        }));
    }
    
    // Se temos uma classe de tensão específica, priorizamos seus valores
    if (classeTensaoValue) {
        const levelData = getIsolationLevels(classeTensaoValue, enrolamentoPrefixo, selectedNorma);
        
        // Adiciona os valores específicos no início das listas de opções
        if (levelData.nbi_list.length > 0) {
            const specificNbi = levelData.nbi_list
                .filter(val => val !== null)
                .map(val => ({
                    label: `${val} kVp`,
                    value: String(val)
                }));
                
            if (specificNbi.length > 0) {
                // Remove duplicatas mantendo a ordem
                const seenNbi = new Set(specificNbi.map(opt => opt.value));
                optionsNbi = [
                    ...specificNbi,
                    ...optionsNbi.filter(opt => !seenNbi.has(opt.value))
                ];
            }
        }
        
        // Similar para SIL
        if (levelData.sil_list.length > 0 && levelData.sil_list[0] !== "NA_SIL") {
            const specificSil = levelData.sil_list
                .filter(val => val !== null && val !== "NA_SIL")
                .map(val => ({
                    label: `${val} kVp`,
                    value: String(val)
                }));
                
            if (specificSil.length > 0) {
                const seenSil = new Set(specificSil.map(opt => opt.value));
                optionsSil = [
                    ...specificSil,
                    ...optionsSil.filter(opt => !seenSil.has(opt.value))
                ];
            }
        }
        
        // Similar para TA
        if (levelData.ta_list.length > 0) {
            const specificTa = levelData.ta_list
                .filter(val => val !== null)
                .map(val => ({
                    label: `${val} kVrms`,
                    value: String(val)
                }));
                
            if (specificTa.length > 0) {
                const seenTa = new Set(specificTa.map(opt => opt.value));
                optionsTa = [
                    ...specificTa,
                    ...optionsTa.filter(opt => !seenTa.has(opt.value))
                ];
            }
        }
        
        // Similar para TI (apenas para AT)
        if (enrolamentoPrefixo === "at" && levelData.ti_list.length > 0) {
            const specificTi = levelData.ti_list
                .filter(val => val !== null)
                .map(val => ({
                    label: `${val} kVrms`,
                    value: String(val)
                }));
                
            if (specificTi.length > 0) {
                const seenTi = new Set(specificTi.map(opt => opt.value));
                optionsTi = [
                    ...specificTi,
                    ...optionsTi.filter(opt => !seenTi.has(opt.value))
                ];
            }
        }
    }
    
    // Popula os dropdowns
    populateDropdown(nbiDropdown, optionsNbi);
    console.log(`[insulation_levels] Opções NBI para ${enrolamentoName}:`, optionsNbi);
    populateDropdown(silDropdown, optionsSil);
    console.log(`[insulation_levels] Opções SIL para ${enrolamentoName}:`, optionsSil);
    populateDropdown(taDropdown, optionsTa);
    console.log(`[insulation_levels] Opções TA para ${enrolamentoName}:`, optionsTa);
    populateDropdown(tiDropdown, optionsTi);
    console.log(`[insulation_levels] Opções TI para ${enrolamentoName}:`, optionsTi);
    
    // Configura visibilidade do SIL com base na classe de tensão
    const silCol = document.getElementById(`sil_${enrolamentoPrefixo}_col`);
    if (silCol) {
        // SIL é aplicável apenas para classes de tensão acima de certos valores
        // IEEE: SIL é aplicável para classes >= 69.0 kV
        // IEC/NBR: SIL é aplicável para classes >= 72.5 kV
        const threshold = selectedNorma === "IEEE" ? 69.0 : 72.5;
        silCol.style.display = (classeTensaoValue && Number(classeTensaoValue) >= threshold) ? "" : "none";
    }
}

// Função auxiliar para popular um dropdown com opções
function populateDropdown(dropdown, options) {
    if (!dropdown) return;
    
    // Salva o valor selecionado atual
    const currentValue = dropdown.value;
    
    // Limpa o dropdown
    dropdown.innerHTML = '';
    
    // Adiciona a opção padrão "Selecione"
    const defaultOption = document.createElement('option');
    defaultOption.value = "";
    defaultOption.disabled = true;
    defaultOption.selected = !currentValue;
    defaultOption.textContent = "Selecione";
    dropdown.appendChild(defaultOption);
    
    // Adiciona as opções
    options.forEach(option => {
        const optElement = document.createElement('option');
        optElement.value = option.value;
        optElement.textContent = option.label;
        optElement.selected = option.value === currentValue;
        dropdown.appendChild(optElement);
    });
    
    // Se o valor atual não está mais nas opções, seleciona o padrão
    if (currentValue && !dropdown.value) {
        dropdown.value = "";
    }
}

// Configura os event listeners para atualizar os dropdowns quando a classe de tensão mudar
function setupIsolationDropdownListeners() {
    const classeTensaoDropdowns = [
        { prefix: 'at', dropdown: 'classe_tensao_at' },
        { prefix: 'bt', dropdown: 'classe_tensao_bt' },
        { prefix: 'terciario', dropdown: 'classe_tensao_terciario' }
    ];
    
    // Event listener para a norma
    const normaSelect = document.getElementById('norma_iso');
    if (normaSelect) {
        normaSelect.addEventListener('change', async () => {
            console.log('[insulation_levels] Norma alterada, atualizando todos os dropdowns de isolamento');
            
            // Atualiza todos os dropdowns quando a norma muda
            for (const item of classeTensaoDropdowns) {
                const classeTensaoEl = document.getElementById(item.dropdown);
                if (classeTensaoEl) {
                    const classeTensaoValue = classeTensaoEl.value;
                    if (classeTensaoValue) {
                        await populateIsolationDropdowns(item.prefix, classeTensaoValue);
                    }
                }
            }
        });
    }
    
    // Event listeners para as classes de tensão
    classeTensaoDropdowns.forEach(item => {
        const dropdown = document.getElementById(item.dropdown);
        if (dropdown) {
            dropdown.addEventListener('change', async (event) => {
                const classeTensaoValue = event.target.value;
                console.log(`[insulation_levels] Classe tensão ${item.prefix} alterada para ${classeTensaoValue}`);
                await populateIsolationDropdowns(item.prefix, classeTensaoValue);
            });
        }
    });
}

// Inicializa todos os dropdowns de isolamento
async function initializeIsolationDropdowns() {
    console.log('[insulation_levels] Iniciando carregamento de níveis de isolamento...');
    
    // Carrega os dados de isolamento
    await loadIsolationLevelData();
    
    // Inicializa os dropdowns com todas as opções disponíveis
    const enrolamentoPrefixos = ['at', 'bt', 'terciario'];
    console.log('[insulation_levels] Populando dropdowns para enrolamentos:', enrolamentoPrefixos);
    
    for (const prefixo of enrolamentoPrefixos) {
        const classeTensaoEl = document.getElementById(`classe_tensao_${prefixo}`);
        if (classeTensaoEl) {
            const classeTensaoValue = classeTensaoEl.value;
            console.log(`[insulation_levels] Inicializando dropdowns para ${prefixo} com classe de tensão: ${classeTensaoValue || 'nenhuma selecionada'}`);
            await populateIsolationDropdowns(prefixo, classeTensaoValue);
        } else {
            console.log(`[insulation_levels] Elemento classe_tensao_${prefixo} não encontrado`);
        }
    }
    
    // Configura os listeners para atualizações
    setupIsolationDropdownListeners();
    
    console.log('[insulation_levels] ✅ Dropdowns de isolamento inicializados com sucesso');
}

// Função para controlar a visibilidade dos campos de neutro
function toggleNeutralFieldsVisibility(enrolamentoPrefixo, conexaoValue) {
    const neutralFieldsRow = document.getElementById(`${enrolamentoPrefixo}_neutral_fields_row`);
    if (neutralFieldsRow) {
        // Exibe os campos de neutro apenas se a conexão for 'Yn' (estrela aterrada)
        neutralFieldsRow.style.display = (conexaoValue === 'estrela') ? '' : 'none';
    }
}

// Exporta as funções para uso global
window.isolationLevels = {
    init: initializeIsolationDropdowns,
    populateDropdowns: populateIsolationDropdowns,
    loadData: loadIsolationLevelData,
    toggleNeutralFields: toggleNeutralFieldsVisibility
};

// Exporta as funções para importação direta
export {
    initializeIsolationDropdowns,
    populateIsolationDropdowns,
    loadIsolationLevelData,
    toggleNeutralFieldsVisibility
};
