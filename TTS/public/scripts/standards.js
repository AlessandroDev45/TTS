// public/scripts/standards.js - ATUALIZADO (Combinado com abas)

import { apiDataSystem, collectFormData, fillFormWithData } from './api_persistence.js'; // Importa o sistema de persistência e funções auxiliares

// Obtém o store de normas
const standardsStore = apiDataSystem.getStore('standards');

// --- Lógica para ABA de Consulta de Normas ---

// Exemplo: Simulação de carregamento de categorias
const loadStandardsCategories = () => {
    const container = document.getElementById('standards-categories-container');
    if (container) {
        container.innerHTML = `
            <div class="list-group list-group-flush">
                <a href="#" class="list-group-item list-group-item-action list-group-item-dark active">Todas</a>
                <a href="#" class="list-group-item list-group-item-action list-group-item-dark">Dielétrico</a>
                <a href="#" class="list-group-item list-group-item-action list-group-item-dark">Transformador</a>
                <a href="#" class="list-group-item list-group-item-action list-group-item-dark">Ensaios</a>
                <a href="#" class="list-group-item list-group-item-action list-group-item-dark">Segurança</a>
            </div>
        `;
        container.querySelectorAll('.list-group-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                container.querySelectorAll('.list-group-item').forEach(li => li.classList.remove('active'));
                e.target.classList.add('active');
                console.log(`Categoria selecionada: ${e.target.textContent}`);
            });
        });
    }
};

// Exemplo: Simulação de carregamento da lista de normas disponíveis (sidebar de consulta)
const loadStandardsNavSidebar = () => {
    const sidebar = document.getElementById('standards-nav-sidebar');
    if (sidebar) {
        sidebar.innerHTML = `
            <div class="list-group list-group-flush">
                <a href="#" class="list-group-item list-group-item-action list-group-item-dark">NBR 5356-1:2007</a>
                <a href="#" class="list-group-item list-group-item-action list-group-item-dark">NBR 5356-3:2014</a>
                <a href="#" class="list-group-item list-group-item-action list-group-item-dark">IEC 60076-1:2011</a>
                <a href="#" class="list-group-item list-group-item-action list-group-item-dark">IEEE C57.12.00:2015</a>
            </div>
        `;
        sidebar.querySelectorAll('.list-group-item').forEach(item => {
            item.addEventListener('click', async (e) => {
                e.preventDefault();
                sidebar.querySelectorAll('.list-group-item').forEach(li => li.classList.remove('active'));
                e.target.classList.add('active');
                const normNumber = e.target.textContent;
                console.log(`Norma selecionada para visualização: ${normNumber}`);
                await displayStandardContent(normNumber);
            });
        });
    }
};

// Exemplo: Simulação de exibição do conteúdo da norma
const displayStandardContent = async (normNumber) => {
    const metadataDisplay = document.getElementById('standards-metadata-display');
    const contentDisplay = document.getElementById('standards-content-display');

    if (metadataDisplay) metadataDisplay.innerHTML = `<div class="text-center py-2"><i class="fas fa-spinner fa-spin"></i> Carregando...</div>`;
    if (contentDisplay) contentDisplay.innerHTML = '';

    await new Promise(resolve => setTimeout(resolve, 500));

    const content = `
        ## ${normNumber} - Título da Norma (Exemplo)
        **Organização:** ABNT / IEC (Exemplo)
        **Ano de Publicação:** 2014 (Exemplo)

        ### Escopo
        Esta norma especifica os requisitos gerais para a fabricação, ensaios e desempenho de transformadores de potência imersos em líquido, conforme a série IEC 60076.

        ### Níveis de Isolamento
        **Tensões de Impulso Atmosférico (LI/BIL):**
        *   Um=72.5kV: 325kVp, 350kVp
        *   Um=145kV: 550kVp, 650kVp

        **Tensões de Impulso de Manobra (SI/SIL):**
        *   Acima de 245kV: Valores específicos
        ...

        ### Condições de Ensaio
        Os ensaios devem ser realizados sob condições ambientais controladas, garantindo a temperatura e umidade especificadas.
    `;
    const metadata = `
        <p><strong>Norma:</strong> ${normNumber}</p>
        <p><strong>Organização:</strong> Exemplo Org.</p>
        <p><strong>Ano:</strong> 2024</p>
    `;

    if (metadataDisplay) metadataDisplay.innerHTML = metadata;
    if (contentDisplay) contentDisplay.innerHTML = content;
};

// Lógica do botão de busca
const setupSearchFunctionality = () => {
    const searchButton = document.getElementById('standards-search-button');
    const searchInput = document.getElementById('standards-search-input');
    const searchResultsContainer = document.getElementById('standards-search-results-container');
    const searchResultsDisplay = document.getElementById('standards-search-results');

    if (searchButton && searchInput && searchResultsContainer && searchResultsDisplay) {
        searchButton.addEventListener('click', async () => {
            const query = searchInput.value.trim();
            if (query.length > 2) {
                searchResultsContainer.style.display = 'block';
                searchResultsDisplay.innerHTML = `<div class="text-center py-3"><i class="fas fa-spinner fa-spin"></i> Buscando por "${query}"...</div>`;

                await new Promise(resolve => setTimeout(resolve, 800));

                const results = [
                    { title: `Resultado 1 para "${query}"`, snippet: 'Trecho da norma relevante...' },
                    { title: `Resultado 2 para "${query}"`, snippet: 'Outro trecho importante...' }
                ];

                if (results.length > 0) {
                    searchResultsDisplay.innerHTML = results.map(r => `
                        <div class="card mb-2" style="background-color: var(--background-card-light);">
                            <div class="card-body p-2">
                                <h6 class="mb-1" style="font-size: 0.9rem; color: var(--primary-color);">${r.title}</h6>
                                <p style="font-size: 0.75rem; color: var(--text-light);">${r.snippet}</p>
                                <button class="btn btn-sm btn-outline-info" style="font-size: 0.7rem;">Ver Detalhes</button>
                            </div>
                        </div>
                    `).join('');
                } else {
                    searchResultsDisplay.innerHTML = `<div class="text-muted text-center py-3">Nenhum resultado encontrado para "${query}".</div>`;
                }
            } else {
                searchResultsContainer.style.display = 'none';
                searchResultsDisplay.innerHTML = '';
                alert('Por favor, digite pelo menos 3 caracteres para buscar.');
            }
        });
    }
};

// --- Lógica para ABA de Gerenciamento de Normas ---

// Carregamento de normas cadastradas
const loadExistingStandards = async () => {
    const listContainer = document.getElementById('existing-standards-list');
    if (listContainer) {
        listContainer.innerHTML = `<div class="text-center py-3"><i class="fas fa-spinner fa-spin"></i> Carregando normas cadastradas...</div>`;
        
        // Garante que o sistema de persistência esteja pronto antes de tentar acessar o store
        await waitForApiSystem(); 
        const standards = await standardsStore.getData();
        
        if (!standards || standards.length === 0) {
            listContainer.innerHTML = `<div class="text-muted text-center py-3">Nenhuma norma cadastrada.</div>`;
            return;
        }
        listContainer.innerHTML = standards.map(norm => `
                <div class="card mb-2" style="background-color: var(--background-card-light);">
                    <div class="card-body p-2 d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1" style="font-size: 0.9rem; color: var(--primary-color);">${norm.number} - ${norm.title}</h6>
                            <small class="text-muted" style="font-size: 0.75rem;">Org: ${norm.org}, Ano: ${norm.year}, Cat: ${norm.categories}</small>
                        </div>
                        <div>
                            <button class="btn btn-sm btn-info me-1 edit-standard-btn" data-id="${norm.id}">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-danger delete-standard-btn" data-id="${norm.id}">
                                <i class="fas fa-trash-alt"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `).join('');
            listContainer.querySelectorAll('.edit-standard-btn').forEach(btn => btn.addEventListener('click', () => console.log('Editar norma ID:', btn.dataset.id)));
            listContainer.querySelectorAll('.delete-standard-btn').forEach(btn => btn.addEventListener('click', async () => {
                if (confirm('Tem certeza que deseja excluir esta norma?')) {
                    let currentStandards = await standardsStore.getData();
                    currentStandards = currentStandards.filter(s => s.id !== parseInt(btn.dataset.id));
                    await standardsStore.setData(currentStandards);
                    await loadExistingStandards();
                    console.log('Excluir norma ID:', btn.dataset.id);
                }
            }));
    }
};

// Lógica para upload de PDF (simulada)
const setupPdfUpload = () => {
    const uploadPdfArea = document.getElementById('upload-standard-pdf');
    if (uploadPdfArea) {
        const fileInput = uploadPdfArea.querySelector('input[type="file"]');
        uploadPdfArea.addEventListener('click', () => {
            if (fileInput) fileInput.click();
        });
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            const uploadInfo = document.getElementById('upload-standard-info');
            if (file) {
                uploadInfo.innerHTML = `<i class="fas fa-file-pdf me-1"></i> ${file.name} (${(file.size / 1024).toFixed(2)} KB) pronto para processar.`;
                document.getElementById('standard-title-input').value = `Nova Norma - ${file.name.split('.pdf')[0]}`;
            } else {
                uploadInfo.innerHTML = '';
            }
        });
    }
};

// Lógica do botão "Processar Norma"
const setupProcessStandardButton = () => {
    const processStandardButton = document.getElementById('process-standard-button');
    if (processStandardButton) {
        processStandardButton.addEventListener('click', async () => {
            const title = document.getElementById('standard-title-input').value;
            const number = document.getElementById('standard-number-input').value;
            const org = document.getElementById('standard-organization-input').value;
            const year = document.getElementById('standard-year-input').value;
            const categories = document.getElementById('standard-categories-input').value;
            const statusDisplay = document.getElementById('processing-status-display');
            const fileInput = document.getElementById('upload-standard-pdf')?.querySelector('input[type="file"]'); // Acessar fileInput de forma segura

            if (!title || !number || !fileInput || !fileInput.files[0]) {
                statusDisplay.innerHTML = '<div class="text-danger">Título, Número e Arquivo PDF são obrigatórios!</div>';
                return;
            }

            statusDisplay.innerHTML = '<div class="text-info"><i class="fas fa-spinner fa-spin me-1"></i> Processando norma...</div>';

            await new Promise(resolve => setTimeout(resolve, 2000));

            const currentStandards = await standardsStore.getData() || [];
            const newNorm = {
                id: Date.now(),
                title, number, org, year: parseInt(year), categories,
                filename: fileInput.files[0].name
            };
            currentStandards.push(newNorm);
            await standardsStore.setData(currentStandards);

            statusDisplay.innerHTML = '<div class="text-success"><i class="fas fa-check-circle me-1"></i> Norma processada e cadastrada com sucesso!</div>';
            document.getElementById('standard-title-input').value = '';
            document.getElementById('standard-number-input').value = '';
            document.getElementById('standard-organization-input').value = '';
            document.getElementById('standard-year-input').value = '';
            document.getElementById('standard-categories-input').value = '';
            document.getElementById('upload-standard-info').innerHTML = '';
            fileInput.value = '';

            await loadExistingStandards();
        });
    }
};

// Função de inicialização do módulo Normas Técnicas
async function initStandards() {
    console.log('Módulo Normas Técnicas (com abas) carregado e pronto para interatividade.');

    // Adicionar listener para o evento transformerDataUpdated
    document.addEventListener('transformerDataUpdated', async (event) => {
        console.log('[standards] Evento transformerDataUpdated recebido:', event.detail);
        // Se houver alguma lógica para atualizar a exibição de normas com base nos dados do transformador,
        // ela pode ser adicionada aqui. Por exemplo, filtrar normas aplicáveis.
        // Por enquanto, apenas recarrega a lista de normas existentes para garantir consistência.
        await loadExistingStandards();
    });

    const standardsTabButtons = document.querySelectorAll('#standardsTabs button[data-bs-toggle="tab"]');
    standardsTabButtons.forEach(button => {
        button.addEventListener('shown.bs.tab', async event => {
            console.log(`Aba "${event.target.id}" mostrada.`);
            if (event.target.id === 'management-tab') {
                await loadExistingStandards();
            } else if (event.target.id === 'consultation-tab') {
                loadStandardsCategories();
                loadStandardsNavSidebar();
            }
        });
    });

    // Chamadas Iniciais para a aba ativa (Consulta)
    loadStandardsCategories();
    loadStandardsNavSidebar();
    setupSearchFunctionality();
    setupPdfUpload();
    setupProcessStandardButton();
}

// SPA routing: executa quando o módulo standards é carregado
document.addEventListener('moduleContentLoaded', (event) => {
    if (event.detail && event.detail.moduleName === 'standards') {
        console.log('[standards] SPA routing init');
        initStandards();
    }
});

// Fallback para carregamento direto da página (se não for SPA)
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('standards-module-container')) { // Assumindo um ID de container principal para o módulo
        console.log('[standards] DOMContentLoaded init (fallback)');
        initStandards();
    }
});