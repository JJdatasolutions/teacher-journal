import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import os
import hashlib

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
st.set_page_config("Leerkrachtenmonitor", "🍎", layout="centered")

DATA_DIR = "data"
USERS_FILE = f"{DATA_DIR}/users.csv"
os.makedirs(DATA_DIR, exist_ok=True)

# -------------------------------------------------
# SECURITY
# -------------------------------------------------
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def check_pw(pw, hashed):
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
    return f"{DATA_DIR}/{email.split('@')[0]}.csv"

# -------------------------------------------------
# AUTO LOGIN VIA QUERY PARAM
# -------------------------------------------------
params = st.experimental_get_query_params()
if "user" in params and "user" not in st.session_state:
    users = load_users()
    u = users[users.email == params["user"][0]]
    if not u.empty:
        st.session_state.user = u.iloc[0].to_dict()

# -------------------------------------------------
# AUTH
# -------------------------------------------------
st.title("🍎 Leerkrachtenmonitor")
users = load_users()

if "user" not in st.session_state:
    tab1, tab2 = st.tabs(["🔐 Inloggen", "🆕 Registreren"])

    with tab1:
        email = st.text_input("Email", key="login_email")
        pw = st.text_input("Wachtwoord", type="password", key="login_pw")
        remember = st.checkbox("Onthoud mij")

        if st.button("Inloggen"):
            u = users[users.email == email]
            if not u.empty and check_pw(pw, u.iloc[0].password):
                st.session_state.user = u.iloc[0].to_dict()
                if remember:
                    st.experimental_set_query_params(user=email)
                st.rerun()
            else:
                st.error("Ongeldige login")

    with tab2:
        r_email = st.text_input("School-email (@vvx.go-next.be)", key="reg_email")
        r_pw = st.text_input("Wachtwoord", type="password", key="reg_pw")

        if st.button("Account aanmaken"):
            if not r_email.endswith("@vvx.go-next.be"):
                st.error("Enkel schoolaccounts toegestaan")
            elif r_email in users.email.values:
                st.error("Account bestaat al")
            elif len(r_pw) < 8:
                st.error("Minstens 8 tekens")
            else:
                role = "director" if r_email.startswith("directie") else "teacher"
                users.loc[len(users)] = [r_email, hash_pw(r_pw), role]
                save_users(users)
                st.success("Account aangemaakt!")

    st.stop()

# -------------------------------------------------
# SESSION
# -------------------------------------------------
user = st.session_state.user
st.sidebar.success(user["email"])

if st.sidebar.button("Uitloggen"):
    st.experimental_set_query_params()
    st.session_state.clear()
    st.rerun()

# -------------------------------------------------
# TEACHER VIEW
# -------------------------------------------------
if user["role"] == "teacher":

    FILE = teacher_file(user["email"])
    if not os.path.exists(FILE):
        pd.DataFrame(columns=[
            "Datum","Klas","Energie","Stress","Didactiek","Klasmanagement","Positief","Negatief"
        ]).to_csv(FILE, index=False)

    df = pd.read_csv(FILE)

    tab1, tab2, tab3 = st.tabs(["📝 Registratie", "🔥 Vergelijk klassen", "🌡️ Lesmood"])

    # ---------- REGISTRATIE ----------
    with tab1:
        with st.form("log"):
            d = st.date_input("Datum", date.today())
            klas = st.selectbox("Klas", ["5MT","6MT","5HW","6WEWI"])
            e = st.slider("Energie", 1, 10, 6)
            s = st.slider("Stress", 1, 10, 3)
            did = st.selectbox("Didactiek", [1,2,3,4,5], index=2)
            km = st.selectbox("Klasmanagement", [1,2,3,4,5], index=2)

            pos = st.multiselect(
                "Positieve leskenmerken",
                ["Inspirerend","Motiverend","Actief","Verbondenheid","Respectvol","Gefocust","Humor"]
            )

            neg = st.multiselect(
                "Negatieve leskenmerken",
                ["Stresserend","Passief","Opstandig","Onrespectvol","Chaotisch","Vermoeiend"]
            )

            if st.form_submit_button("Opslaan"):
                df.loc[len(df)] = [
                    d, klas, e, s, did, km,
                    ", ".join(pos), ", ".join(neg)
                ]
                df.to_csv(FILE, index=False)
                st.success("Les opgeslagen")
                st.rerun()

    # ---------- VERGELIJK KLASSEN ----------
    with tab2:
        if df.empty:
            st.info("Nog geen data")
        else:
            gemiddelden = (
                df.groupby("Klas")
                .mean(numeric_only=True)
                .reset_index()
            )

            fig = px.imshow(
                gemiddelden.set_index("Klas"),
                color_continuous_scale="GnBu",
                aspect="auto"
            )
            st.plotly_chart(fig, use_container_width=True)

    # ---------- LESMOOD ----------
with tab3:
    if df.empty:
        st.info("Nog geen mood-data")
    else:
        # Splits de tags en maak er een platte lijst van
        pos = df["Positief"].fillna("").astype(str).str.split(", ").explode()
        neg = df["Negatief"].fillna("").astype(str).str.split(", ").explode()

        # Filter lege strings weg
        tags = [t for t in list(pos) + list(neg) if t != ""]

        if not tags:
            st.info("Nog geen mood-data")
        else:
            tag_df = pd.DataFrame(tags, columns=["Lesmood"])
            
            # Sorteer op frequentie voor een cleaner overzicht
            fig = px.histogram(
                tag_df,
                y="Lesmood",
                title="Frequentie van lesmoods",
                category_orders={"Lesmood": tag_df["Lesmood"].value_counts().index.tolist()}
            )
            
            # Update layout voor betere leesbaarheid
            fig.update_layout(yaxis_title="Mood Tag", xaxis_title="Aantal keer gekozen")
            
            st.plotly_chart(fig, use_container_width=True)


# -------------------------------------------------
# DIRECTOR VIEW
# -------------------------------------------------
else:
    st.header("🏫 Globaal klasoverzicht")
    all_data = []

    for f in os.listdir(DATA_DIR):
        if f.endswith(".csv") and f != "users.csv":
            all_data.append(pd.read_csv(f"{DATA_DIR}/{f}"))

    if all_data:
        big = pd.concat(all_data)
        overzicht = big.groupby("Klas").mean(numeric_only=True).round(2)
        st.dataframe(overzicht)
    else:
        st.info("Nog geen data beschikbaar")



