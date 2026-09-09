"""
per_loader.py
한국 및 미국 주식 종목의 PER(Price-to-Earnings Ratio) 시계열 데이터를 수집하고 정제하는 모듈.
- 한국 및 미국/해외 주식 전 종목: 일별 종가 및 직전 4개 분기 EPS 기반 분기 롤링 TTM(Trailing Twelve Months) PER 통일 산출
- 12M 선행 PER(Fwd.12M PER): FnGuide 스냅샷 및 yfinance forwardPE 활용
"""

import os
import io
import datetime
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# 1. 환경변수 및 KRX 인증 설정
load_dotenv()

# .env에 없으면 상위 00 API Key 디렉토리 또는 Streamlit Secrets 확인
if not os.getenv('KRX_ID') or not os.getenv('KRX_PW'):
    api_key_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "00 API Key", "KRX ID&PW.txt")
    if os.path.exists(api_key_path):
        try:
            with open(api_key_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if line.startswith("ID :") or line.startswith("ID:"):
                        os.environ['KRX_ID'] = line.split(":", 1)[1].strip()
                    elif line.startswith("PW :") or line.startswith("PW:"):
                        os.environ['KRX_PW'] = line.split(":", 1)[1].strip()
        except Exception:
            pass

    # Streamlit Cloud 배포 시 Secrets 연동
    try:
        import streamlit as st
        if hasattr(st, 'secrets'):
            if 'KRX_ID' in st.secrets and not os.getenv('KRX_ID'):
                os.environ['KRX_ID'] = str(st.secrets['KRX_ID'])
            if 'KRX_PW' in st.secrets and not os.getenv('KRX_PW'):
                os.environ['KRX_PW'] = str(st.secrets['KRX_PW'])
    except Exception:
        pass

# pykrx 안전 로딩 (setuptools/pkg_resources 부재 시에도 앱 크래시 방지)
try:
    from pykrx import stock
    HAS_PYKRX = True
except Exception as e:
    stock = None
    HAS_PYKRX = False
    print(f"pykrx 로딩 건너뜀 (yfinance 폴백 가동): {e}")

import yfinance as yf

# 주요 미국 및 글로벌 주식 프리셋 (한글명 + 티커)
MAJOR_US_STOCKS = [
    "마이크론 (MU)",
    "샌디스크 (SNDK)",
    "TSMC (TSM)",
    "엔비디아 (NVDA)",
    "애플 (AAPL)",
    "마이크로소프트 (MSFT)",
    "테슬라 (TSLA)",
    "아마존 (AMZN)",
    "알파벳A (GOOGL)",
    "메타 (META)",
    "브로드컴 (AVGO)",
    "ASML (ASML)",
    "AMD (AMD)",
    "퀄컴 (QCOM)",
    "인텔 (INTC)",
    "웨스턴디지털 (WDC)",
    "버크셔해서웨이 (BRK-B)",
    "일라이릴리 (LLY)",
    "JP모건 (JPM)",
    "월마트 (WMT)",
    "비자 (V)",
    "엑슨모빌 (XOM)",
    "넷플릭스 (NFLX)",
    "코스트코 (COST)",
    "팔란티어 (PLTR)",
    "아이온큐 (IONQ)"
]


def load_krx_data(cache_file="krx_cache.csv"):
    """
    KRX 상장종목 목록을 로드하여 반환합니다.
    로컬 캐시 파일이 있으면 우선 사용하고, 없으면 FDR로 로드 후 캐시합니다.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_cache_path = os.path.join(current_dir, cache_file)

    if os.path.exists(full_cache_path):
        try:
            df = pd.read_csv(full_cache_path, dtype={'Code': str}, encoding='utf-8-sig')
            if not df.empty and 'Code' in df.columns and 'Name' in df.columns:
                return df
        except Exception:
            try:
                df = pd.read_csv(full_cache_path, dtype={'Code': str}, encoding='cp949')
                if not df.empty and 'Code' in df.columns and 'Name' in df.columns:
                    return df
            except Exception:
                pass

    # FDR이 환경에 설치되어 있는 경우에 한해 온라인 수집 시도
    try:
        import FinanceDataReader as fdr
        df = fdr.StockListing('KRX')
        df_cleaned = df[['Code', 'Name', 'Market']].copy()
        df_cleaned.to_csv(full_cache_path, index=False, encoding='utf-8-sig')
        return df_cleaned
    except Exception:
        pass

    # 최소 폴백 데이터
    fallback_data = [
        {"Code": "005930", "Name": "삼성전자", "Market": "KOSPI"},
        {"Code": "000660", "Name": "SK하이닉스", "Market": "KOSPI"},
        {"Code": "005935", "Name": "삼성전자우", "Market": "KOSPI"},
        {"Code": "035420", "Name": "NAVER", "Market": "KOSPI"},
        {"Code": "035720", "Name": "카카오", "Market": "KOSPI"},
        {"Code": "005380", "Name": "현대차", "Market": "KOSPI"},
        {"Code": "000270", "Name": "기아", "Market": "KOSPI"},
        {"Code": "207940", "Name": "삼성바이오로직스", "Market": "KOSPI"},
        {"Code": "068270", "Name": "셀트리온", "Market": "KOSPI"},
        {"Code": "051910", "Name": "LG화학", "Market": "KOSPI"},
        {"Code": "373220", "Name": "LG에너지솔루션", "Market": "KOSPI"},
        {"Code": "006400", "Name": "삼성SDI", "Market": "KOSPI"},
    ]
    return pd.DataFrame(fallback_data)


def build_stock_options(krx_df):
    """
    사이드바 종목 선택 옵션 리스트를 생성합니다.
    """
    krx_options = []
    if not krx_df.empty:
        krx_options = (krx_df['Name'] + " (" + krx_df['Code'] + ")").tolist()
    
    options = ["선택 안 함"] + krx_options + MAJOR_US_STOCKS + ["[직접 입력]"]
    return options


def resolve_stock_selection(selected_display, custom_input, krx_df):
    """
    사용자가 선택하거나 입력한 종목을 분석하여 (symbol, display_name, market_type) 튜플을 반환합니다.
    - market_type: 'KR' (한국 주식 6자리 코드), 'US' (미국/글로벌 티커)
    """
    target = ""
    if selected_display == "[직접 입력]":
        if custom_input and custom_input.strip():
            target = custom_input.strip()
    elif selected_display and selected_display != "선택 안 함":
        target = selected_display.strip()

    if not target:
        return None, None, None

    # 1. 괄호 형식 파싱 (예: "삼성전자 (005930)" 또는 "마이크론 (MU)")
    if "(" in target and target.endswith(")"):
        code_part = target.split("(", 1)[1].rstrip(")").strip()
        name_part = target.split("(", 1)[0].strip()

        # 한국 6자리 코드 판별
        if code_part.isdigit() and len(code_part) == 6:
            return code_part, name_part, "KR"
        else:
            return code_part.upper(), name_part, "US"

    # 2. 한국 주식 한글명 검색
    if not krx_df.empty:
        match = krx_df[krx_df['Name'].str.lower() == target.lower()]
        if not match.empty:
            code = match.iloc[0]['Code']
            name = match.iloc[0]['Name']
            return code, name, "KR"

    # 3. 6자리 숫자 코드
    clean_code = target.upper()
    if clean_code.endswith('.KS') or clean_code.endswith('.KQ'):
        clean_code = clean_code[:-3]
    if clean_code.isdigit() and len(clean_code) == 6:
        name = f"한국주식({clean_code})"
        if not krx_df.empty:
            match = krx_df[krx_df['Code'] == clean_code]
            if not match.empty:
                name = match.iloc[0]['Name']
        return clean_code, name, "KR"

    # 4. 해외 티커
    symbol = target.upper()
    # 영문 티커의 경우 yfinance로 기업명 간단 조회 시도
    display_name = symbol
    try:
        tk_info = yf.Ticker(symbol).info
        short_name = tk_info.get('shortName') or tk_info.get('longName')
        if short_name:
            display_name = f"{short_name} ({symbol})"
    except Exception:
        display_name = symbol

    return symbol, display_name, "US"


def fetch_ttm_per_series(symbol, start_date, end_date):
    """
    일별 종가와 직전 4개 분기 Reported EPS(또는 Diluted EPS)를 결합하여
    일별 롤링 TTM(Trailing Twelve Months) PER 시계열을 정밀 산출합니다.
    (한국 및 미국/해외 주식 공통 적용)
    """
    # 여유 기간을 두어 주가 및 분기 공시 데이터 로드
    buf_start = (pd.to_datetime(start_date) - pd.Timedelta(days=90)).strftime('%Y-%m-%d')
    buf_end = (pd.to_datetime(end_date) + pd.Timedelta(days=3)).strftime('%Y-%m-%d')

    tk = yf.Ticker(symbol)
    try:
        hist = tk.history(start=buf_start, end=buf_end)
    except Exception:
        return pd.Series(dtype=float)

    if hist.empty:
        return pd.Series(dtype=float)

    hist.index = hist.index.tz_localize(None).normalize()
    prices = hist['Close'].dropna()
    if prices.empty:
        return pd.Series(dtype=float)

    # 1. 분기별 Reported EPS 공시 데이터 우선 확인 (earnings_dates)
    ed = None
    try:
        ed = tk.earnings_dates
    except Exception:
        pass

    if ed is not None and not ed.empty and 'Reported EPS' in ed.columns:
        eps_series = ed['Reported EPS'].dropna().sort_index()
        if len(eps_series) >= 4:
            eps_series.index = eps_series.index.tz_localize(None).normalize()
            eps_series = eps_series[~eps_series.index.duplicated(keep='last')]
            ttm_eps_dates = eps_series.rolling(window=4).sum().dropna()

            if not ttm_eps_dates.empty:
                combined_index = prices.index.union(ttm_eps_dates.index).sort_values()
                ttm_eps_daily = ttm_eps_dates.reindex(combined_index).ffill()
                align_df = pd.DataFrame({'price': prices, 'ttm_eps': ttm_eps_daily.reindex(prices.index)}).dropna()
                align_df = align_df[align_df['ttm_eps'] > 0.01]
                if not align_df.empty:
                    per_series = align_df['price'] / align_df['ttm_eps']
                    per_series = per_series.loc[pd.to_datetime(start_date):pd.to_datetime(end_date)]
                    per_series = per_series[(per_series > 0) & (per_series < 2000)]
                    if not per_series.empty:
                        return per_series

    # 2. quarterly_income_stmt 의 Diluted EPS 또는 Basic EPS 시도
    try:
        stmt = tk.quarterly_income_stmt
        eps_row = None
        if stmt is not None and not stmt.empty:
            if 'Diluted EPS' in stmt.index:
                eps_row = stmt.loc['Diluted EPS']
            elif 'Basic EPS' in stmt.index:
                eps_row = stmt.loc['Basic EPS']

        if eps_row is not None:
            eps_q = eps_row.dropna().sort_index()
            if len(eps_q) >= 4:
                eps_q.index = pd.to_datetime(eps_q.index).normalize()
                eps_q = eps_q[~eps_q.index.duplicated(keep='last')]
                ttm_eps_q = eps_q.rolling(window=4).sum().dropna()
                if not ttm_eps_q.empty:
                    combined_index = prices.index.union(ttm_eps_q.index).sort_values()
                    ttm_eps_daily = ttm_eps_q.reindex(combined_index).ffill()
                    align_df = pd.DataFrame({'price': prices, 'ttm_eps': ttm_eps_daily.reindex(prices.index)}).dropna()
                    align_df = align_df[align_df['ttm_eps'] > 0.01]
                    if not align_df.empty:
                        per_series = align_df['price'] / align_df['ttm_eps']
                        per_series = per_series.loc[pd.to_datetime(start_date):pd.to_datetime(end_date)]
                        per_series = per_series[(per_series > 0) & (per_series < 2000)]
                        if not per_series.empty:
                            return per_series
    except Exception:
        pass

    # 3. 최후의 수단: info의 trailingPE 상수비율 적용
    try:
        trailing_pe = tk.info.get('trailingPE')
        if trailing_pe and trailing_pe > 0:
            latest_price = prices.iloc[-1]
            approx_eps = latest_price / trailing_pe
            per_series = prices / approx_eps
            per_series = per_series.loc[pd.to_datetime(start_date):pd.to_datetime(end_date)]
            return per_series
    except Exception:
        pass

    return pd.Series(dtype=float)


def fetch_korean_per_series(code, start_date, end_date):
    """
    한국 주식의 일별 분기 롤링 TTM PER 시계열을 산출합니다.
    (미국 주식과 100% 동일한 직전 4개 분기 EPS 합산 TTM 기준)
    """
    clean_code = str(code).strip().upper()
    if clean_code.endswith('.KS') or clean_code.endswith('.KQ'):
        candidate_symbols = [clean_code]
    else:
        # KOSPI / KOSDAQ 구분 판별
        krx_df = load_krx_data()
        is_kosdaq = False
        if not krx_df.empty:
            match = krx_df[krx_df['Code'] == clean_code]
            if not match.empty:
                mkt = str(match.iloc[0].get('Market', '')).upper()
                if 'KOSDAQ' in mkt:
                    is_kosdaq = True

        if is_kosdaq:
            candidate_symbols = [f"{clean_code}.KQ", f"{clean_code}.KS"]
        else:
            candidate_symbols = [f"{clean_code}.KS", f"{clean_code}.KQ"]

    for sym in candidate_symbols:
        s = fetch_ttm_per_series(sym, start_date, end_date)
        if s is not None and not s.empty:
            return s

    # 극히 드문 예외(신규상장 등 분기 공시 데이터가 전혀 없는 경우): pykrx 비상 폴백
    if HAS_PYKRX and stock is not None:
        try:
            start_str = pd.to_datetime(start_date).strftime('%Y%m%d')
            end_str = pd.to_datetime(end_date).strftime('%Y%m%d')
            df = stock.get_market_fundamental_by_date(start_str, end_str, clean_code)
            if df is not None and not df.empty and 'PER' in df.columns:
                per_series = df['PER'].copy()
                per_series = per_series[per_series > 0]
                if not per_series.empty:
                    per_series.index = pd.to_datetime(per_series.index).normalize()
                    return per_series
        except Exception:
            pass

    return pd.Series(dtype=float)


def fetch_us_per_series(symbol, start_date, end_date):
    """
    미국 및 해외 주식의 일별 분기 롤링 TTM PER 시계열을 산출합니다.
    """
    return fetch_ttm_per_series(symbol, start_date, end_date)


def fetch_forward_per(symbol, market_type):
    """
    해당 종목의 12개월 선행 PER(Fwd.12M PER / 12MF PER) 수치를 수집합니다.
    - 한국 종목: FnGuide 기업스냅샷 12M Fwd PER 우선 조회 -> 실패 시 yfinance forwardPE 폴백
    - 미국/해외 종목: yfinance forwardPE 조회
    """
    if market_type == 'KR':
        # 1. FnGuide 스냅샷 조회 시도
        try:
            import requests
            from bs4 import BeautifulSoup
            url = f"https://wcomp.fnguide.com/CompanyInfo/Snapshot?cmp_cd={symbol}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            r = requests.get(url, headers=headers, timeout=4)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                btn = soup.find(id='h_12m')
                if btn:
                    ul = btn.find_parent('ul')
                    if ul:
                        lis = ul.find_all('li')
                        if len(lis) >= 2:
                            val = lis[1].get_text(strip=True).replace(',', '')
                            if val and val not in ['-', 'N/A']:
                                return round(float(val), 2)
        except Exception:
            pass

        # 2. yfinance 폴백 시도
        try:
            clean_sym = str(symbol).strip().upper()
            if clean_sym.endswith('.KS') or clean_sym.endswith('.KQ'):
                cand_tickers = [clean_sym]
            else:
                krx_df = load_krx_data()
                is_kosdaq = False
                if not krx_df.empty:
                    match = krx_df[krx_df['Code'] == clean_sym]
                    if not match.empty and 'KOSDAQ' in str(match.iloc[0].get('Market', '')).upper():
                        is_kosdaq = True
                cand_tickers = [f"{clean_sym}.KQ", f"{clean_sym}.KS"] if is_kosdaq else [f"{clean_sym}.KS", f"{clean_sym}.KQ"]

            for cand in cand_tickers:
                tk = yf.Ticker(cand)
                fpe = tk.info.get('forwardPE')
                if fpe and fpe > 0:
                    return round(float(fpe), 2)
        except Exception:
            pass
    else:
        # 미국 및 해외 종목: yfinance forwardPE
        try:
            tk = yf.Ticker(symbol)
            fpe = tk.info.get('forwardPE')
            if fpe and fpe > 0:
                return round(float(fpe), 2)
        except Exception:
            pass

    return None


def get_period_dates(period_str):
    """
    기간 문자열('1M', '3M', '6M', '1Y', '3Y')에 대응하는 (start_date, end_date)를 반환합니다.
    """
    end_date = datetime.date.today()
    days_map = {
        '1M': 30,
        '3M': 90,
        '6M': 180,
        '1Y': 365,
        '3Y': 365 * 3
    }
    days = days_map.get(period_str, 30)
    start_date = end_date - datetime.timedelta(days=days)
    return start_date, end_date


def load_all_per_data(selected_targets, period_str):
    """
    선택된 종목 리스트에 대해 PER 시계열 데이터를 수집하고 정렬된 데이터프레임과 통계 요약을 생성합니다.
    - selected_targets: [(symbol, display_name, market_type), ...]
    - period_str: '1M', '3M', '6M', '1Y', '3Y'
    """
    start_date, end_date = get_period_dates(period_str)
    series_dict = {}
    fwd_per_dict = {}
    errors = {}

    for symbol, display_name, market_type in selected_targets:
        # 1. 일별 PER 시계열 수집
        try:
            if market_type == 'KR':
                s = fetch_korean_per_series(symbol, start_date, end_date)
            else:
                s = fetch_us_per_series(symbol, start_date, end_date)

            if s is not None and not s.empty:
                # 소수점 둘째자리 반올림
                s = s.round(2)
                series_dict[display_name] = s
            else:
                errors[display_name] = f"'{display_name}'의 유효한 PER 데이터를 수집하지 못했습니다."
        except Exception as e:
            errors[display_name] = f"'{display_name}' 데이터 수집 중 오류: {e}"

        # 2. 선행 Fwd(12MF) PER 수집
        try:
            fwd_val = fetch_forward_per(symbol, market_type)
            fwd_per_dict[display_name] = fwd_val
        except Exception:
            fwd_per_dict[display_name] = None

    if not series_dict:
        return pd.DataFrame(), pd.DataFrame(), errors

    # 날짜 인덱스 통합 데이터프레임
    combined_df = pd.DataFrame(series_dict)
    combined_df.index = pd.to_datetime(combined_df.index)
    combined_df.sort_index(inplace=True)

    # 서로 다른 휴장일 간 ffill 적용 후 bfill
    combined_df = combined_df.ffill().bfill()

    # 통계 요약표 계산
    summary_rows = []
    for col in combined_df.columns:
        s = combined_df[col].dropna()
        if s.empty:
            continue
        cur_val = s.iloc[-1]
        start_val = s.iloc[0]
        min_val = s.min()
        max_val = s.max()
        avg_val = s.mean()
        change_pct = ((cur_val - start_val) / start_val) * 100 if start_val != 0 else 0.0

        # 백분위 위치 (0 ~ 100%): 0에 가까우면 최저 수준, 100에 가까우면 최고 수준
        if max_val > min_val:
            percentile = ((cur_val - min_val) / (max_val - min_val)) * 100
        else:
            percentile = 50.0

        # 밸류에이션 상태 판정
        if percentile <= 25:
            val_status = "저평가 구간 (하위 25%)"
        elif percentile <= 75:
            val_status = "적정/평균 구간"
        else:
            val_status = "고평가 구간 (상위 25%)"

        fwd_pe = fwd_per_dict.get(col)

        summary_rows.append({
            "종목명": col,
            "현재 PER": round(cur_val, 2),
            "Fwd(12MF) PER": round(fwd_pe, 2) if fwd_pe is not None else np.nan,
            "시작 PER": round(start_val, 2),
            "기간 평균 PER": round(avg_val, 2),
            "기간 최저 PER": round(min_val, 2),
            "기간 최고 PER": round(max_val, 2),
            "PER 변동률 (%)": round(change_pct, 2),
            "기간 위치 (%)": round(percentile, 1),
            "밸류에이션 구간": val_status
        })

    summary_df = pd.DataFrame(summary_rows)
    return combined_df, summary_df, errors


def generate_excel_download(combined_df, summary_df):
    """
    일별 PER 데이터 및 요약 통계를 엑셀 파일 바이너리로 변환합니다.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet 1: 통계 요약표
        if not summary_df.empty:
            summary_df.to_excel(writer, sheet_name='PER_통계_요약', index=False)
        
        # Sheet 2: 일별 PER 시계열
        if not combined_df.empty:
            export_df = combined_df.copy()
            export_df.index = export_df.index.strftime('%Y-%m-%d')
            export_df.index.name = '날짜'
            export_df.reset_index(inplace=True)
            export_df.to_excel(writer, sheet_name='일별_PER_데이터', index=False)

    return output.getvalue()
