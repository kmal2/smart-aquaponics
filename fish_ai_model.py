import pandas as pd
from sklearn.tree import DecisionTreeClassifier
import joblib

# Load dataset
df = pd.read_csv("data/fish_health_dataset.csv")

# Features
X = df[["water_temp", "ph", "oxygen"]]

# Target
y = df["status"]

# Train model
model = DecisionTreeClassifier()

model.fit(X, y)

# Save model
joblib.dump(model, "fish_health_model.pkl")

print("Fish Health Model Trained Successfully")