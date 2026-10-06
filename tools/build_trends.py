#!/usr/bin/env python3
"""Build docs/trends.html —— N1 出典索引・傾向分析・2026-12 模擬予想（免密页）。

数据源:
  - analysis/source-traces.json（extract_sources.py 生成：読解原文出典＋填空/用法 metadata）
  - n1/past-exams/（统计用扫描；只写聚合数字与出典元数据，不复制真题正文）

输出: docs/trends.html（自包含单文件；真题正文仍在加密 data.json 内）
"""
import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRACES = ROOT / "analysis" / "source-traces.json"
BANK = ROOT / "n1" / "past-exams"
OUT = ROOT / "docs" / "trends.html"
APP = "https://syu-toutousai.github.io/jlpt-question-bank/"

CAT = {
    "vocab-reading": "問題1 読み方", "vocab-context": "問題2 文脈規定",
    "vocab-paraphrase": "問題3 言い換え", "vocab-usage": "問題4 用法",
    "grammar-choice": "問題5 文法形式", "grammar-composition": "問題6 並べ替え",
    "grammar-passage": "問題7 文章の文法",
    "reading-short": "問題8 短文", "reading-mid": "問題9 中文",
    "reading-long": "問題10 長文", "reading-integrated": "問題11 統合",
    "reading-claim": "問題12 主張", "reading-search": "問題13 情報検索",
}


def esc(s):
    return html.escape(str(s or ""))


def qchip(qid):
    return f'<a class="qc" href="{APP}#q={esc(qid)}" target="_blank" rel="noopener">{esc(qid)}</a>'


def scan():
    rows = []
    for f in sorted(BANK.rglob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(d, dict) or not d.get("id"):
            continue
        rows.append(d)
    return rows


def main():
    traces = json.loads(TRACES.read_text(encoding="utf-8"))
    rows = scan()

    by_year = defaultdict(Counter)
    for d in rows:
        by_year[d.get("year")][d.get("section")] += 1
    years = sorted(by_year)
    sections = ["vocab", "grammar", "reading", "listening"]
    sec_label = {"vocab": "語彙", "grammar": "文法", "reading": "読解", "listening": "聴解"}

    top_authors = Counter()
    for p in traces["passages"]:
        m = re.match(r"(.+?)『", p["source"])
        if m:
            top_authors[m.group(1).strip()] += len(p["ids"])

    meta = traces["meta"]

    # ---- 出典索引 rows (year desc)
    src_rows = []
    for p in traces["passages"]:
        badge = ""
        if p.get("corrected"):
            badge += f" <span class='corr' title='{esc(p.get('evidence',''))}'>補正</span>"
        if p.get("suspicious"):
            badge += f" <span class='susp' title='{esc(p.get('suspicious_note',''))}'>要確認</span>"
        src_rows.append(
            "<tr>"
            f"<td>{p['year']}-{p['month']:02d}</td>"
            f"<td class='src'>{esc(p['source'])}{badge}</td>"
            f"<td>{len(p['ids'])}</td>"
            f"<td>{''.join(qchip(i) for i in p['ids'])}</td>"
            "</tr>")
    unknown_rows = []
    for p in traces["unknown_passages"]:
        unknown_rows.append(
            "<tr>"
            f"<td>{p['year']}-{p['month']:02d}</td>"
            f"<td>{esc(p['guess_base'])}</td>"
            f"<td>{''.join(qchip(i) for i in p['ids'])}</td>"
            "</tr>")

    # ---- charts
    def bars(counter, color="#4f6ef7", unit="問"):
        if not counter:
            return ""
        mx = max(counter.values())
        out = []
        for k in sorted(counter, reverse=True):
            w = max(3, round(counter[k] / mx * 220))
            out.append(f"<div class='barrow'><span class='bl'>{esc(k)}</span>"
                       f"<span class='bar' style='width:{w}px;background:{color}'></span>"
                       f"<span class='bv'>{counter[k]}{unit}</span></div>")
        return "".join(out)

    author_bars = bars(Counter(dict(top_authors.most_common(12))))
    year_bars = "".join(
        f"<div class='barrow'><span class='bl'>{y}</span><span class='bar' style='width:{round(by_year[y]['reading']/max(by_year[yy]['reading'] for yy in years)*220)}px;background:#0f766e'></span>"
        f"<span class='bv'>{by_year[y]['reading']}問</span></div>"
        for y in years)
    usage_total = meta["usage_total"]
    usage_repeat_rows = "".join(
        f"<tr><td class='w'>{esc(w)}</td><td>{c} 回</td></tr>"
        for w, c in sorted(traces["usage_repeats"].items()))

    type_rows = []
    for f_type, label in CAT.items():
        if "-" in f_type:
            sec, typ = f_type.split("-", 1)
        else:
            sec, typ = "", f_type
        c = sum(1 for d in rows if d.get("section") == sec and d.get("type") == typ)
        if c:
            type_rows.append(f"<tr><td>{label}</td><td>{c}</td></tr>")

    css = """
:root{--bg:#f5f7fb;--card:#fff;--ink:#1c2333;--sub:#5b6478;--line:#e4e7f0;--acc:#0f766e;--acc2:#e6fffa;--gold:#b8860b}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"PingFang SC","Hiragino Sans GB","Noto Sans CJK SC","Microsoft YaHei",sans-serif;
background:var(--bg);color:var(--ink);line-height:1.8;padding-bottom:60px}
header{background:linear-gradient(135deg,#134e4a,#0f766e);color:#fff;padding:34px 20px 28px}
header h1{font-size:25px}
header p{opacity:.93;font-size:14px;margin-top:6px}
header .tags span{display:inline-block;background:rgba(255,255,255,.22);border-radius:99px;padding:2px 10px;font-size:12px;margin:10px 6px 0 0}
.wrap{max-width:980px;margin:0 auto;padding:0 16px}
main{margin-top:-14px}
.card{background:var(--card);border-radius:16px;padding:20px;margin:14px 0;box-shadow:0 2px 10px rgba(30,40,90,.06)}
h2{font-size:18px;margin-bottom:10px}
p{font-size:14px}
.lead{font-size:14px;color:var(--sub)}
table{width:100%;border-collapse:collapse;font-size:13px;margin-top:8px}
th,td{border:1px solid var(--line);padding:7px 9px;text-align:left;vertical-align:top}
th{background:#f7f8fc;font-weight:700}
td.src{font-family:"Hiragino Mincho ProN","Yu Mincho",serif}
td.w{font-weight:700}
.qc{display:inline-block;background:#f1f3f8;border-radius:6px;padding:0 6px;margin:1px 3px 1px 0;font-size:11px;color:var(--sub);text-decoration:none}
.qc:hover{color:var(--acc);background:var(--acc2)}
.corr{display:inline-block;background:#fff3cd;color:#8a6d3b;border-radius:99px;padding:0 8px;font-size:10.5px;font-weight:700;margin-left:6px;cursor:help}
.susp{display:inline-block;background:#ffe3e3;color:#c92a2a;border-radius:99px;padding:0 8px;font-size:10.5px;font-weight:700;margin-left:6px;cursor:help}
.barrow{display:flex;align-items:center;gap:8px;margin:3px 0}
.bl{width:150px;font-size:12px;color:var(--sub);text-align:right;flex:none;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.bar{height:12px;border-radius:6px;min-width:3px}
.bv{font-size:11.5px;color:var(--sub)}
.warn{background:#fffaf0;border-left:5px solid var(--gold);border-radius:12px;padding:12px 14px;font-size:13.5px;margin-top:10px}
.mock{border-left:5px solid var(--acc);background:#fbfefd;border-radius:12px;padding:14px 16px;margin:12px 0;font-size:14px}
.mock .tag{display:inline-block;background:#fff3cd;color:#8a6d3b;border-radius:99px;padding:1px 10px;font-size:11.5px;font-weight:700;margin-right:8px}
.mock .q{font-family:"Hiragino Mincho ProN","Yu Mincho",serif;font-size:15px;margin:8px 0}
.mock ol{margin:6px 0 6px 22px;font-size:13.8px}
details{margin-top:8px;font-size:13.5px}
summary{cursor:pointer;color:var(--acc);font-weight:700}
footer{text-align:center;color:var(--sub);font-size:12.5px;margin-top:26px;line-height:1.9}
"""

    mock = """
<div class="card"><h2>🎯 2026-12-06 N1 模擬予想（第二版・全 13 問）</h2>
<p class="lead">方法论：从 2010–2025 全部 N1 真題（2746 題）统计题型的轮换与复现，再<b>自写</b>同型模拟题。
下列题目全部为本页自作的<b>模拟题</b>，<b>不是真題</b>，也不预测具体原题；用来校准「近期少考・格式稳定」的考点手感。
（第二版追加：問題7 文章の文法・短読解）</p>

<div class="mock"><span class="tag">模擬・問題1 読み方</span>
<div class="q">彼の説明は（煩雑）で、要点がつかめない。</div>
<ol><li>はんざつ</li><li>ぼんざつ</li><li>はんぞう</li><li>ばんざつ</li></ol>
<details><summary>解答・解説</summary>正解 1（はんざつ）。「煩雑」＝细碎繁杂。3 は「煩悩（ぼんのう）」との混同を誘うダミー。</details></div>

<div class="mock"><span class="tag">模擬・問題1 読み方</span>
<div class="q">長年の慣習を（踏襲）して、式典は滞りなく進んだ。</div>
<ol><li>ふしゅう</li><li>とうしゅう</li><li>とうしゅ</li><li>ふしゅ</li></ol>
<details><summary>解答・解説</summary>正解 2（とうしゅう）。「踏襲」＝沿袭。1 は「復習・風習」系の音の混同を誘う。</details></div>

<div class="mock"><span class="tag">模擬・問題2 文脈規定</span>
<div class="q">長年の功績が広く（　　）され、彼は今年の文化功労者に選ばれた。</div>
<ol><li>称賛</li><li>顕彰</li><li>擁護</li><li>感服</li></ol>
<details><summary>解答・解説</summary>正解 2（顕彰）。功績を広く世に示して褒める語。1 は口頭の褒め、3 はかばう、4 は感心する。</details></div>

<div class="mock"><span class="tag">模擬・問題2 文脈規定</span>
<div class="q">予算不足のため、計画は（　　）を余儀なくされた。</div>
<ol><li>縮小</li><li>削減</li><li>短縮</li><li>圧縮</li></ol>
<details><summary>解答・解説</summary>正解 1（縮小）。計画・規模の縮小が定型。2 は金額・人員、3 は時間、4 は体積・データ。</details></div>

<div class="mock"><span class="tag">模擬・問題4 用法</span>
<div class="q">次の言葉の使い方として最もよいものを選びなさい。　<b>おのずと</b></div>
<ol><li>努力を続けていれば、道はおのずと開けるものだ。</li>
<li>彼はおのずと私の名前を呼び、手を振った。</li>
<li>おのずと雨が降り出したので、試合は中止になった。</li>
<li>昨日はおのずと彼の家を訪ねてしまった。</li></ol>
<details><summary>解答・解説</summary>正解 1。おのずと＝自然に・ひとりでに（抽象的な成り行き）。人の意志的行為（2・4）や単なる気象（3）には使わない。</details></div>

<div class="mock"><span class="tag">模擬・問題5 文法形式</span>
<div class="q">今さら謝った（　　）、失った信頼はそう簡単には戻らない。</div>
<ol><li>ところで</li><li>ものなら</li><li>ばかりに</li><li>とあって</li></ol>
<details><summary>解答・解説</summary>正解 1（〜たところで＝即使…也，前項に無駄・無意味の含意）。3 は原因の後悔、4 は原因の説明。</details></div>

<div class="mock"><span class="tag">模擬・問題5 文法形式</span>
<div class="q">彼は一度決めたら、周囲が何と言おうと（　　）。</div>
<ol><li>聞く耳を持たない</li><li>聞き流してしまう</li><li>耳を貸さざるを得ない</li><li>聞かずにはいられない</li></ol>
<details><summary>解答・解説</summary>正解 1（聞く耳を持たない＝固执不听）。「何と言おうと」は譲歩の呼応で、後件は意志の固さが自然。</details></div>

<div class="mock"><span class="tag">模擬・問題6 並べ替え</span>
<div class="q">次の文の ★ に入る最もよいものを選びなさい。<br>
彼女は ★ 欠かさず続けている。</div>
<ol><li>どんなに</li><li>忙しくても</li><li>日本語の勉強を</li><li>毎朝</li></ol>
<details><summary>解答・解説</summary>並べ替え：どんなに → 忙しくても → 毎朝 → 日本語の勉強を（★＝毎朝）。「どんなに〜ても」の呼応を先に固定するのが定石。</details></div>

<div class="mock"><span class="tag">模擬・問題7 文章の文法</span>
<div class="q">次の文章を読み、［A］〜［C］に入る最もよいものを選びなさい。</div>
<p style="font-size:14px">私たちは眠っている間にも学んでいる。［A］、日中に覚えた事柄は睡眠中に整理され、
定着しやすくなる。眠る時間を削って詰め込むほど、かえって記憶の定着を［B］しまう。
だからといって、長く眠ればよいというものでもない。大切なのは、質のよい睡眠を［C］。</p>
<ol><li>［A］ 1.しかし　2.つまり　3.ところが　4.そこで</li>
<li>［B］ 1.妨げて　2.促して　3.支えて　4.補って</li>
<li>［C］ 1.とることだ　2.とるわけだ　3.とるはずだ　4.とるものか</li></ol>
<details><summary>解答・解説</summary>［A］2（つまり＝前文の言い換え・要約）。［B］1（定着を妨げる）。［C］1（〜ことだ＝忠告・結論）。</details></div>

<div class="mock"><span class="tag">模擬・読解（短文）</span>
<div class="q">次の文章を読んで、後の問いに答えなさい。</div>
<p style="font-size:14px">若い頃は、失敗しないことばかり考えていた。失敗すれば恥をかき、信用を失うと思っていたからだ。
しかし、長く仕事をしてきた今は、少し違う。失敗は、自分の思い込みを壊してくれる。
壊れた場所から、新しいやり方が見えてくる。だから今は、失敗を避けることよりも、
失敗から何を持ち帰るかを考えている。</p>
<ol><li>問1　筆者の考えに最も近いものはどれか。<br>
1.失敗しないように、慎重に行動すべきだ。<br>
2.失敗は、新しいやり方に気づくきっかけになる。<br>
3.失敗すると信用を失うので、避けるべきだ。<br>
4.若い頃の考え方は、今も変わっていない。</li>
<li>問2　「壊れた場所」とあるが、何が壊れるのか。<br>
1.自分の思い込み　2.会社の信用　3.新しいやり方　4.若い頃の記憶</li></ol>
<details><summary>解答・解説</summary>問1＝2（失敗→思い込みが壊れる→新しいやり方）。問2＝1（前文「自分の思い込みを壊してくれる」の照応）。</details></div>
</div>"""

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>JLPT N1 出典索引・傾向分析・2026-12 模擬予想</title>
<style>{css}</style></head>
<body>
<header><div class="wrap">
<h1>📊 JLPT N1 出典索引 ・ 傾向分析 ・ 2026-12 模擬予想</h1>
<p>読解原文の出典行を題面から全量抽出＋填空/用法題は作成文として分類；历年轮换统计 → 押题方法論</p>
<div class="tags"><span>N1 2010–2025</span><span>読解 出典 {meta['reading_with_source']}/{meta['reading_total']}</span>
<span>用法 125 語</span><span>模擬押題</span></div>
</div></header>
<main class="wrap">

<div class="card"><h2>📌 概要と方法</h2>
<p>本页是 <b>免密</b> 的元数据/分析页：真题正文仍只存在于加密题库（<a href="{APP}" target="_blank" rel="noopener">JLPT N1–N5 過去問データベース</a>）。</p>
<table>
<tr><th>层</th><th>数据</th><th>出处处理</th></tr>
<tr><td>読解（問題8–13）</td><td>{meta['reading_total']} 題</td><td>题面末尾「（〜による）」行を抽出：<b>明示 {meta['reading_with_source']} / 未詳 {meta['reading_unknown']}</b>（{len(traces['passages'])} 组明示出处）</td></tr>
<tr><td>填空（問題2・5・7）</td><td>—</td><td>出典行なし＝<b>作成文</b>（試験委員会の書き下ろし）。target 語のみ統計</td></tr>
<tr><td>用法（問題4）</td><td>{meta['usage_total']} 題</td><td>同上＝作成文。target（見出し語）で復現を追跡：<b>{len(traces['usage_repeats'])} 語が復現</b></td></tr>
</table>
<div class="warn">⚠️ 流儀：出典行は<b>題面の明示テキストの抽出</b>であり、転写誤記（著者名の欠落・OCR 崩れ）を含む場合がある。
「未詳」は<b>不存在ではなく未同定</b>。今後、逆引き検索（本文の特徴句で原典を探す）で順次補完する。</div>
</div>

<div class="card"><h2>📚 読解・原文出典索引（明示 {len(traces['passages'])} 组）</h2>
<table><tr><th>回</th><th>出典（題面明示）</th><th>問数</th><th>題（加密站深链）</th></tr>
{''.join(src_rows)}
</table>
<details><summary>未詳 {len(traces['unknown_passages'])} 组（クリックで展開）</summary>
<table><tr><th>回</th><th>推定単位</th><th>題</th></tr>{''.join(unknown_rows)}</table>
</details>
</div>

<div class="card"><h2>🕵️ 逆引き同定と転写清掃（実施結果）</h2>
<table>
<tr><th>作業</th><th>方法</th><th>結果</th></tr>
<tr><td>未詳 65 组の自動逆引き</td><td>特徴句 30 字を実 Chrome で Yahoo! 精确短语检索し、
結果と <b>≥12 字の連続重複</b>がある場合のみ書名『』を候補採用（<code>tools/trace_sources.py</code>）</td>
<td><b>同定 0 组</b>。N1 読解本文は広告・書籍から<b>改変・再構成</b>されており逐字一致しないため、汎用検索では同定不能。
今後は出典一覧を持つ専門資料・過去問解説本との照合が必要（工具は保存済み）</td></tr>
<tr><td>明示出典の転写清掃</td><td>書誌で確証が取れた誤記のみ補正（<code>tools/clean_sources.py</code>）；未確証は「要確認」ラベル</td>
<td><b>補正 8 件</b>：内藤廣『建築のはじまりに向かって』・吉田脩二『精神はいつ生まれたのか ヒトとサルのあいだ』・
池上彰『〈わかりやすさ〉の勉強法』・司馬遼太郎『風塵抄』・成毛眞 ほか。要確認 3 件（OCR 崩れ等）</td></tr>
</table>
<div class="warn">📌 結論：<b>自動逆引きは打ち切り、手法として記録</b>。実用的な次の手は「解説本・予備校の出典一覧」との照合、
または本文の特徴語＋著者候補の組み合わせ検索。本页では「明示出典（補正済み）」と「未詳」を区別して維持する。</div>
</div>

<div class="card"><h2>📈 傾向分析</h2>
<p class="lead">出典著者ランキング（＝同一著者・同書が複数問にまたがる；N1 の読解は<b>現代の評論・新書・エッセイ</b>が主力）</p>
{author_bars}
<p class="lead" style="margin-top:14px">読解題数の年次推移</p>
{year_bars}
<p class="lead" style="margin-top:14px">問題4 用法の復現語（同一語が複数回出題）</p>
<table><tr><th>語</th><th>回数</th></tr>{usage_repeat_rows}</table>
<p class="lead" style="margin-top:10px">N1 題型構成（2010–2025 累計）</p>
<table><tr><th>題型</th><th>題数</th></tr>{''.join(type_rows)}</table>
<p style="margin-top:10px">読み取れること：①読解は長文（問題10）と中文（問題9）が量的主力で、出典は現代の
<b>評論・教育・都市論・メディア論</b>系の新書/単行本；②同一書から 3–4 問まとめて出題される設計＝<b>一つの本文を精読させる</b>；
③用法（問題4）の見出し語は 125 語中 3 語のみ復現＝<b>同一語の再出題は稀で、語の「型」（二字漢語の共起）が繰り返す</b>。</p>
</div>

{mock}

<div class="card"><h2>🔮 2026-12-06 への予測（データに基づく期待値）</h2>
<table>
<tr><th>観点</th><th>観測（2010–2025）</th><th>2026-12 の予想</th></tr>
<tr><td>読解出典</td><td>現代評論・新書の書き下ろし的抜粋が主流；同一著者の複数回登場あり</td><td>同傾向継続。抽象度の高い随筆（教育・科学・文化）＋図表系（問題13）</td></tr>
<tr><td>問題4 用法</td><td>見出し語の再出題は稀（3/125）＝毎回新語</td><td>二字漢語（抽象名詞）＋和語動詞のコロケーション判断が中心</td></tr>
<tr><td>問題7 文章の文法</td><td>説明文・論説文の接続と指示詞が定点</td><td>接続表現（逆接・例示）と「この/その」の照応</td></tr>
<tr><td>模擬題の使い方</td><td>第二版 13 問（問題1/2/4/5/6＋問題7＋短読解）</td><td>形式確認用。未詳出典の自動逆引きは 0/65（改変本文のため）——専門資料との照合に切替</td></tr>
</table>
<div class="warn">🧪 ラベル：本页の予想は<b>統計的傾向</b>に基づく学習方針であり、出題内容の的中を保証しない。
模擬題は自作、引用ではない。真題原文の同定は「明示出典」と「逆引き同定」を区別して記録する。</div>
</div>

<footer>JLPT N1 出典索引・傾向分析（免密） · 真题正文在加密库内 · 個人学習用<br>
{meta['scope']} / reading {meta['reading_with_source']}+{meta['reading_unknown']} / usage {meta['usage_total']}</footer>
</main>
</body>
</html>
"""
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(page.encode())//1024} KB)")
    print(f"  passages {len(traces['passages'])}, unknown {len(traces['unknown_passages'])}, "
          f"authors top: {top_authors.most_common(3)}")


if __name__ == "__main__":
    main()
