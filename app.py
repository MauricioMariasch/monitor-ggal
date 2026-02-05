import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configuración de la página
st.set_page_config(page_title="GGAL Options Dashboard", layout="wide")

st.title("📊 Monitor de Opciones: Grupo Financiero Galicia")
st.sidebar.header("Configuración")

# --- CARGA DE DATOS ---
# Opción 1: Subir archivo manualmente
uploaded_file = st.sidebar.file_uploader("Subí tu archivo Excel ($GGAL - Opex)", type=["xlsx"])

# Opción 2: Intentar cargar uno por defecto si existe en el repo
if uploaded_file is None:
    st.info("💡 Por favor, subí el archivo Excel en la barra lateral para comenzar.")
    st.stop() # Detiene la ejecución hasta que haya archivo

@st.cache_data # Para que la web sea rápida y no procese todo cada vez
def load_data(file):
    df = pd.read_excel(file, sheet_name='Historial')
    df['FECHA'] = pd.to_datetime(df['FECHA'])
    cols_num = ['BASE', 'ÚLTIMO', 'PRECIO GGAL', 'VI %', 'DELTA', 'THETA']
    df[cols_num] = df[cols_num].apply(pd.to_numeric, errors='coerce')
    return df.sort_values('FECHA')

df_historial = load_data(uploaded_file)

# --- FILTROS EN SIDEBAR ---
fechas_disponibles = sorted(df_historial['FECHA'].dt.date.unique(), reverse=True)
fecha_sel = st.sidebar.selectbox("Seleccioná la Fecha", options=fechas_disponibles)

# --- PROCESAMIENTO ---
df_fecha = df_historial[df_historial['FECHA'].dt.date == fecha_sel].copy()
precio_subyacente = df_fecha['PRECIO GGAL'].iloc[0] if not df_fecha.empty else 0

# --- MÉTRICAS RÁPIDAS ---
col1, col2, col3 = st.columns(3)
col1.metric("Precio GGAL", f"${precio_subyacente:,.2f}")
col2.metric("Fecha Seleccionada", str(fecha_sel))
col3.metric("Bases operadas", len(df_fecha))

# --- GRÁFICO 1: VOLATILITY SMILE ---
st.subheader(f"Volatility Smile - {fecha_sel}")

calls = df_fecha[df_fecha['TIPO'] == 'Call'].sort_values('BASE')
puts = df_fecha[df_fecha['TIPO'] == 'Put'].sort_values('BASE')

fig_smile = go.Figure()
fig_smile.add_trace(go.Scatter(x=calls['BASE'], y=calls['VI %'], name='Calls', line=dict(color='#00CC96', width=3)))
fig_smile.add_trace(go.Scatter(x=puts['BASE'], y=puts['VI %'], name='Puts', line=dict(color='#EF553B', width=3)))
fig_smile.add_vline(x=precio_subyacente, line_dash="dash", line_color="gray", annotation_text="ATM")

fig_smile.update_layout(template='plotly_white', hovermode='x unified', height=500)
st.plotly_chart(fig_smile, use_container_width=True)

# --- GRÁFICO 2: SUPERFICIE 3D ---
st.subheader("Superficie de Volatilidad (Histórica)")
df_calls = df_historial[df_historial['TIPO'] == 'Call'].dropna(subset=['VI %', 'BASE'])
surface_data = df_calls.pivot_table(index='BASE', columns='FECHA', values='VI %').interpolate(method='linear', axis=0).ffill().bfill()

fig_3d = go.Figure(data=[go.Surface(z=surface_data.values, x=surface_data.columns, y=surface_data.index, colorscale='Viridis')])
fig_3d.update_layout(scene=dict(xaxis_title='Fecha', yaxis_title='Strike', zaxis_title='VI %'), height=700)
st.plotly_chart(fig_3d, use_container_width=True)
