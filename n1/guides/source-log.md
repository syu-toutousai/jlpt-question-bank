# 来源校对日志 (Source Log)

每次根据互联网资源核对用户录入内容时，在此记录。**只记录非版权元数据**；
下载的版权材料（PDF/图片/答案档）放入本地 `refs/`（gitignore 排除，绝不推送），
本文件本身可入库。

## 索引

| 日期 | 范围 | 来源 URL | 校对结论 | 本地文件 (refs/) |
|------|------|----------|----------|------------------|
| 2026-09-06 | 2024年7月 N1 全部答案速查（词汇/语法/读解/听力） | https://www.diliushixian.com/information/4374.html | 参照（与羊驼有1处差异，见下） | refs/2024-07_answerkey_diliushixian.md |
| 2026-09-06 | 2024年7月 N1 答案速查（羊驼） | https://www.youtibao.net/kaoshi/nxkalqgph3.html | 抓取失败，内容来自搜索摘要；题8应为4 | refs/2024-07_answerkey_youtibao.md |
| 2026-09-06 | 2024年7月 N1 逐题题干+选项+答案+解析（笔试全95题+听力） | https://www.jlptzhen.com/n1%E7%9C%9F%E9%A2%98%E5%9C%A8%E7%BA%BF%E5%81%9A2024%E5%B9%B407%E6%9C%88%E6%97%A5%E6%9C%AC%E8%AF%AD%E8%83%BD%E5%8A%9B%E8%AF%95%E9%AA%8C/ | 录入时逐题对照的首选源 | refs/2024-07_jlptzhen_full.html |
| 2026-09-06 | 2024-07 N1 文法/読解 逐题 | https://passjapanese.com/en/jlpt/n1/exam/2024-07-grammar-reading | 在线参照（未存档） | - |
| 2026-09-06 | 2024-07 N1 聴解 逐题 | https://passjapanese.com/en/jlpt/n1/exam/2024-07-listening | 在线参照（未存档） | - |
| 2026-09-06 | 2024-07 N1 词汇/语法/读解答案（沪江） | https://jp.hujiang.com/nenglikaon1/p1439200/ 等 | 在线参照（未存档） | - |
| 2026-09-06 | 学习材料语注生成：MOJi辞書（读音/释义/JLPT例句+TTS） | https://www.mojidict.com （本地 moji CLI 查询） | 逐词查询，用于生成 analysis/2024-07-vocab-reading-words.md | - |
| 2026-09-06 | 学习材料例句生成：Nadeshiko 动漫/日剧台词库（含截图/音频 URL） | https://nadeshiko.co （本地 nadeshiko CLI 查询） | 每个词条取 SAFE 等级例句，示例见 guides 说明 | - |
| 2026-09-07 | 2024-07 N1 词彙問題1全部题及答案词全文（含問題2 Q7-13 正确答案词） | http://aixinjp.com/a/lianxifangshi/zhentidaan/2024/0708/1143.html | ✅ Q7-13 答案（2・4・4・1・1・3・2）；Q8=返上4 与第六时限=2 相左，判定 4 | - |
| 2026-09-07 | 2024-07 N1 問題2 Q13 题干+4选项（骨折り/足手まとい/裏目/および腰） | https://nihongoaz.com/jlpt-n1-vocabulary-practice-test-30.html | ✅ 与 learnjapaneseaz 同源互证，答案=足手まとい | - |
| 2026-09-07 | 2024-07 N1 語彙・文法・読解 逐题（越南语题面，可核对 Q13 题干） | https://trynihongo.com/ja/de-thi-jlpt-tu-vung-ngu-phap-doc-hieu-n1-07-2024-q1353 | 参照（在线，未存档） | - |
| 2026-09-07 | 問題2 Q7-13 学习材料语注生成（正解7词＋干扰项21词）：MOJi辞書 | https://www.mojidict.com （本地 moji CLI，音频→~/moji_audio） | 逐词查询 → analysis/2024-07-vocab-context-words.md | - |
| 2026-09-07 | 問題2 Q7-13 学习材料例句/截图/音频：Nadeshiko | https://nadeshiko.co （本地 nadeshiko CLI） | SAFE 优先；繰り越す/低迷 无台词、および腰仅1条 | - |
| 2026-09-07 | 「足手まとい」标准读法确认 | コトバンク(大辞泉/精選版)・weblio | ✅ 通行读法 あしてまとい（「あしでまとい」とも）；moji 表记为 あしでまとい④ | www.kotobank.jp/word/足手纏い-424568 |
| 2026-09-08 | 全 58 词卡辞典発音内嵌（MOJi 词条 TTS，_w_ 音频→data URI，覆盖 問題1/問題2 全部卡片；另补下 29 词词条发音） | https://www.mojidict.com （本地 moji CLI，音频库 ~/moji_audio） | ✅ 58/58 内嵌，mp3 校验通过 | - |
| 2026-09-08 | 题干速览 13 条题干文の発音（Edge TTS ja-JP-NanamiNeural，→~/edge_tts_examples）＋ 例文29条合成与 27条MOJi原声 | https://www.mojidict.com / edge-tts | ✅ 13 题干 + 56 例文（27 原声/29 合成）全部发音内嵌 | - |
| 2026-09-08 | 学习页発音ボタン内联化（词/例句/台词/题干 直后按钮，去标签）＋ 发行源凡例区分（MOJi 蓝 / Edge 橙 / Nadeshiko 绿） | 生成器 tools/build_words_html.py | ✅ js 交互/几何位置验证通过；修复题干速览行此前未渲染的问题 | - |
| 2026-09-08 | 2024年12月 N1 真題全文（笔试 問題1-13 共66题，逐句原文） | https://jlpt247.com/n1-jlpt-12-2024/ | ✅ 主题干出处；无正确标记，答案另行交叉核对 | refs/2024-12_jlpt247_full.html |
| 2026-09-08 | 2024年12月 N1 答案66题（数字+选项文本，含並べ替え重建句） | http://aixinjp.com/a/lianxifangshi/zhentidaan/2024/1203/1172.html | ✅ 主答案源；问题1-7/8-13 选项文本逐一匹配；Q34键标③系笔误(自引文本=选项2)；Q13=3とっさに | refs/2024-12_answerkey_aixinjp.html |
| 2026-09-08 | 2024年12月 N1 文字・語彙/文法答案 Q1-44（第二大源） | https://learnjapaneseaz.com/jlpt-n1-12-2024.html | ⚠️ 与aixinjp Q1-44全符，唯一分歧 Q13=1じきに(疑误)；读解未收录 | refs/2024-12_answerkey_learnjapaneseaz.html |
| 2026-09-08 | 2024年12月 N1 答案（第六时限）——页面正文无答案内容 | https://www.diliushixian.com/information/4519.html | ⚠️ 空页（未发布答案），仅存档 | refs/2024-12_answerkey_diliushixian.html |
| 2026-09-08 | 2024年12月 N1 答案（沪江语法/读解） | https://jp.hujiang.com/nenglikaon1/p1443106/ 、 m.hujiang.com/jp_nenglikaoN1/p1443108/ | ⚠️ 页面无正文（仅导航，JS渲染），未采用 | refs/2024-12_answerkey_hujiang_gram.html |
| 2026-09-08 | 2024年12月 N1 答案（nihongoaz / 新干线） | https://nihongoaz.com/jlpt-n1-12-2024.html 、 https://www.xgxedu.com/html/kszx/6401.html | ⚠️ 无正文（JS渲染/GBK图片），未采用 | refs/2024-12_answerkey_nihongoaz.html 、 refs/2024-12_answerkey_xgxedu.html |
| 2026-09-08 | 常用漢字表 本表 2136字（字種・音訓・例・備考，H22内閣告示） | https://www.bunka.go.jp/kokugo_nihongo/sisaku/joho/joho/kijun/naikaku/kanji/joyokanjisakuin/index.html | ✅ 公表HTML、Shift_JIS、2136行；生成 data/joyo-kanji-2136.json 的元数据（例=音訓索引原文，弥/朕/阜等が例無し、極 は〔副〕を例に合流） | refs/joyo_kanji_sakuin_bunkacho.html |
| 2026-09-08 | 学年（教育漢字1026字）＝文部科学省 H29 学習指導要領 学年別漢字配当表 | https://fragment-database.com/kanji.html | ✅ 1年80/2年160/3年200/4年202/5年193/6年191（計1026）；残り1110字→中学(7)。Wikipedia 常用漢字一覧 と学年0差分 | refs/joyo_gakunenbetsu_haitou_fragment-db.html |
| 2026-09-08 | 総画数＝Unicode UCD Unihan kTotalStrokes（国際基準） | https://www.unicode.org/Public/15.1.0/ucd/Unihan.zip | ✅ 2136/2136 全収録；日本の辞書画数（以=5画など）と175字で相違（meta.caveats に記載） | refs/unihan/ |
| 2026-09-08 | 部首＝Unicode UCD 8.0 Unihan kRSKangXi（康熙214部首） | https://www.unicode.org/Public/8.0.0/ucd/Unihan.zip | ✅ 2136/2136 全収録；部首名は康熙214部首表（日本語常用形） | refs/unihan8/ |
| 2026-09-08 | 独立クロスチェック：ja.wikipedia 常用漢字一覧（部首/総画/学年） | https://ja.wikipedia.org/wiki/%E5%B8%B8%E7%94%A8%E6%BC%A2%E5%AD%97%E4%B8%80%E8%A6%A7 | ✅ 学年0差分；部首名は大体KangXi一致（ウィキの部首帰属に方言あり医→酉等）；画数の JP 流は UCD と175字相違（上述 caveat 根拠） | - |
| 2026-09-08 | 2024年7月 N1 聴解フル音声（問題1-5 全30問，128kbps 51:56） | 百度网盘（用户上传 baidupcs 云端 `2013-2021年N1音频/2024年7月新日语能力考试 N1.mp3`，47.55MB） | ✅ ローカル archive のみ（refs/、gitignore・不推送）；本页聴解音声は per-Q リモートURL（jlptzhen.com 202407N10X_Y.mp3，29/29 200 OK）を引き続き使用 | refs/2024-07_listening_baidupcs.mp3 |
| 2026-09-08 | 2024-07 全文読み上げ音声（耳から勉強用）：語彙25 + 文法42 + 読解276 + 聴解187 = 530文、単元別5本＋通し1本（通し 約83分）、文間エコー2s、単元冒頭1フレーズ案内。空欄(【41】・（　　）・___★___)は正解で補完、読解は各選択肢のうち正しい1文のみ読上げ（例：語彙 用法20-25は正解文1文、言い換え14-19は原文＋正解言い換えの2文）、注釈（注/注n/中略）は除去｜行末の設問番号（例「物知り顔55.」）と読解小見出し（例「人には会いに行こう」）は行単位で分割、文中半角空白の混入（「1. 週間」「こ れでもう」等）は正規化、裸の「注）」マーカーも除去 | Edge-TTS ja-JP-NanamiNeural（ツール `tools/gen_exam_tts.py`） | ✅ 530文 全clips生成・検証（0 bad/0空欄/0注釈残り）、音声レベル正常（mean -16〜-22dB・クリップ無し）、経過時間異常なし。音声は gitignore・不推送 | refs/exam_tts/2024-07/（manifest.json に各文・順序） |

| 2026-09-08 | jlptzhen N1 文字語彙クイズ30会場（2010-07〜2025-12、2020-07中止）25問／回、正解マーク+中国語解説、講義 HTML 存档 | https://www.jlptzhen.com（wp-sitemap-posts-post-1.xml 網羅） | ⚠️ **年份標籤不可信**：クイズ内容が実際の該当年次と一致しない場合あり。2024-12 の「N1真题在线做2024年12月」(quiz 330) は 2025 後半以降の別冊と一致せず、実物 2024-12 (jlpt247転写+aixinjp 鍵 211343…) と 0/25 不一致 → バンクへの一括 import は**撤回・全削除（2024-07除く）**。jlpt247 全文転写との照合：2022-12=25/25 完全一致、2022-07=22/25(残3は転記表記ゆれ)、2023-07=18/25(残7は表記ゆれ度合い)、2025-07=18/25。残り会場(2010-2021等)は独立資料による年次・内容監査後にだけ再 import 可 | refs/<session>_jlptzhen_vocab.html + refs/<session>_vocab_jlptzhen.json（30会場） |
| 2026-09-08 | 上記監査後 2022-12 のみ 25/25 完全一致 → バンク利用可（但し正解=サイトマーク単独、仍待第二源） | https://www.jlptzhen.com クイズ＋refs/2022-12_jlpt247.json | ✅ 2022-12 語彙クイズは公式試験と完全一致（25/25） | refs/2022-12_vocab_jlptzhen.json |
| 2026-09-08 | 2024-12 vocab 復旧（quiz 印字で汚染された reading_01-06 等 25 問を jlpt247転写+aixinjp/learnjapaneseaz 鍵から再生成、番号・正解整合 211343|1434213|224311|244321） | refs/2024-12_jlpt247.json + refs/2024-12_answerkey_aixinjp.html + learnjapaneseaz | ✅ 復旧完了、git 状態は quiz import 前と同一 | past-exams/2024/12/vocab/*.json |
| 2026-09-09 | 2017-12 书面卷 70 题全部密钥（語彙・文法・読解），基于 trynihongo 出题接口逐题「服务器裁决」 | trynihongo.com 過去問 `de-thi-jlpt-tu-vung-ngu-phap-doc-hieu-n1-12-2017-q739` 的 `check_single_question_ajax` 接口 POST（每选项 `is_correct` 由服务器返回）+ refs/2017-12_key_asite.html（a-site Q1-49 短语锚）+ 帝京 scribd 快照 | ✅ 70/70（語彙 62-位置 1-19 短语定位、問題4-13 由 API 服务器验证位置；排序 Q36-40=1,4,3,2,2 与 a-site ①④③②② 吻合；问题7=41123、问题8=2432 同 a-site 数字） | refs/2017-12_answer_trynihongo.json + refs/2017-12_keys.json（70 题） |
| 2026-09-09 | 2018-07 书面卷 70 题全部密钥（此前 weilan 51 题数字为官方位、转写已洗牌） | trynihongo 真题页 `de-thi-jlpt-tu-vung-ngu-phap-doc-hieu-n1-7-2018-q740` 出题接口服务器裁决（每选项 `is_correct`） | ✅ 70/70 转写位置（Q28=3 服裁决，此前 weilan=4/帝京=3 争议就此定案）；键 241243\|4323122\|314312\|423141\|4331221423\|13243\|31241\|2411\|444444211\|1321\|34\|2423\|31 | refs/2018-07_answer_trynihongo.json + refs/2018-07_keys.json（70 题，全量重写） |
| 2026-09-09 | 2019-12 书面卷 69 题全部密钥（weilan 59 题数字同为官方位） | trynihongo 真题页 `de-thi-jlpt-tu-vung-ngu-phap-doc-hieu-n1-12-2019-q743` 出题接口服务器裁决 | ✅ 69/69 转写位置（transcript 无 Q70）；文法 26-35=1123323244 与 chuyenngoaingu 官方表逐位一致（该段转写未洗牌） | refs/2019-12_answer_trynihongo.json + refs/2019-12_keys.json（69 题，全量重写） |
| 2026-09-09 | 2018-12 书面卷 70 题全部密钥 | trynihongo 真题页 `de-thi-jlpt-tu-vung-ngu-phap-doc-hieu-n1-12-2018-q741` 出题接口服务器裁决 | ✅ 70/70 转写位置 | refs/2018-12_answer_trynihongo.json + refs/2018-12_keys.json（70 题全量重写；generate_paper 用 trynihongo 路径需先临时移开 refs/2018-12_jlpt247.json） |
| 2026-09-09 | 2019-07 书面卷 69 题全部密钥 | trynihongo 真题页 `de-thi-jlpt-tu-vung-ngu-phap-doc-hieu-n1-7-2019-q742` 出题接口服务器裁决 | ✅ 69/69 转写位置 | refs/2019-07_answer_trynihongo.json + refs/2019-07_keys.json（69 题全量重写） |
| 2026-09-09 | 2016-12 书面卷 70 题全部密钥 | trynihongo 真题页 `de-thi-jlpt-tu-vung-ngu-phap-doc-hieu-n1-12-2016-q737` 出题接口服务器裁决 | ✅ 70/70 转写位置 | refs/2016-12_answer_trynihongo.json + refs/2016-12_keys.json（70 题全量重写） |
| 2026-09-09 | 2016-07 书面卷 70 题全部密钥 | trynihongo 真题页 `de-thi-jlpt-tu-vung-ngu-phap-doc-hieu-n1-7-2016-q736` 出题接口服务器裁决 | ✅ 70/70 转写位置 | refs/2016-07_answer_trynihongo.json + refs/2016-07_keys.json（70 题全量重写） |
| 2026-09-09 | 2010-07～2015-12 十二场书面卷全部密钥（2010 两场各 71 题、其余 70 题） | trynihongo 真题页 q724-q735（`de-thi-jlpt-tu-vung-ngu-phap-doc-hieu-n1-7/12-YYYY`）出题接口服务器裁决 | ✅ 842/842 转写位置；2011-12 Q69 首探转写缺第 4 选项（页面窗口截断所致）→ 修正窗口后 = 川村さん ④；2013-12 前 70 键（xdf 数字）与 2014-12 68 键全部由接口位置取代 | refs/<session>_answer_trynihongo.json + refs/<session>_keys.json（12 场全量重写） |

## 结论标记

- ✅ 已核对一致（附来源）
- ⚠️ 未能确认，保留用户录入原样
- ❌ 发现不符（修正或待用户确认）

## 归档规则

1. 下载/截图版权材料 → `refs/`（文件名格式：`YYYY-MM_科目_来源.ext`）
2. 在本表追加一行：范围、URL、结论、refs 文件名
3. 若某来源已失效，保留记录并将 URL 标记为「失效」

## 2025-07 完整密钥（已验证逐题落库）

- 答案源经交叉核验：uno/一茂（`/tmp/unojapano_2025-07.html`）+ jlpt247 DA（`refs/2025-07_answerkey_jlpt247.html`）+ 宁波爱心 aixinjp（`refs/2025-07_answerkey_nbry.html`, 66题+重建句）+ keedu 搜索快照（keedu 页面抓取为0字节,键取自快照）。
- 争议裁决: Q8 取3 手先（quiz334+aixinjp; uno=4 手際 误）；Q20 取2（aixinjp标③但自引文本系选项2）；Q41 取4 だけが（keedu文本+aixinjp标4; uno=2 文法不通）；Q55 取2 本能（aixinjp+原文「高いところは怖い…インストール」; uno/DA=4 系误断）。
- 問題6（並べ替え）Q36–40 = 2,3,2,1,4（uno=aixinjp 重建逐空一致）。
- 結果: `past-exams/2025/07/*/` 66 问, `guides/source-log.md` 已註, `tools/generate_paper.py::ANSWER_OVERRIDES["2025-07"]` 落盘。聴解键（聴力1-5）已有源但转写待办（2025-07 转录为纯文字版）。

## 衍生数据（無版权・可入库）

| 日期 | 范围 | 来源 | 结论 | 本地文件 |
|------|------|------|------|----------|
| 2026-09-08 | 2024-07+2024-12 全问题バンク 162 问 漢字走査（语幹/选项/正解/読解パッセージ/聴解原文・カナ行のみ） | `past-exams/**/*.json`（自録） | 1070 字（語彙480・文法394・読解754・聴解570），表外 23 字 | `joyokanjihyo-annotated/data/kanji_labels.json` |
| 2026-09-08 | 表外漢字 23 字の音・訓（付録用） | Unihan 8.0 `kJapaneseKun` / `kJapaneseOn`（`refs/unihan8/Unihan_Readings.txt`） | 例（问题バンクの実例）とともに `tools/annotate_pdf.py::EXTRA` に反映 | `refs/unihan8/Unihan_Readings.txt` |- 結果: `past-exams/2025/07/*/` 66 问, `guides/source-log.md` 已註, `tools/generate_paper.py::ANSWER_OVERRIDES["2025-07"]` 落盘。聴解键（聴力1-5）已有源但转写待办（2025-07 转录为纯文字版）。

## 2023-07 完整密钥（已验证逐题落库）

| 日期 | 范围 | 来源 | 结论 | 本地文件 |
|------|------|------|------|----------|
| 2026-09-09 | 2023-07 书面卷 66 题 全密钥（語彙・文法・読解） | aixinjp 宁波爱心 `http://aixinjp.com/a/lianxifangshi/zhentidaan/2023/0704/1078.html`（带 Referer 触发可 200）+ jpnihon `https://jpnihon.com/5649.html`（全题解析,本网络不可直达,仅搜索引擎快照）+ renrendoc 人人文库 `2023年7月N1真题及答案解析` | ✅ 交叉核验；vocab 413423\|2234114\|232414\|423131、問題5 4313242131、問題6(並べ替え★) 13424、問題7 2134、問題8 1322、問題9 34423114、問題10 334、問題11 31、問題12 434、問題13 24 | `refs/2023-07_answerkey_nbry.html`（78,921 B 原文存档） |

- 争议裁决（aixinjp 与 jpnihon/renrendoc 解析两处分歧，均取解析源）:
  - **问题7 (41-44)**: aixinjp=1114 但在 41/43 与文意相违 → 取 jpnihon+renrendoc 两源独立共证 **2,1,3,4**（41=2 小説でもあるまい["まさか自恋…かといって傑作でもない"否定推理]；42=1 褒めたり叱ったりする；43=3 否定できなくなる[“不会动手改自己作品”因由,否定せずにいられなくなる=自我否定逆义]；44=4 とは["所谓一生的工作就是…"定义式]）。
  - **Q56**: aixinjp=1（"多様な使い手が平等だという感覚…作るべき"）vs jpnihon 解析=4（"常に使い手にとっての平等について考えなければならない",关键句 常に/平等/考える）→ 取 **4**。問題9 = 3,4,4,2,3,1,1,4。
- jpnihon 解析与 aixinjp 数字键在 45-59、62-64 全部一致，互相独立（解析文本 vs 键文本），强化信任。
- Q42（问题7 第2空）jlpt247 转写缺选项 → 依 jpnihon/scribd 帝京版补录 4 选项文本，正式卷选项1=褒めたり叱ったりする。
- 结果: `past-exams/2023/07/*/` 66 问；`tools/generate_paper.py::ANSWER_OVERRIDES["2023-07"]` + VERIFY/VERIFY_SOURCES/ANSWER_NOTES 落盘；`tools/organize.py` 新增 `sync` 子命令（镜像 past-exams → question-bank/by-type，当前 294 题全镜像）。

## 2022-07 / 2022-12 / 2021-12 完整密钥（已验证逐题落库）

| 日期 | 范围 | 来源 | 结论 | 本地文件 |
|------|------|------|------|----------|
| 2026-09-09 | 2022-07 书面卷 68 题（真卷问题9=49-57×9 等非标准分节） | aixinjp 宁波爱心 `http://aixinjp.com/a/lianxifangshi/zhentidaan/2022/0705/1039.html`（Referer 触发 200）+ 新泽真题卷参考答案（文字語彙+問題5 数字全同）+ PassJapanese 分节结构印证 | ✅ 键 133424\|4221133\|424331\|231214\|2314123422\|41324(排列 3241/2413/4231/3124/1342)\|3211\|読解 3143\|331322144\|143\|23\|4124\|12；読解答案句与 jlpt247 选项文本逐句吻合 | `refs/2022-07_answerkey_nbry.html`（31,140 B 存档） |
| 2026-09-09 | 2022-12 书面卷 66 题 | aixinjp `https://aixinjp.com/a/lianxifangshi/zhentidaan/2022/1206/1049.html`（Referer 触发 200）+ jlptzhen 词组 quiz 25/25(09-08 审计)+ 第六时限読解分节数字一致 | ✅ 键 324143\|1324321\|421243\|332412\|1331423241\|24213(排列 4231/1342/3421/3412/4132)\|3421\|読解 2112\|23241233\|413\|44\|342\|32；答案句逐一吻合选项文本 | `refs/2022-12_answerkey_nbry.html`（115,328 B 存档） |
| 2026-09-09 | 2021-12 书面卷 69 题（真卷问题9=49-57×9、問題10=58-61×4、問題11=62-64×3） | aixinjp `https://aixinjp.com/a/lianxifangshi/zhentidaan/2021/1223/1004.html`（Referer 触发 200）+ 第六时限（回忆版,文字語彙多处歧异） | ✅ 键 431231\|1424233\|313242\|314421\|3243242311\|14421(排列 3241/1342/3142/4213/1324)\|1342\|読解 3442\|433212321\|1411\|223\|423\|22；読解答案句同步选项文本（其中 Q54/55/57 与第六时限分歧,选项文本核实取 aixinjp）；Q69 单源(aixinjp 自读图表) | `refs/2021-12_answerkey_nbry.html`（77,940 B 存档） |

- 注：两年次的 問題1 键以存档全键为准（放下方误读先例，2022-12 問題1=324143 即 Q1 かんとく 等读音键）。
- 争议说明（2021-12 vs 第六时限回忆版）：問題1 Q3 錯覚=さっかく(aixinjp) 非时限的 视觉(視覚)；Q54/55/57 时限答案均被选项文本核验推翻；其余問題2-5 亦有零星年限回忆差异，均以 aixinjp 重建句为准。
- 结果: `past-exams/2022/07/*/` 68 问、`2022/12/*/` 66 问、`2021/12/*/` 69 问，合计 +203；`ANSWER_OVERRIDES/VERIFY/VERIFY_SOURCES/ANSWER_NOTES[2022-07|2022-12|2021-12]` 落盘；`organize.py sync` 后 bank = 497 题。

## 2020-12 完整密钥（68 题，keymap 文本定位 + 蔚蓝交叉）

| 日期 | 范围 | 来源 | 结论 | 本地文件 |
|------|------|------|------|----------|
| 2026-09-09 | 2020-12 书面卷 68 题 | jlptzhen 词组 quiz（问题1-4 键+选项文本，`refs/2020-12_vocab_jlptzhen.json`）+ 前途教育 `https://qiantu.xdf.cn/202012/10970010.html`（逐题答案+解析+选项文本,问题6 排列 2,3,1,4等×5,答案句逐句吻合）+ 蔚蓝 `http://jp.weilanliuxue.cn/lxks/jlpt/21250.html`（逐题数字键 读解45-68 全文）+ trynihongo 全文转写 `refs/2020-12_trynihongo.json` | ✅ 键 213414\|4221423\|423213\|124133\|4344132233\|42431(并べ替え,排列逐题 4,2,4,3,1)\|2123\|读解 2311\|412313132\|242\|44\|4321\|33；读解题答案句逐一吻合选项文本；Q58=2（约五亿年前~急增后减少又增加）文本三源核对 weilan=4/qiantu=3 位置均不合文案；Q32=2 対戦してくる 转写位置(shuffle-safe) | `refs/2020-12_key_xdfqiantu.html`（179,560 B 原文存档）+ `refs/2020-12_key_weilan.html` + `refs/2020-12_keys.json` + `refs/2020-12_keyreport.txt` |

- 方法：`tools/keymap.py` 新管线——jlptzhen 键与转写选项**文本匹配**求位置（应对 trynihongo 洗牌），前途页 per-question 文本定位 + 排列/数字兜底；蔚蓝逐题数字与 qiantu 文本在 45-68 全部吻合（除 Q58，文本判断胜出）。
- 注：问题4 Q24 weilan=4 系笔误（取 3 収容，jlptzhen=qiantu 双源）；问题6 为**并べ替え**题，键 4 2 4 3 1 为该空位序。
- 结果: `past-exams/2020/12/*/` 68 问；`generate_paper.py` 新增 legacy（trynihongo+keymap keys）输入管线；`organize.py sync` 后 bank = 565 题（加密站点 docs/ 同步重建，Node roundtrip 验证通过）。

## 2017-12 完整密钥（70 题，trynihongo 出题接口服务器裁决 + a-site 短语锚）

| 日期 | 范围 | 来源 | 结论 | 本地文件 |
|------|------|------|------|----------|
| 2026-09-09 | 2017-12 书面卷 70 题 | trynihongo.com 真题页 `https://trynihongo.com/ja/de-thi-jlpt-tu-vung-ngu-phap-doc-hieu-n1-12-2017-q739`（出题接口 `POST /quiz/check_single_question_ajax`，POST `_token/question_id/answer_id/selected_fraction=1`，对每个选项返回服务器 `is_correct`，等同答题提交裁决）+ a-site `http://www.a-site.cn/article/1605966.html`（Q1-49 答案短语逐题锚）+ 帝京 scribd 快照（文法 26-35 选项文、排序全序）+ jlptzhen 词组 quiz Q1-25 | ✅ 键 114323\|4231242\|432132\|241413\|124333\|4112\|14322(并べ替え)\|41123\|2432\|313214412\|3414\|42\|1323\|13；全部 70 题答案文本逐题回填配对到转写选项（transcript 位置），排序 Q36-40=1,4,3,2,2 与 a-site ①④③②② 全合；问题7=41123、问题8=2432 同 a-site 数字 | `refs/2017-12_answer_trynihongo.json`（逐题 answer_pos+answer_text+answer_id）+ `refs/2017-12_keys.json`（70 题） |

- 方法：trynihongo 真题页每题一个 DOM 盒，选项带 `data-question-id`/`data-answer-id`；出题接口对每个答案选项返回 `{data:{is_correct}}` → 唯一的正确选项即答案。因 passage 盒与试题盒会占用相同 DOM id（如 `question-57`），编号须按「文档序中带选项的真实盒」重排（第 k 个真实盒 = 第 k 题）。接口对突发访问限速（`Server error`），用单页 GET 绑定 CSRF token、逐题 4s 间隔、失败 20-25s 退避后重绑，35 题全部命中。
- 交叉核验：1-19 语汇答案短语与 a-site/jpedo 读音、jlptzhen 键互证；20-31 与 a-site 问题4/5 短语全合；32-35 与 a-site ④①②② 全合；36-40 与 a-site ①④③②② 全合；41-49 与 a-site「41123」「②④③②」全合（41-45=4,1,1,2,3 即 41123）。50-70 读解无 a-site 覆盖，全部由接口服务器裁决 + 答案文本与转写选项逐句回填。
- 结果: `past-exams/2017/12/*/` 70 问（0 警告）；`organize.py sync` 后 bank = 635 题；加密站点 docs/ 重建，Node roundtrip 验证通过（635 题可解密、2017-12 70 题在位、错误口令被拒）。

## 2018-07 / 2019-12 完整密钥（trynihongo 接口全量服务器裁决）

| 日期 | 范围 | 来源 | 结论 | 本地文件 |
|------|------|------|------|----------|
| 2026-09-09 | 2018-07 书面卷 70 题 | trynihongo 真题页 `https://trynihongo.com/en/de-thi-jlpt-tu-vung-ngu-phap-doc-hieu-n1-7-2018-q740` → `POST /quiz/check_single_question_ajax`（_token/question_id/answer_id/selected_fraction=1，服务器逐选项返回 `is_correct`） | ✅ 键 241243\|4323122\|314312\|423141\|4331221423\|13243\|31241\|2411\|444444211\|1321\|34\|2423\|31；Q28=3 定案（此前 weilan=4 vs 帝京=3）；排序 36-40=1,3,2,4,3 | `refs/2018-07_answer_trynihongo.json`（70 条 answer_pos/answer_text）+ `refs/2018-07_keys.json`（70 题全量重写） |
| 2026-09-09 | 2019-12 书面卷 69 题（transcript 无 Q70） | trynihongo 真题页 `https://trynihongo.com/en/de-thi-jlpt-tu-vung-ngu-phap-doc-hieu-n1-12-2019-q743` 同接口 | ✅ 键（69 位）：問題1-13 见 `refs/2019-12_keys.json`；文法 26-35=1123323244 与 chuyenngoaingu 官方表逐位一致（该段转写未洗牌） | `refs/2019-12_answer_trynihongo.json`（69 条）+ `refs/2019-12_keys.json`（69 题全量重写） |

- 方法（与新工具 `tools/trynihongo_api.py` 固化）：真题页 DOM 每盒带 `data-question-id`/`data-answer-id`；按「文档序中真实选项盒」重排为题号（passage 盒会占用同号 id）；per-question 单页 GET 绑定 CSRF token（同 cookie jar），逐选项 POST 直到 `is_correct=true`；3s 间距 + 15s 退避。
- 背景：此前这 2 场从蔚蓝 weilan 提取的数字键是「官方位」，trynihongo 转写会洗牌选项（语汇 1-19 尤甚），故整场用服务器裁决重做以保证位置对齐。
- 结果: `past-exams/2018/07/*/` 70 问、`past-exams/2019/12/*/` 69 问；`organize.py sync` 后 bank = 774 题；加密站点重建，Node roundtrip 通过（774 可解密、三场各 70/70/69 在位、错误口令被拒）。

## 2018-12 / 2019-07 / 2016-12 / 2016-07 完整密钥（trynihongo 接口服务器裁决）

| 日期 | 范围 | 来源 | 结论 | 本地文件 |
|------|------|------|------|----------|
| 2026-09-09 | 2018-12 书面卷 70 题 | q741 真题页 → `check_single_question_ajax` | ✅ 70/70；注意 generate_paper 检出源顺序为 jlpt247 优先，生成时需临时移开 refs/2018-12_jlpt247.json | refs/2018-12_answer_trynihongo.json（70 条）+ refs/2018-12_keys.json |
| 2026-09-09 | 2019-07 书面卷 69 题 | q742 真题页同接口 | ✅ 69/69 | refs/2019-07_answer_trynihongo.json + refs/2019-07_keys.json |
| 2026-09-09 | 2016-12 书面卷 70 题 | q737 真题页同接口 | ✅ 70/70 | refs/2016-12_answer_trynihongo.json + refs/2016-12_keys.json |
| 2026-09-09 | 2016-07 书面卷 70 题 | q736 真题页同接口 | ✅ 70/70 | refs/2016-07_answer_trynihongo.json + refs/2016-07_keys.json |

- 同 `tools/trynihongo_api.py` 流程（per-question 单页 GET 绑 token → 逐选项 POST 至 `is_correct=true`，3s 间距+15s 退避）。
- 结果: `past-exams/2018/12/*/` 70 问、`2019/07/*/` 69 问、`2016/12/*/` 70 问、`2016/07/*/` 70 问；`organize.py sync` 后 bank = 1053 题；加密站点重建，Node roundtrip 通过（1053 可解密、七场合计在看、错误口令被拒）。

## 聴解（听力）近十年全量入库（2026-09-10）

| 日期 | 范围 | 来源 URL | 校对结论 | 本地文件 (refs/) |
|------|------|----------|----------|------------------|
| 2026-09-10 | 2010-07 … 2023-07 二十四场聴解（旧式 35-38 题/新式 30 题，共 851 题） | https://trynihongo.com/en/de-thi-jlpt-nghe-n1-thang-{07|12}-nam-{YYYY}-qNNN（馆内嵌 quizContext：题干=问题番号、音频源、每选项 fraction） | ✅ 答案 = 页面内嵌 fraction=1 的位置；每问含音频 URL（trynihongo /upload/mooddata/…，直链可达）；站方对话脚本需登录，暂缺 | refs/<session>_listening_page.html + refs/<session>_listening_trynihongo.json（基于正文 quizContext 归纳：「問題N」含空格/罗马数字/聴解①②等多种节标题统一为問題1-5；问题5 の質問1/2 无独立音频，继承3番故事音频） |
| 2026-09-10 | 2024-12 聴解 | https://trynihongo.com/en/de-thi-jlpt-nghe-n1-thang-12-nam-2024-q1356 | ⚠️ 页面仅存 quiz 元数据、无题目，判为 stub，未采集 | refs/2024-12_listening_page.html（已留档备查） |

- 工具 `tools/fetch_listening.py`（quizContext 解析、节标题归一、音频继承）+ `tools/generate_paper.py` 追加 `refs/<session>_listening_trynihongo.json` 合并写入 `past-exams/<y>/<m>/listening/`（type=point/grammar/overview/detailed/implication）。
- 结果（在既有 2024-07 jlptzhen 30 道聴解之上）：`organize.py sync` 后 bank = 2746 题（其中聴解 881）；docs/ 重建；Node roundtrip 通过（2746 可解密、851 道聴解带音频 URL、错误口令被拒）。

## 2010-07～2015-12 十二场完整密钥（trynihongo 接口服务器裁决，全量收官）

| 日期 | 范围 | 来源 | 结论 | 本地文件 |
|------|------|------|------|----------|
| 2026-09-09 | 2010-07 / 2010-12（各 71 题）、2011-07 / 2011-12 / 2012-07 / 2012-12 / 2013-07 / 2013-12 / 2014-07 / 2014-12 / 2015-07 / 2015-12（各 70 题） | trynihongo 真题页 q724～q735 出题接口 `check_single_question_ajax` 服务器逐选项裁决 | ✅ 842/842 转写位置；旧的 xdf 数字键（2013-12）、缺失键（2014-12 68/70）、weilan/koolearn 官方位数字键全部由接口位置取代 | refs/<session>_answer_trynihongo.json + refs/<session>_keys.json + refs/<session>_keyreport.txt（12 场） |

- 工具 `tools/trynihongo_api.py` 修正：选项窗口 6000→20000 字节（2011-12 Q69 第 4 选项 川村さん 因 passage 超长图片被截断；修正后 = ④）。
- 至此可及场次（2010-07～2019-12 三轮、2020-12、2021-12、2022 两场、2023-07、2024 两场、2025-07）书面卷答案全部齐备；2020-07 当年停考，2023-12 / 2025-12（及 2026 年）无真题来源。
- 结果: `organize.py sync` 后 bank = 1895 题；docs/ 重建；Node roundtrip 通过（1895 可解密、按年份 2010:142 … 2025:66、错误口令被拒）。

## 学习材料全量重产：全27场 語注・例句集 + 聴解

| 日期 | 范围 | 来源 | 结论 | 本地文件 |
|------|------|------|------|----------|
| 2026-09-10 | 2010-07～2025-07 全部 27 场 | tools/gen_learn_md.py（MOJi 辞书 + Nadeshiko 动漫日剧台词 + edge-tts） | 每场生成 9 个 md（q3 言い換え/q4 使い方/q5 文法選択/q6 並べ替え/q7 文章文法/q8-q10 読解/聴解）；建 docs/vocab-words-<session>.html 27 页；docs/index.html 免密列表 + 每页链接 | analysis/<session>-\*.md（243 个）+ docs/vocab-words-\*.html |

- gen_learn_md.SESSIONS 扩至 27 场；enrich 走磁盘缓存 tools/data/learn_cache.json（本次增补约 2300 词条调度，全部落缓存）。
- 聴解五类官方型名统一为：問題1 課題理解 / 問題2 ポイント理解 / 問題3 概要理解 / 問題4 即時応答（旧称 発話表現）/ 問題5 統合理解；修正 gen_learn_md.LISTEN_DESC、docs/index.html TYPEMAP、docs/vocab-words*.html 全部聴解小节标题。
- 旧场次（2010-2019 老格式）聴解问答脚本受 trynihongo 登录墙限制 → 聴解材料仅含题干・选项・音频链接，无原文翻译（2010-07 起）；2024-12 / 2025-07 无聴解文件（该两场收听页缺省/未采）。
- 2024-07 保持基准页 docs/vocab-words.html 命名（免密全66問・含聴解）；其余 26 场 = vocab-words-<session>.html。
- 注意：旧格式笔试 q1/q2（読方/語彙）无独立材料文件（既有生成器未覆盖老格式），页面仅 nav 置灰。
- 本次构建中途曾触发 /home 磁盘满（100%），清理 yay/pacman/pip/uv/chrome 缓存（~7G，pacman 包缓存为 root 属主未能删）后方继续。

## 呼応・搭配 索引与课件（答案复核 + 真題再编）

| 日期 | 范围 | 来源 | 校对结论 | 本地文件 |
|------|------|------|----------|----------|
| 2026-09-12 | 文法 532 问（問題5/6/7，2010-07～2025-07） | refs/<session>_keys.json（trynihongo）· <session>_answerkey_nbry.html · 2024-07_answerkey_diliushixian.md · 题库 verified.note | ✅ 454 可比对题中 453 一致；唯一分歧 2024-07 Q29（第六时限=2 vs jlptzhen/jlpt247=3）判定题库 3 为是 | analysis/呼応-verification.md · analysis/呼応-collocations.md |

- 产出 `analysis/呼応-collocations.md`（按 A 仮定譲歩 / B 全面否定 / C 推量様態 / D 強調程度 / E 文末モダリティ / F 助詞系文型 分类的真题搭配索引）。
- 据此在姊妹仓库 `japanese-learning/koou-courseware/` 生成单文件交互课件（167 パターン・532 問真題全量・405 問真题填空题库・270 TTS + 126 Nadeshiko 原声），数据由 `extract_bank.py` 从本库抽取。
