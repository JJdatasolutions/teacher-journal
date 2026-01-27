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
params = st.query_params
if "user" in params and "user" not in st.session_state:
    users = load_users()
    u = users[users.email == params["user"]]
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
                    st.query_params["user"] = email
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
st.sidebar.success(f"Ingelogd als: {user['email']}")

if st.sidebar.button("Uitloggen"):
    st.query_params.clear()
    st.session_state.clear()
    st.rerun()

# -------------------------------------------------
# MAIN LOGIC (TEACHER vs DIRECTOR)
# -------------------------------------------------
if user["role"] == "teacher":
    FILE = teacher_file(user["email"])
    if not os.path.exists(FILE):
        pd.DataFrame(columns=[
            "Datum","Klas","Energie","Stress","Didactiek","Klasmanagement","Positief","Negatief"
        ]).to_csv(FILE, index=False)

    df = pd.read_csv(FILE)

    tab1, tab2, tab3 = st.tabs(["📝 Registratie", "🔥 Vergelijk klassen", "🌡️ Lesmood"])

    with tab1:
        with st.form("log"):
            d = st.date_input("Datum", date.today())
            klas = st.selectbox("Klas", ["5MT","6MT","5HW","6WEWI"])
            e = st.slider("Energie", 1, 10, 6)
            s = st.slider("Stress", 1, 10, 3)
            did = st.selectbox("Didactiek", [1,2,3,4,5], index=2)
            km = st.selectbox("Klasmanagement", [1,2,3,4,5], index=2)

            pos_tags = st.multiselect(
                "Positieve leskenmerken",
                ["Inspirerend","Motiverend","Actief","Verbondenheid","Respectvol","Gefocust","Humor"]
            )

            neg_tags = st.multiselect(
                "Negatieve leskenmerken",
                ["Stresserend","Passief","Opstandig","Onrespectvol","Chaotisch","Vermoeiend"]
            )

            if st.form_submit_button("Opslaan"):
                new_data = pd.DataFrame([[
                    d, klas, e, s, did, km,
                    ", ".join(pos_tags), ", ".join(neg_tags)
                ]], columns=df.columns)
                df = pd.concat([df, new_data], ignore_index=True)
                df.to_csv(FILE, index=False)
                st.success("Les opgeslagen")
                st.rerun()

    with tab2:
    if df.empty:
        st.info("Nog geen data")
    else:
        norm_df = df.copy()

        # Normaliseren naar schaal /5
        norm_df["Energie (op 5)"] = norm_df["Energie"] / 2
        norm_df["Stress (op 5)"] = norm_df["Stress"] / 2
        norm_df["Didactiek (op 5)"] = norm_df["Didactiek"]
        norm_df["Klasmanagement (op 5)"] = norm_df["Klasmanagement"]

        heatmap_df = (
            norm_df
            .groupby("Klas")[[
                "Energie (op 5)",
                "Stress (op 5)",
                "Didactiek (op 5)",
                "Klasmanagement (op 5)"
            ]]
            .mean()
            .round(2)
        )

        fig = px.imshow(
            heatmap_df,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="RdYlGn",
            title="Gemiddelde leservaring per klas (schaal op 5)"
        )

        fig.update_layout(
            xaxis_title="Dimensie",
            yaxis_title="Klas"
        )

        st.plotly_chart(fig, use_container_width=True)


    with tab3:
    if df.empty:
        st.info("Nog geen mood-data")
    else:
        pos = df["Positief"].fillna("").astype(str).str.split(", ").explode()
        neg = df["Negatief"].fillna("").astype(str).str.split(", ").explode()

        mood_df = pd.DataFrame({
            "Mood": list(pos) + list(neg),
            "Type": (
                ["Positief"] * len(pos)
                + ["Negatief"] * len(neg)
            )
        })

        mood_df = mood_df[mood_df["Mood"] != ""]

        if mood_df.empty:
            st.info("Nog geen mood-tags geregistreerd")
        else:
            fig = px.histogram(
                mood_df,
                y="Mood",
                color="Type",
                barmode="group",
                title="Lesmoods – frequentie",
                color_discrete_map={
                    "Positief": "#2ECC71",
                    "Negatief": "#E74C3C"
                }
            )

            fig.update_layout(
                yaxis_title="Lesmood",
                xaxis_title="Aantal keer gekozen"
            )

            st.plotly_chart(fig, use_container_width=True)


# DIRECTOR VIEW
else:
    st.header("🏫 Globaal klasoverzicht")
    all_data = []

    files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv") and f != "users.csv"]
    
    for f in files:
        df_temp = pd.read_csv(os.path.join(DATA_DIR, f))
        if not df_temp.empty:
            all_data.append(df_temp)

    if all_data:
        big_df = pd.concat(all_data, ignore_index=True)
        overzicht = big_df.groupby("Klas").mean(numeric_only=True).round(2)

        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Cijfers")
            st.dataframe(overzicht, use_container_width=True)
            
        with col2:
            st.subheader("Visuele Trends")
            fig_dir = px.imshow(
                overzicht.T, 
                text_auto=True, 
                aspect="auto",
                color_continuous_scale="RdYlGn",
                title="Sterktes en zwaktes per klas"
            )
            st.plotly_chart(fig_dir, use_container_width=True)
    else:
        st.info("Nog geen data beschikbaar om een overzicht te genereren.")

