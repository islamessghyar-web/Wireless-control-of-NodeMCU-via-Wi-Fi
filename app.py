import streamlit as st
import cv2
import requests
import numpy as np

st.title("Wireless Motion Control for NodeMCU")

# ضع عنوان IP الخاص بـ ESP8266 المطبوع في الـ Serial Monitor
ESP_IP = st.text_input("NodeMCU IP Address:", "http://192.168.1.50")

# إعداد الكاميرا
run = st.checkbox('Start Camera')
FRAME_WINDOW = st.image([])

camera = cv2.VideoCapture(0)

# تهيئة المتغيرات في session_state لمنع الأخطاء
if "prev_frame" not in st.session_state:
    st.session_state.prev_frame = None

def send_command(endpoint):
    try:
        url = f"{ESP_IP.strip('/')}/{endpoint}"
        requests.get(url, timeout=0.5)
    except Exception:
        pass  # يتجاهل أخطاء الاتصال المؤقتة لضمان استمرار البث

while run:
    ret, frame = camera.read()
    if not ret:
        st.error("Failed to capture image from camera.")
        break

    # تحويل الصورة للرمادي وتنعيمها لتقليل الضوضاء
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray_blur = cv2.GaussianBlur(gray, (21, 21), 0)

    # 1. تهيئة prev_frame أول مرة أو إذا تغيرت الأبعاد
    if st.session_state.prev_frame is None or st.session_state.prev_frame.shape != gray_blur.shape:
        st.session_state.prev_frame = gray_blur
        continue

    # 2. حساب الفرق المطلق بشكل آمن بين الإطار الحالي والسابق
    frame_delta = cv2.absdiff(st.session_state.prev_frame, gray_blur)
    thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
    
    # حساب نسبة التغير/الحركة في الصورة
    motion_score = np.sum(thresh)

    # عتبة كشف الحركة (يمكنك تعديل 50000 حسب الحساسية المطلوبة)
    if motion_score > 50000:
        cv2.putText(frame, "MOTION DETECTED - LED ON", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        send_command("on")
    else:
        cv2.putText(frame, "NO MOTION - LED OFF", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        send_command("off")

    # تحديث الإطار السابق للعملية القادمة
    st.session_state.prev_frame = gray_blur

    # عرض الفيديو في Streamlit (تحويل BGR إلى RGB)
    FRAME_WINDOW.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

else:
    camera.release()
    st.session_state.prev_frame = None
    
