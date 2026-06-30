import streamlit as st
import pandas as pd

st.set_page_config(page_title="MSF HK Social Listening", layout="wide")

st.title("无国界医生 MSF Hong Kong — AI News Monitor")
st.caption("Bilingual Hong Kong Market Media Tracker • Updates Hourly")

try:
    df = pd.read_csv("alerts_history.csv")

    total_mentions = len(df)
    critical_alerts = len(df[df["Sentiment"] == "NEGATIVE"])

    col1, col2 = st.columns(2)
    col1.metric("Total HK Mentions Tracked", total_mentions)
    col2.metric("Critical / Negative Mentions 🚨", critical_alerts, delta_color="inverse")

    st.write("---")
    st.subheader("Live Monitoring Log")

    st.dataframe(
        df,
        column_config={
            "Link": st.column_config.LinkColumn("Source Link", display_text="Open Article")
        },
        hide_index=True,
        use_container_width=True
    )

except FileNotFoundError:
    st.info("Waiting for the first automated hourly background run to generate data... Click 'Actions' in GitHub to run manually.")
