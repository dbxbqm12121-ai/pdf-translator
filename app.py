import streamlit as st
import fitz
import google.generativeai as genai
import time

st.set_page_config(page_title="논문 전체 번역기 (최종본)", layout="wide")
st.title("📄 끝까지 번역하는 논문 번역기")

# 세션 상태 관리 (데이터 유실 방지)
if 'result_text' not in st.session_state:
    st.session_state.result_text = ""

api_key = st.sidebar.text_input("Google Gemini API Key", type="password")
uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type="pdf")

if uploaded_file and api_key:
    genai.configure(api_key=api_key)
    
    @st.cache_resource
    def load_model(key):
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods and '1.5-flash' in m.name:
                return m.name
        return "models/gemini-1.5-flash"

    target_model = load_model(api_key)
    model = genai.GenerativeModel(target_model)

    if st.button("번역 시작"):
        st.session_state.result_text = "" # 시작 시 초기화
        
        pdf_data = uploaded_file.read()
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        # 실시간 번역창 생성
        live_display = st.empty() 

        full_content = ""
        total_pages = len(doc)

        for page_num, page in enumerate(doc):
            blocks = page.get_text("blocks")
            for block in blocks:
                original = block[4].strip()
                if len(original) < 30: continue
                
                try:
                    prompt = f"English:\n{original}\n\nKorean Translation:\n(Please translate fully)"
                    response = model.generate_content(prompt)
                    
                    translated = response.text
                    # 문단별로 결과 누적
                    segment = f"--- Paragraph ---\n[ENG]\n{original}\n\n[KOR]\n{translated}\n\n"
                    full_content += segment
                    
                    # 실시간으로 화면에 업데이트하여 연결 유지
                    live_display.text_area("번역 진행 중...", value=full_content, height=400)
                    time.sleep(1.5) 
                except Exception as e:
                    if "429" in str(e):
                        time.sleep(10)
                    continue
            
            progress_bar.progress((page_num + 1) / total_pages)
            status_text.info(f"{page_num + 1} / {total_pages} 페이지 완료")

        # 모든 번역 완료 후 세션에 저장
        st.session_state.result_text = full_content
        st.balloons() # 축하 효과

    # 번역된 결과가 있으면 화면에 표시 및 다운로드 버튼 활성화
    if st.session_state.result_text:
        st.subheader("✅ 전체 번역 완료")
        st.text_area("전체 결과 (복사 가능)", value=st.session_state.result_text, height=600)
        st.download_button(
            label="번역 결과 파일(.txt) 다운로드",
            data=st.session_state.result_text,
            file_name=f"translated_{uploaded_file.name}.txt",
            mime="text/plain"
        )
