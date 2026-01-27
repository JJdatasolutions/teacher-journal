import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import os

# --- CONFIGURATION ---
FILE_PATH = 'teaching_journal.csv'
st.set_page_config(page_title="Teacher's Log", page_icon="🍎", layout="centered") 
# Note: 'centered' layout often looks better on mobile vertical screens than 'wide'

# --- DATA HANDLING ---
def load_data():
    if not os.path.exists(FILE_PATH):
        df = pd.DataFrame(columns=[
            'Date', 'Class_Group', 
            'Mental_State', 'Energy', 'Stress', 
            'Didactics', 'Class_Management', 
            'Tags', 'Notes'
        ])
        df.to_csv(FILE_PATH, index=False)
    return pd.read_csv(FILE_PATH)

def save_data(entry):
    df = load_data()
    # Convert tags list to a string so it saves in CSV easily
    entry['Tags'] = ", ".join(entry['Tags'])
    new_entry_df = pd.DataFrame([entry])
    df = pd.concat([df, new_entry_df], ignore_index=True)
    df.to_csv(FILE_PATH, index=False)

# --- APP HEADER ---
st.title("🍎 Teacher's Log")

# --- INPUT FORM (Mobile Friendly Expander) ---
with st.expander("➕ Tap to Log Day", expanded=True):
    with st.form(key='log_form'):
        st.subheader("1. The Basics")
        col1, col2 = st.columns(2)
        with col1:
            entry_date = st.date_input("Date", date.today())
        with col2:
            # The specific classes you requested
            class_options = ['5MT', '6MT', '5HW', '6WEWI', '5ECMT', '5ECWI', '3MT']
            class_group = st.selectbox("Class Group", class_options)
        
        st.markdown("---")
        st.subheader("2. How did it feel?")
        
        # Tags selection
        tag_options = [
            "Respectful", "Energizing", "Inspiring", "Collaborative", "Active", # Positives
            "Stressful", "Unrespectful", "Rebellious", "Lazy", "Passive",       # Challenges
            "Chaotic", "Funny", "Focused", "Drained", "Proud"                   # Extras
        ]
        tags = st.multiselect("Select Key Vibe(s):", tag_options)
        
        # Sliders - Compact for mobile
        st.write("**(Low 1 — 10 High)**")
        mental = st.slider("🧠 Mental Clarity", 1, 10, 7)
        energy = st.slider("⚡ Energy Level", 1, 10, 6)
        stress = st.slider("😰 Stress Level", 1, 10, 3)
        
        st.markdown("---")
        st.subheader("3. Performance")
        # Using columns to put these side-by-side on wider screens, stacked on phone
        c1, c2 = st.columns(2)
        with c1:
            didactics = st.selectbox("Didactics / Method", [1, 2, 3, 4, 5], index=2, help="5 = Perfect lesson flow")
        with c2:
            management = st.selectbox("Class Management", [1, 2, 3, 4, 5], index=2, help="5 = Perfect control")
        
        notes = st.text_area("Quick Notes (Optional)", placeholder="What stood out?")
        
        submit_button = st.form_submit_button(label='💾 Save Entry', type="primary")

        if submit_button:
            entry = {
                'Date': entry_date,
                'Class_Group': class_group,
                'Mental_State': mental,
                'Energy': energy,
                'Stress': stress,
                'Didactics': didactics,
                'Class_Management': management,
                'Tags': tags,
                'Notes': notes
            }
            save_data(entry)
            st.success("Saved!")
            st.rerun()

# --- DASHBOARD ---
st.markdown("---")
st.header("📊 Your Stats")

df = load_data()

if not df.empty:
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(by='Date')

    # 1. Quick Metrics Row
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Classes", len(df))
    with m2:
        st.metric("Avg Stress", f"{df['Stress'].mean():.1f}")
    with m3:
        st.metric("Avg Energy", f"{df['Energy'].mean():.1f}")

    # 2. Tag Analysis (New Feature!)
    st.subheader("🏷️ Mood Frequency")
    # Process tags: split the strings back into a list of words
    all_tags = []
    for tag_string in df['Tags']:
        if isinstance(tag_string, str):
            all_tags.extend(tag_string.split(", "))
            
    if all_tags:
        # Filter out empty strings if any
        all_tags = [t for t in all_tags if t]
        from collections import Counter
        tag_counts = pd.DataFrame(Counter(all_tags).items(), columns=['Tag', 'Count'])
        
        # Bar chart for tags
        fig_tags = px.bar(tag_counts.sort_values('Count', ascending=True), 
                          x='Count', y='Tag', orientation='h',
                          color='Count', color_continuous_scale='Bluered')
        st.plotly_chart(fig_tags, use_container_width=True)

    # 3. Evolution Chart
    st.subheader("📈 Energy vs Stress")
    fig_line = px.line(df, x='Date', y=['Energy', 'Stress'], 
                       markers=True, color_discrete_map={"Energy": "#2ECC71", "Stress": "#E74C3C"})
    # Move legend to top for mobile visibility
    fig_line.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_line, use_container_width=True)

    # 4. Recent Logs
    with st.expander("📜 Recent Logs History"):
        display_cols = ['Date', 'Class_Group', 'Tags', 'Notes']
        st.dataframe(df[display_cols].sort_values(by='Date', ascending=False), use_container_width=True)

else:
    st.info("No classes logged yet. Tap the '+' above!")
