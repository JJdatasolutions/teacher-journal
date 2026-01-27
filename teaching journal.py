import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import os
import hashlib

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Leerkrachtenmonitor", page_icon="🍎")
DATA_DIR = "data"
USERS_FILE = f"{DATA_DIR}/users.csv"

os.makedirs(DATA_DIR, exist_ok=True)

# ---------------- HELPERS ----------------
def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def check_pw(password: str, hashed: str) -> bool:
    return hash_pw(password) == hashed

def load_users():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame(columns=["email", "password", "role"]).to_csv(USERS_FILE, index=False)
    return pd.read_csv(USERS_FILE)

def save_users(df):
    df.to_csv(USERS_FILE, index=False)

def teacher_file(email):
    name = email.split("@")[0]
    return f"{DATA_DIR}/{name}.csv"

# ---------------- AUTH ----------------
st.title("🍎 Leerkrachtenmonitor")

users = load_users()

if "user" not in st.session_state:
    tab1, tab2 = st.tabs(["🔐 Inloggen", "🆕 Registreren"])

    with tab1:
        email = st.text_input("Email")
        pw = st.text_input("Wachtwoord", type="password")

        if st.button("Inloggen"):
            u = users[users.email == email]
            if not u.empty and check_pw(pw, u.iloc[0].password):
                st.session_state.user = u.iloc[0].to_dict()
                st.rerun()
            else:
                st.error("Ongeldige login")

    with tab2:
        r_email = st.text_input("School-email (@vvx.go-next.be)")
        r_pw = st.text_input("Wachtwoord", type="password")

        if st.button("Account aanmaken"):
            if not r_email.endswith("@vvx.go-next.be"):
                st.error("Enkel schoolaccounts toegestaan")
            elif r_email in users.email.values:
                st.error("Account bestaat al")
            else:
                role = "director" if r_email.startswith("directie") else "teacher"
                users.loc[len(users)] = [r_email, hash_pw(r_pw), role]
                save_users(users)
                st.success("Account aangemaakt!")

    st.stop()

# ---------------- APP ----------------
user = st.session_state.user
st.sidebar.success(f"Ingelogd als {user['email']}")
if st.sidebar.button("Uitloggen"):
    st.session_state.clear()
    st.rerun()

# ---------------- TEACHER VIEW ----------------
if user["role"] == "teacher":
    FILE = teacher_file(user["email"])
    if not os.path.exists(FILE):
        pd.DataFrame(columns=[
            "Datum", "Klas", "Mentale helderheid", "Energie", "Stress",
            "Didactiek", "Klasmanagement"
        ]).to_csv(FILE, index=False)

    df = pd.read_csv(FILE)

    st.header("📝 Les registreren")
    with st.form("log"):
        d = st.date_input("Datum", date.today())
        klas = st.selectbox("Klas", ["5MT", "6MT", "5HW"])
        m = st.slider("Mentale helderheid", 1, 10, 7)
        e = st.slider("Energie", 1, 10, 6)
        s = st.slider("Stress", 1, 10, 3)
        did = st.selectbox("Didactiek", [1,2,3,4,5], index=2)
        km = st.selectbox("Klasmanagement", [1,2,3,4,5], index=2)

        if st.form_submit_button("Opslaan"):
            df.loc[len(df)] = [d, klas, m, e, s, did, km]
            df.to_csv(FILE, index=False)
            st.success("Les opgeslagen!")

    if not df.empty:
        st.header("📊 Persoonlijk overzicht")
        fig = px.line(df, x="Datum", y=["Energie", "Stress"])
        st.plotly_chart(fig, use_container_width=True)

# ---------------- DIRECTOR VIEW ----------------
else:
    st.header("🏫 Overzicht per klas")

    all_data = []
    for f in os.listdir(DATA_DIR):
        if f.endswith(".csv") and f != "users.csv":
            df = pd.read_csv(f"{DATA_DIR}/{f}")
            all_data.append(df)

    if not all_data:
        st.info("Nog geen data beschikbaar")
        st.stop()

    big = pd.concat(all_data)

    grouped = big.groupby("Klas").mean(numeric_only=True).reset_index()
    st.dataframe(grouped, use_container_width=True)

    fig = px.bar(
        grouped,
        x="Klas",
        y=["Energie", "Mentale helderheid", "Stress", "Didactiek", "Klasmanagement"],
        barmode="group"
    )
    st.plotly_chart(fig, use_container_width=True)

