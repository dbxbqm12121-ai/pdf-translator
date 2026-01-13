import streamlit as st
import fitz
from openai import OpenAI
import time # 시간 지연을 위해 추가

st.set_page_config(page_title="논문 전체 번역기", layout="wide")
st.title("📄 논문 전체 번역 (영문+한글 대조)")

api_key = st.sidebar.text_input("OpenAI API Key를 입력하세요", type="password")
uploaded_file = st.file_uploader("번역할 PDF 파일을 업로드하세요", type="pdf")

if uploaded_file and api_key:
    client = OpenAI(api_key=api_key)
    
    if st.button("번역 시작 (전체 내용 출력)"):
        with st.spinner("논문을 분석하고 번역 중입니다..."):
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
                        # 모델을 gpt-4o-mini로 변경하여 안정성 확보
                        response = client.chat.completions.create(
                            model="gpt-4o-mini", 
                            messages=[{"role": "system", "content": "You are a professional translator. Provide English text and Korean translation paragraph by paragraph. Never summarize."},
                                      {"role": "user", "content": original_text}]
                        )
                        translated_text = response.choices[0].message.content
                        final_output += f"{translated_text}\n\n---\n\n"
                        time.sleep(0.5) # API 과부하 방지를 위한 0.5초 휴식
                    except Exception as e:
                        st.error(f"오류 발생: {e}")
                        break
                
                progress_bar.progress((page_num + 1) / total_pages)

            st.success("번역 완료!")
            st.text_area("결과물", value=final_output, height=500)
            st.download_button("결과 파일 다운로드", data=final_output, file_name="translated.txt")
