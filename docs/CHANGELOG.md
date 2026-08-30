# 更新记录（CHANGELOG）

> 版本规则随 name_nlp：主版本.特性.修复。

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

### 对端联动

- name_nlp 侧对应改动见其 CHANGELOG v1.3.0「四仓联合审计与契约化重构」节
- name_nlp s10b 已不再读取 `yiname/iddata/有效数据.txt`（改用脱敏字集存档）；本仓 `train.py` 是该敏感文件的唯一剩余消费方
