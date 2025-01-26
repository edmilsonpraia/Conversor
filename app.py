import streamlit as st
import pandas as pd
import numpy as np
import io
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Adicionar a função get_depth_column que estava faltando
def get_depth_column(df):
    """
    Identifica a coluna de profundidade no DataFrame.
    Procura por nomes comuns de colunas de profundidade.
    """
    depth_columns = ['DEPTH', 'MD', 'TVD', 'DEPT', 'PROFUNDIDADE', 'PROF']
    
    # Primeiro, procura correspondência exata
    for col in depth_columns:
        if col in df.columns:
            return col
    
    # Se não encontrar, procura por correspondência parcial
    for col in df.columns:
        if any(depth_name.lower() in col.lower() for depth_name in depth_columns):
            return col
    
    # Se ainda não encontrou, usa a primeira coluna
    return df.columns[0]

# Import lasio with detailed error handling
try:
    import lasio
except ImportError as e:
    st.error(f"""
        Erro ao importar lasio. 
        Detalhes do erro: {str(e)}
        Verifique se todas as dependências estão instaladas corretamente.
    """)
    st.stop()
except Exception as e:
    st.error(f"""
        Erro inesperado ao importar lasio.
        Detalhes do erro: {str(e)}
        Por favor, contate o administrador.
    """)
    st.stop()

def plot_basic_logs(df, depth_col):
    """Cria um plot básico dos perfis."""
    # Curvas comuns em perfis de poço
    available_curves = ['GR', 'RHOB', 'NPHI', 'RT', 'DT', 'CALI', 'SP']
    curves_to_plot = [curve for curve in available_curves if curve in df.columns]
    
    if not curves_to_plot:
        st.warning("Nenhuma curva padrão encontrada no arquivo.")
        curves_to_plot = list(df.columns)
        if depth_col in curves_to_plot:
            curves_to_plot.remove(depth_col)
    
    if not curves_to_plot:
        st.error("Não há curvas para plotar.")
        return None
        
    # Criar figura
    fig = go.Figure()
    
    # Adicionar cada curva com cores diferentes
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']
    
    for i, curve in enumerate(curves_to_plot):
        fig.add_trace(
            go.Scatter(
                x=df[curve],
                y=df[depth_col],
                name=curve,
                line=dict(color=colors[i % len(colors)], width=1.5)
            )
        )
    
    # Atualizar layout
    fig.update_layout(
        height=800,
        template="plotly_white",
        title={
            'text': "Visualização dos Perfis",
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=24)
        },
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99,
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="rgba(0, 0, 0, 0.2)",
            borderwidth=1
        ),
        yaxis=dict(
            autorange="reversed",
            title=f"Profundidade ({depth_col})",
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)',
            zeroline=False
        ),
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)',
            zeroline=False
        ),
        plot_bgcolor='white'
    )
    
    return fig

def las_to_csv(las_file):
    """Convert LAS file to CSV."""
    try:
        las_bytes = las_file.read()
        las_str = las_bytes.decode('utf-8')
        las_io = io.StringIO(las_str)
        las = lasio.read(las_io)
        
        df = las.df()
        depth_name = las.index_unit
        if not depth_name:
            depth_name = 'DEPTH'
        
        df = df.reset_index()
        df = df.rename(columns={'index': depth_name})
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao ler o arquivo LAS: {str(e)}")
        return None

def csv_to_las(csv_file, well_info=None):
    """Convert CSV file to LAS."""
    try:
        df = pd.read_csv(csv_file)
        las = lasio.LASFile()
        
        if well_info:
            for key, value in well_info.items():
                las.well[key] = value
        
        depth_col = get_depth_column(df)
        depth = df[depth_col].values
        
        las.append_curve(depth_col, depth, unit='m')
        
        for column in df.columns:
            if column != depth_col:
                las.append_curve(column, df[column].values)
        
        return las
        
    except Exception as e:
        st.error(f"Erro ao converter para LAS: {str(e)}")
        return None

def main():
    # Configuração da página
    st.set_page_config(
        page_title="Conversor de LAS para CSV e CSV para LAS",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS personalizado
    st.markdown("""
        <style>
        .main {
            padding: 0rem 1rem;
        }
        .stButton>button {
            width: 100%;
            border-radius: 5px;
            height: 3em;
            background-color: #4CAF50;
            color: white;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        .upload-box {
            border: 2px dashed #cccccc;
            border-radius: 5px;
            padding: 2rem;
            text-align: center;
            background-color: #f8f9fa;
        }
        .success-box {
            padding: 1rem;
            border-radius: 5px;
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
        .info-box {
            background-color: #f8f9fa;
            padding: 1.5rem;
            border-radius: 5px;
            border: 1px solid #dee2e6;
            margin: 1rem 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Título principal com ícone
    st.markdown("""
        <h1 style='text-align: center; color: #2C3E50; margin-bottom: 2rem;'>
            🎯 Well Log Converter
        </h1>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🛠️ Configurações")
        conversion_type = st.radio(
            "Tipo de Conversão:",
            ('LAS para CSV', 'CSV para LAS'),
            key="conversion_type"
        )
    
    # Área principal
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if conversion_type == 'LAS para CSV':
            st.markdown("""
                <div class='info-box'>
                    <h3>📤 Justificações Acadêmicas</h3>
                </div>
            """, unsafe_allow_html=True)
            
            las_file = st.file_uploader(
                "Arraste e solte seu arquivo LAS aqui",
                type=['las'],
                help="Aceita apenas arquivos .las"
            )
            
            if las_file is not None:
                df = las_to_csv(las_file)
                
                if df is not None:
                    depth_col = get_depth_column(df)
                    
                    st.markdown("""
                        <div class='success-box'>
                            ✅ Arquivo convertido com sucesso!
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Estatísticas básicas
                    st.markdown("### 📊 Estatísticas Básicas")
                    st.dataframe(
                        df.describe(),
                        use_container_width=True,
                        height=300
                    )
                    
                    # Download do CSV
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="⬇️ Download CSV",
                        data=csv,
                        file_name="converted.csv",
                        mime="text/csv"
                    )
                    
                    # Plot na coluna 2
                    with col2:
                        st.markdown("### 📈 Visualização dos Perfis")
                        fig = plot_basic_logs(df, depth_col)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
        
        else:  # CSV para LAS
            st.markdown("""
                <div class='info-box'>
                    <h3>📤 Upload do Arquivo CSV</h3>
                </div>
            """, unsafe_allow_html=True)
            
            csv_file = st.file_uploader(
                "Arraste e solte seu arquivo CSV aqui",
                type=['csv'],
                help="Aceita apenas arquivos .csv"
            )
            
            if csv_file is not None:
                st.markdown("### ℹ️ Informações do Poço")
                
                with st.container():
                    well_info = {}
                    col1_sub, col2_sub = st.columns(2)
                    
                    with col1_sub:
                        well_info['WELL'] = st.text_input("Nome do Poço")
                        well_info['FLD'] = st.text_input("Campo")
                    with col2_sub:
                        well_info['COMP'] = st.text_input("Companhia")
                        well_info['DATE'] = st.date_input("Data")
                
                las = csv_to_las(csv_file, well_info)
                
                if las is not None:
                    string_buffer = io.StringIO()
                    las.write(string_buffer)
                    las_str = string_buffer.getvalue().encode('utf-8')
                    
                    st.markdown("""
                        <div class='success-box'>
                            ✅ Arquivo convertido com sucesso!
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.download_button(
                        label="⬇️ Download LAS",
                        data=las_str,
                        file_name="converted.las",
                        mime="text/plain"
                    )
                    
                    with col2:
                        st.markdown("### 📝 Preview do Arquivo LAS")
                        st.text_area(
                            "Conteúdo do arquivo LAS",
                            string_buffer.getvalue()[:1000] + "\n...",
                            height=400
                        )

if __name__ == "__main__":
    main()
