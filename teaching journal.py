import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import os

# --- CONFIGURATION ---
FILE_PATH = 'teaching_journal.csv'
st.set_page_config(page_title="Teacher's Strava", page_icon="🍎", layout="wide")

# --- DATA HANDLING ---
def load_data():
    if not os.path.exists(FILE_PATH):
        # Create an empty dataframe with columns if file doesn't exist
        df = pd.DataFrame(columns=[
            'Date', 'Class_Group', 'Subject_Topic', 
            'Mental_State', 'Energy', 'Stress', 
            'Didactics', 'Class_Management', 'Notes'
        ])
        df.to_csv(FILE_PATH, index=False)
    
    return pd.read_csv(FILE_PATH)

def save_data(entry):
    df = load_data()
    # Convert new entry to dataframe
    new_entry_df = pd.DataFrame([entry])
    # Concatenate and save
    df = pd.concat([df, new_entry_df], ignore_index=True)
    df.to_csv(FILE_PATH, index=False)

# --- SIDEBAR: LOGGING (The "Record Activity" button) ---
st.sidebar.header("📝 Log Your Day")
st.sidebar.write("Reflect on your teaching day.")

with st.sidebar.form(key='log_form'):
    entry_date = st.date_input("Date", date.today())
    class_group = st.text_input("Class/Group (e.g., 4B, Seniors)", "General")
    topic = st.text_input("Topic Taught", "English Literature")
    
    st.markdown("---")
    st.markdown("**Internal State (1-10)**")
    mental = st.slider("Mental Clarity", 1, 10, 7)
    energy = st.slider("Energy Level", 1, 10, 6)
    stress = st.slider("Stress Level (1=Zen, 10=Panic)", 1, 10, 3)
    
    st.markdown("---")
    st.markdown("**Teaching Performance (1-5 Stars)**")
    didactics = st.select_slider("Didactic Success (Methodology)", options=[1, 2, 3, 4, 5], value=3)
    management = st.select_slider("Classroom Management", options=[1, 2, 3, 4, 5], value=3)
    
    notes = st.text_area("Notes / Aha Moment / Struggle")
    
    submit_button = st.form_submit_button(label='Save Entry')

    if submit_button:
        entry = {
            'Date': entry_date,
            'Class_Group': class_group,
            'Subject_Topic': topic,
            'Mental_State': mental,
            'Energy': energy,
            'Stress': stress,
            'Didactics': didactics,
            'Class_Management': management,
            'Notes': notes
        }
        save_data(entry)
        st.success("Day logged successfully!")

# --- MAIN DASHBOARD ---
st.title("🍎 The Teaching Dashboard")
st.markdown("Your professional fitness tracker.")

df = load_data()

if not df.empty:
    # Convert date column to datetime objects
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(by='Date')

    # 1. TOP METRICS (Strava Style)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Classes Logged", len(df))
    with col2:
        avg_energy = df['Energy'].mean()
        st.metric("Avg. Energy", f"{avg_energy:.1f}/10")
    with col3:
        # Calculate trend (compare last entry to average)
        last_stress = df.iloc[-1]['Stress']
        avg_stress = df['Stress'].mean()
        delta = last_stress - avg_stress
        st.metric("Current Stress", f"{last_stress}/10", delta=f"{delta:.1f} vs avg", delta_color="inverse")
    with col4:
        avg_sat = (df['Didactics'].mean() + df['Class_Management'].mean()) / 2
        st.metric("Teaching Satisfaction", f"{avg_sat:.1f}/5")

    st.markdown("---")

    # 2. VISUALIZATIONS
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("⚡ Energy vs. Stress Over Time")
        # Line chart
        fig_line = px.line(df, x='Date', y=['Energy', 'Stress'], 
                           title="Burnout Watcher", markers=True,
                           color_discrete_map={"Energy": "#2ECC71", "Stress": "#E74C3C"})
        st.plotly_chart(fig_line, use_container_width=True)

    with c2:
        st.subheader("🎓 Performance Breakdown")
        # Radar Chart for the latest entry (or average)
        categories = ['Mental', 'Didactics (Scaled)', 'Management (Scaled)', 'Energy', 'Inverted Stress']
        
        # Scaling 1-5 metrics to 1-10 for the chart consistency
        last_entry = df.iloc[-1]
        values = [
            last_entry['Mental_State'],
            last_entry['Didactics'] * 2, # Scale to 10
            last_entry['Class_Management'] * 2, # Scale to 10
            last_entry['Energy'],
            10 - last_entry['Stress'] # Invert stress so "high" is good on the chart
        ]
        
        fig_radar = go.Figure(data=go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Latest Class'
        ))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), showlegend=False)
        st.plotly_chart(fig_radar, use_container_width=True)

    # 3. CORRELATION (Heatmap style logic)
    st.subheader("📊 What affects your teaching?")
    
    chart_tab1, chart_tab2 = st.tabs(["Didactics vs Energy", "Recent Notes"])
    
    with chart_tab1:
        fig_scatter = px.scatter(df, x="Energy", y="Didactics", size="Mental_State", 
                                 color="Class_Group", hover_data=['Notes'],
                                 title="Does High Energy = Better Teaching?")
        st.plotly_chart(fig_scatter, use_container_width=True)

    with chart_tab2:
        st.dataframe(df[['Date', 'Class_Group', 'Notes']].sort_values(by='Date', ascending=False), use_container_width=True)

else:
    st.info("👈 No data yet! Use the sidebar to log your first teaching day.")