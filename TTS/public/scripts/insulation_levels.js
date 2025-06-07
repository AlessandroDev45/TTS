// public/scripts/insulation_levels.js

let isolationLevelsCache = null;

async function loadIsolationLevelData() {
    if (isolationLevelsCache) return isolationLevelsCache;
    try {
        const response = await fetch('/assets/tabela.json'); // Ajuste o caminho se sua estrutura for diferente
        if (!response.ok) throw new Error(`HTTP ${response.status} ao carregar tabela.json`);
        isolationLevelsCache = await response.json();
        console.log('[insulation_levels] tabela.json carregada.');
        return isolationLevelsCache;
    } catch (error) {
        console.error('[insulation_levels] Erro ao carregar tabela.json:', error);
        return null;
    }
}

function populateDropdown(dropdownElement, options, addSelectPlaceholder = true, selectedValue = null) {
    if (!dropdownElement) return;
    
    const previousValue = selectedValue !== null ? selectedValue : dropdownElement.value;
    dropdownElement.innerHTML = '';

    if (addSelectPlaceholder) {
        const placeholder = document.createElement('option');
        placeholder.value = "";
        placeholder.textContent = "Selecione...";
        // placeholder.disabled = true; // Não desabilitar para permitir "limpar" a seleção
        dropdownElement.appendChild(placeholder);
    }

    options.forEach(opt => {
        const optionEl = document.createElement('option');
        optionEl.value = String(opt.value); // Garante que o valor seja string
        optionEl.textContent = opt.label;
        dropdownElement.appendChild(optionEl);
    });

    // Tenta restaurar o valor anterior ou o placeholder
    if (previousValue && Array.from(dropdownElement.options).some(o => o.value === String(previousValue))) {
        dropdownElement.value = String(previousValue);
    } else if (addSelectPlaceholder) {
        dropdownElement.selectedIndex = 0;
    }
     // Se nenhum valor foi restaurado e não há placeholder, seleciona a primeira opção válida se houver
    else if (!dropdownElement.value && dropdownElement.options.length > 0 && !addSelectPlaceholder) {
        dropdownElement.selectedIndex = 0;
    }
}


async function populateClasseTensaoDropdowns() {
    await loadIsolationLevelData();
    if (!isolationLevelsCache || !isolationLevelsCache.insulation_levels) {
        console.error('[insulation_levels] Dados de isolamento não disponíveis para classes de tensão.');
        return;
    }

    const normaSelect = document.getElementById('norma_iso');
    const selectedNorma = (normaSelect && normaSelect.value) ? normaSelect.value.toUpperCase() : 'IEC';

    const umKvValues = [...new Set(
        isolationLevelsCache.insulation_levels
            .filter(item => item.standard && item.standard.toUpperCase().startsWith(selectedNorma))
            .map(item => Number(item.um_kv))
    )].sort((a, b) => a - b);

    const prefixes = ['at', 'bt', 'terciario'];
    prefixes.forEach(prefix => {
        const dropdown = document.getElementById(`classe_tensao_${prefix}`);
        if (dropdown) {
            const options = umKvValues.map(val => ({ label: `${val} kV`, value: String(val) }));
            populateDropdown(dropdown, options, true, dropdown.value); // Passa o valor atual para tentar manter
        }
    });
    // console.log(`[insulation_levels] Dropdowns de Classe de Tensão (re)populados para norma ${selectedNorma}.`);
}

function getIsolationLevelsForClass(umKvValue, standard) {
    if (!isolationLevelsCache || !isolationLevelsCache.insulation_levels || !umKvValue) {
        return { bil_kvp: [], sil_kvp: [], acsd_kv_rms: [], acld_kv_rms: [] }; // Retorna vazio se não houver classe
    }
    const numericUmKv = Number(umKvValue);
    const item = isolationLevelsCache.insulation_levels.find(
        i => i.standard && i.standard.toUpperCase().startsWith(standard.toUpperCase()) && Number(i.um_kv) === numericUmKv
    );
    return item || { bil_kvp: [], sil_kvp: [], acsd_kv_rms: [], acld_kv_rms: [] };
}

async function populateDependentIsolationDropdowns(enrolamentoPrefixo, classeTensaoValue) {
    console.log(`[insulation_levels] populateDependentIsolationDropdowns para ${enrolamentoPrefixo}, classe: ${classeTensaoValue}`);
    await loadIsolationLevelData(); // Garante que tabela.json está carregado
    if (!isolationLevelsCache || !isolationLevelsCache.insulation_levels) {
        console.error('[insulation_levels] Dados de isolamento não disponíveis para dependentes.');
        return;
    }

    const normaSelect = document.getElementById('norma_iso');
    const selectedNorma = (normaSelect && normaSelect.value) ? normaSelect.value : 'IEC';
    console.log(`[insulation_levels] Norma selecionada: ${selectedNorma}`);

    // Obter a lista de classes de tensão (um_kv) para a norma selecionada
    const umKvValues = [...new Set(
        isolationLevelsCache.insulation_levels
            .filter(item => item.standard && item.standard.toUpperCase().startsWith(selectedNorma.toUpperCase()))
            .map(item => Number(item.um_kv))
    )].sort((a, b) => a - b);
    const classeTensaoOptions = umKvValues.map(val => ({ label: `${val} kV`, value: String(val) }));
    console.log(`[insulation_levels] Opções de Classe Tensão geradas:`, classeTensaoOptions);

    const levels = getIsolationLevelsForClass(classeTensaoValue, selectedNorma);

    const nbiDropdown = document.getElementById(`nbi_${enrolamentoPrefixo}`);
    const silDropdown = document.getElementById(`sil_${enrolamentoPrefixo}`);
    const taDropdown = document.getElementById(`teste_tensao_aplicada_${enrolamentoPrefixo}`);
    const tiDropdown = enrolamentoPrefixo === 'at' ? document.getElementById(`teste_tensao_induzida_at`) : null;
    
    // Novos dropdowns para Classe Neutro, NBI Neutro e SIL Neutro
    const classeNeutroDropdown = document.getElementById(`tensao_bucha_neutro_${enrolamentoPrefixo}`);
    const nbiNeutroDropdown = document.getElementById(`nbi_neutro_${enrolamentoPrefixo}`);
    const silNeutroDropdown = document.getElementById(`sil_neutro_${enrolamentoPrefixo}`);

    const nbiOptions = (levels.bil_kvp || []).map(v => ({ label: `${v} kVp`, value: String(v) }));
    let silOptions = [{ label: "Não Aplicável", value: "" }]; // Default

    // Para IEEE, usar BSL (bsl_kvp), para IEC/NBR usar SIL (sil_kvp)
    const isIEEE = selectedNorma.toUpperCase().includes("IEEE");
    const silData = isIEEE ? levels.bsl_kvp : levels.sil_kvp;
    if (silData && silData.length > 0 && silData[0] !== null && silData[0] !== "NA_SIL") {
        silOptions = silData.map(v => ({ label: `${v} kVp`, value: String(v) }));
    }
    const taOptions = (levels.acsd_kv_rms || []).map(v => ({ label: `${v} kVrms`, value: String(v) }));
    let tiOptions = [];
    if (enrolamentoPrefixo === 'at' && levels.acld_kv_rms) {
        tiOptions = levels.acld_kv_rms.map(v => ({ label: `${v} kVrms`, value: String(v) }));
    }

    // Para neutro: Popula Classe Neutro com as mesmas opções de Classe Tensão
    if (classeNeutroDropdown) {
        console.log(`[insulation_levels] Populando dropdown de Classe Neutro para ${enrolamentoPrefixo}. Elemento encontrado.`);
        populateDropdown(classeNeutroDropdown, classeTensaoOptions, true, classeNeutroDropdown.value);
        console.log(`[insulation_levels] Dropdown de Classe Neutro para ${enrolamentoPrefixo} populado.`);
    } else {
        console.warn(`[insulation_levels] Dropdown de Classe Neutro para ${enrolamentoPrefixo} (ID tensao_bucha_neutro_${enrolamentoPrefixo}) não encontrado.`);
    }

    // Para NBI Neutro e SIL Neutro: A lógica de derivação ou busca em tabela.json precisa ser implementada
    // Por ora, vamos popular com base na CLASSE NEUTRO selecionada (se houver)
    // Isso requer um listener no dropdown de Classe Neutro, que será adicionado depois.
    // Por enquanto, populamos com opções vazias ou baseadas na classe principal como fallback.
    // A lógica correta seria: obter a classe neutro selecionada, buscar os níveis de isolamento para essa classe, e popular NBI/SIL Neutro.
    // Como placeholder, vamos popular com as mesmas opções do principal, mas isso NÃO é o comportamento final correto.
    // TODO: Implementar a lógica de dependência de NBI/SIL Neutro na Classe Neutro selecionada.
    const nbiNeutroOptions = nbiOptions; // Placeholder - DEVE DEPENDER DA CLASSE NEUTRO
    const silNeutroOptions = silOptions; // Placeholder - DEVE DEPENDER DA CLASSE NEUTRO

    populateDropdown(nbiDropdown, nbiOptions, true, nbiDropdown ? nbiDropdown.value : null);
    populateDropdown(silDropdown, silOptions, true, silDropdown ? silDropdown.value : null);
    populateDropdown(taDropdown, taOptions, true, taDropdown ? taDropdown.value : null);
    if (tiDropdown) populateDropdown(tiDropdown, tiOptions, true, tiDropdown.value);
    
    // Popula NBI Neutro e SIL Neutro (usando placeholders por enquanto)
    populateDropdown(nbiNeutroDropdown, nbiNeutroOptions, true, nbiNeutroDropdown ? nbiNeutroDropdown.value : null);
    populateDropdown(silNeutroDropdown, silNeutroOptions, true, silNeutroDropdown ? silNeutroDropdown.value : null);
    
    // Visibilidade do SIL principal
    const silCol = document.getElementById(`sil_${enrolamentoPrefixo}_col`);
    if (silCol) {
        // Thresholds corretos baseados nos dados disponíveis na tabela JSON
        // IEEE: BSL disponível a partir de 161 kV
        // IEC/NBR: SIL disponível a partir de 245 kV
        const isIEEE = selectedNorma.toUpperCase().includes("IEEE");
        const threshold = isIEEE ? 161.0 : 245.0;
        const umKvNum = parseFloat(classeTensaoValue);
        const showSil = umKvNum && umKvNum >= threshold && silOptions.length > 0 && !(silOptions.length === 1 && silOptions[0].value === "");
        silCol.style.display = showSil ? "block" : "none"; // Usar block ou ""
        if (!showSil && silDropdown) silDropdown.value = "";
    }
     // Visibilidade dos campos de neutro
    const conexaoDropdown = document.getElementById(`conexao_${enrolamentoPrefixo}`);
    if (conexaoDropdown) {
        toggleNeutralFieldsVisibility(enrolamentoPrefixo, conexaoDropdown.value);
    }
}


function setupIsolationDropdownListeners() {
    const normaSelect = document.getElementById('norma_iso');
    if (normaSelect) {
        if (normaSelect._listenerAttached) normaSelect.removeEventListener('change', normaSelect._eventHandler);
        const handler = async () => {
            console.log('[insulation_levels] Norma alterada, atualizando classes e dependentes.');
            await populateClasseTensaoDropdowns();
            const prefixes = ['at', 'bt', 'terciario'];
            for (const prefix of prefixes) {
                const classeDropdown = document.getElementById(`classe_tensao_${prefix}`);
                await populateDependentIsolationDropdowns(prefix, classeDropdown ? classeDropdown.value : null);
            }
        };
        normaSelect.addEventListener('change', handler);
        normaSelect._listenerAttached = true;
        normaSelect._eventHandler = handler;
    }

    const prefixes = ['at', 'bt', 'terciario'];
    prefixes.forEach(prefix => {
        const classeDropdown = document.getElementById(`classe_tensao_${prefix}`);
        if (classeDropdown) {
            if (classeDropdown._listenerAttached) classeDropdown.removeEventListener('change', classeDropdown._eventHandler);
            const handler = async (event) => {
                await populateDependentIsolationDropdowns(prefix, event.target.value);
            };
            classeDropdown.addEventListener('change', handler);
            classeDropdown._listenerAttached = true;
            classeDropdown._eventHandler = handler;
        }

        const conexaoDropdown = document.getElementById(`conexao_${prefix}`);
        if (conexaoDropdown) {
            if (conexaoDropdown._listenerAttached) conexaoDropdown.removeEventListener('change', conexaoDropdown._eventHandler);
            const handler = (event) => {
                toggleNeutralFieldsVisibility(prefix, event.target.value);
            };
            conexaoDropdown.addEventListener('change', handler);
            conexaoDropdown._listenerAttached = true;
            conexaoDropdown._eventHandler = handler;
        }

        // Listener para classe neutro para controlar visibilidade do SIL neutro
        const classeNeutroDropdown = document.getElementById(`tensao_bucha_neutro_${prefix}`);
        if (classeNeutroDropdown) {
            if (classeNeutroDropdown._listenerAttached) classeNeutroDropdown.removeEventListener('change', classeNeutroDropdown._eventHandler);
            const handler = () => {
                const conexaoDropdown = document.getElementById(`conexao_${prefix}`);
                if (conexaoDropdown) {
                    toggleNeutralFieldsVisibility(prefix, conexaoDropdown.value);
                }
            };
            classeNeutroDropdown.addEventListener('change', handler);
            classeNeutroDropdown._listenerAttached = true;
            classeNeutroDropdown._eventHandler = handler;
        }
    });
}

async function initializeIsolationDropdowns() {
    console.log('[insulation_levels] Inicializando dropdowns de isolamento...');
    await loadIsolationLevelData();
    await populateClasseTensaoDropdowns(); 

    const enrolamentoPrefixos = ['at', 'bt', 'terciario'];
    for (const prefixo of enrolamentoPrefixos) {
        const classeTensaoEl = document.getElementById(`classe_tensao_${prefixo}`);
        const classeTensaoValue = classeTensaoEl ? classeTensaoEl.value : null;
        await populateDependentIsolationDropdowns(prefixo, classeTensaoValue);
        const conexaoEl = document.getElementById(`conexao_${prefixo}`);
        if (conexaoEl) toggleNeutralFieldsVisibility(prefixo, conexaoEl.value);
    }
    setupIsolationDropdownListeners();
    console.log('[insulation_levels] ✅ Dropdowns de isolamento inicializados.');
}

function toggleNeutralFieldsVisibility(enrolamentoPrefixo, conexaoValue) {
    const neutralFieldsRow = document.getElementById(`${enrolamentoPrefixo}_neutral_fields_row`);
    const tensaoBuchaNeutroCol = document.getElementById(`tensao_bucha_neutro_${enrolamentoPrefixo}_col`);

    // Conexões que tipicamente têm neutro acessível e relevante para isolamento separado
    const hasNeutral = conexaoValue === 'estrela' || conexaoValue === 'ziguezague'; // 'estrela' corresponde a Yn, 'ziguezague' a Zn

    if (neutralFieldsRow) {
        neutralFieldsRow.style.display = hasNeutral ? "flex" : "none"; // 'flex' para .row
    }
    if (tensaoBuchaNeutroCol) {
        tensaoBuchaNeutroCol.style.display = hasNeutral ? "block" : "none"; // ou "flex" se for um .col
    }

    // Controlar visibilidade do SIL neutro baseado na tensão da classe neutro
    if (hasNeutral) {
        const classeNeutroDropdown = document.getElementById(`tensao_bucha_neutro_${enrolamentoPrefixo}`);
        const silNeutroDropdown = document.getElementById(`sil_neutro_${enrolamentoPrefixo}`);

        if (classeNeutroDropdown && silNeutroDropdown) {
            const normaSelect = document.getElementById('norma_iso');
            const selectedNorma = (normaSelect && normaSelect.value) ? normaSelect.value.toUpperCase() : 'IEC';
            const isIEEE = selectedNorma.includes("IEEE");
            const threshold = isIEEE ? 161.0 : 245.0;
            const classeNeutroValue = parseFloat(classeNeutroDropdown.value);

            // Mostrar/ocultar SIL neutro baseado no threshold de tensão
            const showSilNeutro = classeNeutroValue && classeNeutroValue >= threshold;

            // Controlar visibilidade da coluna inteira do SIL neutro (label + dropdown)
            const silNeutroCol = silNeutroDropdown.closest('.col-6');
            if (silNeutroCol) {
                silNeutroCol.style.display = showSilNeutro ? "block" : "none";
            } else {
                // Fallback: controlar apenas o dropdown se não encontrar a coluna
                silNeutroDropdown.style.display = showSilNeutro ? "block" : "none";
            }

            if (!showSilNeutro) {
                silNeutroDropdown.value = "";
            }
        }
    }

    // Limpar valores se os campos forem ocultados
    if (!hasNeutral) {
        const idsToClear = [
            `tensao_bucha_neutro_${enrolamentoPrefixo}`,
            `nbi_neutro_${enrolamentoPrefixo}`,
            `sil_neutro_${enrolamentoPrefixo}`
        ];
        idsToClear.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = "";
        });
    }
}

// Exporta para uso global e módulos
window.isolationLevels = {
    init: initializeIsolationDropdowns,
    populateDependentDropdowns: populateDependentIsolationDropdowns,
    populateClasseTensao: populateClasseTensaoDropdowns,
    toggleNeutralFields: toggleNeutralFieldsVisibility
};
export { initializeIsolationDropdowns, populateDependentIsolationDropdowns, populateClasseTensaoDropdowns, toggleNeutralFieldsVisibility };