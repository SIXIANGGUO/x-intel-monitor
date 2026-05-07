# X Intel Monitor

用 Hermes Agent 自动监控 X/Twitter 大佬推文的完整方案。基于 xgo.ing 免费 RSS，数据采集 → 内容过滤 → AI 文案生成 → Discord 推送，全自动运行。

## 架构

```
xgo.ing RSS (160个账号)
        ↓
  x_rss_fetcher.py   ← 并发抓取，48h窗口，ID去重
        ↓
 Hermes Agent        ← 选题判断 + 文案写作 + 格式输出
        ↓
   Discord           ← 推送格式化好的评论文+转发文
```

## 快速开始

### 1. 克隆

```bash
git clone https://github.com/SIXIANGGUO/x-intel-monitor.git
cd x-intel-monitor
```

### 2. 安装依赖

```bash
pip install feedparser
```

### 3. 运行采集

```bash
python x_rss_fetcher.py
```

输出：`x大佬-fetched-tweets.json`，包含最近48小时内所有账号的新推文。

### 4. 配置 Hermes Cron

把以下 cron prompt 配置到 Hermes，定时触发（建议每4小时）：

```markdown
## 身份

你是踩过坑的从业者，不是记者，不是翻译。
你不是在报道「大佬发了什么」——你是在讲「我走过类似的弯路，这个推文让我停下来想了什么」。

---

## 硬规则

- 标题：【账号名】一句话，不超过20字
- 链接放代码块外面
- 结尾不停「值得关注」，停在最后一个具体发现

---

## 选题标准

1. 反直觉观点 > 行业判断 > 真实困惑 > 技术辩论空间
2. 实用工具/产品体验 > 论文研究
3. 有具体参数/场景/案例 > 概念讨论
4. 纯产品发布、情绪碎碎念、链接分享 → 跳过

---

## 转发文案门槛

英文账号：400-800字，有实质内容才写，写不够400字直接跳过
中文账号：100-200字，有判断就说清楚

---

## 采集

先跑采集脚本读取数据，再逐条判断是否值得写：

有好内容才出文案，没内容输出：`暂无更新，下轮见 👋`

---

## 输出格式

每条文案结构：
```txt
【标题】

评论文正文（给 timeline 里的陌生人看，要有判断、有角度）

---

转发文正文（给点进原文的人看，要短、要有钩子）

https://x.com/xxx/status/123456
```

评论文和转发文全部放在 txt 代码块里，链接放代码块外面。
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `x_rss_fetcher.py` | 主力采集脚本，xgo.ing RSS 并发抓取，48h窗口，ID去重 |
| `requirements.txt` | Python 依赖 |

## 数据源

- **RSS 源**：[BestBlogs RSS Twitters OPML](https://github.com/ginobefun/BestBlogs/blob/main/BestBlogs_RSS_Twitters.opml)（160个AI圈账号）
- **RSS 服务**：xgo.ing（免费，无需 API Key）
- **覆盖账号**：模型厂官方（OpenAI/Anthropic/DeepSeek...）、核心人物（karpathy/sama/ylecun...）、产品/应用（huggingface/cursor_ai...）、Infra工具（Docker/GitHub/Vercel...）

## 两套方案对比

| | xgo.ing RSS（开源这套） | TikHub SDK |
|--|----------------------|-----------|
| 费用 | 免费 | 有（~¥0.001/请求） |
| 覆盖 | 原文推文，不含转发/QT | 全覆盖 |
| 配置 | 只需 Python + feedparser | 需注册 + API Key |
| 稳定性 | 高（纯HTTP） | 可能遇到429限速 |

实战建议：先用这套 RSS 方案跑起来。如果发现漏掉了转发类内容，再加 TikHub SDK 做补充。

## 开源地址

https://github.com/SIXIANGGUO/x-intel-monitor
