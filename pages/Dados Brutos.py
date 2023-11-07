import streamlit as st
import pandas as pd
import requests 
import time

@st.cache_data
def converte_frame(df):
    return df.to_csv(index = False).encode('utf-8')

def mesagem_secesso():
    sucesso = st.success('Arquivo baixado com sucesso', icon="✅")
    time.sleep(5)
    sucesso.empty()


st.title('Dados brutos')

url = 'https://labdados.com/produtos'

responde = requests.get(url)
dados = pd.DataFrame.from_dict(responde.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format= '%d/%m/%Y')

with st.expander('Colunas'):
    colunas = st.multiselect('Selecione as colunas', list(dados.columns), list(dados.columns))

st.sidebar.title('Filtros')
with st.sidebar.expander('Nome do produto'):
    produtos = st.multiselect('Selecione os produtos', dados['Produto'].unique(), dados['Produto'].unique())

with st.sidebar.expander('Preço do produto'):
    preco = st.slider('Selecione os preço', 0, 5000, (0, 5000))

with st.sidebar.expander('Data da compra'):
    data_compra = st.date_input('Selecione a data', (dados['Data da Compra'].min(), dados['Data da Compra'].max()))

query = '''
    Produto in @produtos and \
    @preco[0] <= Preço <= @preco[1] and \
    @data_compra[0] <= `Data da Compra` <= @data_compra[1] 
'''
data_filtrados = dados.query(query)
data_filtrados = data_filtrados[colunas]

st.dataframe(data_filtrados)

st.markdown(f'A tabela possui :blue[{data_filtrados.shape[0]}] linhas e :blue[{data_filtrados.shape[1]}] colunas')
st.markdown('Escreva um nome para o arquivo')
coluna1, coluna2 = st.columns(2)
with coluna1:
    name_arq = st.text_input('', label_visibility='collapsed', value='dados')
    name_arq += '.csv'
with coluna2:
    st.download_button('Fazer o download da tabela em csv', data= converte_frame(data_filtrados), file_name=name_arq, mime='text/csv', on_click=mesagem_secesso)
