import pandas as pd
from sklearn.tree import DecisionTreeClassifier
import joblib

# Load dataset
df = pd.read_csv("data/fish_health_dataset.csv")

# 🔥 تعديل: إضافة الأمونيا لتتطابق تماماً مع مدخلات واجهة ستريم ليت
X = df[["water_temp", "ph", "oxygen", "ammonia"]]

# Target
y = df["status"]

# Train model
model = DecisionTreeClassifier()
model.fit(X, y)

# Save model
joblib.dump(model, "fish_health_model.pkl")

print("🏆 Fish Health Model (with Ammonia) Trained Successfully!")
