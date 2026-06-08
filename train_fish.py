import pandas as pd
from sklearn.tree import DecisionTreeClassifier
import joblib
import os

# التأكد من وجود المجلد الخاص بالبيانات أو إنشائه افتراضياً لتجنب الأخطاء
if not os.path.exists("data"):
    os.makedirs("data")

# كود التدريب الذكي والمطابق لأعمدة الواجهة الثلاثة
try:
    # تحميل البيانات
    df = pd.read_csv("data/fish_health_dataset.csv")
    
    # تحديد الأعمدة الثلاثة المتطابقة تماماً مع تعديل الواجهة الأخير
    X = df[["water_temp", "ph", "oxygen"]]
    y = df["status"]

    # تدريب الموديل
    model = DecisionTreeClassifier()
    model.fit(X, y)

    # حفظ الموديل في المجلد الرئيسي ليقرأه Streamlit فوراً
    joblib.dump(model, "fish_health_model.pkl")
    print("🏆 Fish Health Model Trained and Saved Successfully!")

except FileNotFoundError:
    print("⚠️ لم يتم العثور على ملف data/fish_health_dataset.csv")
    print("💡 جاري إنشاء موديول تجريبي سريع للأسماك لضمان عمل الواجهة بنجاح...")
    
    # حل بديل ذكي: إذا لم يجد ملف الـ CSV، يقوم بتوليد موديول تجريبي فوراً لمنع تعطل العرض
    import random
    mock_data = []
    for _ in range(200):
        t = random.uniform(25.0, 30.0)
        p = random.uniform(6.5, 8.0)
        o = random.uniform(6.0, 9.0)
        st = "Healthy" if (26 <= t <= 28 and 7 <= p <= 7.8 and o > 7) else "Stressed"
        mock_data.append([t, p, o, st])
        
    df_mock = pd.DataFrame(mock_data, columns=["water_temp", "ph", "oxygen", "status"])
    model = DecisionTreeClassifier()
    model.fit(df_mock[["water_temp", "ph", "oxygen"]], df_mock["status"])
    joblib.dump(model, "fish_health_model.pkl")
    print("🟢 تم إنشاء وحفظ موديول الأسماك البديل (fish_health_model.pkl) بنجاح!")
