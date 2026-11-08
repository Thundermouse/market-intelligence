---
name: 每日美国市场圆桌分析
schedule_id: 16454ee5
cron: "10 8 * * MON-FRI"
timezone: Asia/Shanghai
status: active
skill: investment-roundtable
created_at: 2026-11-05T01:30:44Z
# 恢复方式：用 Schedule 工具 create，cron / timezone 同上，message 取下方 Prompt 全文
---

## Prompt

执行美国市场每日圆桌分析（仅覆盖美股，不涉及中国市场）。调用 investment-roundtable 技能。

【K线数据准备·阶段0，必须最先执行】
读取持仓与观察列表，提取全部美股代码，调用 market-intelligence-fetch 技能确保多周期数据就绪：
- 对每个美股代码执行 ensure（市场=美股，周期=daily weekly monthly 15min 1h）
- 新股票自动全量初始化，已有股票自动补丁最新数据。所有周期返回 ✅ 后再启动子智能体。
- 各周期历史要求：15min 7个交易日、1h 3个月、日线 6个月、周线 3年、月线 10年。分钟级仅校验新鲜度（API历史上限约50天）。
- 数据落盘由 market-intelligence-db 技能管理，数据库位于 /home/yuhaic/workspace/market-intelligence/data/market_data.db。

【数据与文件】
- 持仓：/home/yuhaic/workspace/market-intelligence/result/US-market/holdings_us.csv；观察：watchlist.csv
- 场次目录：/home/yuhaic/workspace/market-intelligence/result/US-market/roundtable/us-daily/
- 取数（按优先级）：①iFinD 首选，拉取全部美股持仓、观察标的与 3 个指数（纳斯达克、标普500、费城半导体）的当日/最新价；②若 iFinD 不可用，运行 python3 /home/yuhaic/workspace/market-intelligence/result/US-market/tools/snapshot.py --session daily；③若脚本也不可用，用 WebSearch/WebFetch 从 Nasdaq、Yahoo Finance、Google Finance 等获取；取数结果写入 /home/yuhaic/workspace/market-intelligence/result/US-market/snapshots/<YYYYMMDD-HHMM>-daily.json，字段含 snapshot_id、collected_at、symbols{代码:{last,prev_close,pct,source}}。以最新快照为主要参照，可查阅同目录历史快照与历史纪要作趋势背景对照，但不得被历史结论锚定。
- 核算：python3 /home/yuhaic/workspace/market-intelligence/result/US-market/tools/positions.py --snapshot <快照文件> [--sell 代码:数量 ...]；数字须与脚本输出一致。

【信息源】
第一优先：wsj.com、bloomberg.com、高盛、花旗研究与观点；覆盖美联储政策、财报与行业动态。付费墙内容引用标题与公开摘要，注明来源与时间。

【外部聪明钱信号源（参考权重校准，不得作为当日买卖触发）】
①ARK Invest 每日交易 ②巴菲特 Berkshire 13F ③Tepper Appaloosa 13F ④Ackman Pershing Square 13F/公开信 ⑤Burry Scion 13F ⑥Druckenmiller Duquesne 13F ⑦佩洛西及国会议员交易披露（House Clerk PTR / Senate eFD）。引用须注明来源名称、披露日期与滞后天数（13F 约45天、国会PTR最长45天、ARK每日）；无新披露写"本期无新披露"。纪要必含「外部信号源引用与决策影响归因」章节。

【输出板块】
①美股指数环境（纳斯达克、标普500、费城半导体多空判断与关键位）②持仓分析（holdings_us.csv 中全部持仓，逐只给持有/加仓/减仓建议）③观察标的分析（买入机会与触发条件）④全球/美股新闻解读（来源、时间、影响标的）

【纪要】
保存至 /home/yuhaic/workspace/market-intelligence/result/US-market/roundtable/us-daily/，文件名 YYYY-MM-DD-daily-us.md（不带下划线），中间产物以下划线 _ 开头。纪要末尾追加「附录：独立全局审计（主智能体）」：对全篇自查，分价格与数字硬矛盾、规则与结论冲突、统计与流程记录矛盾、覆盖缺口四类，逐条编号，只标注不修改正文。回复不超过 200 字结论摘要、外部源归因要点与纪要链接。

【看门狗】
每轮分发前运行 python3 /home/yuhaic/workspace/market-intelligence/result/US-market/tools/watchdog.py --timeout 20；退出码 2 即超时，写 ALERT-<run_id>-<时间戳>.md 并停止；恢复从最后完整轮继续。每轮完成写 _progress-<run_id>.json 心跳。

【跨报告一致性自检】
会前读取同目录上一份盘前纪要与上一份 daily 纪要，核对持仓基数、权重、止损价位与操作方向；上份建议未成交须明写"上日建议未执行：基数维持 X 股"；同标的方向反转须给失效原因与新证据。
