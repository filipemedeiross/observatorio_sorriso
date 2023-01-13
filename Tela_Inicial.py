import sqlite3
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# Configurações iniciais da página
st.set_page_config(page_title="Observatório do Sorriso", layout="centered")

# Função auxiliar para carregar os dados
@st.cache
def carregar_dados(base_dados):
    # Conectando a base de dados e obtendo o cursor
    conn = sqlite3.connect(base_dados)
    cur = conn.cursor()

    # Obtendo a tabela fato
    res = cur.execute("SELECT * FROM CPO_D")
    tabela_fato = pd.DataFrame(res.fetchall(),
                               columns=np.array(res.description)[:, 0])
    tabela_fato.drop(columns=["index"], inplace=True)
    
    # Obtendo a dimensão 'Escola'
    res = cur.execute("SELECT * FROM Escola")
    escolas = pd.DataFrame(res.fetchall(),
                           columns=np.array(res.description)[:, 0])
    escolas.drop(columns=["index"], inplace=True)

    # Obtendo a dimensão 'Faixa_etaria'
    res = cur.execute("SELECT * FROM Faixa_etaria")
    faixa_etaria = pd.DataFrame(res.fetchall(),
                                columns=np.array(res.description)[:, 0])
    faixa_etaria.drop(columns=["index"], inplace=True)

    # Obtendo a dimensão 'Exame'
    res = cur.execute("SELECT * FROM Exame")
    exame = pd.DataFrame(res.fetchall(),
                         columns=np.array(res.description)[:, 0])
    exame.drop(columns=["index"], inplace=True)
    
    # Fechar conexão
    conn.close()

    return tabela_fato, escolas, faixa_etaria, exame

# Carregando dados utilizados em todas as pages do app
st.session_state.fato, st.session_state.escolas, st.session_state.fe, st.session_state.exame = carregar_dados("observatorio_sorriso")

# Obtendo dados a serem utilizados
fato, escolas = st.session_state.fato, st.session_state.escolas

# Cabeçalho inicial
st.title("Observatório do Sorriso")

# Quantidade de alunos por região
st.header("Quantidade de alunos examinados em Palmas-TO")

alunos_regiao = fato.join(escolas["escola.região"], on="escola_id")
alunos_regiao = alunos_regiao.groupby("escola.região")["quantidade_populacao"].sum()

fig = px.pie(values=alunos_regiao, names=alunos_regiao.index, hole=.7)
fig.update_layout(annotations=[dict(text=f"<b>{alunos_regiao.sum()}</b>", x=0.5, y=0.55, font_size=30, showarrow=False),
                               dict(text="alunos", x=0.5, y=0.45, font_size=20, showarrow=False)])
st.plotly_chart(fig)

# Sumário de informações relevantes
# Média do CPO-D em Palmas/TO
# Quantidade de escolas, territórios e regiões analisadas
col1, col2, col3, col4 = st.columns(4)

col1.metric("CPO-D Palmas", np.round(fato["soma_cpo"].sum() / fato["quantidade_populacao"].sum(), 2))
col2.metric("escolas públicas", escolas.shape[0])
col3.metric("territórios", escolas["escola.território"].nunique())
col4.metric("regiões", escolas["escola.região"].nunique())

# Referências dos dados brutos
st.caption("Dados brutos disponíveis na [página do github](https://github.com/filipemedeiross/observatorio_sorriso/tree/main/dados) do projeto.")