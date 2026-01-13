import streamlit as st
import fitz
import google.generativeai as genai
import time

st.set_page_config(page_title="논문 전체 번역기 (무료 버전)", layout="wide")
st.title("📄 Gemini 무료 논문 번역기 (영문+한글 대조)")

# Gemini API 키 입력
api_key = st.sidebar.text_input("Google Gemini API Key를 입력하세요", type="password")

uploaded_file = st.file_uploader("번역할 PDF 파일을 업로드하세요", type="pdf")

if uploaded_file and api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash') # 무료이면서 빠른 모델
    
    if st.button("번역 시작"):
        with st.spinner("Gemini가 번역 중입니다..."):
            pdf_data = uploaded_file.read()
            doc = fitz.open(stream=pdf_data, filetype="pdf")
            final_output = ""
            
            progress_bar = st.progress(0)
            total_pages = len(doc)

            for page_num, page in enumerate(doc):
                text_blocks = page.get_text("blocks")
                for block in text_blocks:
                    original_text = block[4].strip()
                    if len(original_text) < 20: continue
                    
                    try:
                        # Gemini에게 번역 요청
                        prompt = f"Translate the following text into Korean. Keep the original English paragraph first, then the Korean translation. Do not summarize.\n\n{original_text}"
                        response = model.generate_content(prompt)
                        
                        final_output += f"{response.text}\n\n---\n\n"
                        time.sleep(1) # 무료 티어 속도 제한(RPM) 준수
                    except Exception as e:
                        st.error(f"오류 발생: {e}")
                        break
                
                progress_bar.progress((page_num + 1) / total_pages)

            st.success("번역 완료!")
            st.text_area("결과물", value=final_output, height=500)
            st.download_button("결과 파일 다운로드", data=final_output, file_name="translated_gemini.txt")
