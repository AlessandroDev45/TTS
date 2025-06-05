// public/scripts/history.js - ATUALIZADO

import { loadAndPopulateTransformerInfo } from './common_module.js';
import { apiDataSystem, collectFormData, fillFormWithData } from './api_persistence.js'; // Importa o sistema de persistência e funções auxiliares

// Obtém o store de sessões
const historyStore = apiDataSystem.getStore('sessions'); // Usar 'sessions' conforme o backend

// Função para carregar sessões
async function loadSessions() {
    try {
        await waitForApiSystem(); // Garante que o sistema de persistência esteja pronto
        let sessions = await historyStore.getData();

        // Garante que sessions seja sempre um array
        if (!sessions || !Array.isArray(sessions)) {
            sessions = [];
        }

        if (sessions.length === 0) {
            // Se não houver sessões na API, cria algumas de exemplo APENAS EM MEMÓRIA
            console.log('[loadSessions] Nenhuma sessão encontrada, criando dados mock em memória');
            sessions = [
                { id: 'sessao_1', name: 'Simulação Inicial', notes: 'Primeiro projeto de teste', timestamp: new Date(2023, 0, 15, 10, 30).toISOString() },
                { id: 'sessao_2', name: 'Trafo Grande EOL', notes: 'Configuração para parque eólico', timestamp: new Date(2023, 1, 20, 14, 0).toISOString() },
                { id: 'sessao_3', name: 'Otimização Perdas', notes: 'Foco em perdas em vazio', timestamp: new Date(2023, 2, 5, 9, 0).toISOString() },
            ];
            // NÃO salva no backend para evitar erro 422
        }
        return sessions;
    } catch (error) {
        console.error('[loadSessions] Erro ao carregar sessões:', error);
        return []; // Retorna array vazio em caso de erro
    }
}

// Função para renderizar a tabela de sessões
async function renderSessionsTable(sessions) {
    const tableBody = document.getElementById('history-table-body-content');
    if (!tableBody) return;

    // Garante que sessions seja um array
    if (!Array.isArray(sessions)) {
        console.error('[renderSessionsTable] sessions não é um array:', sessions);
        sessions = [];
    }

    if (sessions.length === 0) {
        tableBody.innerHTML = '<div class="text-muted text-center py-5">Nenhuma sessão encontrada.</div>';
        return;
    }

    tableBody.innerHTML = sessions.map(session => `
        <div class="row g-0 align-items-center table-row">
            <div class="col-3 py-2 px-3">${new Date(session.timestamp).toLocaleString()}</div>
            <div class="col-4 py-2 px-3">${session.name}</div>
            <div class="col-3 py-2 px-3">${session.notes || '-'}</div>
            <div class="col-2 py-2 px-3 text-center">
                <button class="btn btn-sm btn-info me-1 load-session-btn" data-id="${session.id}" title="Carregar Sessão"><i class="fas fa-folder-open"></i></button>
                <button class="btn btn-sm btn-danger delete-session-btn" data-id="${session.id}" title="Excluir Sessão"><i class="fas fa-trash-alt"></i></button>
            </div>
        </div>
    `).join('');

    // Adicionar listeners aos botões de ação
    tableBody.querySelectorAll('.load-session-btn').forEach(button => {
        button.addEventListener('click', async (e) => {
            const sessionId = e.currentTarget.dataset.id;
            console.log(`Carregar sessão: ${sessionId}`);
            alert(`Funcionalidade de carregar sessão ${sessionId} seria implementada aqui.`);
        });
    });

    tableBody.querySelectorAll('.delete-session-btn').forEach(button => {
        button.addEventListener('click', (e) => {
            const sessionId = e.currentTarget.dataset.id;
            const deleteModal = new bootstrap.Modal(document.getElementById('history-delete-session-modal'));
            deleteModal.show();
            document.getElementById('history-delete-modal-confirm-button').dataset.sessionId = sessionId;
        });
    });

    // Atualizar estatísticas
    document.getElementById('history-stats-total-sessions').textContent = sessions.length;
}

// Função de inicialização do módulo Histórico
async function initHistory() {
    console.log('Módulo Histórico carregado e pronto para interatividade.');

    // Adicionar listener para o evento transformerDataUpdated
    document.addEventListener('transformerDataUpdated', async (event) => {
        console.log('[history] Evento transformerDataUpdated recebido:', event.detail);
        // Se houver alguma lógica para atualizar a exibição do histórico com base nos dados do transformador,
        // ela pode ser adicionada aqui. Por exemplo, para mostrar um preview do estado atual.
        // Por enquanto, apenas recarrega a tabela de sessões para garantir consistência.
        await renderSessionsTable(await loadSessions());
    });

    // Lógica para o modal de salvar sessão
    const saveModalEl = document.getElementById('history-save-session-modal');
    const saveModal = new bootstrap.Modal(saveModalEl);

    document.getElementById('history-open-save-modal-button').addEventListener('click', () => {
        document.getElementById('history-session-name-input').value = '';
        document.getElementById('history-session-notes-input').value = '';
        document.getElementById('history-save-modal-error').textContent = '';
        saveModal.show();
    });

    document.getElementById('history-save-modal-cancel-button').addEventListener('click', () => {
        saveModal.hide();
    });

    document.getElementById('history-save-modal-confirm-button').addEventListener('click', async () => {
        const sessionName = document.getElementById('history-session-name-input').value.trim();
        const sessionNotes = document.getElementById('history-session-notes-input').value.trim();
        const errorMessageDiv = document.getElementById('history-save-modal-error');

        if (!sessionName) {
            errorMessageDiv.textContent = 'O nome da sessão é obrigatório.';
            return;
        }

        let sessions = await loadSessions();
        if (sessions.some(s => s.name.toLowerCase() === sessionName.toLowerCase())) {
            errorMessageDiv.textContent = 'Já existe uma sessão com este nome.';
            return;
        }

        const newSession = {
            id: `sessao_${Date.now()}`,
            name: sessionName,
            notes: sessionNotes,
            timestamp: new Date().toISOString(),
            data: {} // Aqui você pode adicionar os dados do transformador ou de outros módulos se necessário
        };
        sessions.push(newSession);
        await historyStore.setData(sessions);

        errorMessageDiv.textContent = '';
        saveModal.hide();
        await renderSessionsTable(sessions);
        document.getElementById('history-action-message').innerHTML = '<div class="alert alert-success py-1 px-2">Sessão salva com sucesso!</div>';
        setTimeout(() => { document.getElementById('history-action-message').innerHTML = ''; }, 3000);
        console.log('Nova sessão salva:', newSession);
    });

    // Lógica para o modal de exclusão
    const deleteModalEl = document.getElementById('history-delete-session-modal');
    const deleteModal = new bootstrap.Modal(deleteModalEl);

    document.getElementById('history-delete-modal-cancel-button').addEventListener('click', () => {
        deleteModal.hide();
    });

    document.getElementById('history-delete-modal-confirm-button').addEventListener('click', async (e) => {
        const sessionIdToDelete = e.currentTarget.dataset.sessionId;
        let sessions = await loadSessions();
        sessions = sessions.filter(s => s.id !== sessionIdToDelete);
        await historyStore.setData(sessions);

        deleteModal.hide();
        await renderSessionsTable(sessions);
        document.getElementById('history-action-message').innerHTML = '<div class="alert alert-success py-1 px-2">Sessão excluída com sucesso!</div>';
        setTimeout(() => { document.getElementById('history-action-message').innerHTML = ''; }, 3000);
        console.log('Sessão excluída:', sessionIdToDelete);
    });

    // Lógica de busca e filtro
    const searchInput = document.getElementById('history-search-input');
    const searchButton = document.getElementById('history-search-button');

    async function filterSessions() {
        const searchTerm = searchInput.value.toLowerCase();
        const allSessions = await loadSessions();
        const filtered = allSessions.filter(session =>
            session.name.toLowerCase().includes(searchTerm) ||
            (session.notes && session.notes.toLowerCase().includes(searchTerm))
        );
        await renderSessionsTable(filtered);
    }

    if (searchButton) {
        searchButton.addEventListener('click', filterSessions);
    }
    if (searchInput) {
        searchInput.addEventListener('input', filterSessions);
    }

    // Carregar sessões ao carregar a página
    await renderSessionsTable(await loadSessions());
}

// SPA routing: executa quando o módulo history é carregado
document.addEventListener('moduleContentLoaded', (event) => {
    if (event.detail && event.detail.moduleName === 'history') {
        console.log('[history] SPA routing init');
        initHistory();
    }
});

// Fallback para carregamento direto da página (se não for SPA)
document.addEventListener('DOMContentLoaded', () => {
    // Verifica se o elemento principal do módulo está presente para evitar execução em outras páginas
    if (document.getElementById('history-module-container')) { // Assumindo um ID de container principal para o módulo de histórico
        console.log('[history] DOMContentLoaded init (fallback)');
        initHistory();
    }
});