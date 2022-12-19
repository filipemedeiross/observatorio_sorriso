import sqlite3
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


# Auxiliary functions

@st.cache
def load_data(name_database):
    # Connecting to the database and getting cursor
    conn = sqlite3.connect(name_database)
    cur = conn.cursor()

    # Getting the fact table
    res = cur.execute("SELECT * FROM CPO_D")
    fact_table = pd.DataFrame(res.fetchall(),
                              columns=np.array(res.description)[:, 0])
    fact_table.drop(columns=["index"], inplace=True)
    
    # Getting the dimension 'Escola'
    res = cur.execute("SELECT * FROM Escola")
    schools = pd.DataFrame(res.fetchall(),
                           columns=np.array(res.description)[:, 0])
    schools.drop(columns=["index"], inplace=True)

    return fact_table, schools


# Initial header

st.title('Observatório do Sorriso')


# Loading data

DATA = 'observatorio_sorriso'

fact_table, schools = load_data(DATA)

# Displaying the data summary

st.header("Quantidade de alunos examinados em Palmas-TO")

student_counts = fact_table.join(schools["escola.região"], on="escola_id").groupby("escola.região")["quantidade_populacao"].sum()

fig = px.pie(student_counts, values="quantidade_populacao",
                names=student_counts.index, hole=.7)

fig.update_layout(annotations=[dict(text=f"<b>{student_counts.sum()}</b>", x=0.5, y=0.55, font_size=30, showarrow=False),
                                dict(text="alunos", x=0.5, y=0.45, font_size=20, showarrow=False)])

st.plotly_chart(fig)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.header(np.round(fact_table["soma_cpo"].sum() / fact_table["quantidade_populacao"].sum(), 2))

    st.write("CPO-D Palmas")

with col2:
    st.header(schools.shape[0])

    st.write("escolas públicas")

with col3:
    st.header(schools["escola.território"].unique().shape[0])

    st.write("territórios") 

with col4:
    st.header(schools["escola.região"].unique().shape[0])

    st.write("regiões")   
