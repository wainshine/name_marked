# 更新记录（CHANGELOG）

> 版本规则（用户钦定口径）：
> - 格式固定 `v主.次.补丁`（如 v1.0.0）
> - **同一天、同一大模块的更新，只允许动补丁位**（v1.0.0 → v1.0.1）
> - 次版本晋升（v1.0.x → v1.1.0）**仅当用户主动要求**
> - 主版本晋升（→ v2.0.0）**仅当项目推翻重来**；例外：v1.9.9 用尽才允许 v2.0.0
> - **git 提交/发版由用户本人执行**，Agent 只改代码与文档，绝不代提交

## v2.2.2 (2026-09-03)

### 自审计修复（主会话2代接手审计）

- **为什么改**：新主会话接手时做全仓自审计（代码↔文档一致性/bug/测试匹配性），发现 1 处健壮性缺口 + 2 处文档不一致 + 1 处测试覆盖缺口，集中修复。无算法/契约变更。
- **改了什么**：
  - `tests/anchor_check.py`：§2 契约格式/§4 一致性在 CSV 缺失时改为显式 FAIL + 提示（原为 `FileNotFoundError` traceback）——CSV 不入库（仅 pkl 入库），全新克隆环境此前会直接崩溃，与 HANDOVER §10"接手自检第一步"矛盾
  - `tests/test_guessers.py`：新增 `TestTrainLabels`（15 项）——`parse_id`/`decade_of`/`zodiac_of`/`season_of`/`solar_of` 边界测试，及 train/evaluate/namecore 三处重复常量的一致性断言（漂移兜底）；此前标签函数零测试，边界写错会静默污染 10 张表
  - 合规审查跟进：`_make_id` 虚构测试编码的地区码由真实区划码改为 `000000`，消除真实身份证号外观（全仓四类合规扫描其余零命中：隐私/违法/破解类/指定企业名）
  - `namecore/__init__.py` docstring：删除 v1 遗留的过期示例数字（0.99/0.86），改指向 README（审计原则 7）
  - `namecore/utils.py` docstring："三字名极少"→"个数为 0"，与 HANDOVER §3.3 及 train_stats（no_name_rows=0）对齐
  - HANDOVER：§4 坑清单新增第 11 条（train_stats `unique_given_names` 字段名误导说明）；§5/§10 注明 anchor_check 需训练机产物在场的前提；§5 测试计数改机制描述（原则 7）
  - README：测试节用例计数改机制描述
- **新契约是什么**：无新产物契约；文档/测试层面新增约定——train.py 标签函数改动必须同步过 `TestTrainLabels`
- **什么操作会破坏它**：改 train/evaluate 的类别常量或边界函数而不更新新测试；删 anchor_check 缺失提示断言
- **对端仓库条目引用**：无（不触及 3 个对外契约与 5 个函数签名，§9 不变量全部保持）

## v2.2.1 (2026-08-31)

### 文档体系统一改造（四仓统一标准 v2）

> 驱动：四仓统一文档矩阵（README 对外 / HANDOVER 对内 / CHANGELOG 版本史），目标"新会话只读 3~4 个文档 10 分钟接手"。

- **改了什么（文件级）**：
  - 新建 `docs/HANDOVER.md`（来龙去脉/血缘图/设计决策§3/坑清单/测试体系/编码规范/审计原则/路线图/不变量清单/自检清单）
  - 重写 `README.md`（按对外矩阵九要素；设计决策与踩坑史迁入 HANDOVER；新增对外契约清单——已与 name_nlp s12_moe.py/artifacts.py 实际消费代码核对）
  - 新建 `tests/anchor_check.py`（39 项只读锚点断言：产物存在/契约格式/接口锚点/行数一致性，全 PASS）
  - 改写本文件（版本规则头 + 五要素补齐 v1.0.0~v2.1.0 版本史）
- **自审修复（同日早些时候）**：holdout.txt 敏感衍生物删除 + evaluate.py 缺档指引 + 契约文档第 5 条（衍生物同规则）；README 版本号与 VERSION 不一致修复；export_gender_guess.py 依赖文件存在性检查
- **新契约是什么**：无新产物契约；文档契约=三件套各自独立存在（README/HANDOVER/CHANGELOG），锚点自检为接手与审计的入口
- **什么操作会破坏它**：删改 `tests/anchor_check.py` 锚点而不更新 HANDOVER §5；README 契约清单与对端消费脱节（改契约不走 requests 机制）
- **对端仓库条目引用**：name_nlp docs/CHANGELOG.md v1.3.1「四仓联合审计与契约化重构」

## v2.2.0 (2026-08-30)

### 为什么有这次改动（前因后果）

2026-08-30 四仓联合审计（name_nlp / name_marked / name_tag / NameMoe 四个会话交叉盘点依赖关系）发现本仓两处结构性问题，本版本集中修复：

1. **"只读产物"名不副实**：name_nlp s12 一直 `sys.path.insert` 后跨仓 `from namecore import guess_gender`（52 万次/轮回退调用）——本仓任何重构都会崩下游管线，且 `namemarked→namecore` 改名已真实断过一次。
2. **敏感训练数据无契约**:`有效数据.txt`（姓名+身份证式编码）是训练真值但无格式文档、无处置规则。

### 改动清单

- **新增 `scripts/export_gender_guess.py`**：把回退调用预算成文件契约 `namecore/tables/gender_guess.csv`（492 万行，name,boy_prob）。name_nlp s12 自同日起改读此文件，不再 import 本仓代码
  - **何时必须重导**：name_nlp 的 `NameC词频-修正.csv` 重建后（该表是回退表的键集来源）
  - 调用方式锁定：`guess_gender("王"+名)` 拼万能姓（与 name_nlp 历史调用逐字一致）
- **新增 `docs/有效数据-格式契约.md`**：编码位定义（7~14 位出生日期、17 位性别奇男偶女）+ 敏感数据处置规则（不留档/不备份/不入 git；重训需用户从移动硬盘拷贝，用完即删）
- **`train.py` 强化**：`parse_id` 对短编码（<17 位，含 15 位一代证）从静默丢弃改为显式计数并在 pass1 报告 ⚠（此前混入即无声丢样本）
- README：训练输入节注明敏感数据规则与契约文档指针

### 新契约是什么

- `gender_guess.csv`（`name,boy_prob`，utf-8-sig）：name_nlp s12 性别回退的唯一来源
- `docs/有效数据-格式契约.md`：训练输入的位定义与处置规则

### 什么操作会破坏它

- name_nlp NameC 修正表重建后不重跑 export_gender_guess.py（键集静默过期）
- 在本仓任何目录留存 `有效数据.txt` 副本（违反处置规则第 4 条）

### 对端联动

- name_nlp 侧对应改动见其 CHANGELOG v1.3.0「四仓联合审计与契约化重构」节（实际落地于 v1.3.1）
- name_nlp s10b 已不再读取 `yiname/iddata/有效数据.txt`（改用脱敏字集存档）；本仓 `train.py` 是该敏感文件的唯一剩余消费方

## v2.1.0 (2026-08-28)

### UniHan_Year 真数据导出

- **为什么改**：NameMoe `UniHan_Year` 表为假数据占位（其 v2.1.1 删除假数据生成器后未补真源），name_nlp 经 `docs/requests/name_marked-unihan-year.md` 提出需求，本仓 decade_char.csv 是唯一可信真源
- **改了什么**：新增 `scripts/export_unihan_year.py`（decade_char.csv 跨位置 p0~p3 按字求和 → `namecore/tables/unihan_year.csv`，6,736 字 × 6 年代 = 40,416 行）；README 增「下游导出」节
- **新契约**：`unihan_year.csv`（`UniHan,Year,TF`，utf-8-sig，字升序+字内年代升序，`1950s前→1950-01-01` 六档映射），格式冻结
- **什么操作会破坏它**：改动 decade_char.csv 列序/年代类定义；导出不跑或改排序编码而不通知 name_nlp
- **对端联动**：name_nlp 验收全过（6,736 字/40,416 行/抽样 2,000 字数值零误差），s12 子步骤⑦集成、s13 部署替换假数据；粒度裁定=十年（年度/日度数据稀疏，待新数据源）
- **注意**：2000s 列为插值估计（ChineseNames 字频外推），非真实样本计数，三处声明（README/脚本 docstring/requests 文档）

## v2.0.0 (2026-08-06)

### 推翻重构 + 全量重训

- **为什么改**：v1 效果差（性别 86.2% 为训练集自评、虚高不可复现；未知字/三字名/生僻字频繁"未知"；5 个 guesser + 5 个 build 脚本重复代码散落根目录）
- **改了什么**：
  - 架构：根目录 12 个模块删除 → `namecore/` 包（core 统一引擎 + 5 模型声明式）+ `scripts/`（train/evaluate/batch_guess）+ `tests/`
  - 算法：人名级+字符级双层贝叶斯、Lidstone 平滑、缺键跳过（修复"易烊千玺→女 0.877"的分母偏置 bug）、对数概率、三字名 p1/p2 回退、OpenCC 快速路径（34k→61k 行/s）
  - 训练：`scripts/train.py` 单管线两遍扫描 3327 万行（246s），按姓名 crc32 切 10% 真实 holdout（写出时 shuffle，修复小样本评估偏倚）
  - 评估：`scripts/evaluate.py` 真实 holdout 对账——性别 88.3%、年代精确 41.3%/±1 82.0%（v1 对照 87.6%/32.1%/70.1%，且 v1 含测试泄漏）
  - 分发：模型表 pkl 入库、CSV 不入库；core 加载「CSV 缺失时信任 pkl」（修复克隆即坏）
- **新契约**：`from namecore import guess_gender 等`（替代 v1 `from gender_guess import guess`，无兼容 shim，干净切换）；10 张模型表 `{model}_{char|name}.csv`
- **什么操作会破坏它**：重命名包/改 guess_* 签名（name_nlp 当时仍跨仓 import，v2.2.0 才改文件契约）；改位置键格式 `{字}_{p0..p3}`
- **对端联动**：无（此版本 name_nlp 尚未建立文件契约）
- 训练数据：`yiname/iddata/有效数据.txt`（3327 万行，敏感，处置规则见 v2.2.0 契约文档）

## v1.0.0 (2026-05)

### 初版

- **为什么做**：基于海量中文人名数据的姓名属性识别（性别/年代/星座/四季/节气）
- **做了什么**：5 个 guesser 模块（gender/decade/zodiac/season/solar）+ 5 个 build 脚本 + 批处理 CLI + 5 张频率表；算法参考 ngender 朴素贝叶斯，位置感知（p0~p3）字符级建模；2000s 经 ChineseNames 插值；训练数据 1930~1999 年真实登记样本
- **已知局限**（v2.0.0 推翻重来的原因）：无评估集切分（自评虚高）、低频键填充 (5,5) 致未知字判"未知"、无平滑、无三字名支持、重复代码
