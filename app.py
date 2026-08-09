import cv2
import numpy as np
import requests
import streamlit as st

# ضبط إعدادات الصفحة
st.set_page_config(
    page_title="كاشف الحركة - NodeMCU Wi-Fi", page_icon="📡", layout="wide"
)

st.title("📡 التحكم اللاسلكي في NodeMCU عبر الواي فاي")
st.write(
    "التقط صورة للتحرك أمام الكاميرا؛ عند رصد الحركة سيتم إرسال أمر تشغيل للـ LED لاسلكياً لمدة 3 ثوانٍ."
)

# -------------------------------------------------------------
# 1. إعدادات عنوان الـ IP
# -------------------------------------------------------------
st.sidebar.header("🌐 إعدادات الشبكة")
ip_address = st.sidebar.text_input(
    "عنوان IP الخاصة بـ NodeMCU:",
    value="192.168.1.50",
    help="اكتب عنوان الـ IP الذي ظهر لك في Serial Monitor بعد رفع الكود",
)

enable_wifi = st.sidebar.checkbox("تفعيل التحكم اللاسلكي", value=True)

# ذاكرة لحفظ الإطار السابق للكشف عن الحركة
if "prev_frame" not in st.session_state:
    st.session_state.prev_frame = None

# -------------------------------------------------------------
# 2. واجهة المعالجة والتفاعل
# -------------------------------------------------------------
col1, col2 = st.columns([2, 1])

with col1:
    img_file = st.camera_input("التقط صورة للكشف عن الحركة")

if img_file is not None:
    bytes_data = img_file.getvalue()
    cv_img = cv2.imdecode(
        np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR
    )

    # معالجة الصورة لكشف الحركة
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    gray_blur = cv2.GaussianBlur(gray, (21, 21), 0)

    motion_detected = False

    if st.session_state.prev_frame is not None:
        frame_delta = cv2.absdiff(st.session_state.prev_frame, gray_blur)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        contours, _ = cv2.findContours(
            thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        for contour in contours:
            if cv2.contourArea(contour) > 1500:  # حد حساسية الحركة
                motion_detected = True
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(cv_img, (x, y), (x + w, y + h), (0, 255, 0), 2)

    st.session_state.prev_frame = gray_blur

    # -------------------------------------------------------------
    # 3. إرسال أمر التشغيل اللاسلكي
    # -------------------------------------------------------------
    with col1:
        st.image(
            cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB),
            caption="معاينة كشف الحركة",
            use_container_width=True,
        )

    with col2:
        st.subheader("📊 حالة الاستشعار والشبكة")

        if motion_detected:
            st.success("🚨 تم رصد حركة! جاري الإرسال عبر الواي فاي...")

            if enable_wifi and ip_address:
                try:
                    # إرسال طلب HTTP إلى NodeMCU
                    response = requests.get(
                        f"http://{ip_address}/led/trigger", timeout=1.5
                    )
                    if response.status_code == 200:
                        st.info("✅ تم استلام الأمر: الـ LED يعمل لمدة 3 ثوانٍ.")
                except Exception as e:
                    st.error(f"فشل الاتصال بـ NodeMCU: {e}")
        else:
            st.warning("⚪ لا توجد حركة جديدة.")
