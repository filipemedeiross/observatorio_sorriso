import pandas as pd
import plotly.express as px
import streamlit as st

# Configurações iniciais da página
st.set_page_config(layout="wide")

# Obtendo dados a serem utilizados
fato, escolas, fe = st.session_state.fato, st.session_state.escolas, st.session_state.fe

# Preparando os dados
dados = fato.join(escolas["escola.região"], on="escola_id").join(fe, on="faixa_etaria_id")
dados = dados.astype({"idade" : str})          

dados.drop(["escola_id", "faixa_etaria_id", "exame_id"], axis=1, inplace=True)

# Computando as informações relevantes
alunos_regiao = dados.groupby("escola.região")[["C", "P", "O", "soma_cpo", "quantidade_populacao"]].sum()

alunos_regiao["cpo-d"] = alunos_regiao["soma_cpo"] / alunos_regiao["quantidade_populacao"]
alunos_regiao["cpo-d"] = alunos_regiao["cpo-d"].apply(lambda cpo: round(cpo, 2))

alunos_regiao.rename(columns={"C" : "Cariados", "P" : "Perdidos", "O" : "Obturados"}, inplace=True)

alunos_regiao_idade = dados.groupby(["escola.região", "idade"])[["soma_cpo", "quantidade_populacao"]].sum()

alunos_15_19 = alunos_regiao_idade[alunos_regiao_idade.index.get_level_values(1).isin(["15", "16", "17", "18", "19"])].groupby(level=0).sum()
alunos_15_19.index = pd.MultiIndex.from_product([alunos_regiao_idade.index.get_level_values(0).unique(), ["15-19"]],
                                                names=alunos_regiao_idade.index.names)

alunos_regiao_idade = alunos_regiao_idade.append(alunos_15_19)

alunos_regiao_idade = alunos_regiao_idade[alunos_regiao_idade.index.get_level_values(1).isin(["12", "15", "15-19"])]

alunos_regiao_idade["cpo-d"] = alunos_regiao_idade["soma_cpo"] / alunos_regiao_idade["quantidade_populacao"]
alunos_regiao_idade["cpo-d"] = alunos_regiao_idade["cpo-d"].apply(lambda cpo: round(cpo, 2))

alunos_regiao_idade.sort_values(by="idade", inplace=True)

# Constantes e funções auxiliares
labels = {col : "" for col in alunos_regiao.columns}
labels[alunos_regiao.index.name] = labels["value"] = labels["variable"] = ""

labels_cpo_d_regiao = {"x" : "faixa etária", "y" : "CPO-D", "color" : "região"}

multi_indice = lambda x: alunos_regiao_idade.index.get_level_values(x)

# Exibindo dados

col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

# Quantidade de alunos por região de Palmas
fig1 = px.bar(alunos_regiao, y="quantidade_populacao", labels=labels, text_auto=True,
              title="Quantidade de alunos por região de Palmas")
fig1.update_traces(textfont_size=18, textposition="outside", cliponaxis=False)

col1.plotly_chart(fig1, use_container_width=True)

# CPO-D por região
fig2 = px.bar(alunos_regiao, x="cpo-d", labels=labels, text_auto=True, title="CPO-D por região")
fig2.update_traces(textfont_size=14)

col2.plotly_chart(fig2, use_container_width=True)

# Evolução CPO-D por zona
fig3 = px.line(alunos_regiao_idade, x=[str(i) + " anos" for i in multi_indice(1)], y="cpo-d",
               text="cpo-d", color=multi_indice(0), labels=labels_cpo_d_regiao, range_y=[1.1, 3.7],
               title="Evolução CPO-D por região")
fig3.update_traces(textposition="top center")
fig3.update_layout(legend_x=0)

col3.plotly_chart(fig3, use_container_width=True)

# Composição CPO-D por zona
fig4 = px.bar(alunos_regiao, y=["Cariados", "Perdidos", "Obturados"], labels=labels, title="Composição CPO-D por região")
fig4.update_layout(legend_x=0)

col4.plotly_chart(fig4, use_container_width=True)