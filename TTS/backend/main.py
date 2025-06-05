# backend/main.py
import os
import sys
import pathlib
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import webbrowser
import socket
import time
import threading
from fastapi.responses import Response

# Configuração dos caminhos para importação correta independente de onde o script é executado
current_file = pathlib.Path(__file__).absolute()
current_dir = current_file.parent
root_dir = current_dir.parent

# Adiciona o diretório raiz e o diretório backend ao path
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Tenta importar os módulos usando diferentes estratégias
# Esta abordagem funcionará tanto executando de backend/ quanto do diretório raiz
try:
    # Tenta importação absoluta (quando executado como módulo)
    from backend.routers import transformer_routes, data_routes
    from backend.mcp.data_manager import MCPDataManager
    from backend.mcp.session_manager import MCPSessionManager
except ImportError:
    try:
        # Tenta importação relativa (quando executado diretamente de backend/)
        from routers import transformer_routes, data_routes
        from mcp.data_manager import MCPDataManager
        from mcp.session_manager import MCPSessionManager
    except ImportError:
        print("ERRO: Não foi possível importar os módulos necessários.")
        print("Certifique-se de que está executando o script do diretório correto:")
        print("1. Do diretório raiz: python -m backend.main")
        print("2. Do diretório backend: python main.py")
        sys.exit(1)

# Criar a instância da aplicação FastAPI
app = FastAPI(
    title="Simulador de Testes de Transformadores",
    description="API para o Simulador de Testes de Transformadores",
    version="1.9.9"
)

# Configurar CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar o sistema de dados
mcp_data_manager = MCPDataManager()
session_manager = MCPSessionManager(mcp_data_manager)

# Configurar os data managers nos routers
transformer_routes.mcp_data_manager = mcp_data_manager
data_routes.set_data_manager(mcp_data_manager)

# Incluir routers na aplicação
app.include_router(transformer_routes.router)
app.include_router(data_routes.router)

# Rota de teste para verificar se a API está funcionando
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "API está funcionando"}

# Rota para servir favicon.ico para evitar 404
@app.get("/favicon.ico")
async def favicon():
    # Retorna uma resposta vazia com status 204 (No Content) para evitar erro 404
    return Response(status_code=204)

# Montar arquivos estáticos (frontend)
# Utiliza caminhos relativos para funcionar independente de onde é executado
frontend_dir = os.path.join(root_dir, "public")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")
else:
    print(f"Aviso: Diretório frontend não encontrado em {frontend_dir}")

def check_port_in_use(port):
    """Verifica se uma porta está em uso"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            result = sock.connect_ex(('localhost', port))
            return result == 0
        except:
            return False

def open_browser_delayed():
    """Abre o navegador após um pequeno delay"""
    time.sleep(1.5)  # Aguarda o servidor inicializar
    webbrowser.open('http://localhost:8000')

# Ponto de entrada para executar diretamente
if __name__ == "__main__":
    port = 8000
    
    # Verifica se já há algo rodando na porta
    if check_port_in_use(port):
        print(f"⚠️  Porta {port} já está em uso. O navegador não será aberto automaticamente.")
        print(f"   Se for outra instância desta aplicação, acesse: http://localhost:{port}")
    else:
        print(f"Iniciando servidor na porta {port}...")
        print(f"Abrindo navegador automaticamente em http://localhost:{port}")
        # Inicia thread para abrir o navegador após delay
        threading.Thread(target=open_browser_delayed, daemon=True).start()
    
    # Determina o módulo correto para o uvicorn
    # Isto permitirá que o script seja executado de qualquer lugar
    is_in_backend_dir = os.path.basename(os.getcwd()) == "backend"
    module_path = "main:app" if is_in_backend_dir else "backend.main:app"
      # Inicia o servidor Uvicorn
    uvicorn.run(
        module_path, 
        host="0.0.0.0", 
        port=port, 
        reload=True,
        # Se executado diretamente do backend, mantém dentro desse diretório
        reload_dirs=[str(current_dir) if is_in_backend_dir else str(root_dir)]
    )