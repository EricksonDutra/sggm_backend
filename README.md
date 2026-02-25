# 🎵 SGGM — Sistema de Gerenciamento de Grupos Musicais

Backend do **SGGM**, uma API REST desenvolvida com **Django** e **Django REST Framework** para gerenciar músicos, eventos, escalas e repertório de grupos musicais (igrejas, bandas, etc.).

---

## 🚀 Tecnologias

- **Python 3.x**
- **Django 5.1**
- **Django REST Framework 3.15**
- **Simple JWT** — autenticação via tokens JWT
- **MySQL** — banco de dados relacional (`mysqlclient`)
- **Firebase Admin SDK** — notificações push (FCM)
- **AWS S3** — armazenamento de arquivos (opcional)
- **Gunicorn** — servidor WSGI para produção
- **django-jazzmin** — painel administrativo customizado
- **Pytest** — testes automatizados

---

## 📁 Estrutura do Projeto

```
sggm_backend/
├── SGGM/                   # Configurações do projeto Django
│   ├── settings/           # Settings separados por ambiente
│   ├── settings_test.py    # Settings para testes
│   ├── firebase_config.py  # Configuração do Firebase
│   ├── urls.py             # URLs raiz
│   ├── asgi.py
│   └── wsgi.py
├── core/                   # App principal
│   ├── api/                # ViewSets, Serializers e Routers
│   ├── migrations/         # Migrações do banco de dados
│   ├── services/           # Regras de negócio
│   ├── tests/              # Testes automatizados
│   ├── admin.py            # Painel administrativo
│   ├── models.py           # Modelos de dados
│   ├── signals.py          # Signals do Django
│   └── views.py
├── templates/              # Templates HTML (e-mails, etc.)
├── manage.py
├── requirements.txt
├── pytest.ini
└── .env-example
```

---

## 🗂️ Modelos de Dados

| Modelo                  | Descrição                                              |
|-------------------------|--------------------------------------------------------|
| `Musico`                | Perfil do músico com tipo (Músico, Líder, Admin), status e token FCM |
| `Instrumento`           | Instrumentos disponíveis no grupo                      |
| `Artista`               | Artistas/bandas para categorização das músicas         |
| `Musica`                | Músicas com tom, link de cifra e link do YouTube       |
| `Evento`                | Eventos (Culto, Conferência, Célula, Especial) com repertório |
| `Escala`                | Escala de músicos por evento e instrumento             |
| `ComentarioPerformance` | Comentários pós-evento sobre músicas do repertório     |
| `ReacaoComentario`      | Reações (curtidas) em comentários de performance       |

---

## ⚙️ Configuração do Ambiente

### 1. Clonar o repositório

```bash
git clone https://github.com/EricksonDutra/sggm_backend.git
cd sggm_backend
```

### 2. Criar e ativar o ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar as variáveis de ambiente

Copie o arquivo de exemplo e preencha com seus dados:

```bash
cp .env-example .env
```

Edite o arquivo `.env`:

```env
SECRET_KEY=sua_secret_key_aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Banco de dados
DB_NAME=sggm
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_PORT=3306

# Armazenamento S3 (opcional)
USE_S3=False
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
AWS_S3_REGION_NAME=

# E-mail
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=seu@email.com
EMAIL_HOST_PASSWORD=sua_senha_app
EMAIL_USE_TLS=True

# CSRF
CSRF_TRUSTED_ORIGINS=http://localhost:3000
```

### 5. Aplicar as migrações

```bash
python manage.py migrate
```

### 6. Criar superusuário

```bash
python manage.py createsuperuser
```

### 7. Iniciar o servidor de desenvolvimento

```bash
python manage.py runserver
```

A API estará disponível em: `http://localhost:8000/`

O painel administrativo estará em: `http://localhost:8000/admin/`

---

## 🔐 Autenticação

A API utiliza **JWT (JSON Web Tokens)** via `djangorestframework-simplejwt`.

| Endpoint             | Método | Descrição                  |
|----------------------|--------|----------------------------|
| `/api/token/`        | POST   | Obter access e refresh token |
| `/api/token/refresh/`| POST   | Renovar o access token     |

Inclua o token nas requisições:

```
Authorization: Bearer <access_token>
```

---

## 🧪 Testes

Execute os testes com o `pytest`:

```bash
pytest
```

Para gerar o relatório de cobertura:

```bash
pytest --cov=core --cov-report=html
```

---

## 🔔 Notificações Push (Firebase)

O projeto integra o **Firebase Admin SDK** para envio de notificações push via FCM. Adicione o arquivo de credenciais do Firebase (`serviceAccountKey.json`) conforme configurado em `SGGM/firebase_config.py`.

---

## 📦 Deploy (Produção)

Para subir em produção com Gunicorn:

```bash
gunicorn SGGM.wsgi:application --bind 0.0.0.0:8000
```

Lembre-se de definir `DEBUG=False` e configurar corretamente `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS` no `.env`.

---

## 📱 App Mobile

O aplicativo mobile deste projeto está disponível em: [sggm_mobile](https://github.com/EricksonDutra/sggm_mobile)

---

## 👨‍💻 Autor

Desenvolvido por [EricksonDutra](https://github.com/EricksonDutra).
