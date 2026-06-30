import feedparser
import pandas as pd
import smtplib
import os
import sys
import traceback
from email.mime.text import MIMEText
from transformers import pipeline

try:
    # 1. HONG KONG CONFIGURATION WITH YOUR REAL GOOGLE ALERTS LINKS
    RSS_URLS = [
        "https://www.google.com/alerts/feeds/04663313462165007582/14573298916450479100",  # Chinese: 無國界醫生
        "https://www.google.com/alerts/feeds/04663313462165007582/5813613186843736031"    # English: "MSF Hong Kong"
    ]
    CSV_FILE = "alerts_history.csv"

    # Secure credentials provided via GitHub secrets vault
    SENDER_EMAIL = os.environ.get("ALERT_EMAIL_SENDER")
    SENDER_PASSWORD = os.environ.get("ALERT_EMAIL_PASSWORD")
    RECEIVER_EMAIL = os.environ.get("ALERT_EMAIL_RECEIVER")

    def send_alert_email(title, link, sentiment_label):
        if not SENDER_EMAIL or not SENDER_PASSWORD:
            print("Email credentials missing. Skipping email notification.")
            return
        
        body = f"MSF HK Monitoring Alert!\n\nA critical or negative mention was detected.\n\nHeadline: {title}\nAI Classification: {sentiment_label}\nLink: {link}"
        msg = MIMEText(body)
        msg['Subject'] = "🚨 MSF HK Social Listening: Critical Mention Detected"
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
            print("Alert email sent successfully.")
        except Exception as e:
            print("Email failed to send:", e)

    # 2. LOAD RELIABLE, FULLY PUBLIC OPEN MULTILINGUAL AI MODEL
    print("Loading open multilingual AI sentiment engine...")
    classifier = pipeline(
        "sentiment-analysis", 
        model="lxyuan/distilbert-base-multilingual-cased-sentiments-student"
    )

    # 3. FETCH DATA FROM BOTH ALERTS
    print("Scanning Hong Kong market feeds...")
    feed_entries = []
    for url in RSS_URLS:
        if url.startswith("http"):
            feed = feedparser.parse(url)
            feed_entries.extend(feed.entries)

    # Load existing tracking history to avoid duplicate emails
    try:
        existing_df = pd.read_csv(CSV_FILE)
        tracked_links = set(existing_df['Link'].tolist())
    except FileNotFoundError:
        existing_df = pd.DataFrame()
        tracked_links = set()

    new_mentions = []

    # 4. RUN AI ANALYSIS
    for entry in feed_entries:
        if entry.link in tracked_links:
            continue # Skip if already recorded
            
        clean_title = entry.title.replace('<b>', '').replace('</b>', '')
        
        # Process text through Multilingual AI model
        ai_result = classifier(clean_title[:512])[0]
        sentiment = str(ai_result['label']).upper() # Outputs 'POSITIVE', 'NEUTRAL', or 'NEGATIVE'
        
        # Trigger email alert if sentiment is explicitly negative
        if "NEG" in sentiment:
            print(f"Alert Triggered: {clean_title}")
            send_alert_email(clean_title, entry.link, sentiment)
            
        new_mentions.append({
            "Title": clean_title,
            "Link": entry.link,
            "Published": entry.published,
            "Sentiment": sentiment,
            "Confidence": round(ai_result['score'], 2)
        })

    # 5. SAVE DATA FILE
    if new_mentions:
        new_df = pd.DataFrame(new_mentions)
        updated_df = pd.concat([new_df, existing_df], ignore_index=True).head(500)
        updated_df.to_csv(CSV_FILE, index=False)
        print(f"Data updated successfully. Logged {len(new_mentions)} new entries.")
    else:
        print("No new mentions found this hour.")

except Exception as e:
    print("❌ AN ERROR OCCURRED IN THE EXECUTION FLOW:")
    traceback.print_exc()
    sys.exit(1)
