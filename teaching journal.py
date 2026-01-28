import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
import os
import hashlib
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Leerkrachtenmonitor",
    page_icon="❤️",
    layout="centered"  # mobile first
)

DATA_DIR = "data"
USERS_FILE = f"{DATA_DIR}/users.csv"
os.makedirs(DATA_DIR, exist_ok=True)

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def normalize_email(email):
    return email.strip().lower()

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def day_file(email):
    return f"{DATA_DIR}/{email.split('@')[0]}_day.csv"

def lesson_file(email):
    return f"{DATA_DIR}/{email.split('@')[0]}_lessons.csv"

# -------------------------------------------------
# USERS
# -------------------------------------------------
def load_users():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame(columns=["email", "password", "role"]).to_csv(USERS_FILE, index=False)
    return pd.read_csv(USERS_FILE)

def save_users(df):
    df.to_csv(USERS_FILE, index=False)

# -------------------------------------------------
# SESSION STATE INIT
# -------------------------------------------------
defaults = {
    "energie": 3,
    "stress": 3,
    "lesaanpak": 3,
    "klasmanagement": 3,
    "remember": False
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -------------------------------------------------
# AUTO LOGIN (permanent)
# -------------------------------------------------
params = st.query_params
if "user" in params and "user" not in st.session_state:
    users = load_users()
    email = normalize_email(params["user"])
    u = users[users.email == email]
    if not u.empty:
        st.session_state.user = u.iloc[0].to_dict()

# -------------------------------------------------
# AUTH
# -------------------------------------------------
st.title("❤️ Leerkrachtenmonitor")
users = load_users()

if "user" not in st.session_state:
    tab1, tab2 = st.tabs(["🔐 Inloggen", "🆕 Registreren"])

    with tab1:
        email = normalize_email(st.text_input("E-mail", key="login_email"))
        pw = st.text_input("Wachtwoord", type="password", key="login_pw")
        remember = st.checkbox("Onthoud mij", key="remember_me")

        if st.button("Inloggen"):
            u = users[users.email == email]
            if not u.empty and hash_pw(pw) == u.iloc[0].password:
                st.session_state.user = u.iloc[0].to_dict()
                if remember:
                    st.query_params["user"] = email
                st.rerun()
            else:
                st.error("Ongeldige login")

    with tab2:
        r_email = normalize_email(st.text_input("School-e-mail", key="reg_email"))
        r_pw = st.text_input("Wachtwoord", type="password", key="reg_pw")

        if st.button("Account aanmaken"):
            if r_email in users.email.values:
                st.error("Account bestaat al")
            else:
                role = "director" if r_email.startswith("directie") else "teacher"
                users.loc[len(users)] = [r_email, hash_pw(r_pw), role]
                save_users(users)
                st.success("Account aangemaakt")

    st.stop()

# -------------------------------------------------
# LOGOUT
# -------------------------------------------------
user = st.session_state.user
st.sidebar.success(f"Ingelogd als {user['email']}")

if st.sidebar.button("Uitloggen"):
    st.query_params.clear()
    st.session_state.clear()
    st.rerun()

# -------------------------------------------------
# MOODS
# -------------------------------------------------
POS_MOODS = ["Inspirerend", "Motiverend", "Actief", "Verbonden", "Respectvol", "Gefocust"]
NEG_MOODS = ["Demotiverend", "Passief", "Onrespectvol", "Chaotisch", "Afgeleid"]

# -------------------------------------------------
# TEACHER VIEW
# -------------------------------------------------
if user["role"] == "teacher":
    DAY_FILE = day_file(user["email"])
    LES_FILE = lesson_file(user["email"])

    if not os.path.exists(DAY_FILE):
        pd.DataFrame(columns=["Datum", "Energie", "Stress"]).to_csv(DAY_FILE, index=False)

    if not os.path.exists(LES_FILE):
        pd.DataFrame(columns=[
            "Datum", "Klas", "Lesaanpak", "Klasmanagement", "Positief", "Negatief"
        ]).to_csv(LES_FILE, index=False)

    day_df = pd.read_csv(DAY_FILE)
    day_df["Datum"] = pd.to_datetime(day_df["Datum"], errors="coerce")

    les_df = pd.read_csv(LES_FILE)
    les_df["Datum"] = pd.to_datetime(les_df["Datum"], errors="coerce")

    tab1, tab2, tab3, tab4 = st.tabs([
        "🧠 Daggevoel", "📝 Lesregistratie", "📊 Visualisaties", "📄 Maandrapport"
    ])

    # ---------------- DAGGEVOEL ----------------
    with tab1:
        with st.form("daggevoel"):
            st.slider("Energie", 1, 5, key="energie")
            st.caption("Uitgeput · Weinig energie · Oké · Veel energie · Barstend van energie")

            st.slider("Stress", 1, 5, key="stress")
            st.caption("Volkomen rustig · Licht gespannen · Gemiddeld · Erg gestresseerd · Enorm gestresseerd")

            if st.form_submit_button("Opslaan"):
                day_df.loc[len(day_df)] = [date.today(), st.session_state.energie, st.session_state.stress]
                day_df.to_csv(DAY_FILE, index=False)
                st.success("Geregistreerd!")
                st.session_state.energie = 3
                st.session_state.stress = 3
                st.rerun()

    # ---------------- LESREGISTRATIE ----------------
with tab2:
    with st.form("lesregistratie"):
        klas = st.text_input("Klas / Groep", key="klas_input")

        st.slider("Lesaanpak", 1, 5, key="lesaanpak")
        st.caption("Zeer onduidelijk · Onvoldoende · Oké · Duidelijk · Zeer sterk")

        st.slider("Klasmanagement", 1, 5, key="klasmanagement")
        st.caption("Chaotisch · Moeizaam · Redelijk · Goed · Zeer sterk")

        positief = st.multiselect(
            "Positieve sfeer (meerdere mogelijk)",
            POS_MOODS,
            key="pos_moods"
        )

        negatief = st.multiselect(
            "Negatieve sfeer (meerdere mogelijk)",
            NEG_MOODS,
            key="neg_moods"
        )

        if st.form_submit_button("Les opslaan"):
            if not klas:
                st.error("Vul een klas of groep in.")
            else:
                les_df.loc[len(les_df)] = [
                    date.today(),
                    klas,
                    st.session_state.lesaanpak,
                    st.session_state.klasmanagement,
                    ", ".join(positief),
                    ", ".join(negatief)
                ]
                les_df.to_csv(LES_FILE, index=False)
                st.success("Les succesvol geregistreerd!")

                st.session_state.lesaanpak = 3
                st.session_state.klasmanagement = 3
                st.session_state.pos_moods = []
                st.session_state.neg_moods = []

                st.rerun()

    # ---------------- VISUALISATIES ----------------
with tab3:
    st.subheader("📈 Trends over tijd")

    if day_df.empty:
        st.info("Nog geen dagregistraties beschikbaar.")
    else:
        day_plot = day_df.sort_values("Datum")

        fig1 = px.line(
            day_plot,
            x="Datum",
            y=["Energie", "Stress"],
            markers=True,
            title="Energie & Stress over tijd"
        )
        st.plotly_chart(fig1, use_container_width=True)

    st.divider()
    st.subheader("📊 Leskwaliteit")

    if les_df.empty:
        st.info("Nog geen lesregistraties beschikbaar.")
    else:
        les_plot = les_df.sort_values("Datum")

        fig2 = px.bar(
            les_plot,
            x="Datum",
            y=["Lesaanpak", "Klasmanagement"],
            barmode="group",
            title="Lesaanpak & Klasmanagement per les"
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader("😊 Sfeerwoorden (frequentie)")

    if not les_df.empty:
        pos_counts = (
            les_df["Positief"]
            .dropna()
            .str.split(", ")
            .explode()
            .value_counts()
        )

        neg_counts = (
            les_df["Negatief"]
            .dropna()
            .str.split(", ")
            .explode()
            .value_counts()
        )

        col1, col2 = st.columns(2)

        with col1:
            if not pos_counts.empty:
                fig3 = px.bar(
                    pos_counts,
                    x=pos_counts.index,
                    y=pos_counts.values,
                    title="Positieve sfeer"
                )
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("Nog geen positieve labels.")

        with col2:
            if not neg_counts.empty:
                fig4 = px.bar(
                    neg_counts,
                    x=neg_counts.index,
                    y=neg_counts.values,
                    title="Negatieve sfeer"
                )
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("Nog geen negatieve labels.")

    # ---------------- PDF ----------------
    with tab4:
        today = date.today()
        last_month = (today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        subset = day_df[day_df["Datum"].dt.to_period("M").astype(str) == last_month]

        if subset.empty:
            st.info("Nog geen gegevens voor vorige maand.")
        else:
            if st.button("Genereer maandrapport"):
                pdf_path = f"{DATA_DIR}/{user['email'].split('@')[0]}_{last_month}.pdf"
                doc = SimpleDocTemplate(pdf_path)
                styles = getSampleStyleSheet()
                story = []

                story.append(Paragraph(f"<b>Maandrapport {last_month}</b>", styles["Title"]))
                story.append(Spacer(1, 12))
                story.append(Paragraph(f"Gemiddelde energie: {subset['Energie'].mean():.2f}", styles["Normal"]))
                story.append(Paragraph(f"Gemiddelde stress: {subset['Stress'].mean():.2f}", styles["Normal"]))

                doc.build(story)

                with open(pdf_path, "rb") as f:
                    st.download_button("Download PDF", f, file_name=f"Maandrapport_{last_month}.pdf")


