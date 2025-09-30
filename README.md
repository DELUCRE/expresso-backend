# Expresso Itaporanga - Backend API

Sistema de gestão de entregas e logística para a Expresso Itaporanga.

## Arquitetura

Este backend foi desenvolvido seguindo as melhores práticas de desenvolvimento Python/Flask:

- **Estrutura modular** com blueprints separados
- **Factory pattern** para criação da aplicação
- **Separação de responsabilidades** (routes, models, config)
- **Logging estruturado** para monitoramento
- **Middleware de segurança** implementado
- **Health checks** para monitoramento de infraestrutura

## Estrutura do Projeto

```
expresso-backend/
├── src/
│   ├── __init__.py
│   ├── app.py              # Aplicação principal e modelos
│   └── routes/
│       ├── __init__.py
│       ├── auth.py         # Autenticação
│       ├── api.py          # Endpoints principais
│       └── health.py       # Health checks
├── tests/                  # Testes automatizados
├── docs/                   # Documentação
├── scripts/                # Scripts utilitários
├── config/                 # Configurações
├── requirements.txt        # Dependências Python
├── railway.json           # Configuração Railway
├── Dockerfile             # Container Docker
└── README.md              # Este arquivo
```

## Tecnologias

- **Python 3.11+**
- **Flask 2.3.3** - Framework web
- **SQLAlchemy 2.0** - ORM
- **PostgreSQL** - Banco de dados (produção)
- **SQLite** - Banco de dados (desenvolvimento)
- **Flask-CORS** - Suporte a CORS
- **Gunicorn** - Servidor WSGI

## Configuração

### Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|---------|
| `DATABASE_URL` | URL do PostgreSQL | SQLite local |
| `SECRET_KEY` | Chave secreta Flask | dev-secret-key |
| `FLASK_ENV` | Ambiente (development/production) | production |
| `PORT` | Porta do servidor | 5000 |

### Usuários Padrão

| Usuário | Senha | Perfil |
|---------|-------|--------|
| admin | admin123 | Administrador |
| operador | operador123 | Operador |

## Endpoints da API

### Autenticação
- `POST /api/auth/login` - Login de usuário
- `POST /api/auth/logout` - Logout de usuário
- `GET /api/auth/check` - Verificar autenticação

### Entregas
- `GET /api/entregas` - Listar entregas
- `POST /api/entregas` - Criar nova entrega
- `PUT /api/entregas/<id>` - Atualizar entrega

### Dashboard
- `GET /api/dashboard/stats` - Estatísticas do dashboard

### Público
- `GET /api/rastreamento/<codigo>` - Rastrear entrega
- `POST /api/contato` - Enviar mensagem de contato

### Health Checks
- `GET /` - Health check básico
- `GET /health` - Health check detalhado
- `GET /api/health` - Health check da API

## Desenvolvimento Local

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar aplicação
python src/app.py
```

## Deploy

### Railway

1. Conecte este repositório ao Railway
2. Configure as variáveis de ambiente
3. Adicione PostgreSQL como serviço
4. O deploy será automático

### Docker

```bash
# Build
docker build -t expresso-backend .

# Run
docker run -p 5000:5000 expresso-backend
```

## Segurança

- Headers de segurança implementados
- Validação de entrada de dados
- Autenticação baseada em sessão
- CORS configurado adequadamente
- Logs de auditoria

## Monitoramento

- Health checks em `/health`
- Logs estruturados
- Métricas de performance
- Alertas de erro

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request
