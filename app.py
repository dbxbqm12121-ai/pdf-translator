import streamlit as st
import fitz
import google.generativeai as genai
import time

st.set_page_config(page_title="논문 번역기", layout="wide")
st.title("🚀 논문 전체 번역 (긴급 모드)")

api_key = st.sidebar.text_input("Google API Key", type="password")
uploaded_file = st.file_uploader("PDF 업로드", type="pdf")

if uploaded_file and api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    if st.button("지금 바로 번역 시작"):
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        
        # 1. 화면에 진행 상황을 실시간으로 뿌려줄 빈 칸을 미리 만듭니다.
        display_area = st.container() 
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            
            if len(text.strip()) < 50: continue # 내용 없는 페이지 건너뜀
            
            try:
                # 페이지 단위로 통째로 요청 (속도 향상)
                prompt = f"Translate the following page into Korean. Show English original first, then Korean. Do not summarize.\n\n{text}"
                response = model.generate_content(prompt)
                
                # 2. 번역이 한 페이지 끝날 때마다 화면에 바로 출력 (이게 안 뜰 수가 없습니다)
                with display_area:
                    st.subheader(f"Page {page_num + 1}")
                    st.markdown(response.text)
                    st.divider()
                
                time.sleep(2) # 무료 계정 속도 제한 방지
            except Exception as e:
                st.error(f"Page {page_num + 1} 에러: {e}")
                time.sleep(5)
        
        st.success("전체 번역이 완료되었습니다. 화면을 드래그해서 복사하세요!")
