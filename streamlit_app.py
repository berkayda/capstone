import streamlit as st
import httpx
import time
import os
from dotenv import load_dotenv
from websocket_client import get_binance_ws

# === Session State Initialize ===
if "token" not in st.session_state:
    st.session_state["token"] = ""
if "auth_page" not in st.session_state:
    st.session_state["auth_page"] = "login"
if "ws_client" not in st.session_state:
    st.session_state["ws_client"] = get_binance_ws()
if "page" not in st.session_state:
    st.session_state["page"] = "Market Data"

# .env dosyasını yükle
dotenv_path = os.path.join(os.path.dirname(__file__), "../backend/.env")
load_dotenv(dotenv_path)

BASE_URL = "http://localhost:8000"


# === Giriş yapılmamışsa, sidebar gizle ve login/register sayfası göster ===
if not st.session_state["token"]:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {display: none;}
        </style>
        """,
        unsafe_allow_html=True
    )

    if st.session_state["auth_page"] == "login":
        st.title("🔑 Capstone Projesi – Giriş")
        st.header("Kullanıcı Girişi")
        email = st.text_input("E-posta adresi", key="login_email")
        password = st.text_input("Şifre", type="password", key="login_password")

        # Üç kolon: ilk ve üçüncüde butonlar, ortadaki sütun çok dar (neredeyse sıfır)
        col1, col_gap, col2 = st.columns([1, 0.001, 1])
        with col1:
            if st.button("Giriş Yap"):
                with httpx.Client() as client:
                    response = client.post(
                        f"{BASE_URL}/auth/login",
                        json={"email": email, "password": password}
                    )
                if response.status_code == 200:
                    st.session_state["token"] = response.json()['access_token']
                    st.success("Başarıyla giriş yaptınız!")
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

        # Üç kolon: boşluğu neredeyse sıfıra çekmek için
        col1, col_gap, col2 = st.columns([1, 0.001, 1])
        with col1:
            if st.button("Kayıt Ol"):
                with httpx.Client() as client:
                    response = client.post(
                        f"{BASE_URL}/auth/register",
                        json={"email": email, "password": password}
                    )
                if response.status_code == 200:
                    st.success("Kayıt başarıyla oluşturuldu!")
                else:
                    st.error(response.json().get("detail", "Bir hata oluştu."))

        with col2:
            if st.button("Giriş Yap"):
                st.session_state["auth_page"] = "login"
                st.rerun()

# === Giriş yapıldıysa ===
else:
    # --- Sidebar Menüsü ---
    menu = st.sidebar.radio(
        "Menü",
        ["Kullanıcı Bilgileri", "Market Data"],
        index=1 if st.session_state["page"] == "Market Data" else 0
    )

    if menu == "Kullanıcı Bilgileri":
        st.header("Kullanıcı Bilgilerim")

        token = st.session_state["token"]
        if token:
            headers = {"Authorization": f"Bearer {token}"}
            with httpx.Client() as client:
                response = client.get(f"{BASE_URL}/user/me", headers=headers)
            if response.status_code == 200:
                user_data = response.json()
                st.markdown(
                    f"""
                    <div style="background-color: #fff; border: 1px solid #ddd;
                                border-radius: 12px; padding: 20px; margin-bottom: 20px;
                                box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                        <p><strong>E-posta:</strong> {user_data['email']}</p>
                        <p><strong>Kayıt Tarihi:</strong> {user_data['created_at']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.error("Kullanıcı bilgileri alınamadı!")
        else:
            st.warning("Lütfen yeniden giriş yapın.")

        if st.button("Çıkış Yap"):
            st.session_state["token"] = ""
            st.session_state["auth_page"] = "login"
            st.session_state["page"] = "Market Data"
            st.rerun()

    elif menu == "Market Data":
        st.session_state["page"] = "Market Data"

        # Sayfa başlığı
        st.markdown("## Canlı Fiyatlar – Binance USDS Futures")

        # ======================
        # 0) Ortak CSS
        # ======================
        st.markdown(
            """
            <style>
            .ticker-container {
                display: flex; 
                gap: 15px; 
                justify-content: center; 
                flex-wrap: wrap; 
                margin-bottom: 15px;
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
                transition: all 0.3s ease-in-out;
            }
            /* Portföy */
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
            /* Trade History */
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
            """,
            unsafe_allow_html=True
        )

        # ======================
        # 1) Ticker yukarıda gösterilsin
        # ======================
        ticker_placeholder = st.empty()

        def render_ticker(prices):
            """Her saniye güncellenecek Ticker HTML'ini oluşturur."""
            small_coin_map = {
                "BTCUSDT": "BTC/USDT",
                "ETHUSDT": "ETH/USDT",
                "BNBUSDT": "BNB/USDT",
                "SOLUSDT": "SOL/USDT",
                "XRPUSDT": "XRP/USDT"
            }
            # Eğer websocketten bir coin verisi gelmezse "N/A" gösterilsin
            ticker_html = '<div class="ticker-container">'
            for symbol, short_label in small_coin_map.items():
                raw_price = prices.get(symbol)  # dict.get() -> None if not found
                if raw_price is not None:
                    price_float = float(raw_price)
                    formatted_price = f"${price_float:,.2f}"
                else:
                    formatted_price = "N/A"

                # Ticker kutusu
                ticker_html += (
                    f'<div class="ticker-box">'
                    f'<p class="small-ticker-label">{short_label}</p>'
                    f'<p class="small-ticker-price">{formatted_price}</p>'
                    f'</div>'
                )
            ticker_html += "</div>"
            return ticker_html

        # ======================
        # 2) Portföy ve Trade
        # ======================
        portfolio_html = """
        <div class="portfolio-container">
            <div class="portfolio-title">Portföy Bilgisi</div>
            <div class="portfolio-value">$12,548.32</div>
            <div class="portfolio-changes">
                <div class="change-box">
                    <div class="change-label">Saatlik</div>
                    <div class="change-value">+2.5%</div>
                </div>
                <div class="change-box">
                    <div class="change-label">Günlük</div>
                    <div class="change-value">-1.2%</div>
                </div>
                <div class="change-box">
                    <div class="change-label">Haftalık</div>
                    <div class="change-value">+5.6%</div>
                </div>
            </div>
        </div>
        """

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

        # Portföy + Trade tabloyu alt tarafta SABİT gösterelim:
        st.markdown(portfolio_html, unsafe_allow_html=True)
        st.markdown(trade_html, unsafe_allow_html=True)

        # ======================
        # 3) Sadece Ticker'ı sürekli güncelle
        # ======================
        while True:
            # 3a) Websocket'ten anlık fiyatları al
            prices = st.session_state["ws_client"].latest_prices
            # Örnek: prices = {"BTCUSDT": 24882.5, "ETHUSDT": 1550.4, ...}

            # 3b) Ticker HTML'i oluştur
            new_ticker_html = render_ticker(prices)

            # 3c) Yukarıdaki placeholder'da göster
            ticker_placeholder.markdown(new_ticker_html, unsafe_allow_html=True)

            # 3d) Her 1 saniyede bir güncelleme
            time.sleep(1)
