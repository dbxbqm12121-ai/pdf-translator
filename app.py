import streamlit as st
import fitz
import google.generativeai as genai
import time

st.set_page_config(page_title="논문 번역기", layout="wide")
st.title("🚀 논문 전체 번역 (404 에러 해결 버전)")

api_key = st.sidebar.text_input("Google API Key", type="password")
uploaded_file = st.file_uploader("PDF 업로드", type="pdf")

if uploaded_file and api_key:
    try:
        genai.configure(api_key=api_key)
        
        # [수정] 내 계정에서 실제로 작동하는 모델 경로를 직접 가져옵니다.
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # flash 모델이 있으면 쓰고, 없으면 첫 번째 모델을 강제 지정
        target_model = next((m for m in models if "flash" in m), models[0] if models else "")
        
        if not target_model:
            st.error("사용 가능한 모델이 없습니다. API 키를 확인하세요.")
        else:
            model = genai.GenerativeModel(target_model)
            st.info(f"연결 성공: {target_model}")

            if st.button("지금 바로 번역 시작"):
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                display_area = st.container() 
                
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text = page.get_text()
                    
                    if len(text.strip()) < 50: continue
                    
                    try:
                        # 1:1 대조 번역 지시 (축약 금지)
                        prompt = f"Original text:\n{text}\n\nTranslate the text above into Korean fully. Do not summarize. Show English first, then Korean translation."
                        response = model.generate_content(prompt)
                        
                        with display_area:
                            st.subheader(f"Page {page_num + 1}")
                            st.markdown(response.text)
                            st.divider()
                        
                        time.sleep(2) # 무료 티어 속도 제한 방지
                    except Exception as e:
                        st.error(f"Page {page_num + 1} 오류: {e}")
                        time.sleep(5)
                
                st.success("전체 번역이 완료되었습니다!")
    except Exception as e:
        st.error(f"초기 설정 에러: {e}")
