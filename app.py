import streamlit as st
import fitz  # PyMuPDF
from openai import OpenAI
import io

st.set_page_config(page_title="논문 전체 번역기", layout="wide")
st.title("📄 논문 전체 번역 (영문+한글 대조)")

# API 키 설정
api_key = st.sidebar.text_input("OpenAI API Key를 입력하세요", type="password")

uploaded_file = st.file_uploader("번역할 PDF 파일을 업로드하세요", type="pdf")

if uploaded_file and api_key:
    client = OpenAI(api_key=api_key)
    
    if st.button("번역 시작 (전체 내용 출력)"):
        with st.spinner("논문 전체를 번역 중입니다. 잠시만 기다려주세요..."):
            pdf_data = uploaded_file.read()
            doc = fitz.open(stream=pdf_data, filetype="pdf")
            
            final_output = ""
            
            # 페이지별 루프
            for page_num, page in enumerate(doc):
                text_blocks = page.get_text("blocks")
                
                for block in text_blocks:
                    original_text = block[4].strip()
                    if len(original_text) < 20: continue # 너무 짧은 텍스트(페이지 번호 등) 제외
                    
                    # AI에게 생략 없는 1:1 번역 지시
                    prompt = f"Translate the following academic text into Korean. Output format: [Original English Paragraph] followed by [Korean Translation]. Do not summarize, do not omit any sentences, and do not provide any extra commentary.\n\nText: {original_text}"
                    
                    response = client.chat.completions.create(
                        model="gpt-4o", # 또는 gpt-4o-mini (비용 절감 시)
                        messages=[{"role": "user", "content": prompt}]
                    )
                    
                    translated_text = response.choices[0].message.content
                    final_output += f"{translated_text}\n\n"
                    
                st.write(f"현재 {page_num + 1} / {len(doc)} 페이지 처리 중...")

            # 결과 화면 출력 및 다운로드 버튼
            st.success("번역이 완료되었습니다!")
            st.text_area("번역 결과 (전체)", value=final_output, height=400)
            
            # 결과물 파일로 다운로드 가능하게 생성
            st.download_button(
                label="번역 결과 파일(.txt) 다운로드",
                data=final_output,
                file_name=f"translated_{uploaded_file.name}.txt",
                mime="text/plain"
            )
