import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path
import sys

# Adiciona o diretório pai ao path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.queries import get_metrics_data, get_daily_cases, get_monthly_cases

get_metrics_data = st.cache_data(ttl=3600)(get_metrics_data)
get_daily_cases = st.cache_data(ttl=3600)(get_daily_cases)
get_monthly_cases = st.cache_data(ttl=3600)(get_monthly_cases)

st.set_page_config(
    page_title="Indicium HealthCare Inc.",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 Indicium HealthCare Inc.")

# Carrega dados das métricas
metrics = get_metrics_data()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "📈 Taxa de Aumento de Casos (MoM.)", f"{metrics['taxa_aumento']:.1f}%", chart_data=metrics["casos_mensais"],
        chart_type="line", border=True
    )
with col2:
    st.metric(
        "💀 Taxa de Mortalidade", f"{metrics['taxa_mortalidade']:.1f}%", chart_data=metrics['taxa_mortalidade_mensal'], chart_type="line", border=True
    )
with col3:
    st.metric(
        "🏥 Ocupação UTI", f"{metrics['ocupacao_uti']:.1f}%", chart_data=metrics['ocupacao_uti_mensal'], chart_type="line", border=True
    )
with col4:
    st.metric(
        "💉 Taxa de Vacinação", f"{metrics['taxa_vacinacao']:.1f}%", chart_data=metrics['taxa_vacinacao_mensal'], chart_type="line", border=True
    )

st.markdown("---")

col_graficos, col_chat = st.columns([65, 35])

with col_graficos:

    # ----------------- GRÁFICO DIÁRIO -----------------
    df_diario = get_daily_cases()
    
    # Se não houver dados, cria um dataframe vazio
    if df_diario.empty:
        st.warning("Nenhum dado disponível para o gráfico diário.")
        df_diario = pd.DataFrame({"data": pd.date_range(end=pd.Timestamp.today(), periods=30, freq="D"), "casos": 0})
    else:
        # Converte coluna de data se necessário
        df_diario['data'] = pd.to_datetime(df_diario['data'])

    fig_diario = go.Figure()

    fig_diario.add_trace(
        go.Scatter(
            x=df_diario["data"],
            y=df_diario["casos"],
            mode="lines",
            line=dict(color="#2563EB", width=3),
            fill="tozeroy",
            fillcolor="rgba(37, 99, 235, 0.25)",
            hovertemplate=(
                "<b>📅 %{x|%d/%m/%Y}</b><br><br>"
                "Casos: <b>%{y}</b>"
                "<extra></extra>"
            )
        )
    )

    fig_diario.update_layout(
        title="Número diário de casos de SRAG (últimos 30 dias)",
        template="plotly_white",
        height=380,
        dragmode=False,
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis=dict(title=None, fixedrange=True, showgrid=False),
        yaxis=dict(title=None, fixedrange=True),
        showlegend=False,
        hoverlabel=dict(
            bgcolor="#303030",
            bordercolor="#303030",
            font=dict(color="white", size=14),
            align="left"
        ),
        font=dict(
            family="Source Sans Pro",
            size=14
        )
    )

    st.plotly_chart(fig_diario,
        config={"displayModeBar": False, "scrollZoom": False, "doubleClick": False}
    )

    # ----------------- GRÁFICO MENSAL -----------------
    df_mensal = get_monthly_cases()
    
    # Se não houver dados, cria um dataframe vazio
    if df_mensal.empty:
        st.warning("Nenhum dado disponível para o gráfico mensal.")
        df_mensal = pd.DataFrame({"mes": pd.date_range(end=pd.Timestamp.today(), periods=12, freq="MS"), "casos": 0})
    else:
        # Converte coluna de data se necessário
        df_mensal['mes'] = pd.to_datetime(df_mensal['mes'])

    fig_mensal = go.Figure()

    fig_mensal.add_trace(
        go.Bar(
            x=df_mensal["mes"],
            y=df_mensal["casos"],
            marker=dict(color="#2563EB", line=dict(width=0)),
            hovertemplate=(
                "<b>📅 %{x|%m/%Y}</b><br><br>"
                "Casos: <b>%{y}</b>"
                "<extra></extra>"
            )
        )
    )

    fig_mensal.update_layout(
        title="Número mensal de casos de SRAG (últimos 12 meses)",
        template="plotly_white",
        height=380,
        dragmode=False,
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis=dict(title=None, fixedrange=True),
        yaxis=dict(title=None, fixedrange=True),
        showlegend=False,
        hoverlabel=dict(
            bgcolor="#303030",
            bordercolor="#303030",
            font=dict(color="white", size=14),
            align="left"
        ),
        font=dict(
            family="Source Sans Pro",
            size=14
        )
    )

    st.plotly_chart(fig_mensal,
        config={"displayModeBar": False, "scrollZoom": False, "doubleClick": False}
    )

# ----------------- CHAT -----------------
with col_chat:
    st.title("💬 SRAG Agent")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Digite sua mensagem...")

    if prompt:
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        response = f"Echo: {prompt}"

        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })

        st.rerun()

