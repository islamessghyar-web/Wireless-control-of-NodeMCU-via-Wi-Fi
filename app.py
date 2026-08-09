import streamlit as st
import cv2
import requests
import numpy as np

st.title("Wireless Motion Control for NodeMCU")

ESP_IP = st.text_input("NodeMCU IP Address:", "http://192.168.4.1")

# استخدام التقاط الصور المباشر المدمج في Streamlit
img_file_buffer = st.camera_input("Take a photo to detect motion")

if "prev_frame" not in st.session_state:
    st.session_state.prev_frame = None

def send_command(endpoint):
    try:
        url = f"{ESP_IP.strip('/')}/{endpoint}"
        requests.get(url, timeout=0.5)
    except Exception:
        pass

if img_file_buffer is not None:
    # تحويل الصورة الملتقطة إلى مصفوفة OpenCV
    bytes_data = img_file_buffer.getvalue()
    cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

    # معالجة الصورة وتحويلها للرمادي
    gray = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2GRAY)
    gray_blur = cv2.GaussianBlur(gray, (21, 21), 0)

    # التحقق من وجود الإطار السابق وتطابق الأبعاد
    if st.session_state.prev_frame is not None and st.session_state.prev_frame.shape == gray_blur.shape:
        frame_delta = cv2.absdiff(st.session_state.prev_frame, gray_blur)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        motion_score = np.sum(thresh)

        if motion_score > 50000:
            st.success("MOTION DETECTED - LED ON")
            send_command("on")
        else:
            st.info("NO MOTION - LED OFF")
            send_command("off")
    else:
        st.info("First frame saved. Take another picture to compare motion.")

    # حفظ الإطار الحالي للمقارنة القادمة
    st.session_state.prev_frame = gray_blur
    
