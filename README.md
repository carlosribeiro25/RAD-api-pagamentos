# Sabor Rápido - API de Pagamentos

Serviço REST desenvolvido sob metodologia RAD para processamento de transações financeiras da plataforma **Sabor Rápido**.

---

## Tecnologias

- **Python 3** + **FastAPI**
- **PyMySQL** — conexão com banco de dados MySQL
- **Pydantic** — validação de dados de entrada
- **Uvicorn** — servidor ASGI

---

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/` | Status da API |
| `POST` | `/pagamentos` | Registrar e processar um pagamento |
| `GET` | `/pagamentos/{id_pedido}` | Consultar dados de um pagamento existente |

Documentação interativa disponível em: `http://localhost:8000/docs`

---

## Fluxo de Processamento de Pagamento

```mermaid
flowchart TD
    A([Requisição POST /pagamentos]) --> B{Método de pagamento\né válido?}
    B -- Não --> C[❌ 400 Bad Request\nMétodo não aceito]
    B -- Sim\nPix / Cartão / Dinheiro --> D{Método == Pix?}
    D -- Sim --> E[Aplica desconto de 10%\nsobre o valor total]
    D -- Não --> F[Valor total sem alteração]
    E --> G[Simula status do pagamento]
    F --> G
    G --> H{Conexão com\nbanco de dados}
    H -- Falhou --> I[❌ 500 Internal Server Error]
    H -- OK --> J[INSERT na tabela PAGAMENTO]
    J -- Sucesso --> K[✅ 201 Created\nPagamento processado]
    J -- ID duplicado --> L[❌ 409 Conflict\nPagamento já existe]
    J -- Erro SQL --> M[❌ 500 Internal Server Error]
```

---

## Regras de Negócio

### Métodos de Pagamento Aceitos

```mermaid
flowchart LR
    entrada([metodo_pagamento]) --> val{Pertence ao\nset de válidos?}
    val -- Sim --> pix[Pix]
    val -- Sim --> cartao[Cartão]
    val -- Sim --> dinheiro[Dinheiro]
    val -- Não --> erro[❌ 400 Bad Request]
```

### Incentivo Financeiro — Desconto Pix

Pagamentos realizados via **Pix** recebem automaticamente **10% de desconto** sobre o valor total antes de serem registrados no banco de dados.

```
valor_total = valor_total - (0.10 × valor_total)
```

### Simulação de Status

| Método | Lógica |
|--------|--------|
| `Dinheiro` | Sempre `Aprovado` |
| `Pix` / `Cartão` | 90% `Aprovado` · 10% `Recusado` |

---

## Modelo de Dados

```mermaid
erDiagram
    PAGAMENTO {
        int id_pedido PK
        float valor_total
        string metodo_pagamento
        string status_pagamento
    }
```

---

## Como Executar

```bash
# Ativar ambiente virtual
.venv\Scripts\Activate.ps1

# Iniciar servidor
uvicorn main:app --reload
```

Acesse: [http://localhost:8000/docs](http://localhost:8000/docs)
