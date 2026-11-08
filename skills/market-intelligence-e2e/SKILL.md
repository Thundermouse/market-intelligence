---
name: market-intelligence-e2e
description: 行情数据管线端到端（E2E）测试 Skill。针对完整功能做全流程验证，不是单元测试。覆盖 A股/港股/美股的拉取→存储→查询→新鲜度→就绪校验全链路，以及时段过滤、周/月线聚合一致性、ensure 三分支（跳过/补丁/初始化）。Use when 需要对行情数据管线做完整功能验证、回归测试、或验证新接入的市场/周期是否跑通全流程。不适用于隔离的单元测试或代码格式检查。
---

# 行情数据管线端到端测试 Skill

## 定位

**这是端到端（E2E）测试，不是单元测试。**

- ✅ 验证**完整功能**：从数据源拉取 → 写入 DB → 查询 → 新鲜度校验 → ensure 自动补全
- ✅ 依赖**真实网络与真实 API**（akshare），不 mock 数据源
- ✅ 断言**业务结果**（数据量、时段边界、聚合一致性、分支走向），不 mock 内部函数
- ❌ 不做隔离的单元测试（不测单个函数的纯逻辑）
- ❌ 不做代码格式检查（不引入 ruff / black / pre-commit 等保护工具）

## 测试文件

- 位置：`/home/yuhaic/workspace/market-intelligence/tests/e2e/test_pipeline.py`
- 标的：A股 `600519`（贵州茅台）、美股 `AAPL`（苹果）、港股 `00700`（腾讯）
- 周期：`daily / weekly / monthly / 15min / 1h`

## 运行方式

### 方式一：直接运行（带彩色输出与汇总）

```bash
cd /home/yuhaic/workspace/market-intelligence
python3 tests/e2e/test_pipeline.py
```

退出码：`0` = 全部通过，`1` = 有失败项。

### 方式二：pytest

```bash
cd /home/yuhaic/workspace/market-intelligence
pytest tests/e2e/test_pipeline.py -v
```

## 测试覆盖范围

### 1. 三市场全流程（`test_market_full_pipeline`）

对 A股 / 美股 / 港股 各跑一遍：
1. 拉取全周期数据（daily/weekly/monthly/15min/1h）
2. 查询验证：每个周期都能查到非空数据
3. 新鲜度校验：daily ≤ 2天，weekly ≤ 8天，monthly ≤ 35天
4. 就绪校验：`check_period` 全部返回 OK

### 2. 美股时段过滤（`test_us_session_filter`）

验证 `1h` / `15min` 数据中不含盘前盘后 bar：
- 将北京时间转换为纽约时间（`zoneinfo` 自动处理 DST/EST）
- 检查所有 bar 落在 9:30–16:00 ET 之间

### 3. A股时段校验（`test_a_share_session`）

验证 `1h` / `15min` bar 落在 A股交易时段：
- 上午 9:30–11:30，下午 13:00–15:00

### 4. 周线聚合一致性（`test_weekly_aggregation`）

验证周线 OHLC 等于当周日线聚合：
- 取最新一周周线的 `week_start`
- 推算该周周一~周五
- 取该周内日线，聚合得到 O/H/L/C
- 与周线对比，误差 < 0.01

### 5. ensure 三分支（`test_ensure_branches`）

验证 `ensure_one` 的三种分支走向：
1. **已有达标 → 跳过**：新鲜数据，msg 含「已有」
2. **过期数据 → 补丁**：插入两条过期日线（covered>0），msg 含「补丁」
3. **无数据 → 初始化**：删除全部日线，msg 含「初始化」

## 如何新增 E2E 测试

1. 在 `tests/e2e/` 下新建或扩展测试文件
2. 测试必须走**真实管线**（调用 `fetch_one` / `ensure_one` / `query_*`），不要 mock
3. 断言聚焦**业务可观测结果**：数据行数、日期范围、时段边界、聚合一致性
4. 如需构造边界场景（如过期数据），直接操作 DB（DELETE/INSERT），不要打补丁函数

## 注意事项

- 测试会真实写入 `/home/yuhaic/workspace/market-intelligence/data/market_data.db`，运行前确认 DB 可写
- `test_ensure_branches` 会删除并重建 A股 `600519` 的日线数据，属于测试副作用（最终状态是已初始化的最新数据）
- 分钟级数据（15min/1h）受 akshare 历史上限（约 50 天）限制，仅校验新鲜度
- 美股代码直接用 `AAPL`，akshare 内部会加 `105.` 前缀
- 全量跑一次约 2–5 分钟（取决于网络），建议在数据更新后或修改管线代码后运行
