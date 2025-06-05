# Simulador de Testes de Transformadores (TTS)

Este projeto implementa uma aplicação web para simulação de testes em transformadores.

## Requisitos

- Python 3.8 ou superior
- FastAPI
- Uvicorn
- Outras dependências listadas no arquivo `requirements.txt`

## Como executar

A aplicação foi projetada para ser iniciada de duas maneiras:

### Método 1: Executar a partir do diretório raiz

```bash
# Navegue até o diretório raiz do projeto
cd caminho/para/TTS

# Execute o módulo backend.main
python -m backend.main
```

### Método 2: Executar diretamente do diretório backend

```bash
# Navegue até o diretório backend
cd caminho/para/TTS/backend

# Execute o arquivo main.py
python main.py
```

Em ambos os casos, o servidor será iniciado na porta 8000 e a interface web estará disponível em http://localhost:8000.

## Estrutura do Projeto

- `backend/`: Contém a API e a lógica de negócios
  - `main.py`: Ponto de entrada principal da aplicação
  - `routers/`: Definição das rotas da API
  - `services/`: Serviços para cálculos e lógica de negócios
  - `models/`: Modelos de dados
  - `utils/`: Utilitários e constantes
- `public/`: Arquivos da interface do usuário
- `docs/`: Documentação

## Documentação

A documentação completa está disponível no diretório `docs/` e no endpoint `/docs` da API em execução.