import sqlite3
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

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

# Carregando os dados
fato, escolas, fe, exame = carregar_dados("observatorio_sorriso")

# Preparando os dados
dados = fato.join(escolas["escola.região"], on="escola_id").join(fe, on="faixa_etaria_id")

dados["escola.região"] = dados["escola.região"].map({regiao : "RURAL" if regiao=="RURAL" else "URBANO"
                                                     for regiao in dados["escola.região"].unique()})
dados = dados.astype({"idade" : str})                                                     

dados.rename(columns={"escola.região" : "escola.zona"}, inplace=True)
dados.drop(["escola_id", "faixa_etaria_id", "exame_id"], axis=1, inplace=True)

# Computando as informações relevantes
alunos_zona = dados.groupby("escola.zona")[["C", "P", "O", "soma_cpo", "quantidade_populacao"]].sum()

alunos_zona["cpo-d"] = alunos_zona["soma_cpo"] / alunos_zona["quantidade_populacao"]
alunos_zona["cpo-d"] = alunos_zona["cpo-d"].apply(lambda cpo: round(cpo, 2))

alunos_zona.rename(columns={"C" : "Cariados", "P" : "Perdidos", "O" : "Obturados"}, inplace=True)

alunos_zona_idade = dados.groupby(["escola.zona", "idade"])[["soma_cpo", "quantidade_populacao"]].sum()

alunos_15_19 = alunos_zona_idade[alunos_zona_idade.index.get_level_values(1).isin(["15", "16", "17", "18", "19"])].groupby(level=0).sum()
alunos_15_19.index = pd.MultiIndex.from_product([alunos_zona_idade.index.get_level_values(0).unique(), ["15-19"]],
                                                names=alunos_zona_idade.index.names)

alunos_zona_idade = alunos_zona_idade.append(alunos_15_19)

alunos_zona_idade = alunos_zona_idade[alunos_zona_idade.index.get_level_values(1).isin(["12", "15", "15-19"])]

alunos_zona_idade["cpo-d"] = alunos_zona_idade["soma_cpo"] / alunos_zona_idade["quantidade_populacao"]
alunos_zona_idade["cpo-d"] = alunos_zona_idade["cpo-d"].apply(lambda cpo: round(cpo, 2))

alunos_zona_idade.sort_values(by="idade", inplace=True)

# Constantes e funções auxiliares
labels = {col : "" for col in alunos_zona.columns}
labels[alunos_zona.index.name] = labels["value"] = labels["variable"] = ""

labels_cpo_d_zona = {"x" : "faixa etária", "y" : "CPO-D", "color" : "zona"}

multi_indice = lambda x: alunos_zona_idade.index.get_level_values(x)

# Exibindo dados

col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

# Quantidade de alunos por zona de Palmas
fig1 = px.bar(alunos_zona, y="quantidade_populacao", labels=labels, text_auto=True,
              title="Quantidade de alunos por zona de Palmas")
fig1.update_traces(textfont_size=18, textposition="outside", cliponaxis=False)

col1.plotly_chart(fig1, use_container_width=True)

# CPO-D por zona
fig2 = px.bar(alunos_zona, x="cpo-d", labels=labels, text_auto=True, title="CPO-D por zona")
fig2.update_traces(textfont_size=14)

col2.plotly_chart(fig2, use_container_width=True)

# Evolução CPO-D por zona
fig3 = px.line(alunos_zona_idade, x=[str(i) + " anos" for i in multi_indice(1)], y="cpo-d", text="cpo-d",
               color=multi_indice(0), labels=labels_cpo_d_zona, title="Evolução CPO-D por zona")
fig3.update_traces(textposition="top center")
fig3.update_layout(legend_x=0)

col3.plotly_chart(fig3, use_container_width=True)

# Composição CPO-D por zona
fig4 = px.bar(alunos_zona, y=["Cariados", "Perdidos", "Obturados"], labels=labels, title="Composição CPO-D por zona")
fig4.update_layout(legend_x=0)

col4.plotly_chart(fig4, use_container_width=True)