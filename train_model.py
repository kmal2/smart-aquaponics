import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib

# Load dataset
df = pd.read_csv("aquaponics_training_data.csv")

# Features
X = df[["water_temp", "ph", "oxygen", "humidity", "air_temp", "water_level"]]

# Label
y = df["status"]

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42
)

# Model
model = RandomForestClassifier(
    n_estimators=200,
    random_state=42
)

model.fit(X_train, y_train)

# Evaluate
pred = model.predict(X_test)

print("\nClassification Report:\n")
print(classification_report(y_test, pred))

# Save model
joblib.dump(model, "aquaponics_model.pkl")

print("\nModel saved as aquaponics_model.pkl")