import pandas as pd
from .models import db, Feedback
import logging

def etl(df):
    if df.empty:
        logging.warning("Empty DataFrame received; no data to upload.")
        return

    try:
      
        missing_data = df.isnull().sum()
        if missing_data.any():
            logging.warning(f"Columns with missing data: {missing_data[missing_data > 0].to_dict()}")
            df.fillna({'Rating': 3, 'Sentiment Score': 'Neutral'}, inplace=True)  
       
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        invalid_date = df[df['Date'].isna()]
        if not invalid_date.empty:
            logging.warning(f"Invalid Date entries found: {len(invalid_date)}")
            df.dropna(subset=['Date'], inplace=True)  
        valid_sources = ["Social Media", "Survey", "Review Site"]
        invalid_source = df[~df["Source"].isin(valid_sources)]
        if not invalid_source.empty:
            logging.warning(f"Invalid Source entries found: {len(invalid_source)}")
            df = df[df["Source"].isin(valid_sources)] 
    
        valid_sentiments = ["Positive", "Neutral", "Negative"]
        invalid_sentiment = df[~df["Sentiment Score"].isin(valid_sentiments)]
        if not invalid_sentiment.empty:
            logging.warning(f"Invalid Sentiment Score entries found: {len(invalid_sentiment)}")
            df = df[df["Sentiment Score"].isin(valid_sentiments)]
        if "Rating" in df.columns:
            df.loc[(df["Rating"] < 1) | (df["Rating"] > 5), "Rating"] = None
            df['Rating'].fillna(df['Rating'].median(), inplace=True)

     
        df["Feedback Length"] = df["Feedback Text"].apply(len)  
        df["Date"] = df["Date"].dt.date
        df["Sentiment Category"] = df["Sentiment Score"].map({"Positive": "Good", "Neutral": "Neutral", "Negative": "Bad"})  # Map Sentiment Category
        df["Feedback Text"] = df["Feedback Text"].str.capitalize()  # Capitalize Feedback Text
        df["Sentiment Numeric"] = df["Sentiment Score"].map({"Positive": 1, "Neutral": 0, "Negative": -1})  # Map to numeric

        required_columns = [
            "Date", "Source", "Feedback Text", "Sentiment Score",
            "Product/Service Category", "Rating", "Feedback Length",
            "Sentiment Category", "Sentiment Numeric"
        ]
        
        for column in required_columns:
            if column not in df.columns:
                logging.error(f"Missing column: {column}")
                return
        for _, row in df.iterrows():
            try:
                feedback_record = Feedback(
                    date=row['Date'],
                    source=row['Source'],
                    feedback_text=row['Feedback Text'],
                    sentiment_score=row['Sentiment Score'],
                    product_service_category=row['Product/Service Category'],
                    rating=row['Rating'],
                    feedback_length=row['Feedback Length'],
                    sentiment_category=row['Sentiment Category'],
                    sentiment_numeric=row['Sentiment Numeric']
                )
                db.session.add(feedback_record)
                logging.info(f"Added record: {feedback_record}")
            except Exception as row_error:
                logging.error(f"Error adding record: {row_error}")
                continue  # Skip problematic row and proceed

        db.session.commit()
        logging.info("Data successfully uploaded to the database.")
    except Exception as e:
        logging.error(f"Error uploading data to the database: {e}")
        db.session.rollback()
