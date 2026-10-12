# name_marked 交接文档（HANDOVER）

> 给接手者：这篇讲"为什么"，用法看 [README.md](../README.md)，版本史看 [CHANGELOG.md](CHANGELOG.md)。

## 1. 项目来龙去脉

四仓协作定位：**识别算法库**（name_nlp=训练管线 / name_tag=LLM 标签体系 / NameMoe=MVP 产品最下游；裁定见 name_nlp HANDOVER §3.10-18）。

| 版本 | 时间 | 事件 | 证据 |
|---|---|---|---|
| v1.0.0 | 2026-05 | 初版：ngender 式朴素贝叶斯，5 个 guesser + 5 个 build 脚本散在根目录，字符级频率表 5 张 | git `628fe43`、v1 README（git 历史） |
| v2.0.0 | 2026-08-06 | 推翻重构：`namecore/` 包 + 统一 train.py 单管线 + 真实 holdout 评估体系；3327 万行全量重训；后更名 `namecore`（原 `namemarked`，与项目名撞车） | git `edc28d9` |
| v2.1.0 | 2026-08-28 | 按 name_nlp 需求导出 `unihan_year.csv`（NameMoe UniHan_Year 真数据源），验收全过 | name_nlp `docs/requests/name_marked-unihan-year.md` |
| v2.2.0 | 2026-08-30 | 四仓联合审计修复：新增 `export_gender_guess.py` 文件契约（消灭跨仓 import）+ 敏感数据格式契约 + train.py 短编码显式计数 | docs/CHANGELOG.md v2.2.0 |
| v2.2.1 | 2026-08-31 | 文档体系统一改造（本文档落地）+ holdout 敏感衍生物清理 | docs/CHANGELOG.md v2.2.1 |
| v2.2.2 | 2026-09-03 | 主会话2代自审计修复：anchor_check 缺 CSV 健壮化 + 训练标签函数边界测试 + 文档不一致清理 | docs/CHANGELOG.md v2.2.2 |
| v2.2.3 | 2026-09-03 | 安全与健壮性复查修复：curl 去 --insecure + pkl 固定 protocol 4 + batch_guess 原子写 + 插值兜底补文档 | docs/CHANGELOG.md v2.2.3 |
| v2.2.4 | 2026-10-12 | 跨仓对账登记（name_nlp 同步单 §三）+ 4 条隐含口径成文（§9 第 10-13 条）+ `export_gender_guess.py` 关系自证 + 锚点值改指 anchor_check | docs/CHANGELOG.md v2.2.4 |

关键背景：训练真值 `有效数据.txt` 为敏感个人数据，上游 yiname 的原始输入已丢失、**不可再生**；移动硬盘为唯一真源，本机不常驻（契约见 [有效数据-格式契约.md](有效数据-格式契约.md)）。

## 2. 数据血缘与依赖图

```
yiname/iddata/有效数据.txt (敏感, 3327万行, 移动硬盘为唯一真源, 本机不常驻)
  └─ scripts/train.py (两遍扫描)
       ├─ namecore/tables/{gender,decade,zodiac,season,solar}_{char,name}.csv  (10张模型表, 不入库)
       │    └─ 首次加载生成 .pkl 缓存 (入库分发, 无CSV时直接读pkl)
       ├─ data/holdout.txt (10%评估集, 敏感衍生物, 用完即删)
       └─ data/train_stats.json (规模/分布/行数登记)
GitHub ChineseNames ─字频比值→ decade_* 2000s列 (插值估计, 非真实样本)

【对外契约, 格式冻结】
decade_char.csv ─export_unihan_year.py→ unihan_year.csv ──▶ name_nlp s12⑦ ─▶ NameMoe UniHan_Year
gender_name.csv ───────────────────────────────────────────▶ name_nlp s12④ 直查
name_nlp NameC词频-修正.csv (键集, 反向输入只读)
  └─ export_gender_guess.py (回退预算：对 NameC 中直查表未覆盖的名预算；调用口径见 CONTRACTS 注 3)
       └─ gender_guess.csv ───────────────────────────────▶ name_nlp s12④ 回退
```

跨仓纪律：**只允许文件契约，禁止 import 对方代码**（2026-08-30 审计裁定）。
给本仓的改进需求走 name_nlp `docs/requests/` 机制；本仓消费 name_nlp 的 NameC 修正表为只读。

## 3. 核心设计决策（每一条都是踩坑换来的）

### 3.1 双层贝叶斯：人名级优先，字符级回退
v1 性别/年代只有字符级（稀有字名不准），星座/四季/节气只有人名级（频次<10 直接"未知"，覆盖率 94%）。
v2 统一为：人名出现 ≥10 次用人名级 `(n_c + β·π_c)/(N + β)`（β=3），否则字符级对数贝叶斯。
性别人名级覆盖 94% 的评估样本，是该模型准确率的主要来源。

### 3.2 Lidstone 平滑 + 未登录键跳过（v2.0.0 开发期真实 bug）
初版对缺键按计数 0 计 `log(α/denom)`——各类 denom 不同（男性样本多），**缺键系统性偏向样本少的类**，
`易烊千玺` 被判"女 0.877"。修复：缺键直接跳过（无信息），全部缺键回退先验分布。教训：**平滑时"未知"不能计 0，要跳过**。

### 3.3 三字名按 p1/p2 处理
曾设计 t1/t2/t3 独立位置键，训练后发现 3327 万行中**三字名个数为 0**（上游校验：单姓总长 2~3 字、复姓 3~4 字），
t 键全空。改为首字 `_p1` + 末字 `_p2` 复用双字统计。

### 3.4 holdout 按姓名 crc32 哈希切分 + 写出时 shuffle
v1 无评估集（README 的 86.2% 是训练集上算的，虚高且不可复现）。v2 按 `crc32(姓名)%10` 切 10%，
训练/评估严格分离。 shuffle 的由来：输入文件按编码前缀有序，未 shuffle 时 `--limit 30000` 评估性别 82.7% vs 全量 88.3%，
小样本严重有偏；写出前 `random.seed(42)+shuffle` 后子样与全量一致。

### 3.5 pkl 入库、CSV 不入库（用户裁定）
CSV 模型表大可审查但不入库；pkl 缓存作为分发格式入库。core 加载逻辑：CSV 存在且更新 → 重建 pkl；**CSV 缺失 → 信任 pkl**
（曾是克隆即坏的 P0 bug：旧逻辑要求 CSV 在场才读 pkl）。导出脚本（export_*）依赖 CSV，只能在训练机运行。
- **信任假设**：`pickle.load` 对入库 pkl 盲信（pickle 反序列化可执行任意代码），前提是本仓库与分发链路受控；**勿加载来路不明的 pkl**。
- **协议固定 4**（v2.2.3 起）：pkl 以 `protocol=4` 生成（Python 3.4+ 可读），不用 `HIGHEST_PROTOCOL`——避免高版本训练机产物低版本消费方读不了。

### 3.6 性别/年代先验用人口普查，不用训练集分布
训练集男性占 65%（特定登记样本构成），先验取七普 51.24/48.76——部署目标是全人群，不是训练集。
代价：在本训练集 holdout 上评估略有损失，换来全人群校准。

### 3.7 OpenCC 快速路径
每个 guess 原都过 OpenCC convert（占 40% 耗时）。改为先扫标准汉字表，无繁体字直接返回——
简体输入零开销，批处理 34k→61k 行/s（5 项全开）。

### 3.8 2000s 插值（数据止于 1999 的妥协）
上游校验限定出生年份 1930~1999，2000s 无真值。插值：每字 `count_1990s × r × 10/9`，
r = ChineseNames 该字 2000s/1990s 频次比（无比值时相邻年代趋势外推，限幅 0.3~3.0）；人名级行的 r 为名字各字比值的几何均值。
两个兜底分支（v2.2.3 补录，此前未文档化）：
① 该键有 90s 计数、但 ChineseNames 无比值且 80s 计数也为 0 时，r 取全局均值（全体字比值的均值；ChineseNames 下载失败/为空时全局兜底 0.7）；
② 该键 90s 计数为 0 但 80s>0 时，按 `count_1980s × 全局r × 0.5 × 10/9` 估算。
**2000s 列是估计值**，已在 README/导出脚本/name_nlp 需求文档三处声明。原始输入已丢，无法靠重跑上游修复，需新数据源。

### 3.9 文件契约替代跨仓 import（2026-08-30 审计）
name_nlp s12 曾 `sys.path.insert` 后 `from namecore import guess_gender`（52 万次/轮回退），
本仓重构即崩下游（`namemarked→namecore` 改名真实断过一次）。修复：把回退调用预算成
`gender_guess.csv`（name,boy_prob），name_nlp 改读文件，逐值对账 0 差异（见 name_nlp CHANGELOG v1.3.1）。
调用口径（拼万能姓 `guess_gender("王"+名)` 等 4 条隐含约定）**以 [name_nlp docs/CONTRACTS.md](../../name_nlp/docs/CONTRACTS.md#1-入向契约name_nlp-只读谁) §1 注 3 为准**，本仓不复述。

### 3.10 敏感数据处置（用户裁定 2026-08-30）
`有效数据.txt` 不留档/不备份/不入 git；重训需用户从移动硬盘拷回，用完即删；本机副本用户亲删。
holdout.txt 是同类衍生物，评估后即删（2026-08-30 已删现存副本，契约第 5 条）。
15 位编码（一代证）不作猜测性兼容，train.py 显式计数+⚠ 报告（此前静默丢弃）。

## 4. 已知坑与防坑清单

1. **平滑分母偏置**：新增特征键时，缺键必须跳过，不得按 0 计数（§3.2）
2. **样本构成偏差**：训练集男 65%、80 后 36%/90 后 8%——TF 计数反映该登记样本，非全国人口分布
3. **2000s 列是插值**：任何下游展示/统计都该知悉；勿当真实样本引用（§3.8）
4. **性别位规则**：编码第 17 位奇男偶女，仅经锚点抽样验证（强/建国→男，芳/秀英→女）；换数据源必须重验
5. **15 位编码**：train.py 显式丢弃并计数；看到 ⚠ 报告说明数据混入了一代证格式，查来源
6. **绝对路径耦合**：`export_gender_guess.py` 硬编码 name_nlp 输出路径（键集来源）；name_nlp 侧 `config.NAME_MARKED` 硬编码本仓路径——目录搬迁双断
7. **NameC 修正表重建 → 必须重跑 export_gender_guess.py**（键集过期 = 回退表静默缺名）
8. **BOM 字面量**：源码里不可见字符曾混入 `lstrip('﻿')`，一律用 `'\ufeff'` 转义
9. **评估集不常驻**：evaluate.py 需要先重训生成 holdout；别惊讶于"评估集不存在"报错，这是设计
10. **3 字名/4 字以上名**：训练数据无 3 字名（§3.3）；4 字以上名 pos_keys 返回空 → 输出"未知"（少数民族名，设计如此）
11. **train_stats 字段名误导**：`unique_given_names` 实为"频次≥10 的人名数"（恰等于 `*_name` 表行数），非全量唯一人名数——后者在 pass2 前已释放未登记。字段名为历史遗留，无消费方（anchor_check 只读 `table_rows`），改名收益低于留痕成本，特此说明

## 5. 测试体系说明

### 怎么跑

```bash
python tests/test_guessers.py    # 单元测试（unittest, ~0.2s）
python tests/anchor_check.py     # 锚点自检（只读断言, ~5s, 退出码 0/1）
python scripts/evaluate.py       # 全量评估（需 holdout 在场, ~100s/332万行）
```

> 前提：CSV 模型表/契约表不入库（仅 pkl 入库，§3.5），anchor_check 的 §2 契约格式/§4 一致性
> 依赖 CSV 在场，**需在训练机/产物齐备环境运行**；全新克隆环境下这些项会报产物缺失 FAIL，属预期。

### 测什么

- **单元测试**：utils（姓氏/位置键/汉字表）、5 模型典型姓名方向、模式一致性、先验和为 1、生僻字不回"未知"
- **锚点自检**（tests/anchor_check.py，改产物/契约后必过）：
  - 产物存在：10 pkl + 2 契约 CSV
  - 契约格式：unihan_year（BOM/表头/行数%6/字内升序/锚点值 `一` 两档年代）、gender_guess（BOM/表头/概率∈[0,1]/行数下限）
  - 接口锚点：`guess_gender('王伟')→男`、`('刘亦菲')→女`、`('張偉')→男`（繁体）、`guess_decade('张宇轩')→90s/00s`、5 模型返回形状
  - 一致性：train_stats.json 登记行数 == CSV 实际行数

  > **具体断言值（锚点、抽样下限等常量）不在本文硬编码，唯一出处是 [tests/anchor_check.py](../tests/anchor_check.py) §2/§3**——
  > 数字更替只改该脚本；本表只描述"测什么"。脚本 FAIL 时会打印期望值与实测值，足够定位。
- **评估基线**（v2.2.0 训练批，332 万真实 holdout，模型从未见过）：

  | 模型 | 准确率 | ±1 | 覆盖率 |
  |---|---|---|---|
  | 性别 | 88.3% | — | 100% |
  | 年代 | 41.3% | 82.0% | 100% |
  | 四季 | 29.8% | — | 100% |
  | 星座 | 10.8% | — | 100% |
  | 节气 | 5.5% | — | 100% |

  （随机基线：50%/16.7%/25%/8.3%/4.2%；星座/四季/节气信号本质弱，接近天花板）

### 什么算过

- 单元测试全 OK + 锚点自检全 PASS（退出码 0）——用例数随迭代增长，以实跑输出为准，不在文档硬编码
- 重训后 `evaluate.py` 全量对账上表：性别/年代波动 **±1pp 内**可接受，超出必须解释（数据变了？代码变了？）
- 契约文件改动后：anchor_check 全过 + 通知 name_nlp 侧验收

## 6. 编码规范

### 命名/目录
- `namecore/`：包。模型文件 `{属性}.py`，只含类别定义/先验/表名，逻辑全在 `core.py`
- `scripts/`：可执行脚本（train/evaluate/batch/export_*），入口 `if __name__ == '__main__'`
- 模型表命名 `{model}_{char|name}.csv`；导出契约小写下划线（unihan_year/gender_guess）
- `data/ref/` 参考数据（入库）；`data/holdout.txt` 敏感衍生物（不入库、不常驻）

### 写文件纪律
- **契约 CSV 一律 utf-8-sig**（带 BOM，下游 Excel/duckdb 兼容）；模型表 utf-8 无 BOM
- **原子写**：先写 `xxx.tmp` 再 `os.replace`（export_gender_guess.py 先例）
- 表头冻结，数值列不留空字符串
- 源码禁用不可见字符，BOM 用 `'\ufeff'` 转义

### 依赖纪律
- 零第三方强依赖（纯标准库）；OpenCC 可选，缺失时静默降级
- **跨仓只允许文件契约，禁止 import 对方代码**（2026-08-30 审计裁定）
- 新增三方库需用户批准

### 变更纪律
- 改**契约文件**（3 个对外契约任一）：先经 name_nlp `docs/requests/` 机制通知 → 改完过 `anchor_check.py` + `test_guessers.py` → CHANGELOG 五要素留痕
- name_nlp **NameC 修正表重建后**：必须重跑 `export_gender_guess.py`
- 改训练逻辑：重训 → `evaluate.py` 对账基线（§5）→ 更新 train_stats.json
- **git 提交/发版由用户本人执行**，Agent 只改代码与文档，绝不代提交

## 7. 审计原则（四仓统一文本，原文收录）

1. **测试为依据**：审计首先跑测试套件/锚点自检/基线对账，结论以测试输出为准
2. **只读实测其次**：测试未覆盖的，用只读实测补（查文件/curl 接口/跑只读脚本），不接受"文档这么说"
3. **AI 通读源码兜底**：前两者都不可及时才通读源码推断，且推断结论必须标注"未经测试/实测验证"
4. **交叉验证**：关键事实需两个以上独立来源印证才算成立
5. **对账基线**：关键指标有基线值，改动后逐行/逐值对账，差异必须解释
6. **留痕强制**：改代码必须同步写清前因后果（CHANGELOG 五要素）；不留痕的修改视为未完成
7. **不写会过期的数字**：文档中不硬编码会随代码变化的计数（阶段数/行数等），用机制描述替代
8. **金标回归**：评估类逻辑改动必须过金标集，指标进可追踪的记录体系

## 8. 路线图

| 优先级 | 事项 | 状态/成本 |
|---|---|---|
| P1 | 补 pytest 测试框架（现 unittest+锚点脚本，够用小仓规模） | 待评估，半天 |
| P1 | 2010s+ 真实人名数据源 → 重训替换 2000s 插值列 | 阻塞：需新数据源（上游原始输入已丢） |
| P2 | gender_guess 反向路径耦合收敛（export 脚本硬编码 name_nlp 输出路径） | 待四仓统一约定产物寻址方式 |
| ~~P2~~ | `~/.agents/skills/name-marked` skill 副本同步 v2 | **已关闭**（2026-09-03 用户手动删除该 skill，不再维护，无需同步） |
| P3 | 年度粒度字级年代表 | 暂缓：数据稀疏，待新数据源 |

## 9. 不变量清单（改动违反任一条 = 破坏下游）

> 本清单与 README「对外契约清单」同属对外契约。**对方侧的口径书写处是 [name_nlp docs/CONTRACTS.md](../../name_nlp/docs/CONTRACTS.md#1-入向契约name_nlp-只读谁) §1（I1-I3）+ 注 3**；
> 本文只登记"本仓必须保持什么"，不抄对方的理由与实现细节。对端三条集合关系由 name_nlp `run_docchecks` C6 守，本仓由 `export_gender_guess.py` 收尾的关系自证守。

1. `gender_name.csv` 列序：`given_name,female,male`（name_nlp 按位置读 row[0..2]）
2. `guess_gender(name, mode='auto') → (性别, 概率)` 2 元组签名
3. `guess_decade/zodiac/season/solar(name, mode='auto') → (标签, 概率, 分布)` 3 元组签名
4. `unihan_year.csv`：表头 `UniHan,Year,TF`、utf-8-sig、字 Unicode 升序+字内年代升序、年代映射 1950s前→1950-01-01 起 6 档
5. `gender_guess.csv`：表头 `name,boy_prob`、utf-8-sig、键集 = name_nlp NameC 修正表**全集 − `gender_name` 已覆盖名**
   （两表**互斥且互补**：交集必须为空，并集必须覆盖 NameC 键集；违反任一条 → 对方 s12 静默兜底 0.5）
6. 位置键格式 `{字}_{p0|p1|p2|p3}`；pos_keys：单字 p0、双字 p1/p2、叠字 p3、三字 p1+p2
7. 各模型 PRIORS 和为 1
8. 年代 6 类：`1950s前,1960s,1970s,1980s,1990s,2000s`（顺序即 ±1 评估的邻接定义）
9. 契约变更必须提前通知 name_nlp（docs/requests 机制），禁止静默改格式
10. `boy_prob` 以 `f"{boy:.4f}"` **四位小数**写出（少位即对下游静默降精度）
11. 空值/缺失键的约定值是 **0.5**（非 0）：对端 s12 对回退表外名取常数 0.5，本表若漏名即静默走该分支
12. 列名语义：`male/total → Boy`、`female/total → Girl`（性别比例取自直查表两列之和，不是全量人名计数）
13. 对方 s12 只按 **位置** 读 `gender_name.csv`（`row[0..2]`）、按 **列名** 读 `gender_guess.csv`（`name`/`boy_prob`），
    `unihan_year.csv` 按位置流式读 `row[0..2]`——即**本仓无需向对端提供任何"中文字段键名"**；本表只冻结列名与列序。
    真正的键名依赖在**对端内部**（`In.UNIHAN` 的 `_strokes`/`_pinyinA` 等由 name_nlp `shared/unihan.py` 消费），不在 I1-I3 契约内。

> 第 10-13 条此前双方都未成文（2026-10-12 对账补齐）。第 13 条**已按实测修订**：对方 [CONTRACTS.md](../../name_nlp/docs/CONTRACTS.md#1-入向契约name_nlp-只读谁) 注 3 第 4 条写
> "s12 取上游表中文字段键名（`_strokes`/`_pinyinA` 等）"，但该键名在四仓代码/产物中均不存在（四仓定向 grep 为空），
> 且 s12 的拼音/笔画由 name_nlp `shared/pinyin.py` + `shared/unihan.py` 本地计算、不读本仓——故该条**不适用本仓 I1-I3**，已回执对端。

## 10. 接手自检清单（10 分钟）

```bash
cd /Users/wainshine/newAI/name_marked
python3 tests/anchor_check.py        # 产物齐备时应全 PASS，退出码 0；全新克隆缺 CSV 时 §2/§4 报缺失属预期（§5）
python3 tests/test_guessers.py       # 应全 OK
python3 -c "from namecore import guess_gender; print(guess_gender('王伟'))"   # ('男', ~0.9)
head -2 namecore/tables/unihan_year.csv     # BOM + UniHan,Year,TF
head -2 namecore/tables/gender_guess.csv    # BOM + name,boy_prob
python3 -c "import json; s=json.load(open('data/train_stats.json')); print(s['train_rows'], s['male_ratio'])"  # 训练规模/性别比
```

全部正常 = 环境与产物完好。之后先读 §3 设计决策再动手；改任何 §9 不变量前，先看 §6 变更纪律。
