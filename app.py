import streamlit as st
import fitz
import google.generativeai as genai
import time

st.set_page_config(page_title="논문 전체 번역기 (최종 수정본)", layout="wide")
st.title("📄 Gemini 무료 논문 번역기 (404 오류 해결 버전)")

api_key = st.sidebar.text_input("Google Gemini API Key를 입력하세요", type="password")
uploaded_file = st.file_uploader("번역할 PDF 파일을 업로드하세요", type="pdf")

if uploaded_file and api_key:
    try:
        genai.configure(api_key=api_key)
        
        # [수정 포인트] 사용 가능한 모델을 찾아서 리스트에 저장
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        # 가장 적절한 모델 선택 (1.5-flash -> 1.5-pro -> 첫 번째 모델 순)
        target_model = ""
        for name in available_models:
            if "1.5-flash" in name:
                target_model = name
                break
        if not target_model and available_models:
            target_model = available_models[0]

        if target_model:
            st.info(f"선택된 모델: {target_model}")
            model = genai.GenerativeModel(model_name=target_model)
        else:
            st.error("사용 가능한 모델을 찾을 수 없습니다. API 키 권한을 확인해주세요.")
        
        if st.button("번역 시작") and target_model:
            with st.spinner("중단 없이 전체 내용을 번역 중입니다..."):
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
                            # 프롬프트: 원문 유지 및 번역 지시
                            prompt = f"Please provide the following text in both English and Korean. \nFormat: [English Paragraph] \n\n[Korean Translation] \n\nDo not summarize. Translate everything.\n\nText: {original_text}"
                            
                            response = model.generate_content(prompt)
                            
                            if response.text:
                                final_output += f"{response.text}\n\n---\n\n"
                                # 무료 티어 안전을 위해 2초 대기
                                time.sleep(2.0) 
                        except Exception as e:
                            # 429(속도제한) 발생 시 대기 후 재시도
                            if "429" in str(e):
                                time.sleep(10)
                                continue
                            st.warning(f"문단 오류 건너뜀: {e}")
                            continue
                    
                    progress_bar.progress((page_num + 1) / total_pages)

                if final_output:
                    st.success("번역 완료!")
                    st.text_area("결과물", value=final_output, height=500)
                    st.download_button("결과물 다운로드(.txt)", data=final_output, file_name="translated_full.txt")
    except Exception as e:
        st.error(f"초기화 실패: {e}")
