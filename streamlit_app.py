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
if "ws_client" not in st.session_state:
    st.session_state["ws_client"] = get_binance_ws()  # WebSocket nesnesini oluştur

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

#st.title("🔑 Capstone Projesi – Giriş & Dashboard")

# Sayfa: Kayıt Ol
if page == "Kayıt Ol":
    st.title("🔑 Capstone Projesi – Kaydol")
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
    st.title("🔑 Capstone Projesi – Giriş")
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
            st.session_state["page"] = "Market Data"
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

# (Ön kısım: session_state, token, ws_client init vs. aynı kalsın...)
# Burada sadece Market Data sayfasını güncelliyoruz.

elif page == "Market Data":
    # 1) Üst Kısım: Küçük Ticker Satırı (5 coin)
    st.write("## Canlı Fiyatlar – Binance USDS Futures")

    ws_client = st.session_state["ws_client"]  # WebSocket nesnesi
    prices = ws_client.latest_prices  # 5 coin (BTC, ETH, BNB, SOL, XRP)

    # Bu coinler "küçük ticker" olarak gösterilecek
    small_coin_map = {
        "BTCUSDT": "BTC",
        "ETHUSDT": "ETH",
        "BNBUSDT": "BNB",
        "SOLUSDT": "SOL",
        "XRPUSDT": "XRP"
    }

    # CSS: Inter font, ufak ticker stili
    css_code = """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
        body, .small-ticker-label, .small-ticker-price {
            font-family: 'Inter', sans-serif;
        }
        .ticker-container {
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
            flex-wrap: wrap;  /* Alt satıra geçebilir */
        }
        .ticker-box {
            background-color: #fafafa;
            border-radius: 8px;
            padding: 8px 12px;
            text-align: center;
            box-shadow: 1px 1px 4px rgba(0,0,0,0.1);
            min-width: 90px;
        }
        .small-ticker-label {
            color: #555;
            font-size: 14px;
            margin: 0;
            font-weight: 600;
        }
        .small-ticker-price {
            color: #007bff;
            font-size: 16px;
            font-weight: 600;
            margin: 0;
        }
        /* Orta kısım: Portföy */
        .portfolio-container {
            margin-top: 20px;
            padding: 20px;
            border-radius: 10px;
            background-color: #f0f2f6;
            text-align: center;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.1);
        }
        .portfolio-title {
            font-size: 24px;
            color: #333;
            margin-bottom: 15px;
            font-weight: 600;
        }
        .portfolio-value {
            font-size: 32px;
            color: #007bff;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .portfolio-changes {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 10px;
        }
        .change-box {
            background-color: #fff;
            padding: 8px 12px;
            border-radius: 8px;
            box-shadow: 1px 1px 4px rgba(0,0,0,0.1);
            min-width: 80px;
        }
        .change-label {
            font-size: 14px;
            color: #666;
            margin-bottom: 3px;
        }
        .change-value {
            font-size: 16px;
            font-weight: bold;
        }
        /* Alt kısım: Trade History */
        .trade-history {
            margin-top: 30px;
        }
        .trade-history h3 {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 10px;
        }
        </style>
        """

    # Ticker HTML
    ticker_html = '<div class="ticker-container">'
    if prices:
        for symbol, short_label in small_coin_map.items():
            raw_price = prices.get(symbol, None)
            if raw_price is not None:
                price_float = float(raw_price)
                formatted_price = f"${price_float:,.2f}"
            else:
                formatted_price = "N/A"

            ticker_html += f"""
                <div class="ticker-box">
                    <p class="small-ticker-label">{short_label}</p>
                    <p class="small-ticker-price">{formatted_price}</p>
                </div>
                """
    else:
        # Fiyat yoksa
        ticker_html += """
            <div style="color: #999;">Fiyat verisi bekleniyor...</div>
            """
    ticker_html += "</div>"

    # 2) Orta Kısım: Kullanıcının Portföy Bilgisi (Sahte veriler)
    # Burada gerçekte Binance Account Info API / user data stream'den verileri çekebilirsin.
    # Örnek veriler:
    portfolio_value = 12548.32  # Sahte
    hourly_change = "+2.5%"
    daily_change = "-1.2%"
    weekly_change = "+5.6%"

    portfolio_html = f"""
        <div class="portfolio-container">
            <div class="portfolio-title">Portföy Bilgisi</div>
            <div class="portfolio-value">${portfolio_value:,.2f}</div>
            <div class="portfolio-changes">
                <div class="change-box">
                    <div class="change-label">Saatlik</div>
                    <div class="change-value">{hourly_change}</div>
                </div>
                <div class="change-box">
                    <div class="change-label">Günlük</div>
                    <div class="change-value">{daily_change}</div>
                </div>
                <div class="change-box">
                    <div class="change-label">Haftalık</div>
                    <div class="change-value">{weekly_change}</div>
                </div>
            </div>
        </div>
        """

    # 3) Alt Kısım: Trade History
    # Gerçekte Binance user data stream "ORDER_TRADE_UPDATE" event veya
    # account trade history endpoint ile doldurabilirsin.
    # Burada placeholder tablo yapıyoruz.
    trade_html = """
        <div class="trade-history">
            <h3>Trade History</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background-color: #eee; text-align: left;">
                    <th style="padding: 8px;">Coin</th>
                    <th style="padding: 8px;">Side</th>
                    <th style="padding: 8px;">Quantity</th>
                    <th style="padding: 8px;">Price</th>
                    <th style="padding: 8px;">PNL</th>
                    <th style="padding: 8px;">Time</th>
                </tr>
                <tr>
                    <td style="padding: 8px;">BTC/USDT</td>
                    <td style="padding: 8px;">BUY</td>
                    <td style="padding: 8px;">0.002</td>
                    <td style="padding: 8px;">$28,500.00</td>
                    <td style="padding: 8px; color: green;">+$10.50</td>
                    <td style="padding: 8px;">2025-03-23 14:30</td>
                </tr>
                <tr>
                    <td style="padding: 8px;">ETH/USDT</td>
                    <td style="padding: 8px;">SELL</td>
                    <td style="padding: 8px;">0.05</td>
                    <td style="padding: 8px;">$1,800.00</td>
                    <td style="padding: 8px; color: red;">-$3.25</td>
                    <td style="padding: 8px;">2025-03-23 15:10</td>
                </tr>
            </table>
        </div>
        """

    final_html = css_code + ticker_html + portfolio_html + trade_html

    components.html(final_html, height=700, scrolling=True)

    time.sleep(1)
    st.rerun()
