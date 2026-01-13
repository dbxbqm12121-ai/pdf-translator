import streamlit as st
import fitz
import google.generativeai as genai
import time

st.set_page_config(page_title="논문 전체 번역기 (Gemini)", layout="wide")
st.title("📄 Gemini 무료 논문 번역기")

api_key = st.sidebar.text_input("Google Gemini API Key를 입력하세요", type="password")
uploaded_file = st.file_uploader("번역할 PDF 파일을 업로드하세요", type="pdf")

if uploaded_file and api_key:
    try:
        genai.configure(api_key=api_key)
        # 모델 명칭을 가장 호환성 높은 버전으로 변경
        model = genai.GenerativeModel('gemini-1.5-flash-latest') 
        
        if st.button("번역 시작"):
            with st.spinner("논문을 한 문단씩 읽고 번역하는 중입니다..."):
                pdf_data = uploaded_file.read()
                doc = fitz.open(stream=pdf_data, filetype="pdf")
                final_output = ""
                
                progress_bar = st.progress(0)
                total_pages = len(doc)

                for page_num, page in enumerate(doc):
                    text_blocks = page.get_text("blocks")
                    for block in text_blocks:
                        original_text = block[4].strip()
                        # 의미 있는 길이의 텍스트만 처리
                        if len(original_text) < 30: continue
                        
                        try:
                            prompt = f"Original English:\n{original_text}\n\nKorean Translation:\n(Please translate fully without skipping any sentences)"
                            response = model.generate_content(prompt)
                            
                            # 번역 결과 추출
                            translated_text = response.text
                            final_output += f"--- 문단 시작 ---\n[English]\n{original_text}\n\n[Korean]\n{translated_text}\n\n"
                            
                            # 무료 티어는 요청 간격이 중요합니다 (1.5초 대기)
                            time.sleep(1.5) 
                        except Exception as e:
                            st.warning(f"일부 문단 건너뜀 (오류: {e})")
                            continue
                    
                    progress_bar.progress((page_num + 1) / total_pages)

                if final_output:
                    st.success("모든 작업이 완료되었습니다!")
                    st.text_area("번역 결과 미리보기", value=final_output, height=500)
                    st.download_button("전체 번역본(.txt) 다운로드", data=final_output, file_name="translated_paper.txt")
                else:
                    st.error("번역된 내용이 없습니다. PDF의 텍스트를 읽을 수 없거나 API 키를 확인해주세요.")
    except Exception as e:
        st.error(f"초기 설정 오류: {e}")
