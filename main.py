import os
import random
from typing import Dict, Any
import pymysql 
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

load_dotenv()

# Inicialização da instancia no FastAPI

app = FastAPI(
    title="Sabor Rápido - API de Pagamentos",
    description="Serviço REST desenvolvido sob metologia RAD para processamento de transações.",
    version="1.0.0"
)

@app.get("/", summary="Status da API")
def root():
    return {"status": "online", "docs": "/docs"}

# Conecxao com o database

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT", 3306)),
}

def get_conection():
    try:
        conection = pymysql.connect(**DB_CONFIG)
        return conection
    except pymysql.MySQLError as error:
        print(f"Erro de conexao com o SGBD:{error}")
        return None
    
class SolicitacaoPagamento(BaseModel):
    id_pedido: int = Field(..., description="Identificador numérico do pedido", gt=0)
    valor_total: float = Field(..., description="Valor total da tansação financeira", gt=0)
    metodo_pagamento: str = Field(..., description="Forma de pagamento utilizada EX(: Cartao, Pix, Dinheiro)")
    
@app.post("/pagamentos", status_code=status.HTTP_201_CREATED, summary="Registrar e processar um pagamento")

def processar_pagamento(pagamento:SolicitacaoPagamento) -> Dict[str, Any]:
    id_pedido = pagamento.id_pedido
    valor_total = pagamento.valor_total
    metodo_pagamento = pagamento.metodo_pagamento
    
    # 2 implementação- Validação Customizada de Métodos de Pagamento para que a API rejeite qualquer requisição que 
    # envie um método de pagamento diferente de "Pix", "Cartão" ou "Dinheiro", retornando o 
    # código de erro HTTP adequado (400 Bad Request).
    
    metodos_validos = {'Pix', 'Cartão', 'Dinheiro' }
    
    if pagamento.metodo_pagamento not in metodos_validos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="400 Bad request, esse método de pagamento não é aceito! "
        )
        
    # 1. Implementação da regra de Incentivo Financeiro (Desconto 10% no pagamento por Pix):
    if pagamento.metodo_pagamento.lower() == 'pix':
        valor_total = valor_total - (0.10 * valor_total)
        
        # ---------------------
    status_simulado = (
        "Aprovado"
        if metodo_pagamento.lower() =="dinheiro"
        else random.choices(["Aprovado", "Recusado"], weights=[90, 10])[0]
    )

    conection = get_conection()
    if not conection:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nao foi possivel estabelecer conexão com o banco de dados de pagamentos."
        )
    
    try: 
        cursor = conection.cursor()
        sql_insert= """
            INSERT INTO PAGAMENTO(id_pedido, valor_total, metodo_pagamento, status_pagamento)
            VALUES (%s, %s, %s, %s);
            """
        cursor.execute(
            sql_insert, (id_pedido, valor_total, metodo_pagamento, status_simulado)
        )

        conection.commit()

        return {
            "mensagem": "Pagamento processado com sucesso!",
            "id_pedido": id_pedido,
            "status": status_simulado,
            "valor-total": valor_total,
        }

    except pymysql.IntegrityError: 
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe um registro de pagamento para o pedido ID{id_pedido}."
        )
    except pymysql.MySQLError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno de processamento de banco de dados: {err}"
        )
    finally:
        cursor.close()
        conection.close()
    
@app.get("/pagamentos/{id_pedido}", summary="Consultar dados de um pagamento existente")
def consultar_pagamento(id_pedido:int) -> Dict[str, Any]:
    conection = get_conection()
    if not conection:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nao foi possivel estabelecer conexao com o banco de dados."
        )
    
    try: 
        cursor = conection.cursor(pymysql.cursors.DictCursor)

        sql_select="SELECT * FROM PAGAMENTO WHERE id_pedido = %s;"
        cursor.execute(sql_select,(id_pedido,))
        registro = cursor.fetchone()

        cursor.close()
        conection.close()

        if not registro:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pagamento associado ao pedido {id_pedido} nao encontrado."
            )
        
        return registro
    except pymysql.MySQLError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro de comunicação com o a base de dados: {err}"
        )
    