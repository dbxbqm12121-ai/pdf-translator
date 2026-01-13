import streamlit as st
import fitz
import google.generativeai as genai
import time

st.set_page_config(page_title="논문 번역기 최종", layout="wide")
st.title("📄 논문 전체 번역기 (텍스트 강제 출력 버전)")

# 세션 상태에 결과 저장 (새로고침 방지)
if 'final_res' not in st.session_state:
    st.session_state.final_res = ""

api_key = st.sidebar.text_input("Google Gemini API Key", type="password")
uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type="pdf")

if uploaded_file and api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    if st.button("번역 시작"):
        st.session_state.final_res = "" # 초기화
        pdf_data = uploaded_file.read()
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        
        full_text_accumulator = ""
        progress_bar = st.progress(0)
        
        # 화면에 실시간으로 보일 영역
        output_placeholder = st.empty()

        for page_num, page in enumerate(doc):
            # 페이지의 모든 텍스트를 그냥 가져옵니다 (가장 확실한 방법)
            page_text = page.get_text()
            # 줄바꿈 기준으로 나누되, 너무 짧은 줄은 합치거나 무시
            paragraphs = [p.strip() for p in page_text.split('\n\n') if len(p.strip()) > 20]
            
            for para in paragraphs:
                try:
                    prompt = f"Translate the following academic text into Korean. Keep English first, then Korean. Do not omit anything.\n\n{para}"
                    response = model.generate_content(prompt)
                    
                    translated = response.text
                    chunk = f"**[Original]**\n{para}\n\n**[Translation]**\n{translated}\n\n---\n"
                    
                    full_text_accumulator += chunk
                    # 매 문단마다 화면을 강제로 갱신합니다.
                    output_placeholder.markdown(full_text_accumulator)
                    
                    time.sleep(1.0) # 속도 제한 방지
                except Exception as e:
                    continue
            
            progress_bar.progress((page_num + 1) / len(doc))
        
        st.session_state.final_res = full_text_accumulator
        st.success("모든 번역이 완료되었습니다!")

    # 결과가 있을 때만 다운로드 버튼 표시
    if st.session_state.final_res:
        st.download_button(
            label="번역 결과 파일(.txt) 다운로드",
            data=st.session_state.final_res,
            file_name="translated_paper.txt"
        )
