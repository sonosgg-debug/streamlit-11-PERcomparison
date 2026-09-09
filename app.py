import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import datetime

import per_loader

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="한국 및 미국 시장 종목별 PER 변화 추이 비교",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 커스텀 CSS 스타일링 (31 PerformanceChart 및 다크 테마 일관성 유지)
st.markdown("""
<style>
    /* 메인 배경 및 폰트 */
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2.5rem;
    }
    
    /* 사이드바 스타일링 (기존 기본 폭 대비 약 20% 축소) */
    [data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1F2937;
    }
    section[data-testid="stSidebar"][aria-expanded="true"],
    [data-testid="stSidebar"][aria-expanded="true"] {
        width: 270px !important;
        min-width: 270px !important;
        max-width: 270px !important;
    }
    
    /* 메트릭 카드 커스텀 디자인 */
    .metric-card {
        background: linear-gradient(135deg, #1E2430 0%, #171C26 100%);
        border: 1px solid #2D3748;
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .metric-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #94A3B8;
        margin-bottom: 4px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .metric-val {
        font-size: 1.55rem;
        font-weight: 800;
        color: #F8FAFC;
        letter-spacing: -0.5px;
    }
    .metric-sub {
        font-size: 0.76rem;
        color: #64748B;
        margin-top: 4px;
    }
    .badge-up {
        color: #F43F5E;
        font-weight: 700;
    }
    .badge-down {
        color: #38BDF8;
        font-weight: 700;
    }
    
    /* 탭 디자인 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px 6px 0px 0px;
        padding: 8px 16px;
        background-color: #1E2430;
        color: #94A3B8;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2D3748 !important;
        color: #8AB4F8 !important;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# 3. 데이터 로딩 캐싱 함수
@st.cache_data(ttl=86400)
def get_cached_krx_data():
    return per_loader.load_krx_data()

@st.cache_data(ttl=3600)
def get_cached_per_data(targets_tuple, period_str):
    return per_loader.load_all_per_data(list(targets_tuple), period_str)

krx_df = get_cached_krx_data()
stock_select_options = per_loader.build_stock_options(krx_df)

# 디폴트 5개 종목 인덱스 탐색
def find_default_index(search_keys):
    for key in search_keys:
        for idx, opt in enumerate(stock_select_options):
            if key in opt:
                return idx
    return 0

default_idx1 = find_default_index(["삼성전자 (005930)", "삼성전자"])
default_idx2 = find_default_index(["SK하이닉스 (000660)", "SK하이닉스"])
default_idx3 = find_default_index(["마이크론 (MU)", "(MU)"])
default_idx4 = find_default_index(["샌디스크 (SNDK)", "(SNDK)"])
default_idx5 = find_default_index(["TSMC (TSM)", "(TSM)"])

# ==================== 사이드바 (왼쪽 대시보드 패널) ====================
st.sidebar.markdown("<h2 style='font-size: 1.25rem; font-weight: 700; color: #F8FAFC; margin-bottom: 8px;'>⚙️ 대시보드 설정</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<hr style='border: 0; height: 1px; background-color: #334155; margin-bottom: 18px;'>", unsafe_allow_html=True)

st.sidebar.markdown("<h3 style='font-size: 0.98rem; font-weight: 600; color: #8AB4F8; margin-bottom: 8px;'>🔍 종목 선택 (5개)</h3>", unsafe_allow_html=True)

# 종목 1
select_s1 = st.sidebar.selectbox("종목 1", options=stock_select_options, index=default_idx1, key="sb1")
custom_s1 = st.sidebar.text_input("종목 1 직접 입력", placeholder="예: 005930, AAPL", key="ci1") if select_s1 == "[직접 입력]" else ""

# 종목 2
select_s2 = st.sidebar.selectbox("종목 2", options=stock_select_options, index=default_idx2, key="sb2")
custom_s2 = st.sidebar.text_input("종목 2 직접 입력", placeholder="예: 000660, NVDA", key="ci2") if select_s2 == "[직접 입력]" else ""

# 종목 3
select_s3 = st.sidebar.selectbox("종목 3", options=stock_select_options, index=default_idx3, key="sb3")
custom_s3 = st.sidebar.text_input("종목 3 직접 입력", placeholder="예: MU, MSFT", key="ci3") if select_s3 == "[직접 입력]" else ""

# 종목 4
select_s4 = st.sidebar.selectbox("종목 4", options=stock_select_options, index=default_idx4, key="sb4")
custom_s4 = st.sidebar.text_input("종목 4 직접 입력", placeholder="예: SNDK, WDC", key="ci4") if select_s4 == "[직접 입력]" else ""

# 종목 5
select_s5 = st.sidebar.selectbox("종목 5", options=stock_select_options, index=default_idx5, key="sb5")
custom_s5 = st.sidebar.text_input("종목 5 직접 입력", placeholder="예: TSM, ASML", key="ci5") if select_s5 == "[직접 입력]" else ""

st.sidebar.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# 기간 선택
st.sidebar.markdown("<h3 style='font-size: 0.98rem; font-weight: 600; color: #8AB4F8; margin-bottom: 8px;'>📅 기간 선택</h3>", unsafe_allow_html=True)
period_options = ["1M", "3M", "6M", "1Y", "3Y"]
selected_period = st.sidebar.selectbox(
    "조회 기간",
    options=period_options,
    index=0,  # 디폴트 1M
    help="1M: 1개월, 3M: 3개월, 6M: 6개월, 1Y: 1년, 3Y: 3년"
)

st.sidebar.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

# 조회 버튼
query_button = st.sidebar.button("조회 🚀", use_container_width=True, type="primary")


# ==================== 메인 화면 (오른쪽 패널) ====================

# 1. 타이틀 영역 (서브타이틀 없이 폰트 색상 #8AB4F8)
st.markdown("<h1 style='text-align: center; font-size: 1.85rem; font-weight: 800; color: #8AB4F8; margin-top: 5px; margin-bottom: 12px;'>한국 및 미국 시장 종목별 PER 변화 추이 비교</h1>", unsafe_allow_html=True)

# 2. 타이틀 영역과 차트 영역 사이 가로선
st.markdown("<hr style='border: 0; height: 1px; background-color: #334155; margin-bottom: 22px;'>", unsafe_allow_html=True)

# 상태 세션 초기화
if "executed" not in st.session_state:
    st.session_state["executed"] = True

# 조회 실행 여부 확인 (최초 진입 또는 버튼 클릭 시)
if query_button or st.session_state.get("executed", False):
    st.session_state["executed"] = True

    # 5개 종목 타겟 파싱
    raw_selections = [
        (select_s1, custom_s1),
        (select_s2, custom_s2),
        (select_s3, custom_s3),
        (select_s4, custom_s4),
        (select_s5, custom_s5),
    ]

    valid_targets = []
    seen_symbols = set()

    for idx, (sel_disp, cust_inp) in enumerate(raw_selections):
        symbol, disp_name, mkt_type = per_loader.resolve_stock_selection(sel_disp, cust_inp, krx_df)
        if symbol:
            if symbol not in seen_symbols:
                seen_symbols.add(symbol)
                valid_targets.append((symbol, disp_name, mkt_type))
            else:
                st.sidebar.warning(f"⚠️ 중복된 종목 '{disp_name}'은(는) 한 번만 포함됩니다.")

    if not valid_targets:
        st.warning("⚠️ 선택된 유효한 종목이 없습니다. 왼쪽 사이드바에서 종목을 선택한 후 [조회] 버튼을 눌러주세요.")
    else:
        # 데이터 로딩 스피너
        with st.spinner(f"선택한 {len(valid_targets)}개 종목의 과거 PER 시계열 데이터를 수집 및 분석 중입니다..."):
            combined_df, summary_df, err_dict = get_cached_per_data(tuple(valid_targets), selected_period)

        if err_dict:
            for item, msg in err_dict.items():
                st.sidebar.info(f"ℹ️ {msg}")

        if combined_df.empty:
            st.error("❌ 선택한 종목 및 기간에 대한 PER 데이터를 확보하지 못했습니다. 종목 코드나 기간을 다시 확인해 주세요.")
        else:
            # ----------------------------------------------------
            # 1. 상단 전문가 요약 KPI 카드 (5개 종목 핵심 지표)
            # ----------------------------------------------------
            st.markdown("<h3 style='font-size: 1.15rem; font-weight: 700; color: #F8FAFC; margin-bottom: 4px;'>📌 핵심 밸류에이션 요약 (현재 PER 및 기간 변화)</h3>", unsafe_allow_html=True)
            st.caption("※ 한국 및 미국 전 종목 모두 직전 4개 분기 실적 합산(TTM: Trailing Twelve Months) 기준의 분기 롤링 PER로 동일하게 산출되어 왜곡 없이 1:1 비교됩니다.")
            
            card_cols = st.columns(len(summary_df))
            for i, (_, row) in enumerate(summary_df.iterrows()):
                name = row["종목명"]
                cur_pe = row["현재 PER"]
                fwd_pe = row.get("Fwd(12MF) PER")
                fwd_text = f"{fwd_pe:.2f}배" if pd.notnull(fwd_pe) and fwd_pe is not None else "-"
                avg_pe = row["기간 평균 PER"]
                chg_pct = row["PER 변동률 (%)"]
                badge_class = "badge-up" if chg_pct >= 0 else "badge-down"
                sign = "+" if chg_pct > 0 else ""

                with card_cols[i]:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title" title="{name}">{name}</div>
                        <div class="metric-val">{cur_pe:.2f} <span style="font-size: 0.85rem; font-weight: 500; color: #94A3B8;">배 (Trailing TTM)</span></div>
                        <div class="metric-sub" style="margin-top: 6px;">
                            변동: <span class="{badge_class}">{sign}{chg_pct:.2f}%</span> | 평균: <span style="color: #CBD5E1;">{avg_pe:.2f}배</span><br/>
                            <span style="color: #94A3B8; font-weight: 600;">Fwd(12MF):</span> <span style="color: #34D399; font-weight: 700;">{fwd_text}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            # ----------------------------------------------------
            # 2. 차트 영역 (차트 탭 구성: 절대 PER 추이 vs 상대 멀티플 지수)
            # ----------------------------------------------------
            st.markdown("<h3 style='font-size: 1.15rem; font-weight: 700; color: #F8FAFC; margin-bottom: 12px;'>📉 PER 시계열 변화 추이 차트</h3>", unsafe_allow_html=True)
            
            chart_tab1, chart_tab2, chart_tab3 = st.tabs(["📊 PER 절대 수치 추이", "📈 상대 멀티플 지수 (기준일=100)", "🎯 밸류에이션 밴드 (최저~평균~최고)"])

            chart_colors = ['#38BDF8', '#F43F5E', '#10B981', '#FBBF24', '#A855F7', '#EC4899', '#6366F1']

            # Tab 1: PER 절대 수치 꺾은선 그래프
            with chart_tab1:
                fig1 = go.Figure()
                for i, col_name in enumerate(combined_df.columns):
                    c = chart_colors[i % len(chart_colors)]
                    series = combined_df[col_name].dropna()
                    fig1.add_trace(go.Scatter(
                        x=series.index,
                        y=series.values,
                        mode='lines+markers',
                        name=col_name,
                        marker=dict(size=4),
                        line=dict(width=2.5, color=c),
                        hovertemplate='<b>' + col_name + '</b>: %{y:.2f}배<extra></extra>'
                    ))

                fig1.update_layout(
                    title=dict(
                        text=f"<b>종목별 PER(Price-to-Earnings Ratio) 일별 변화 추이 ({selected_period})</b>",
                        font=dict(size=16, color="#F8FAFC"),
                        x=0.0
                    ),
                    xaxis=dict(
                        title=dict(text="일자", font=dict(color="#CBD5E1", size=13)),
                        gridcolor="#2A3342",
                        showline=True,
                        linewidth=1,
                        linecolor="#3E4C5E",
                        tickfont=dict(color="#CBD5E1")
                    ),
                    yaxis=dict(
                        title=dict(text="PER (배)", font=dict(color="#CBD5E1", size=13)),
                        gridcolor="#2A3342",
                        showline=True,
                        linewidth=1,
                        linecolor="#3E4C5E",
                        ticksuffix="배",
                        tickfont=dict(color="#CBD5E1")
                    ),
                    hovermode="x unified",
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1,
                        font=dict(size=12, color="#E2E8F0"),
                        bgcolor="rgba(30, 36, 48, 0.9)",
                        bordercolor="#3E4C5E",
                        borderwidth=1
                    ),
                    hoverlabel=dict(
                        bgcolor="#0F172A",
                        font_color="#FFFFFF",
                        font_size=12,
                        bordercolor="#3E4C5E"
                    ),
                    font=dict(
                        family="Pretendard, -apple-system, Malgun Gothic, sans-serif",
                        color="#E2E8F0"
                    ),
                    plot_bgcolor="#161B24",
                    paper_bgcolor="#1E2430",
                    margin=dict(l=40, r=40, t=75, b=40),
                    height=530
                )
                st.plotly_chart(fig1, use_container_width=True, theme=None)

            # Tab 2: 상대 멀티플 지수 (시작가 100 기준 밸류에이션 확장/수축)
            with chart_tab2:
                fig2 = go.Figure()
                normalized_df = combined_df.copy()
                for col in normalized_df.columns:
                    first_val = normalized_df[col].dropna().iloc[0] if not normalized_df[col].dropna().empty else 1.0
                    normalized_df[col] = (normalized_df[col] / first_val) * 100

                for i, col_name in enumerate(normalized_df.columns):
                    c = chart_colors[i % len(chart_colors)]
                    series = normalized_df[col_name].dropna()
                    fig2.add_trace(go.Scatter(
                        x=series.index,
                        y=series.values,
                        mode='lines',
                        name=col_name,
                        line=dict(width=2.5, color=c),
                        hovertemplate='<b>' + col_name + '</b>: %{y:.2f}p<extra></extra>'
                    ))

                fig2.add_hline(y=100, line_dash="dash", line_color="#94A3B8", opacity=0.7, annotation_text="기준점(100)", annotation_position="top right")

                fig2.update_layout(
                    title=dict(
                        text=f"<b>상대적 밸류에이션 멀티플 확장/수축 추이 (시작일 = 100pt, {selected_period})</b>",
                        font=dict(size=16, color="#F8FAFC"),
                        x=0.0
                    ),
                    xaxis=dict(
                        title=dict(text="일자", font=dict(color="#CBD5E1")),
                        gridcolor="#2A3342",
                        linecolor="#3E4C5E",
                        tickfont=dict(color="#CBD5E1")
                    ),
                    yaxis=dict(
                        title=dict(text="멀티플 지수 (100pt 기준)", font=dict(color="#CBD5E1")),
                        gridcolor="#2A3342",
                        linecolor="#3E4C5E",
                        ticksuffix="p",
                        tickfont=dict(color="#CBD5E1")
                    ),
                    hovermode="x unified",
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1,
                        font=dict(size=12, color="#E2E8F0"),
                        bgcolor="rgba(30, 36, 48, 0.9)",
                        bordercolor="#3E4C5E"
                    ),
                    plot_bgcolor="#161B24",
                    paper_bgcolor="#1E2430",
                    margin=dict(l=40, r=40, t=75, b=40),
                    height=530
                )
                st.plotly_chart(fig2, use_container_width=True, theme=None)

            # Tab 3: 전문가 밸류에이션 밴드 (Min - Avg - Max - Current Range Bar)
            with chart_tab3:
                fig3 = go.Figure()
                for i, (_, row) in enumerate(summary_df.iterrows()):
                    name = row["종목명"]
                    min_v = row["기간 최저 PER"]
                    max_v = row["기간 최고 PER"]
                    avg_v = row["기간 평균 PER"]
                    cur_v = row["현재 PER"]
                    c = chart_colors[i % len(chart_colors)]

                    # 전체 범위 (최저 ~ 최고 선)
                    fig3.add_trace(go.Scatter(
                        x=[min_v, max_v],
                        y=[name, name],
                        mode='lines',
                        line=dict(color=c, width=6),
                        hoverinfo='none',
                        showlegend=False
                    ))
                    # 최저 / 최고 포인트
                    fig3.add_trace(go.Scatter(
                        x=[min_v, max_v],
                        y=[name, name],
                        mode='markers',
                        marker=dict(size=10, color="#64748B", symbol='line-ns-open', line=dict(width=3, color='#94A3B8')),
                        name='최저/최고 범위' if i == 0 else None,
                        showlegend=(i == 0),
                        hovertemplate=f'<b>{name}</b><br>최저: {min_v:.2f}배<br>최고: {max_v:.2f}배<extra></extra>'
                    ))
                    # 평균 포인트
                    fig3.add_trace(go.Scatter(
                        x=[avg_v],
                        y=[name],
                        mode='markers',
                        marker=dict(size=12, color="#FBBF24", symbol='diamond'),
                        name='기간 평균' if i == 0 else None,
                        showlegend=(i == 0),
                        hovertemplate=f'<b>{name} 평균 PER</b>: {avg_v:.2f}배<extra></extra>'
                    ))
                    # 현재 포인트
                    fig3.add_trace(go.Scatter(
                        x=[cur_v],
                        y=[name],
                        mode='markers',
                        marker=dict(size=14, color=c, line=dict(width=2, color="#FFFFFF")),
                        name='현재 PER (Trailing TTM)' if i == 0 else None,
                        showlegend=(i == 0),
                        hovertemplate=f'<b>{name} 현재 PER</b>: {cur_v:.2f}배<extra></extra>'
                    ))
                    # 선행 Fwd(12MF) 포인트
                    fwd_v = row.get("Fwd(12MF) PER")
                    if pd.notnull(fwd_v) and fwd_v is not None:
                        fig3.add_trace(go.Scatter(
                            x=[fwd_v],
                            y=[name],
                            mode='markers',
                            marker=dict(size=14, color="#34D399", symbol='star', line=dict(width=1.5, color="#FFFFFF")),
                            name='Fwd(12MF) PER' if i == 0 else None,
                            showlegend=(i == 0),
                            hovertemplate=f'<b>{name} Fwd(12MF) PER</b>: {fwd_v:.2f}배<extra></extra>'
                        ))

                fig3.update_layout(
                    title=dict(
                        text=f"<b>종목별 PER 밸류에이션 밴드 및 현재 위치 비교 ({selected_period})</b>",
                        font=dict(size=16, color="#F8FAFC"),
                        x=0.0
                    ),
                    xaxis=dict(
                        title=dict(text="PER (배)", font=dict(color="#CBD5E1")),
                        gridcolor="#2A3342",
                        linecolor="#3E4C5E",
                        ticksuffix="배",
                        tickfont=dict(color="#CBD5E1")
                    ),
                    yaxis=dict(
                        title="",
                        tickfont=dict(color="#F8FAFC", size=13),
                        autorange="reversed"
                    ),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1,
                        font=dict(size=12, color="#E2E8F0"),
                        bgcolor="rgba(30, 36, 48, 0.9)",
                        bordercolor="#3E4C5E"
                    ),
                    plot_bgcolor="#161B24",
                    paper_bgcolor="#1E2430",
                    margin=dict(l=100, r=40, t=75, b=40),
                    height=450
                )
                st.plotly_chart(fig3, use_container_width=True, theme=None)

            # ----------------------------------------------------
            # 3. 데이터 영역 (통계 요약표 & 일별 수치 데이터 & 엑셀 다운로드)
            # ----------------------------------------------------
            st.markdown("<hr style='border: 0; height: 1px; background-color: #334155; margin-top: 30px; margin-bottom: 20px;'>", unsafe_allow_html=True)
            
            head_col1, head_col2 = st.columns([3, 1])
            with head_col1:
                st.markdown("<h3 style='font-size: 1.15rem; font-weight: 700; color: #F8FAFC;'><span style='font-size: 1.15rem;'>📋</span> 데이터 테이블 및 통계 요약</h3>", unsafe_allow_html=True)
            with head_col2:
                # 엑셀 다운로드 버튼
                excel_data = per_loader.generate_excel_download(combined_df, summary_df)
                today_tag = datetime.date.today().strftime('%Y%m%d')
                st.download_button(
                    label="📥 엑셀 다운로드 (.xlsx)",
                    data=excel_data,
                    file_name=f"PER_비교데이터_{selected_period}_{today_tag}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            # 데이터 탭 구성: 요약 분석표 vs 일별 상세 데이터
            data_tab1, data_tab2 = st.tabs(["📊 기간별 PER 요약 통계", "📅 일별 PER 시계열 데이터"])

            with data_tab1:
                formatted_summary = summary_df.copy()
                
                # 컬럼 순서 조정: 현재 PER 바로 옆에 Fwd(12MF) PER 배치
                cols_order = [
                    "종목명", "현재 PER", "Fwd(12MF) PER", "시작 PER", 
                    "기간 평균 PER", "기간 최저 PER", "기간 최고 PER", 
                    "PER 변동률 (%)", "기간 위치 (%)", "밸류에이션 구간"
                ]
                cols_order = [c for c in cols_order if c in formatted_summary.columns]
                formatted_summary = formatted_summary[cols_order]

                formatted_summary["현재 PER"] = formatted_summary["현재 PER"].apply(lambda x: f"{x:.2f}배")
                if "Fwd(12MF) PER" in formatted_summary.columns:
                    formatted_summary["Fwd(12MF) PER"] = formatted_summary["Fwd(12MF) PER"].apply(lambda x: f"{x:.2f}배" if pd.notnull(x) else "-")
                formatted_summary["시작 PER"] = formatted_summary["시작 PER"].apply(lambda x: f"{x:.2f}배")
                formatted_summary["기간 평균 PER"] = formatted_summary["기간 평균 PER"].apply(lambda x: f"{x:.2f}배")
                formatted_summary["기간 최저 PER"] = formatted_summary["기간 최저 PER"].apply(lambda x: f"{x:.2f}배")
                formatted_summary["기간 최고 PER"] = formatted_summary["기간 최고 PER"].apply(lambda x: f"{x:.2f}배")
                formatted_summary["PER 변동률 (%)"] = formatted_summary["PER 변동률 (%)"].apply(lambda x: f"{'+' if x>0 else ''}{x:.2f}%")
                formatted_summary["기간 위치 (%)"] = formatted_summary["기간 위치 (%)"].apply(lambda x: f"{x:.1f}%")

                st.dataframe(
                    formatted_summary,
                    use_container_width=True,
                    hide_index=True
                )

            with data_tab2:
                display_df = combined_df.copy()
                display_df.index = display_df.index.strftime('%Y-%m-%d')
                display_df.index.name = "일자"
                # 최근 일자 순으로 정렬
                display_df = display_df.sort_index(ascending=False)
                
                st.dataframe(
                    display_df.style.format("{:.2f}배"),
                    use_container_width=True
                )

            # ----------------------------------------------------
            # 4. 전문가 밸류에이션 인사이트
            # ----------------------------------------------------
            st.markdown("<h3 style='font-size: 1.15rem; font-weight: 700; color: #F8FAFC; margin-top: 25px; margin-bottom: 12px;'>💡 전문가 밸류에이션 인사이트</h3>", unsafe_allow_html=True)
            
            # 최저 PER 및 최고 PER 종목
            highest_per_stock = summary_df.loc[summary_df["현재 PER"].idxmax()]
            lowest_per_stock = summary_df.loc[summary_df["현재 PER"].idxmin()]
            max_expansion_stock = summary_df.loc[summary_df["PER 변동률 (%)"].idxmax()]

            st.markdown(f"""
            <div style="background-color: #1E2430; border: 1px solid #2D3748; border-radius: 8px; padding: 16px 20px; font-size: 0.82rem; color: #E2E8F0; line-height: 1.8;">
                • <b>현재 최고 밸류에이션(Trailing TTM):</b> 비교 종목 중 현재 PER이 가장 높은 종목은 <b>{highest_per_stock['종목명']}</b> ({highest_per_stock['현재 PER']:.2f}배)입니다.<br/>
                • <b>현재 최저 밸류에이션(Trailing TTM):</b> 비교 종목 중 가장 낮은 PER 배수를 형성하고 있는 종목은 <b>{lowest_per_stock['종목명']}</b> ({lowest_per_stock['현재 PER']:.2f}배)입니다.<br/>
                • <b>12개월 선행 Fwd(12MF) PER:</b> 시장 컨센서스 기반의 향후 12개월 순이익을 반영한 Fwd PER을 제공하여, 향후 실적 개선 및 업황 턴어라운드에 따른 밸류에이션 완화 효과를 직관적으로 비교할 수 있습니다.<br/>
                • <b>최대 멀티플 확장(Expansion):</b> 선택 기간({selected_period}) 동안 PER 멀티플이 가장 많이 확장된 종목은 <b>{max_expansion_stock['종목명']}</b> ({max_expansion_stock['PER 변동률 (%)']:+.2f}%)입니다.<br/>
                • <b>데이터 산출 기준:</b> 한국 및 미국/해외 전 종목 모두 최근 4개 분기 실적 합산(TTM: Trailing Twelve Months) 기준의 분기 롤링 PER로 일원화하여 산출되었습니다. 선행 지표의 경우 한국 종목은 FnGuide 12M Fwd 컨센서스, 미국 및 해외 종목은 Yahoo Finance 12M Fwd PER을 결합하여 왜곡 없는 글로벌 1:1 비교가 가능합니다.
            </div>
            """, unsafe_allow_html=True)
