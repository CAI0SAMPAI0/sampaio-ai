# PRD - Sampaio AI

## 1. Visão Geral

### Nome do Projeto

Sampaio AI

### Objetivo

O Sampaio AI é uma plataforma pessoal de estudos de programação construída com Django, LangChain e LangGraph.

O sistema funcionará como um assistente inteligente capaz de:

* Armazenar materiais de estudo.
* Processar documentos automaticamente.
* Criar uma base de conhecimento própria.
* Responder perguntas utilizando os materiais enviados.
* Gerar resumos, flashcards e exercícios.
* Auxiliar no aprendizado de programação.
* Organizar sessões de estudo.
* Atuar como mentor técnico personalizado.

O sistema será utilizado por apenas um usuário inicialmente, mas deve ser desenvolvido de forma organizada e escalável.

---

# 2. Objetivos do Produto

## Objetivos Principais

* Centralizar todo material de estudo.
* Criar uma base de conhecimento pessoal.
* Permitir consultas inteligentes sobre documentos.
* Automatizar geração de conteúdo de estudo.
* Melhorar produtividade e retenção de conhecimento.
* Servir como mentor técnico para aprendizado contínuo.

---

# 3. Stack Tecnológica

## Backend

* Python 3.12+
* Django 6+
* PostgreSQL
* Celery
* Redis
* RabbitMQ

## Inteligência Artificial

* LangChain 1+
* LangGraph
* OpenAI GPT-5.5-mini

## Frontend

* Django Templates
* HTMX
* Alpine.js
* TailwindCSS

## Infraestrutura

* Docker
* Docker Compose
* Docker Swarm
* Traefik

## Documentação

* MKDocs
* Mermaid

---

# 4. Estrutura de Apps

## core

Configurações principais do projeto.

## base

Classes compartilhadas.

## accounts

Usuários e autenticação.

## uploads

Upload e gerenciamento de arquivos.

## knowledge_base

Base vetorial e documentos processados.

## chat

Sessões de conversa.

## ai_agents

Agentes LangGraph.

## studies

Planos de estudo.

## flashcards

Flashcards gerados pela IA.

## quizzes

Questionários automáticos.

## notifications

Notificações do sistema.

---

# 5. Funcionalidades

## Autenticação

### Requisitos

* Login por email.
* Recuperação de senha.
* Controle de sessão.
* Perfil do usuário.

---

## Upload de Arquivos

### Suporte

* PDF
* DOCX
* TXT
* Markdown
* CSV
* XLSX
* PPTX
* PNG
* JPG
* JPEG

### Requisitos

* Upload único.
* Upload múltiplo.
* Arrastar e soltar arquivos.
* Remoção de arquivos.
* Download de arquivos.
* Visualização de metadados.

---

## Processamento de Arquivos

Após upload:

1. Celery recebe tarefa.
2. Arquivo é processado.
3. Texto é extraído.
4. Conteúdo é dividido em chunks.
5. Embeddings são gerados.
6. Dados são armazenados.

---

## Biblioteca de Conhecimento

Cada documento deve possuir:

* Nome.
* Tipo.
* Data de envio.
* Tamanho.
* Status de processamento.
* Quantidade de chunks.
* Tags.

---

## Busca Semântica

Campo global de pesquisa.

Exemplo:

"Explique Dependency Injection"

O sistema deverá:

* Buscar documentos relevantes.
* Recuperar chunks.
* Enviar contexto ao modelo.

---

## Chat Inteligente

### Recursos

* Histórico de sessões.
* Streaming de resposta.
* Markdown.
* Citações das fontes.
* Contexto baseado em documentos.

---

## Agentes Especializados

### Mentor

Cria planos de estudo.

### Python

Especialista em Python.

### Django

Especialista em Django.

### DevOps

Especialista em Docker e Linux.

### Code Review

Analisa código.

### Arquitetura

Especialista em arquitetura de software.

---

## Flashcards

Gerados automaticamente.

Campos:

* Pergunta
* Resposta
* Categoria
* Documento de origem

---

## Quizzes

Gerados automaticamente.

Tipos:

* Múltipla escolha
* Verdadeiro/Falso
* Perguntas abertas

---

## Resumos

A IA poderá gerar:

* Resumo curto
* Resumo detalhado
* Resumo técnico
* Resumo executivo

---

## Plano de Estudos

O usuário poderá informar:

* Objetivo
* Tempo disponível
* Tecnologia

A IA gerará:

* Cronograma
* Sequência de tópicos
* Exercícios
* Metas semanais

---

# 6. Modelagem Inicial

## User

Dados do usuário.

## KnowledgeDocument

Documento enviado.

## KnowledgeChunk

Fragmentos processados.

## ChatSession

Sessão de conversa.

## ChatMessage

Mensagens.

## Agent

Agentes disponíveis.

## Flashcard

Flashcards.

## Quiz

Questionários.

## StudyPlan

Plano de estudo.

## Notification

Notificações.

---

# 7. Processamento Assíncrono

Celery será utilizado para:

* Processamento de arquivos.
* Geração de embeddings.
* Geração de flashcards.
* Geração de quizzes.
* Resumos.
* Atualizações da base vetorial.

---

# 8. Dashboard

Indicadores:

* Arquivos enviados.
* Documentos processados.
* Chats realizados.
* Flashcards criados.
* Quizzes realizados.
* Horas estudadas.
* Temas estudados.

---

# 9. Segurança

* CSRF habilitado.
* Proteção de uploads.
* Controle de acesso por usuário.
* Arquivos privados.
* Variáveis sensíveis no .env.
* Docker Secrets em produção.

---

# 10. Deploy

## Ambientes

### Desenvolvimento

Docker Compose.

### Produção

Docker Swarm.

Serviços:

* app
* postgres
* redis
* rabbitmq
* celery_worker
* celery_beat
* traefik

---

# 11. CI/CD

GitHub Actions

Fluxo:

1. Push.
2. Build.
3. Teste.
4. Push GHCR.
5. Deploy automático.

---

# 12. Roadmap

## Sprint 1

* [x] Criar projeto Django
* [x] Configurar PostgreSQL
* [x] Configurar Docker
* [x] Configurar autenticação

## Sprint 2

* [x] Upload único
* [x] Upload múltiplo
* [x] Gestão de arquivos

## Sprint 3

* [x] Celery
* [x] Redis
* [x] RabbitMQ

## Sprint 4

* [x] Extração de texto
* [x] Chunks
* [x] Embeddings

## Sprint 5

* [x] Busca semântica
* [x] RAG

## Sprint 6

* [x] Chat IA
* [x] Streaming
* [x] Histórico

## Sprint 7

* [x] Agentes LangGraph

## Sprint 8

* [x] Flashcards
* [x] Quizzes

## Sprint 9

* [x] Planos de estudo
* [x] Dashboard

## Sprint 10

* [x] Docker Swarm
* [x] Traefik
* [x] Deploy produção

## Sprint 11

* [x] Observabilidade
* [x] Backup
* [x] Hardening

## Sprint 12

* [x] Otimizações
* [x] Refatorações
* [x] Documentação final
