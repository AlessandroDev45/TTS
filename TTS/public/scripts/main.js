// public/scripts/main.js - Versão Atualizada para Roteamento SPA

import { waitForApiSystem, apiDataSystem, setupApiFormPersistence, collectFormData, fillFormWithData, handleDataPropagation } from './api_persistence.js';
document.addEventListener('DOMContentLoaded', async () => { // Tornar o listener DOMContentLoaded assíncrono
    // --- Existing Functionality (Preserved and Integrated) ---
    // Theme Toggle
    const themeToggle = document.getElementById('theme-toggle');
    const themeToggleIcon = document.getElementById('theme-toggle-icon');
    const themeToggleText = document.getElementById('theme-toggle-text');
    const body = document.body;
    
    // Function to apply the selected theme
    function applyTheme(theme) {
        // Remove classes anteriores
        body.classList.remove('light-theme', 'dark-theme');

        // Aplica o atributo data-bs-theme para compatibilidade com Bootstrap
        body.setAttribute('data-bs-theme', theme);

        if (theme === 'dark') {
            body.classList.add('dark-theme');
            if (themeToggleIcon) themeToggleIcon.classList.replace('fa-sun', 'fa-moon');
            if (themeToggleText) themeToggleText.textContent = 'Tema Escuro';
        } else {
            body.classList.add('light-theme');
            if (themeToggleIcon) themeToggleIcon.classList.replace('fa-moon', 'fa-sun');
            if (themeToggleText) themeToggleText.textContent = 'Tema Claro';
        }
        localStorage.setItem('theme', theme);

        // Log para debug
        console.log(`[Theme] Tema aplicado: ${theme}, classes do body:`, body.className);
    }

    // Initialize theme based on localStorage or default to dark
    const storedTheme = localStorage.getItem('theme');
    applyTheme(storedTheme || 'dark');

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            let newTheme = body.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
            applyTheme(newTheme);
        });
    }

    // Modal for Clearing Fields
    const globalClearButton = document.getElementById('global-clear-button');
    const clearConfirmModalElement = document.getElementById('clearConfirmModal');
    let clearConfirmModalInstance;
    if (clearConfirmModalElement) {
        clearConfirmModalInstance = new bootstrap.Modal(clearConfirmModalElement);
    }
    const clearConfirmButton = document.getElementById('clear-confirm-button');

    if (globalClearButton && clearConfirmModalInstance) {
        globalClearButton.addEventListener('click', () => {
            clearConfirmModalInstance.show();
        });
    }

    if (clearConfirmButton && clearConfirmModalInstance) {
        clearConfirmButton.addEventListener('click', () => {
            const scopeElement = document.querySelector('input[name="clearScopeRadio"]:checked');
            if (scopeElement) {
                const scope = scopeElement.value;
                console.log(`Confirmado: Limpar ${scope}`);
                
                if (scope === 'current_module') {
                    const currentModuleHash = window.location.hash.substring(1);
                    const moduleToClear = currentModuleHash || 'transformer_inputs';
                    const event = new CustomEvent('clearModuleData', { detail: { module: moduleToClear } });
                    document.dispatchEvent(event);
                    console.log(`Event clearModuleData dispatched for module: ${moduleToClear}`);
                } else if (scope === 'all_modules') {
                    const event = new CustomEvent('clearAllModulesData');
                    document.dispatchEvent(event);
                    console.log("Event clearAllModulesData dispatched.");
                }
            }
            clearConfirmModalInstance.hide();
        });
    }
    
    // Usage Counter Simulation
    const usageValueElement = document.getElementById('usage-value');
    const usageBarElement = document.getElementById('usage-bar');
    const limitAlertDiv = document.getElementById('limit-alert-div');
    const MAX_USAGE = 1000; // Example limit
    let currentUsage = 0; // This should ideally be loaded/managed from a persistent state or backend

    function updateUsageDisplay() {
        if (usageValueElement) usageValueElement.textContent = currentUsage;
        if (usageBarElement) {
            const percentage = (currentUsage / MAX_USAGE) * 100;
            usageBarElement.style.width = `${Math.min(percentage, 100)}%`;
        }
        if (limitAlertDiv) {
            if (currentUsage >= MAX_USAGE) {
                limitAlertDiv.classList.remove('d-none');
            } else {
                limitAlertDiv.classList.add('d-none');
            }
        }
    }
    updateUsageDisplay();

    // --- SPA Routing Logic ---
    const mainContentArea = document.getElementById('main-content-area');
    // CORREÇÃO: O seletor agora aponta para o ID do div que contém os links de navegação.
    const navLinks = document.querySelectorAll('#navbarContent .nav-link[data-module]'); 
    
    const homeLink = document.getElementById('home-link');
    let currentModuleScriptTag = null;
    let currentLoadedModule = null;
    const moduleCache = new Map();

    // Função para limpar cache de módulos específicos
    window.clearModuleCache = function(moduleName) {
        if (moduleName) {
            moduleCache.delete(moduleName);
            console.log(`[clearModuleCache] Cache do módulo ${moduleName} limpo`);
        } else {
            moduleCache.clear();
            console.log(`[clearModuleCache] Cache de todos os módulos limpo`);
        }
    };

    function setActiveNavLink(moduleName) {
        navLinks.forEach(link => {
            if (link.dataset.module === moduleName) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }

    async function loadModulePage(moduleName, pushToHistory = true) {
        if (!moduleName) {
            console.warn('loadModulePage chamada sem moduleName. Usando transformer_inputs como padrão.');
            moduleName = 'transformer_inputs';
        }

        // Evita recarregar o mesmo módulo apenas se não for navegação do histórico
        if (currentLoadedModule === moduleName && pushToHistory) {
            console.log(`[main.js] Módulo ${moduleName} já está carregado. Ignorando.`);
            return;
        }

        // Limpa cache automaticamente se for um recarregamento (não pushToHistory)
        if (!pushToHistory && moduleCache.has(moduleName)) {
            moduleCache.delete(moduleName);
            console.log(`[main.js] Cache do módulo ${moduleName} limpo automaticamente para recarregamento`);
        }        // Caminhos para os arquivos HTML e JS
        const htmlFilePath = `pages/${moduleName}.html`;

        // Mostra um indicador de carregamento
        if (mainContentArea) {
            mainContentArea.innerHTML = `
                <div class="d-flex justify-content-center align-items-center" style="height: 200px;">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Carregando...</span>
                    </div>
                    <p class="ms-3 mb-0">Carregando módulo ${moduleName}...</p>
                </div>`;
        }

        try { // Outer try for HTML fetch
            const response = await fetch(htmlFilePath);
            if (!response.ok) {
                throw new Error(`Erro HTTP ${response.status} ao buscar ${htmlFilePath}`);
            }
            const htmlContent = await response.text();
            console.log(`[main.js] HTML carregado com sucesso para o módulo: ${moduleName}`);
            if (mainContentArea) mainContentArea.innerHTML = htmlContent;

            // Remove previous script tag if it exists (for fallback approach)
            if (currentModuleScriptTag) {
                 // If we used scriptTag.remove() previously, we'd do it here.
                 // Since we didn't, just clear the reference.
                 currentModuleScriptTag = null;
            }

            try { // Inner try for script import
                // Verifica cache primeiro
                let module;
                if (moduleCache.has(moduleName)) {
                    module = moduleCache.get(moduleName);
                    console.log(`[main.js] Módulo ${moduleName}.js carregado do cache.`, module);
                } else {
                    // SEMPRE adiciona timestamp para evitar cache do browser
                    const scriptFilePath = `/scripts/${moduleName}.js`; // Define scriptFilePath
                    const scriptFilePathWithCache = `${scriptFilePath}?t=${Date.now()}`;
                    console.log(`[main.js] Tentando carregar módulo de: ${scriptFilePathWithCache}`);
                    // Adiciona log antes de tentar o import dinâmico
                    console.log(`[main.js] Caminho do script para import dinâmico: ${window.location.origin}${scriptFilePathWithCache}`);
                    module = await import(scriptFilePathWithCache);
                    moduleCache.set(moduleName, module);
                    console.log(`[main.js] Módulo ${moduleName}.js carregado dinamicamente com timestamp.`, module);
                }

                currentLoadedModule = moduleName;
                // Dispatch event after successful module load/import
                document.dispatchEvent(new CustomEvent('moduleContentLoaded', { detail: { moduleName } }));
                console.log(`[main.js] Evento moduleContentLoaded disparado para ${moduleName}`);

                // Update UI and history after successful load
                setActiveNavLink(moduleName);
                if (pushToHistory) {
                    history.pushState({ module: moduleName }, `${moduleName.replace('_', ' ')} - Simulador`, `#${moduleName}`);
                } else {
                    document.title = `${moduleName.replace('_', ' ')} - Simulador`;
                }            } catch (scriptLoadError) { // Catch for inner try (script loading)
                console.error(`[main.js] Erro ao carregar o script do módulo ${moduleName} em scripts/${moduleName}.js:`, scriptLoadError);
                // Remove from cache in case of error to force reload next time
                if (moduleCache.has(moduleName)) {
                    moduleCache.delete(moduleName);
                    console.log(`[main.js] Módulo ${moduleName} removido do cache devido ao erro`);
                }

                // If it's a network error or similar, try script tag fallback
                if (scriptLoadError instanceof TypeError && scriptLoadError.message.includes('Failed to fetch dynamically imported module')) {
                     console.log(`[main.js] Tentando abordagem alternativa (script tag) para carregar o módulo ${moduleName}`);
                     try {
                         const scriptTag = document.createElement('script');
                         scriptTag.src = `/scripts/${moduleName}.js?t=${Date.now()}`;
                         scriptTag.type = 'module';
                         document.head.appendChild(scriptTag);
                         currentModuleScriptTag = scriptTag; // Store the tag reference
                         console.log(`[main.js] Script tag criada como fallback para ${moduleName}`);
                         currentLoadedModule = moduleName; // Update loaded module even on fallback attempt

                         // Wait for script to load and execute (approximation)
                         scriptTag.onload = () => {
                             document.dispatchEvent(new CustomEvent('moduleContentLoaded', { detail: { moduleName } }));
                             console.log(`[main.js] Evento disparado via fallback (onload) para ${moduleName}`);
                             // Update UI and history after successful fallback load
                             setActiveNavLink(moduleName);
                             if (pushToHistory) {

                                 history.pushState({ module: moduleName }, `${moduleName.replace('_', ' ')} - Simulador`, `#${moduleName}`);
                             } else {
                                 document.title = `${moduleName.replace('_', ' ')} - Simulador`;
                             }
                         };                         scriptTag.onerror = (e) => {
                             console.error(`[main.js] Erro ao carregar script tag fallback para ${moduleName} em ${scriptTag.src}:`, e);
                             // Dispatch error event or handle failure
                             // Maybe show an error message in mainContentArea?
                             if (mainContentArea) {
                                 mainContentArea.innerHTML = `<div class="alert alert-danger m-3" style="background-color: var(--background-card); color: var(--text-light); border-left: 4px solid var(--danger-color);">
                                                                     <i class="fas fa-exclamation-circle me-2"></i> Erro ao carregar o script do módulo: ${moduleName} via fallback. Verifique o console.
                                                                 </div>`;
                             }
                             setActiveNavLink(null); // Clear active link on failure
                         };

                     } catch (scriptTagError) {
                         console.error(`[main.js] Erro ao usar fallback para ${moduleName}:`, scriptTagError);
                          if (mainContentArea) {
                             mainContentArea.innerHTML = `<div class="alert alert-danger m-3" style="background-color: var(--background-card); color: var(--text-light); border-left: 4px solid var(--danger-color);">
                                                             <i class="fas fa-exclamation-circle me-2"></i> Erro crítico ao tentar carregar o módulo: ${moduleName}. Verifique o console.
                                                         </div>`;
                         }
                         setActiveNavLink(null); // Clear active link on failure
                     }
                } 
                else {
                    // Handle other script loading errors (SyntaxError, ReferenceError, etc.)
                     if (mainContentArea) {
                         mainContentArea.innerHTML = `<div class="alert alert-danger m-3" style="background-color: var(--background-card); color: var(--text-light); border-left: 4px solid var(--danger-color);">
                                                         <i class="fas fa-exclamation-circle me-2"></i> Erro ao executar o script do módulo: ${moduleName}. Verifique o console.
                                                     </div>`;
                     }
                     setActiveNavLink(null); // Clear active link on failure
                }
            } // End of inner try/catch (script loading)


        } catch (error) { // Catch for outer try (HTML loading)
            console.error(`Erro ao carregar o HTML do módulo ${moduleName}:`, error);
            if (mainContentArea) {
                mainContentArea.innerHTML = `<div class="alert alert-danger m-3" style="background-color: var(--background-card); color: var(--text-light); border-left: 4px solid var(--danger-color);">
                                                <i class="fas fa-exclamation-circle me-2"></i> Erro ao carregar o HTML do módulo: ${moduleName}. Verifique o console.
                                            </div>`;
            }
            setActiveNavLink(null); // Clear active link on failure
        }
    }

    navLinks.forEach(link => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            const moduleName = link.dataset.module;
            if (moduleName) {
                const currentHashModule = window.location.hash.substring(1);
                if (moduleName !== currentHashModule) {
                    loadModulePage(moduleName);
                } else {
                    console.log("Módulo já ativo:", moduleName);
                }
            }
            // Para fechar o menu hamburger em mobile após clicar
            const navbarToggler = document.querySelector('.navbar-toggler');
            const navbarCollapse = document.querySelector('#navbarContent');
            if (navbarToggler && navbarCollapse.classList.contains('show')) {
                const bsCollapse = new bootstrap.Collapse(navbarCollapse, { toggle: false });
                bsCollapse.hide();
            }
        });
    });
    
    if (homeLink) {
        homeLink.addEventListener('click', (event) => {
            event.preventDefault();
            loadModulePage('transformer_inputs', true);
            // Também fechar o menu hamburger em mobile
            const navbarToggler = document.querySelector('.navbar-toggler');
            const navbarCollapse = document.querySelector('#navbarContent');
            if (navbarToggler && navbarCollapse.classList.contains('show')) {
                const bsCollapse = new bootstrap.Collapse(navbarCollapse, { toggle: false });
                bsCollapse.hide();
            }
        });
    }

    window.addEventListener('popstate', (event) => {
        let moduleToLoad = 'transformer_inputs';
        if (event.state && event.state.module) {
            moduleToLoad = event.state.module;
        } else {
            const hash = window.location.hash.substring(1);
            if (hash) {
                const isValidModule = Array.from(navLinks).some(navLink => navLink.dataset.module === hash);
                if (isValidModule) {
                    moduleToLoad = hash;
                } else {
                    console.warn(`Módulo inválido no hash em popstate: ${hash}. Carregando padrão.`);
                }
            }
        }
        loadModulePage(moduleToLoad, false);
    });    // Função para verificar se existem dados salvos
    async function checkForExistingData() {
        try {
            const apiSystem = await waitForApiSystem();
            if (!apiSystem) return false;

            await apiSystem.init();

            // Verifica se há dados no store principal (transformerInputs)
            const store = apiSystem.getStore('transformerInputs');
            const data = await store.getData();

            // Considera que há dados se formData existe e tem pelo menos um campo preenchido
            if (data && data.formData && Object.keys(data.formData).length > 0) {
                // Verifica se há pelo menos um valor não-nulo/não-vazio
                const hasData = Object.values(data.formData).some(value =>
                    value !== null && value !== undefined && value !== ''
                );
                return hasData;
            }

            return false;
        } catch (error) {
            console.error('[checkForExistingData] Erro ao verificar dados existentes:', error);
            return false;
        }
    }

    // Função para limpar todos os dados
    async function clearAllData() {
        try {
            const apiSystem = await waitForApiSystem();
            if (!apiSystem) return;

            // Lista de stores conhecidos para limpar
            const storesToClear = ['transformerInputs', 'losses', 'shortCircuit', 'history'];

            for (const storeId of storesToClear) {
                try {
                    const store = apiSystem.getStore(storeId);
                    await store.updateData({}); // Limpa o store
                    console.log(`[clearAllData] Store '${storeId}' limpo.`);
                } catch (error) {
                    console.warn(`[clearAllData] Erro ao limpar store '${storeId}':`, error);
                }
            }

            console.log('[clearAllData] Todos os dados foram limpos.');
        } catch (error) {
            console.error('[clearAllData] Erro ao limpar dados:', error);
        }
    }

    // Função para mostrar modal de inicialização
    async function showStartupModal() {
        return new Promise((resolve) => {
            const startupModalElement = document.getElementById('startupModal');
            if (!startupModalElement) {
                resolve('continue'); // Default se modal não existir
                return;
            }

            const startupModal = new bootstrap.Modal(startupModalElement);

            const continueButton = document.getElementById('continueProjectButton');
            const newProjectButton = document.getElementById('newProjectButton');

            const handleContinue = () => {
                startupModal.hide();
                resolve('continue');
            };

            const handleNewProject = async () => {
                startupModal.hide();
                await clearAllData();
                resolve('new');
            };

            // Remove listeners anteriores se existirem
            if (continueButton) {
                continueButton.replaceWith(continueButton.cloneNode(true));
                document.getElementById('continueProjectButton').addEventListener('click', handleContinue);
            }

            if (newProjectButton) {
                newProjectButton.replaceWith(newProjectButton.cloneNode(true));
                document.getElementById('newProjectButton').addEventListener('click', handleNewProject);
            }

            startupModal.show();
        });
    }

    async function initializeAppRouting() { // Tornar a função assíncrona
        // Aguarda o sistema de persistência estar disponível
        console.log('[initializeAppRouting] Aguardando sistema de persistência...');
        const apiSystem = await waitForApiSystem(); // Usa a função importada diretamente

        if (apiSystem) {
            console.log('[initializeAppRouting] Inicializando sistema de persistência...');
            await apiSystem.init();
            console.log('[initializeAppRouting] Sistema de persistência inicializado.');
        } else {
            console.warn('[initializeAppRouting] Sistema de persistência não encontrado após aguardar.');
        }

        // Verifica se existem dados salvos e mostra modal se necessário
        const hasExistingData = await checkForExistingData();
        if (hasExistingData) {
            console.log('[initializeAppRouting] Dados existentes encontrados. Mostrando modal de escolha...');
            const userChoice = await showStartupModal();
            console.log(`[initializeAppRouting] Usuário escolheu: ${userChoice}`);
        }

        const initialHash = window.location.hash.substring(1);
        let moduleToLoadOnStart = 'transformer_inputs';

        if (initialHash) {
            const isValidModule = Array.from(navLinks).some(navLink => navLink.dataset.module === initialHash);
            if (isValidModule) {
                moduleToLoadOnStart = initialHash;
                loadModulePage(moduleToLoadOnStart, false);
            } else {
                console.warn(`Módulo inválido no hash da URL inicial: '${initialHash}'. Carregando módulo padrão.`);
                loadModulePage(moduleToLoadOnStart, true);
            }
        } else {
            loadModulePage(moduleToLoadOnStart, true);
        }
    }

    initializeAppRouting();

    // ===== FUNÇÕES GLOBAIS PARA DEBUG =====
    // Disponibiliza globalmente para debug (dentro do escopo onde loadModulePage existe)
    window.loadModulePage = loadModulePage;
});

// Função global para limpar cache de módulos (funciona no console do navegador)
window.clearModuleCache = function(moduleNames) {
    if (typeof moduleNames === 'string') {
        moduleNames = [moduleNames];
    }

    console.log(`[clearModuleCache] Iniciando limpeza para: ${moduleNames.join(', ')}`);

    moduleNames.forEach(moduleName => {
        // Limpa cache do localStorage
        const keys = Object.keys(localStorage);
        let removedCount = 0;

        keys.forEach(key => {
            if (key.includes(moduleName)) {
                localStorage.removeItem(key);
                console.log(`[clearModuleCache] Removido do localStorage: ${key}`);
                removedCount++;
            }
        });

        // Dispara evento de limpeza
        const event = new CustomEvent('clearModuleData', { detail: { module: moduleName } });
        document.dispatchEvent(event);

        console.log(`[clearModuleCache] Módulo '${moduleName}': ${removedCount} itens removidos`);
    });

    const result = `✅ Cache limpo para: ${moduleNames.join(', ')}`;
    console.log(`[clearModuleCache] ${result}`);
    return result;
};

// Função para limpar todos os caches
window.clearAllCache = function() {
    const allModules = ['history', 'standards', 'transformerInputs', 'losses', 'impulse',
                       'appliedVoltage', 'inducedVoltage', 'shortCircuit', 'temperatureRise', 'dielectricAnalysis'];
    return window.clearModuleCache(allModules);
};

// Função para mostrar ajuda
window.showCacheHelp = function() {
    console.log(`
🔧 COMANDOS DE CACHE DISPONÍVEIS (execute no console do navegador):

1. Limpar módulo específico:
   clearModuleCache('history')
   clearModuleCache('standards')

2. Limpar múltiplos módulos:
   clearModuleCache(['history', 'standards'])

3. Limpar todos os caches:
   clearAllCache()

4. Mostrar esta ajuda:
   showCacheHelp()

⚠️ IMPORTANTE: Execute estes comandos no CONSOLE DO NAVEGADOR (F12),
   NÃO no terminal do Windows!
`);
    return "Ajuda exibida no console";
};

// ===== LIMPEZA AUTOMÁTICA DE CACHE =====

// Limpa automaticamente cache antigo na inicialização
function autoCleanCache() {
    const cacheVersion = '1.0.0';
    const lastVersion = localStorage.getItem('tts_cache_version');

    if (lastVersion !== cacheVersion) {
        console.log('[autoCleanCache] Nova versão detectada, limpando cache automaticamente...');

        // Limpa todos os caches automaticamente
        const keys = Object.keys(localStorage);
        let removedCount = 0;

        keys.forEach(key => {
            if (key.startsWith('store_') || key.includes('cache') || key.includes('session')) {
                localStorage.removeItem(key);
                removedCount++;
            }
        });

        // Atualiza versão do cache
        localStorage.setItem('tts_cache_version', cacheVersion);

        console.log(`[autoCleanCache] ✅ ${removedCount} itens de cache removidos automaticamente`);
        console.log('[autoCleanCache] Cache limpo e atualizado para nova versão');
    } else {
        console.log('[autoCleanCache] Cache já está atualizado');
    }
}

// Executa limpeza automática na inicialização
autoCleanCache();

console.log("🔧 Sistema de cache automático ativo. Cache será limpo automaticamente quando necessário.");
document.addEventListener('DOMContentLoaded', function() {
    const currentYearSpan = document.getElementById('current-year');
    if (currentYearSpan) {
        currentYearSpan.textContent = new Date().getFullYear();
    }
});