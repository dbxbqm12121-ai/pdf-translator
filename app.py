import streamlit as st
import fitz
import google.generativeai as genai
import time

st.set_page_config(page_title="논문 전체 번역기 (자동 모델 찾기)", layout="wide")
st.title("📄 Gemini 무료 논문 번역기 (오류 해결 버전)")

api_key = st.sidebar.text_input("Google Gemini API Key를 입력하세요", type="password")
uploaded_file = st.file_uploader("번역할 PDF 파일을 업로드하세요", type="pdf")

def get_working_model(api_key):
    genai.configure(api_key=api_key)
    # 내 계정에서 사용 가능한 모델 목록 확인
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            # flash 모델이 있으면 우선 선택, 없으면 아무거나 선택
            if '1.5-flash' in m.name:
                return m.name
    return "models/gemini-pro" # 기본값

if uploaded_file and api_key:
    try:
        # 작동하는 모델 자동 검색
        target_model = get_working_model(api_key)
        st.info(f"사용 중인 모델: {target_model}")
        model = genai.GenerativeModel(target_model)
        
        if st.button("번역 시작"):
            with st.spinner("중단 없이 전체 번역을 진행 중입니다..."):
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
                            # 1:1 대조 번역 지시 (축약 금지 강화)
                            prompt = f"Translate the following text into Korean. Show the original English text first, and then the Korean translation. Translation must be full and complete without any omission or summary.\n\n[Original English]\n{original_text}"
                            response = model.generate_content(prompt)
                            
                            final_output += f"{response.text}\n\n---\n\n"
                            # 무료 티어 안정성을 위해 대기 시간 확보
                            time.sleep(2.0) 
                        except Exception as e:
                            if "429" in str(e): # 속도 제한 에러 시 더 오래 대기
                                st.warning("속도 제한 발생. 5초 대기 후 다시 시도합니다...")
                                time.sleep(5)
                                continue
                            st.warning(f"문단 오류: {e}")
                            continue
                    
                    progress_bar.progress((page_num + 1) / total_pages)

                if final_output:
                    st.success("번역이 완료되었습니다!")
                    st.text_area("결과물", value=final_output, height=500)
                    st.download_button("결과물 다운로드(.txt)", data=final_output, file_name="translated_full.txt")
                else:
                    st.error("번역 결과가 생성되지 않았습니다.")
    except Exception as e:
        st.error(f"초기화 실패: {e}")
