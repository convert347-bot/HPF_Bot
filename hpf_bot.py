import ccxt
import pandas as pd
import time
import requests
from datetime import datetime

# ========== ÒÂÎÈ ÍÀÑÒÐÎÉÊÈ (ÍÅ ÒÐÎÃÀÒÜ) ==========
BOT_TOKEN = "8514251161:AFAHwx9cETJBoHeAX-v_PBpPEXWJCRrC6s"
CHAT_ID = "5916071793"
TIMEFRAME = "30m"
DROP_PERCENT = 1.5
MIN_BARS = 6
# ================================================

def send_tg(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": text}
        requests.post(url, data=data)
    except:
        pass

def get_all_pairs():
    print("?? Ïîëó÷àþ ñïèñîê ìîíåò...")
    try:
        ex = ccxt.bingx({'options': {'defaultType': 'future'}})
        markets = ex.load_markets()
        pairs = [s for s in markets if s.endswith('/USDT') and 'future' in str(markets[s])]
        pairs = sorted([p.split(':')[0] for p in pairs])
        print(f"? Çàãðóæåíî {len(pairs)} ìîíåò")
        return pairs
    except Exception as e:
        print(f"? Îøèáêà: {e}")
        return []

def check_c_point(symbol):
    try:
        ex = ccxt.bingx({'options': {'defaultType': 'future'}})
        bars = ex.fetch_ohlcv(symbol, TIMEFRAME, limit=100)
        if len(bars) < 50:
            return None
        
        df = pd.DataFrame(bars, columns=['t', 'o', 'h', 'l', 'c', 'v'])
        highs = df['h'].values
        lows = df['l'].values
        
        # Èùåì âåðøèíó B (ëîêàëüíûé ïèê)
        idx_b = None
        for i in range(3, len(highs)-3):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                idx_b = i
                break
        if idx_b is None:
            return None
        
        price_b = highs[idx_b]
        
        # Èùåì âïàäèíó C ïîñëå B
        idx_c = None
        for i in range(idx_b+1, len(lows)-3):
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                idx_c = i
                break
        if idx_c is None:
            return None
        
        price_c = lows[idx_c]
        bars_bc = idx_c - idx_b
        if bars_bc < MIN_BARS:
            return None
        
        drop = (price_b - price_c) / price_b * 100
        if drop < DROP_PERCENT:
            return None
        
        return {
            'symbol': symbol,
            'b': round(price_b, 8),
            'c': round(price_c, 8),
            'drop': round(drop, 1),
            'bars': bars_bc
        }
    except:
        return None

def main():
    print("="*50)
    print("Áîò HPF (Òî÷êà C) ÇÀÏÓÙÅÍ")
    send_tg("? Áîò çàïóùåí. Èùó òî÷êè C...")
    
    all_pairs = get_all_pairs()
    if not all_pairs:
        print("Íåò ìîíåò. Ïðîâåðü èíòåðíåò.")
        return
    
    sent = set()
    while True:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Ñêàíèðóþ {len(all_pairs)} ìîíåò...")
        for i, p in enumerate(all_pairs):
            print(f"[{i+1}/{len(all_pairs)}] {p}...", end=" ", flush=True)
            res = check_c_point(p)
            if res:
                key = f"{res['symbol']}_{res['b']}"
                if key not in sent:
                    sent.add(key)
                    msg = (f"?? ÒÎ×ÊÀ C ÑÔÎÐÌÈÐÎÂÀÍÀ!\n\n"
                           f"Ìîíåòà: {res['symbol']}\n"
                           f"?? Ïèê B: {res['b']}\n"
                           f"?? Òî÷êà C: {res['c']}\n"
                           f"?? Ïàäåíèå: {res['drop']}%\n"
                           f"?? Áàðîâ B->C: {res['bars']}\n\n"
                           f"?? Ñìîòðè ãðàôèê! Âõîä îò C, ñòîï çà A")
                    send_tg(msg)
                    print("? ÑÈÃÍÀË!")
            else:
                print("? íåò")
            time.sleep(0.3)
        print("? Ñïëþ 15 ìèíóò...")
        time.sleep(900)

if name == "main":
    try:
        main()
    except KeyboardInterrupt:
        print("\nÁîò âûêëþ÷åí.")
        send_tg("?? Áîò îñòàíîâëåí.")
