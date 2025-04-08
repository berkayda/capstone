import streamlit as st
import streamlit.components.v1 as components
import httpx
import time
import os
from dotenv import load_dotenv
from websocket_client import get_binance_ws

# === Session State Initialize ===
# Eğer token yoksa, kullanıcı henüz giriş yapmamıştır.
if "token" not in st.session_state:
    st.session_state["token"] = ""
# "auth_page" kontrolü: 'login' veya 'register'
if "auth_page" not in st.session_state:
    st.session_state["auth_page"] = "login"
# Eğer ws_client daha önce oluşturulmamışsa, oluştur
if "ws_client" not in st.session_state:
    st.session_state["ws_client"] = get_binance_ws()

# .env dosyasını yükle
dotenv_path = os.path.join(os.path.dirname(__file__), "../backend/.env")
load_dotenv(dotenv_path)

BASE_URL = "http://localhost:8000"

# === Eğer kullanıcı henüz giriş yapmamışsa, sidebar gizlensin ===
if not st.session_state["token"]:
    # Sidebar gizlemek için CSS
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {display: none;}
        </style>
        """,
        unsafe_allow_html=True
    )
    # Auth ekranı: login veya register modunda çalışır.
    if st.session_state["auth_page"] == "login":
        st.title("🔑 Capstone Projesi – Giriş")
        st.header("Kullanıcı Girişi")
        email = st.text_input("E-posta adresi", key="login_email")
        password = st.text_input("Şifre", type="password", key="login_password")
        # İki sütun: sol Giriş Yap, sağ Kayıt Ol butonu
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Giriş Yap"):
                with httpx.Client() as client:
                    response = client.post(f"{BASE_URL}/auth/login", json={
                        "email": email,
                        "password": password
                    })
                if response.status_code == 200:
                    st.session_state["token"] = response.json()['access_token']
                    st.success("Başarıyla giriş yaptınız!")
                    # Giriş sonrası Market Data sayfası varsayılan olsun
                    st.session_state["page"] = "Market Data"
                    st.rerun()
                else:
                    st.error(response.json().get("detail", "Hata oluştu."))
        with col2:
            if st.button("Kayıt Ol"):
                st.session_state["auth_page"] = "register"
                st.rerun()

    elif st.session_state["auth_page"] == "register":
        st.title("🔑 Capstone Projesi – Kayıt Ol")
        st.header("Yeni Hesap Oluştur")
        email = st.text_input("E-posta adresi", key="register_email")
        password = st.text_input("Şifre", type="password", key="register_password")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Kayıt Ol"):
                with httpx.Client() as client:
                    response = client.post(f"{BASE_URL}/auth/register", json={
                        "email": email,
                        "password": password
                    })
                if response.status_code == 200:
                    st.success("Kayıt başarıyla oluşturuldu!")
                else:
                    st.error(response.json().get("detail", "Bir hata oluştu."))
        with col2:
            if st.button("Giriş Yap"):
                st.session_state["auth_page"] = "login"
                st.rerun()

else:
    # === Kullanıcı Giriş yaptıysa: Sidebar görünür, yalnızca "Kullanıcı Bilgileri" ve "Market Data" seçenekleri olsun.
    menu = st.sidebar.radio("Menü", ["Kullanıcı Bilgileri", "Market Data"])

    if menu == "Kullanıcı Bilgileri":
        st.header("Kullanıcı Bilgilerim")
        token = st.session_state["token"]
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
            st.warning("Lütfen yeniden giriş yapın.")

    elif menu == "Market Data":
        # === Market Data Sayfası: Üst kısımda küçük ticker, orta portföy, alt trade history ===
        st.markdown("## Canlı Fiyatlar – Binance USDS Futures")
        # A) Üst Kısım: Küçük Ticker Satırı (Ticker'ın tasarımını çok yer kaplamayacak şekilde ayarlıyoruz)
        ws_client = st.session_state["ws_client"]
        prices = ws_client.latest_prices
        small_coin_map = {
            "BTCUSDT": "BTC/USDT",
            "ETHUSDT": "ETH/USDT",
            "BNBUSDT": "BNB/USDT",
            "SOLUSDT": "SOL/USDT",
            "XRPUSDT": "XRP/USDT"
        }

        # CSS ve HTML Tasarımı – Ticker, Portföy ve Trade History bölümleri
        css_code = """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
        body, .small-ticker-label, .small-ticker-price, .portfolio-title, .portfolio-value, .trade-history h3 {
            font-family: 'Inter', sans-serif;
        }
        /* Üst Ticker için */
        .ticker-container {
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
            justify-content: center;
            flex-wrap: wrap;
        }
        .ticker-box {
            background-color: #fafafa;
            border-radius: 8px;
            padding: 6px 10px;
            text-align: center;
            box-shadow: 1px 1px 4px rgba(0,0,0,0.1);
            min-width: 80px;
        }
        .small-ticker-label {
            color: #555;
            font-size: 12px;
            margin: 0;
            font-weight: 600;
        }
        .small-ticker-price {
            color: #007bff;
            font-size: 14px;
            font-weight: 600;
            margin: 0;
        }
        /* Orta: Portföy Bilgisi */
        .portfolio-container {
            margin-top: 20px;
            padding: 15px 20px;
            border-radius: 10px;
            background-color: #f0f2f6;
            text-align: center;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.1);
        }
        .portfolio-title {
            font-size: 20px;
            color: #333;
            margin-bottom: 10px;
            font-weight: 600;
        }
        .portfolio-value {
            font-size: 28px;
            color: #007bff;
            font-weight: bold;
            margin-bottom: 8px;
        }
        .portfolio-changes {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-top: 10px;
        }
        .change-box {
            background-color: #fff;
            padding: 6px 8px;
            border-radius: 8px;
            box-shadow: 1px 1px 4px rgba(0,0,0,0.1);
            min-width: 70px;
        }
        .change-label {
            font-size: 12px;
            color: #666;
            margin-bottom: 3px;
        }
        .change-value {
            font-size: 14px;
            font-weight: bold;
        }
        /* Alt: Trade History */
        .trade-history {
            margin-top: 20px;
        }
        .trade-history h3 {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        table.trade-table {
            width: 100%;
            border-collapse: collapse;
        }
        table.trade-table th, table.trade-table td {
            padding: 6px;
            border: 1px solid #ddd;
            text-align: left;
            font-size: 12px;
        }
        table.trade-table th {
            background-color: #eee;
        }
        </style>
        """

        # A) Ticker HTML: Üst kısımda küçük ticker kutuları
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
            ticker_html += """<div style="color: #999;">Fiyat verisi bekleniyor...</div>"""
        ticker_html += "</div>"

        # B) Orta: Portföy Bilgisi (placeholder değerler; gerçek API ile değiştirilebilir)
        portfolio_value = 12548.32  # Örnek
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

        # C) Alt: Trade History (placeholder tablo)
        trade_html = """
            <div class="trade-history">
                <h3>Trade History</h3>
                <table class="trade-table">
                    <tr>
                        <th>Coin</th>
                        <th>Side</th>
                        <th>Quantity</th>
                        <th>Price</th>
                        <th>PNL</th>
                        <th>Time</th>
                    </tr>
                    <tr>
                        <td>BTC/USDT</td>
                        <td>BUY</td>
                        <td>0.002</td>
                        <td>$28,500.00</td>
                        <td style="color: green;">+$10.50</td>
                        <td>2025-03-23 14:30</td>
                    </tr>
                    <tr>
                        <td>ETH/USDT</td>
                        <td>SELL</td>
                        <td>0.05</td>
                        <td>$1,800.00</td>
                        <td style="color: red;">-$3.25</td>
                        <td>2025-03-23 15:10</td>
                    </tr>
                </table>
            </div>
            """

        # Final HTML birleştirme
        final_html = css_code + ticker_html + portfolio_html + trade_html
        components.html(final_html, height=700, scrolling=True)

        time.sleep(1)
        st.rerun()
