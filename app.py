import streamlit as st
import fitz
import google.generativeai as genai
import time

st.set_page_config(page_title="논문 전체 번역기 (완주 버전)", layout="wide")
st.title("📄 끝까지 번역하는 논문 번역기")

# 세션 상태 초기화 (중간에 초기화되는 것을 방지)
if 'full_text' not in st.session_state:
    st.session_state.full_text = ""
if 'is_translating' not in st.session_state:
    st.session_state.is_translating = False

api_key = st.sidebar.text_input("Google Gemini API Key", type="password")
uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type="pdf")

if uploaded_file and api_key:
    genai.configure(api_key=api_key)
    
    # 작동하는 모델 찾기
    @st.cache_resource
    def load_model(key):
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods and '1.5-flash' in m.name:
                return m.name
        return "models/gemini-1.5-flash"

    target_model = load_model(api_key)
    model = genai.GenerativeModel(target_model)

    if st.button("번역 시작"):
        st.session_state.is_translating = True
        st.session_state.full_text = "" # 새로 시작할 때 초기화
        
        pdf_data = uploaded_file.read()
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        total_pages = len(doc)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        result_area = st.empty() # 실시간으로 번역 내용을 보여줄 공간

        for page_num, page in enumerate(doc):
            blocks = page.get_text("blocks")
            for block in blocks:
                original = block[4].strip()
                if len(original) < 30: continue
                
                try:
                    prompt = f"Translate the following into Korean. Provide English first, then Korean translation. No summaries.\n\n[English]\n{original}"
                    response = model.generate_content(prompt)
                    
                    # 결과를 세션에 계속 누적
                    translated = response.text
                    st.session_state.full_text += f"{translated}\n\n---\n\n"
                    
                    # 실시간으로 화면에 업데이트 (사용자가 멈춘 게 아니라는 걸 알게 함)
                    result_area.text_area("실시간 번역 진행 상황", value=st.session_state.full_text, height=300)
                    
                    time.sleep(1.5) # 속도 제한 방지
                except Exception as e:
                    if "429" in str(e):
                        status_text.warning("속도 제한 발생! 10초간 대기합니다...")
                        time.sleep(10)
                    continue
            
            progress_bar.progress((page_num + 1) / total_pages)
            status_text.info(f"현재 {page_num + 1} / {total_pages} 페이지 완료")

        st.session_state.is_translating = False
        st.success("🎉 모든 번역이 완료되었습니다!")

    # 번역이 완료되었거나 진행 중일 때 다운로드 버튼 항상 표시
    if st.session_state.full_text:
        st.download_button(
            label="지금까지 번역된 결과 다운로드",
            data=st.session_state.full_text,
            file_name="translated_full_paper.txt",
            mime="text/plain"
        )
