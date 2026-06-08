import pandas as pd
from sklearn.tree import DecisionTreeClassifier
import joblib
import random

# 1. توليد بيانات محاكاة ذكية لدورة النيتروجين وصحة النبات
data = []
for _ in range(500):
    ph = random.uniform(6.0, 8.0)
    nitrate = random.uniform(10.0, 40.0)
    humidity = random.uniform(50.0, 80.0)
    air_temp = random.uniform(20.0, 30.0)
    
    # وضع قواعد بيولوجية منطقية ليتعلمها الذكاء الاصطناعي
    if 6.5 <= ph <= 7.5 and 15 <= nitrate <= 30 and humidity > 60:
        status = "Excellent Growth"
    elif nitrate < 10 or nitrate > 50:
        status = "Nutrient Imbalance / Leaf Yellowing"
    else:
        status = "Normal Growth"
        
    data.append([ph, nitrate, humidity, air_temp, status])

# 2. تحويل البيانات إلى DataFrame وتحديد الأعمدة المتوافقة مع الواجهة تماماً
df = pd.DataFrame(data, columns=["ph", "nitrate", "humidity", "air_temp", "status"])

X = df[["ph", "nitrate", "humidity", "air_temp"]]
y = df["status"]

# 3. التدريب والحفظ
model = DecisionTreeClassifier()
model.fit(X, y)

joblib.dump(model, "plant_health_model.pkl")
print("🏆 Plant Health Intelligence Model Trained and Saved Successfully!")
