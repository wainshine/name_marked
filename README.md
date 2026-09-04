# Name Marked — 中文姓名属性识别系统 (v2.2.3)

> 基于双层贝叶斯的中文姓名属性识别算法库：性别、出生年代、星座、四季、节气。
> 定位：四仓协作中的**识别算法库**（name_nlp=训练管线 / name_tag=标签体系 / NameMoe=展示产品）。

设计原理、数据血缘、踩坑史见 **[docs/HANDOVER.md](docs/HANDOVER.md)**；版本史见 **[docs/CHANGELOG.md](docs/CHANGELOG.md)**。

## 快速开始

### Python API

```python
from namecore import guess_gender, guess_decade, guess_zodiac, guess_season, guess_solar

guess_gender('王伟')        # → ('男', 0.8999)
guess_decade('张宇轩')      # → ('2000s', 0.4810, {'1950s前':..., ...})
guess_zodiac('刘亦菲')      # → ('天秤座', 0.1853, {...})
guess_season('王伟')        # → ('秋', 0.2974, {...})
guess_solar('王伟')         # → ('寒露', 0.0554, {...})

guess_gender('張偉')        # 繁体自动转换 → ('男', 0.8999)
guess_gender('易烊千玺')    # 三字名 → ('男', 0.8112)
```

输入模式：`auto`/`namea`（完整姓名）、`namec`（纯名）、`named`/`namee`/`namef`（单字/首字/末字）。

### 批处理 CLI

```bash
python scripts/batch_guess.py names.txt                        # 5项全标
python scripts/batch_guess.py names.txt --models gender,decade # 指定模型
python scripts/batch_guess.py names.txt --mode namec           # 输入为纯名
python scripts/batch_guess.py names_gbk.txt --encoding gbk     # GBK编码
```

输入首行可声明 `namea`/`namec`（不区分大小写、兼容 BOM）。输出 CSV 为每项属性+概率两列。

## 功能模块

| 模型 | 类别数 | 算法 | 信号强度 |
|------|:--:|------|:--:|
| 性别 | 2 | 人名级+字符级双层贝叶斯 | 强 |
| 年代 | 6（1950s前~2000s） | 人名级+字符级双层贝叶斯 | 中 |
| 四季 | 4 | 同上 | 弱 |
| 星座 | 12 | 同上 | 弱 |
| 节气 | 24 | 同上 | 弱 |

任何输入都会给出预测：有统计用统计，无统计回退先验并给出诚实的低置信度。
星座/四季/节气与姓名本质关联极弱（随机基线 8.3%/25%/4.2%），准确率天花板低，价值在覆盖率与概率可信。

## 目录结构

```
name_marked/
├── namecore/                      # Python 包
│   ├── __init__.py                  #   暴露 guess_gender 等 5 个入口
│   ├── core.py                      #   贝叶斯引擎（平滑/对数概率/双层回退）
│   ├── utils.py                     #   姓氏加载、名提取、位置键、繁简转换
│   ├── gender.py / decade.py / zodiac.py / season.py / solar.py
│   └── tables/                      #   频率表（模型表不入库，pkl 缓存入库）+ 导出契约
├── scripts/
│   ├── train.py                     # 统一训练管线（单扫全数据，10表一次生成）
│   ├── evaluate.py                  # holdout 评估（需先重训生成评估集）
│   ├── batch_guess.py               # 批处理 CLI
│   ├── export_unihan_year.py        # 导出 unihan_year.csv
│   └── export_gender_guess.py       # 导出 gender_guess.csv
├── docs/
│   ├── HANDOVER.md                  # 交接文档（原理/决策/坑/测试体系/编码规范）
│   ├── CHANGELOG.md                 # 更新记录
│   └── 有效数据-格式契约.md          # 训练数据格式契约 + 敏感数据处置规则
├── data/
│   ├── ref/                         # 姓氏表、标准汉字表、ChineseNames缓存
│   ├── samples/                     # 测试样本
│   └── train_stats.json             # 训练统计（规模/分布/表行数）
└── tests/
    ├── test_guessers.py             # 单元测试（unittest）
    └── anchor_check.py              # 锚点自检（产物/契约/接口断言）
```

## 对外契约清单

以下产物被其他仓真实消费（已与对端代码核对），**格式冻结**，变更须先通知消费方：

| 产物 | 格式 | 消费方 |
|------|------|------|
| `namecore/tables/gender_name.csv` | `given_name,female,male`，utf-8 | name_nlp s12 性别直查 |
| `namecore/tables/gender_guess.csv` | `name,boy_prob`，utf-8-sig | name_nlp s12 性别回退 |
| `namecore/tables/unihan_year.csv` | `UniHan,Year,TF`，utf-8-sig，字升序+字内年代升序 | name_nlp s12 → NameMoe UniHan_Year |
| `guess_gender(name) → (性别, 概率)` | 函数签名 | 直接使用方（requests 文档冻结） |
| `guess_decade/zodiac/season/solar(name) → (标签, 概率, 分布)` | 函数签名 | 直接使用方 |

反向输入契约：`export_gender_guess.py` 以 name_nlp 的 `NameC词频-修正.csv` 为键集来源（文件只读）；
该表重建后必须重跑导出。

再生命令：`python scripts/export_unihan_year.py` / `python scripts/export_gender_guess.py`。

## 环境与依赖

| 依赖 | 用途 | 必需 |
|------|------|:--:|
| Python 3.x | 运行环境（零第三方强依赖） | ✓ |
| `data/ref/nameb.txt` | 姓氏表 | ✓ |
| `data/ref/《通用规范汉字表》（2013年）.txt` | 标准汉字表 | ✓ |
| [OpenCC](https://github.com/BYVoid/OpenCC) | 繁简转换 | 可选 |
| [ChineseNames](https://github.com/psychbruce/ChineseNames) | 2000s 插值 | 仅训练 |

模型以 pkl 缓存分发（入库），CSV 频率表不入库；首次加载 CSV 自动生成 pkl，无 CSV 时直接读 pkl。

## 训练与评估

```bash
python scripts/train.py --input /path/有效数据.txt   # 重训（约4分钟，产出模型表+评估集）
python scripts/evaluate.py                           # 评估（需评估集在场）
```

训练输入格式与**敏感数据处置规则**见 [docs/有效数据-格式契约.md](docs/有效数据-格式契约.md)：
原文件为敏感个人数据，不留档/不备份/不入 git；评估集（holdout）为同类衍生物，用完即删，不常驻本机。

## 如何跑测试

```bash
python tests/test_guessers.py    # 单元测试（utils/5模型/先验/模式/train 标签函数边界）
python tests/anchor_check.py     # 锚点自检（产物存在/契约格式/接口锚点/行数一致性）
```

两者全过 = 本仓完好。测试体系详见 [docs/HANDOVER.md](docs/HANDOVER.md)。

## License

训练数据与参考数据的版权归原始数据提供方所有。代码遵循 Apache 2.0 协议。

## 致谢

- [ngender](https://github.com/observerss/ngender) — 性别识别的朴素贝叶斯实现参考
- [ChineseNames](https://github.com/psychbruce/ChineseNames) — 年代模型 2000s 类别字频数据
- [OpenCC](https://github.com/BYVoid/OpenCC) — 繁简转换引擎
