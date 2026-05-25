import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

# Load dataset
df = pd.read_csv("dataset/school_students_feedback_8000.csv")

X = df["Feedback_Text"]
y = df["Sentiment_Label"]

# Train test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Better Vectorizer
vectorizer = TfidfVectorizer(
    lowercase=True,
    stop_words=None,
    ngram_range=(1,2),   # THIS IS IMPORTANT
    min_df=2
)

X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# Better Model
model = LogisticRegression(max_iter=1000)
model.fit(X_train_vec, y_train)

# Evaluate
y_pred = model.predict(X_test_vec)
print(classification_report(y_test, y_pred))

# Save
pickle.dump((model, vectorizer), open("model/sentiment_model.pkl", "wb"))

print("New model trained and saved successfully.")