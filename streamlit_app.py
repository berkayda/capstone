import streamlit as st
import httpx
import time
import os
from dotenv import load_dotenv
from websocket_client import get_binance_ws  # websocket_client.py dosyasından import
import streamlit.components.v1 as components


# Gerekli session state değişkenlerini initialize et
if "page" not in st.session_state:
    st.session_state["page"] = "Giriş Yap"
if "token" not in st.session_state:
    st.session_state["token"] = ""

# .env dosyasını yükle (backend .env dosyasının yolunu ayarla)
dotenv_path = os.path.join(os.path.dirname(__file__), "../backend/.env")
load_dotenv(dotenv_path)

BASE_URL = "http://localhost:8000"

# Websocket client'ını tek sefer oluşturmak için st.cache kullanıyoruz.
@st.cache(allow_output_mutation=True)
def init_ws_client():
    return get_binance_ws()

ws_client = init_ws_client()

# Sidebar navigasyonu: Radio buton ile sayfa seçimi
options = ["Giriş Yap", "Kayıt Ol", "Kullanıcı Bilgileri", "Market Data"]
default_index = options.index(st.session_state["page"]) if st.session_state["page"] in options else 0
page = st.sidebar.radio("Sayfa Seçimi:", options, index=default_index)
st.session_state["page"] = page  # Navigasyon seçimini güncelle

st.title("🔑 Capstone Projesi – Giriş & Dashboard")

# Sayfa: Kayıt Ol
if page == "Kayıt Ol":
    st.header("Yeni Hesap Oluştur")
    email = st.text_input("E-posta adresi", key="register_email")
    password = st.text_input("Şifre", type="password", key="register_password")
    if st.button("Kaydol"):
        with httpx.Client() as client:
            response = client.post(f"{BASE_URL}/auth/register", json={
                "email": email,
                "password": password
            })
        if response.status_code == 200:
            st.success("Kayıt başarıyla oluşturuldu!")
        else:
            st.error(response.json().get("detail", "Bir hata oluştu."))

# Sayfa: Giriş Yap
elif page == "Giriş Yap":
    st.header("Kullanıcı Girişi")
    email = st.text_input("E-posta adresi", key="login_email")
    password = st.text_input("Şifre", type="password", key="login_password")
    if st.button("Giriş Yap"):
        with httpx.Client() as client:
            response = client.post(f"{BASE_URL}/auth/login", json={
                "email": email,
                "password": password
            })
        if response.status_code == 200:
            st.session_state["token"] = response.json()['access_token']
            st.success("Başarıyla giriş yaptınız!")
            st.session_state["page"] = "Kullanıcı Bilgileri"
            st.rerun()  # Sayfayı yeniden render et
        else:
            st.error(response.json().get("detail", "Hata oluştu."))

# Sayfa: Kullanıcı Bilgileri
elif page == "Kullanıcı Bilgileri":
    st.header("Kullanıcı Bilgilerim")
    token = st.session_state.get("token")
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        with httpx.Client() as client:
            response = client.get(f"{BASE_URL}/user/me", headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            st.write(f"E-posta: {user_data['email']}")
            st.write(f"Kayıt Tarihi: {user_data['created_at']}")
        else:
            st.error("Kullanıcı bilgileri alınamadı!")
    else:
        st.warning("Önce giriş yapmalısınız!")

elif page == "Market Data":
    st.markdown("## Canlı Fiyatlar – Binance USDS Futures")
    st.write("Her satırda 3 coin. Veriler her saniye yenilenir, caching yok.")

    # En güncel fiyatlar
    prices = ws_client.latest_prices

    # 5 coin
    coin_map = {
        "BTCUSDT": "BTC/USDT",
        "ETHUSDT": "ETH/USDT",
        "BNBUSDT": "BNB/USDT",
        "SOLUSDT": "SOL/USDT",
        "XRPUSDT": "XRP/USDT"
    }

    # CSS (Inter font, 3'lü satırlar)
    css_code = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    body, .coin-label, .coin-price {
        font-family: 'Inter', sans-serif;
    }
    .coin-row {
      display: flex;
      flex-wrap: wrap;   /* Alt satıra geçebilir */
      gap: 20px;
      justify-content: center;
      margin-top: 20px;
      margin-bottom: 20px;
    }
    .coin-box {
      background-color: #f8f9fa;
      width: 180px;
      min-width: 180px;
      padding: 25px;
      border-radius: 15px;
      text-align: center;
      box-shadow: 3px 3px 8px rgba(0,0,0,0.15);
      margin-bottom: 20px;
    }
    .coin-label {
      color: #333;
      font-size: 18px;
      font-weight: bold;
      margin-bottom: 10px;
    }
    .coin-price {
      color: #007bff;
      font-size: 32px;
      font-weight: bold;
      margin: 0;
      white-space: nowrap;
    }
    </style>
    """

    def chunk_list(items, n):
        for i in range(0, len(items), n):
            yield items[i:i+n]

    coin_items = list(coin_map.items())
    html_content = css_code

    if prices:
        # 4) 3'lü satırlar
        for row in chunk_list(coin_items, 3):
            row_html = '<div class="coin-row">'
            for symbol, label in row:
                raw_price = prices.get(symbol, None)
                if raw_price is not None:
                    price_float = float(raw_price)
                    formatted_price = f"${price_float:,.2f}"
                else:
                    formatted_price = "Veri Yok"
                row_html += f"""
                <div class="coin-box">
                    <div class="coin-label">{label}</div>
                    <div class="coin-price">{formatted_price}</div>
                </div>
                """
            row_html += "</div>"
            html_content += row_html
    else:
        html_content += """
        <div style="text-align: center; color: #666; margin-top: 20px;">
            📡 Fiyat verisi bekleniyor...
        </div>
        """

    # 5) Render
    components.html(html_content, height=600, scrolling=False)

    time.sleep(1)
    st.rerun()