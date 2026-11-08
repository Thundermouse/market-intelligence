---
name: A股盘后分析
schedule_id: 329b6cc7
cron: "15 15 * * MON-FRI"
timezone: Asia/Shanghai
status: active
skill: investment-roundtable
created_at: 2026-11-04T19:27:07Z
# 恢复方式：用 Schedule 工具 create，cron / timezone 同上，message 取下方 Prompt 全文
---

## Prompt

执行中国市场盘后分析（只分析中国 A 股市场，不涉及港股美股）。调用 investment-roundtable 技能。

【K线数据准备·阶段0，必须最先执行】
读取持仓与观察列表，提取全部 A 股代码，调用 market-intelligence-fetch 技能确保多周期数据就绪：
- 对每个 A 股代码执行 ensure（市场=A股，周期=daily weekly monthly 15min 1h）
- 新股票自动全量初始化，已有股票自动补丁最新数据。所有周期返回 ✅ 后再启动子智能体。
- 各周期历史要求：15min 7个交易日、1h 3个月、日线 6个月、周线 3年、月线 10年。分钟级仅校验新鲜度（API历史上限约50天）。
- 数据落盘由 market-intelligence-db 技能管理，数据库位于 /home/yuhaic/workspace/market-intelligence/data/market_data.db。

【数据与文件】
- 持仓：/home/yuhaic/workspace/market-intelligence/result/China-market/holdings_cn.csv；观察：watchlist.csv
- 场次目录：/home/yuhaic/workspace/market-intelligence/result/China-market/roundtable/cn-close/
- 取数（按优先级）：①iFinD 首选，拉取全部 A 股持仓、观察标的与 4 个指数（沪深300、上证50、创业板指、科创50）的当日收盘价；②若 iFinD 不可用，用 WebSearch/WebFetch 从交易所官网、东方财富、雪球等获取；③取数结果写入 /home/yuhaic/workspace/market-intelligence/result/China-market/snapshots/<YYYYMMDD-HHMM>-cn-close.json，字段含 snapshot_id、collected_at(Asia/Shanghai)、symbols{代码:{last,prev_close,pct,volume,source}}。收盘后取数须标注"收盘定格"，执行前重取。以最新快照为主要参照，可查阅同目录历史快照与历史纪要作趋势背景对照，但不得被历史结论锚定。
- 核算：python3 /home/yuhaic/workspace/market-intelligence/result/China-market/tools/positions.py --holdings holdings_cn.csv --snapshot <快照>。本任务只算 A 股，不含港股。

【信息源】
财新、证券时报、上海证券报等中国权威财经媒体为主；参照 wsj.com、bloomberg.com、高盛、花旗对中国市场观点。检索当日及近几日相关新闻，付费墙内容引用标题与公开摘要，注明来源与时间。

【输出板块】
①A 股当日整体回顾（指数涨跌、板块热点、资金面）②持仓标的涨跌复盘与原因分析（逐只给持有/加仓/减仓建议）③观察标的分析（当日异动与买入机会）④重要新闻解读（来源、时间、影响标的）

【纪要】
保存至 /home/yuhaic/workspace/market-intelligence/result/China-market/roundtable/cn-close/，文件名 YYYY-MM-DD-cn-close.md（不带下划线），中间产物以下划线 _ 开头。回复不超过 200 字结论摘要与纪要链接。

【看门狗】
每轮分发前运行 python3 /home/yuhaic/workspace/market-intelligence/result/China-market/tools/watchdog.py --timeout 20；退出码 2 即超时，写 ALERT-<run_id>-<时间戳>.md 并停止；恢复从最后完整轮继续。每轮完成写 _progress-<run_id>.json 心跳。

【持仓约束·硬约束】
持仓数量上限 10 只（A 股账户）；单只标的市值上限为组合总资产（含现金）的 33%。数量已达 10 只时禁止任何新增买入，若给买入建议须同时指定卖出标的并保证执行后数量仍 ≤10 只；任何加仓/买入建议须给出执行后权重，执行后单只权重 >33% 的建议无效。纪要「最终结论」与「可执行建议」须逐条核验并注明：持仓数量 X/10、单只最高权重 Y%（上限 33%）。
