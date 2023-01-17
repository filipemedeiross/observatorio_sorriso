import pandas as pd
import plotly.express as px
import streamlit as st

# Configurações iniciais da página
st.set_page_config(page_title="Territórios 🌎", layout="wide")

# Obtendo dados a serem utilizados
fato, escolas, fe = st.session_state.fato, st.session_state.escolas, st.session_state.fe

# Preparando os dados
dados = fato.join(escolas["escola.território"], on="escola_id").join(fe, on="faixa_etaria_id")
dados = dados.astype({"idade" : str})

dados.drop(["escola_id", "faixa_etaria_id", "exame_id"], axis=1, inplace=True)

# Computando as informações relevantes
alunos_escola = dados.groupby("escola.território")[["C", "P", "O", "soma_cpo", "quantidade_populacao"]].sum()

alunos_escola["cpo-d"] = alunos_escola["soma_cpo"] / alunos_escola["quantidade_populacao"]
alunos_escola["cpo-d"] = alunos_escola["cpo-d"].apply(lambda cpo: round(cpo, 2))

alunos_escola.rename(columns={"C" : "Cariados", "P" : "Perdidos", "O" : "Obturados"}, inplace=True)

alunos_escola_idade = dados.groupby(["escola.território", "idade"])[["soma_cpo", "quantidade_populacao"]].sum()

alunos_15_19 = alunos_escola_idade[alunos_escola_idade.index.get_level_values(1).isin(["15", "16", "17", "18", "19"])].groupby(level=0).sum()
alunos_15_19.index = pd.MultiIndex.from_product([alunos_escola_idade.index.get_level_values(0).unique(), ["15-19"]],
                                                names=alunos_escola_idade.index.names)

alunos_escola_idade = alunos_escola_idade.append(alunos_15_19)

alunos_escola_idade = alunos_escola_idade[alunos_escola_idade.index.get_level_values(1).isin(["12", "15", "15-19"])]

alunos_escola_idade["cpo-d"] = alunos_escola_idade["soma_cpo"] / alunos_escola_idade["quantidade_populacao"]
alunos_escola_idade["cpo-d"] = alunos_escola_idade["cpo-d"].apply(lambda cpo: round(cpo, 2))

alunos_escola_idade.sort_values(by="idade", inplace=True)

# Constantes e funções auxiliares
labels = {col : "" for col in alunos_escola.columns}
labels[alunos_escola.index.name] = labels["value"] = labels["variable"] = ""

labels_cpo_d_territorio = {"x" : "faixa etária", "y" : "CPO-D", "color" : "território"}

multi_indice = lambda x: alunos_escola_idade.index.get_level_values(x)

# Exibindo dados

col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

# Quantidade de alunos por território de Palmas
fig1 = px.bar(alunos_escola, y="quantidade_populacao", labels=labels, text_auto=True,
              title="Quantidade de alunos por território de Palmas")
fig1.update_traces(textfont_size=18, textposition="outside", cliponaxis=False)

col1.plotly_chart(fig1, use_container_width=True)

# CPO-D por território
fig2 = px.bar(alunos_escola, x="cpo-d", labels=labels, text_auto=True, title="CPO-D por território")
fig2.update_traces(textfont_size=14)

col2.plotly_chart(fig2, use_container_width=True)

# Evolução CPO-D por território
fig3 = px.line(alunos_escola_idade, x=[str(i) + " anos" for i in multi_indice(1)], y="cpo-d",
               text="cpo-d", color=multi_indice(0), labels=labels_cpo_d_territorio, range_y=[1.1, 3.7],
               title="Evolução CPO-D por território")
fig3.update_traces(textposition="top center")
fig3.update_layout(legend_x=0)

col3.plotly_chart(fig3, use_container_width=True)

# Composição CPO-D por território
fig4 = px.bar(alunos_escola, y=["Cariados", "Perdidos", "Obturados"], labels=labels, title="Composição CPO-D por território")
fig4.update_layout(legend_x=0)

col4.plotly_chart(fig4, use_container_width=True)