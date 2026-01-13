import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import re
import io

# 1. 앱 제목 및 설명 설정
st.title("🖍️ PDF 형광펜 추출기")
st.write("PDF 파일을 업로드하면 형광펜으로 칠한 부분과 페이지 번호를 엑셀로 추출해줍니다.")

# 2. 사이드바: 변수 설정 (사용자가 직접 입력 가능)
st.sidebar.header("설정")
front_matter = st.sidebar.number_input(
    "앞부속 페이지 수 (실제 1페이지가 시작되기 전 페이지 수)", 
    min_value=0, 
    value=16, 
    step=1
)

# 3. 파일 업로드 기능
uploaded_file = st.file_uploader("PDF 파일을 드래그하거나 선택하세요", type=["pdf"])

# 텍스트 정제 함수
def clean_text(text):
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)

if uploaded_file is not None:
    # 업로드된 파일을 메모리에서 열기
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    data = []

    # 진행 상황 표시 바
    progress_bar = st.progress(0)
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # 진행률 업데이트
        progress_bar.progress((page_num + 1) / len(doc))

        for annot in page.annots() or []:
            if annot.type[0] == 8:  # 하이라이트
                highlight_text = ""
                quads = annot.vertices
                for i in range(0, len(quads), 4):
                    rect = fitz.Quad(quads[i:i+4]).rect
                    highlight_text += page.get_text("text", clip=rect)
                
                highlight_text = clean_text(highlight_text.strip())
                
                if highlight_text:
                    data.append({
                        "페이지": page_num + 1 + front_matter,
                        "하이라이트 내용": highlight_text
                    })
    
    # 결과 처리
    if data:
        df = pd.DataFrame(data)
        
        # 4. 엑셀 다운로드 버튼 생성 (메모리 버퍼 사용)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        st.success(f"총 {len(data)}개의 하이라이트를 찾았습니다! 아래 버튼을 눌러 다운로드하세요.")
        
        st.download_button(
            label="📥 엑셀 파일 다운로드",
            data=output.getvalue(),
            file_name="highlighted_keywords.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("형광펜으로 표시된 내용을 찾지 못했습니다.")