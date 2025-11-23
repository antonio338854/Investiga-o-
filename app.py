import streamlit as st
from PIL import Image, ExifTags
import pandas as pd
import folium
from streamlit_folium import st_folium

# === Configuração da Página ===
st.set_page_config(page_title="Extrator Forense Tony", page_icon="🔬", layout="wide")

st.title("🔬 Extrator Forense de Metadados (CSI)")
st.markdown("### Revele o que está escondido dentro do arquivo da foto.")

# === Funções Cirúrgicas do Tony ===
def converter_coordenada(coords, ref):
    """Converte coordenadas GPS do formato EXIF (DMS) para Decimal"""
    decimal_degrees = coords[0] + coords[1] / 60 + coords[2] / 3600
    if ref == "S" or ref == "W":
        decimal_degrees = -decimal_degrees
    return decimal_degrees

def extrair_metadados(image):
    img_exif = image.getexif()
    dados = {}
    gps_dados = {}

    if not img_exif:
        return None, None

    # Mapeia os códigos numéricos para nomes legíveis (Ex: 306 -> DateTime)
    for tag_id, value in img_exif.items():
        tag = ExifTags.TAGS.get(tag_id, tag_id)
        
        # Se for dados de GPS, precisa de tratamento especial
        if tag == "GPSInfo":
            for key in value.keys():
                sub_tag = ExifTags.GPSTAGS.get(key, key)
                gps_dados[sub_tag] = value[key]
        else:
            dados[tag] = value

    return dados, gps_dados

def processar_gps(gps_info):
    """Extrai Lat/Lon se existir"""
    if not gps_info:
        return None, None
    
    try:
        lat_raw = gps_info.get("GPSLatitude")
        lat_ref = gps_info.get("GPSLatitudeRef")
        lon_raw = gps_info.get("GPSLongitude")
        lon_ref = gps_info.get("GPSLongitudeRef")
        
        if lat_raw and lat_ref and lon_raw and lon_ref:
            lat = converter_coordenada(lat_raw, lat_ref)
            lon = converter_coordenada(lon_raw, lon_ref)
            return lat, lon
        return None, None
    except:
        return None, None

# === Interface Principal ===
st.sidebar.info("💡 Dica do Tony: Fotos enviadas pelo WhatsApp perdem os metadados (o Zap apaga). Use fotos originais da câmera ou enviadas como 'Documento'.")

upload_arquivo = st.file_uploader("Arraste a foto suspeita aqui (JPG/JPEG)", type=["jpg", "jpeg"])

if upload_arquivo:
    image = Image.open(upload_arquivo)
    
    # Colunas para layout bonito
    col_img, col_dados = st.columns([1, 2])
    
    with col_img:
        st.image(image, caption="Evidência", use_column_width=True)
    
    with col_dados:
        st.subheader("🔍 Análise Técnica")
        try:
            dados_gerais, dados_gps = extrair_metadados(image)
            
            if dados_gerais:
                # Cria tabela limpa com os dados principais
                info_importante = {
                    "Fabricante": dados_gerais.get("Make", "Desconhecido"),
                    "Modelo": dados_gerais.get("Model", "Desconhecido"),
                    "Software": dados_gerais.get("Software", "N/A"),
                    "Data/Hora Original": dados_gerais.get("DateTimeOriginal", dados_gerais.get("DateTime", "N/A")),
                    "Dimensões": f"{dados_gerais.get('ExifImageWidth', '?')} x {dados_gerais.get('ExifImageHeight', '?')}"
                }
                st.table(pd.DataFrame(info_importante.items(), columns=["Propriedade", "Valor"]))
                
                with st.expander("Ver Todos os Dados Brutos (Avançado)"):
                    # Filtra dados binários que quebram a tela
                    dados_limpos = {k: str(v) for k, v in dados_gerais.items() if len(str(v)) < 500}
                    st.json(dados_limpos)
            else:
                st.warning("Esta imagem não possui metadados (EXIF). Pode ter sido editada ou baixada de rede social.")

        except Exception as e:
            st.error(f"Erro na extração: {e}")

    # === Seção GPS (O Ouro) ===
    st.markdown("---")
    st.subheader("🌍 Rastreamento de Localização")
    
    if dados_gps:
        lat, lon = processar_gps(dados_gps)
        
        if lat and lon:
            st.success(f"📍 Coordenadas Encontradas: {lat}, {lon}")
            st.info("Local exato onde o obturador da câmera disparou.")
            
            # Mapa
            m = folium.Map(location=[lat, lon], zoom_start=15)
            folium.Marker(
                [lat, lon], 
                popup="Local da Foto", 
                icon=folium.Icon(color="red", icon="camera"),
                tooltip="Clique aqui"
            ).add_to(m)
            
            st_folium(m, width=800, height=500)
            
            # Link para Google Maps Externo
            st.markdown(f"[➡️ Abrir no Google Maps](https://www.google.com/maps/search/?api=1&query={lat},{lon})")
        else:
            st.warning("A imagem tem dados de GPS, mas estão corrompidos ou incompletos.")
    else:
        st.error("🚫 Rastro Limpo: Nenhuma informação de GPS encontrada nesta imagem.")

# === Rodapé ===
st.markdown("---")
st.markdown("<center>Laboratório Forense Tony</center>", unsafe_allow_html=True)
