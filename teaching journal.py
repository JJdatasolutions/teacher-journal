import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import os
import hashlib

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Leerkrachtenmonitor",
    page_icon="🍎",
    layout="centered"
)

DATA_DIR = "data"
USERS_FILE = f"{DATA_DIR}/users.csv"
os.makedirs(DATA_DIR, exist_ok=True)

# -------------------------------------------------
# SECURITY
# -------------------------------------------------
def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def check_pw(pw: str, hashed: str) -> bool:
    return hash_pw(pw) == hashed

# -------------------------------------------------
# USERS
# -------------------------------------------------
def load_users():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame(columns=["email", "password", "role"]).to_csv(USERS_FILE, index=False)
    return pd.read_csv(USERS_FILE)

def save_users(df):
    df.to_csv(USERS_FILE, index=False)

def teacher_file(email):
    name = email.split("@")[0]
    return f"{DATA_DIR}/{name}.csv"

# -------------------------------------------------
# AUTH
# -------------------------------------------------
st.title("🍎 Leerkrachtenmonitor")

users = load_users()

if "user" not in st.session_state:
    tab_login, tab_reg = st.tabs(["🔐 Inloggen", "🆕 Registreren"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        pw = st.text_input("Wachtwoord", type="password", key="login_pw")

        if st.button("Inloggen"):
            u = users[users.email == email]
            if not u.empty and check_pw(pw, u.iloc[0].password):
                st.session_state.user = u.iloc[0].to_dict()
                st.rerun()
            else:
                st.error("Ongeldige login")

    with tab_reg:
        r_email = st.text_input("School-email (@vvx.go-next.be)", key="reg_email")
        r_pw = st.text_input("Wachtwoord", type="password", key="reg_pw")

        if st.button("Account aanmaken"):
            if not r_email.endswith("@vvx.go-next.be"):
                st.error("Enkel schoolaccounts toegestaan")
            elif r_email in users.email.values:
                st.error("Account bestaat al")
            elif len(r_pw) < 8:
                st.error("Wachtwoord moet minstens 8 tekens bevatten")
            else:
                role = "director" if r_email.startswith("directie") else "teacher"
                users.loc[len(users)] = [r_email, hash_pw(r_pw), role]
                save_users(users)
                st.success("Account succesvol aangemaakt!")

    st.stop()

# -------------------------------------------------
# SESSION
# -------------------------------------------------
user = st.session_state.user
st.sidebar.success(f"Ingelogd als {user['email']}")

if st.sidebar.button("Uitloggen"):
    st.session_state.clear()
    st.rerun()

# -------------------------------------------------
# TEACHER VIEW
# -------------------------------------------------
if user["role"] == "teacher":

    FILE = teacher_file(user["email"])

    if not os.path.exists(FILE):
        pd.DataFrame(columns=[
            "Datum",
            "Klas",
            "Mentale helderheid",
            "Energie",
            "Stress",
            "Didactiek",
            "Klasmanagement"
        ]).to_csv(FILE, index=False)

    df = pd.read_csv(FILE)

    st.header("📝 Les registreren")

    with st.form("log_form"):
        datum = st.date_input("Datum", date.today(), key="log_date")
        klas = st.selectbox("Klas", ["5MT", "6MT", "5HW", "6WEWI"], key="log_class")
        m = st.slider("Mentale helderheid", 1, 10, 7, key="log_mental")
        e = st.slider("Energie", 1, 10, 6, key="log_energy")
        s = st.slider("Stress", 1, 10, 3, key="log_stress")
        d = st.selectbox("Didactiek", [1,2,3,4,5], index=2, key="log_did")
        k = st.selectbox("Klasmanagement", [1,2,3,4,5], index=2, key="log_km")

        if st.form_submit_button("💾 Opslaan"):
            df.loc[len(df)] = [datum, klas, m, e, s, d, k]
            df.to_csv(FILE, index=False)
            st.success("Les succesvol opgeslagen")
            st.rerun()

    if not df.empty:
        st.header("📊 Jouw overzicht")
        fig = px.line(df, x="Datum", y=["Energie", "Stress"], markers=True)
        st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------
# DIRECTOR VIEW
# -------------------------------------------------
else:
    st.header("🏫 Overzicht per klas")

    all_data = []

    for f in os.listdir(DATA_DIR):
        if f.endswith(".csv") and f != "users.csv":
            all_data.append(pd.read_csv(f"{DATA_DIR}/{f}"))

    if not all_data:
        st.info("Nog geen gegevens beschikbaar")
        st.stop()

    big = pd.concat(all_data)

    overzicht = (
        big
        .groupby("Klas")
        .mean(numeric_only=True)
        .round(2)
        .reset_index()
    )

    st.dataframe(overzicht, use_container_width=True)

    fig = px.bar(
        overzicht,
        x="Klas",
        y=[
            "Mentale helderheid",
            "Energie",
            "Stress",
            "Didactiek",
            "Klasmanagement"
        ],
        barmode="group"
    )

    st.plotly_chart(fig, use_container_width=True)
