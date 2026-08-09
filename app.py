import streamlit as st
import cv2
import requests
import numpy as np
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, WebRtcMode, RTCConfiguration

# إعداد خوادم STUN من Google لفك حجب اتصال الفيديو على الشبكات المحمولة
RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

st.title("Wireless Motion Control for NodeMCU")

ESP_IP = st.text_input("NodeMCU IP Address:", "http://192.168.4.1")

class MotionDetector(VideoTransformerBase):
    def __init__(self):
        self.prev_frame = None

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        
        # تحويل الصورة للرمادي وتنعيمها
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray_blur = cv2.GaussianBlur(gray, (21, 21), 0)

        # تهيئة الإطار السابق
        if self.prev_frame is None or self.prev_frame.shape != gray_blur.shape:
            self.prev_frame = gray_blur
            return img

        # حساب الفرق
        frame_delta = cv2.absdiff(self.prev_frame, gray_blur)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        
        motion_score = np.sum(thresh)

        # إرسال الأمر للوحة
        if motion_score > 50000:
            cv2.putText(img, "MOTION DETECTED - LED ON", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            try:
                requests.get(f"{ESP_IP.strip('/')}/on", timeout=0.2)
            except:
                pass
        else:
            cv2.putText(img, "NO MOTION - LED OFF", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            try:
                requests.get(f"{ESP_IP.strip('/')}/off", timeout=0.2)
            except:
                pass

        self.prev_frame = gray_blur
        return img

# تشغيل الكاميرا مع دعم خادم STUN
webrtc_streamer(
    key="motion-detection",
    mode=WebRtcMode.SENDRECV,
    rtc_configuration=RTC_CONFIGURATION,
    video_transformer_factory=MotionDetector,
    media_stream_constraints={"video": True, "audio": False},
        )
        
