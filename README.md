# Name Marked — 中文姓名属性识别系统

> v2.0.0（重构版）

基于双层贝叶斯算法，从中文姓名中识别性别、出生年代、星座、四季、节气五种属性。
3327 万条真实数据训练，332 万条真实 holdout 评估。

## 目录结构

```
name_marked/
├── namecore/                      # Python 包
│   ├── __init__.py                  #   暴露 guess_gender 等 5 个入口
│   ├── core.py                      #   贝叶斯引擎（平滑/对数概率/双层回退）
│   ├── utils.py                     #   姓氏加载、名提取、位置键、繁简转换
│   ├── gender.py                    #   性别（2类）
│   ├── decade.py                    #   年代（6类）
│   ├── zodiac.py                    #   星座（12类）
│   ├── season.py                    #   四季（4类）
│   ├── solar.py                     #   节气（24类）
│   └── tables/                      #   频率表（10个CSV + .pkl缓存）
│       ├── gender_char.csv          #     字符级：字-位置 → 性别计数
│       ├── gender_name.csv          #     人名级：名 → 性别计数
│       ├── decade_char.csv / decade_name.csv
│       ├── zodiac_char.csv / zodiac_name.csv
│       ├── season_char.csv / season_name.csv
│       └── solar_char.csv / solar_name.csv
├── scripts/
│   ├── train.py                     # 统一训练管线（单扫全数据，10表一次生成）
│   ├── evaluate.py                  # holdout 评估
│   └── batch_guess.py               # 批处理 CLI
├── data/
│   ├── ref/                         # 姓氏表、标准汉字表、ChineseNames缓存
│   ├── samples/                     # 测试样本
│   ├── holdout.txt                  # 评估集（训练时生成，不入库）
│   └── train_stats.json             # 训练统计
├── tests/test_guessers.py           # 单元测试（42项）
└── README.md / VERSION / LICENSE
```

## 依赖

| 依赖 | 用途 | 必需 |
|------|------|:--:|
| Python 3.x | 运行环境 | ✓ |
| `data/ref/nameb.txt` | 姓氏表 | ✓ |
| `data/ref/《通用规范汉字表》（2013年）.txt` | 标准汉字表 | ✓ |
| [OpenCC](https://github.com/BYVoid/OpenCC) | 繁简转换 | 可选 |
| [ChineseNames](https://github.com/psychbruce/ChineseNames) | 2000s插值 | 仅训练 |

零第三方强依赖。OpenCC 未安装时繁体输入原样处理（简体输入不受影响）。

## 快速开始

### Python API

```python
from namecore import guess_gender, guess_decade, guess_zodiac, guess_season, guess_solar

guess_gender('王伟')        # → ('男', 0.8999)
guess_decade('张宇轩')      # → ('2000s', 0.4810, {'1950s前':..., ...})
guess_zodiac('刘亦菲')      # → ('天秤座', 0.1853, {...})
guess_season('王伟')        # → ('秋', 0.2974, {...})
guess_solar('王伟')         # → ('寒露', 0.0554, {...})

# 支持繁体自动转换
guess_gender('張偉')        # → ('男', 0.8999)

# 支持三字名
guess_gender('易烊千玺')    # → ('男', 0.8112)
```

### 批处理 CLI

```bash
python scripts/batch_guess.py names.txt                        # 5项全标
python scripts/batch_guess.py names.txt --models gender,decade # 指定模型
python scripts/batch_guess.py names.txt --mode namec           # 输入为名
python scripts/batch_guess.py names_gbk.txt --encoding gbk     # GBK编码
python scripts/batch_guess.py names.txt --output result.csv    # 指定输出
```

输入首行可声明 `namea`（完整姓名）或 `namec`（名），不区分大小写、兼容 BOM。

**输出格式：**

```csv
input,性别,性别概率,年代,年代概率,星座,星座概率,四季,四季概率,节气,节气概率
建国,男,0.9878,1970s,0.3291,天秤座,0.1206,秋,0.3103,秋分,0.0626
```

## 核心算法

### 双层贝叶斯

**人名级**（名在训练集中出现 ≥10 次时启用）：

```
P(class|name) = (n_class + β·π_class) / (N + β)      β=3 先验伪计数
```

**字符级**（人名级未命中时回退，位置感知）：

```
log P(class|name) = log π_class + Σ log P(key_i|class)
P(key|class) 用 Lidstone 平滑 (α=1)，未登录键直接跳过（不带偏见）
```

任何输入都会给出预测：有统计用统计，无统计回退先验并给出诚实的低置信度。

### 位置编码

| 后缀 | 含义 | 示例 |
|------|------|------|
| `_p0` | 单字名 | 王**伟** → `伟_p0` |
| `_p1` | 双字名第1字 | 李**建**国 → `建_p1` |
| `_p2` | 双字名第2字 | 李建**国** → `国_p2` |
| `_p3` | 叠字名 | 黄婷**婷** → `婷_p3` |

三字名按首字 `_p1` + 末字 `_p2` 处理（训练数据中三字名极少，不单独建模）。

### 输入模式

| mode | 含义 | 示例 | 支持模型 |
|------|------|------|:--:|
| `auto`/`namea` | 完整姓名，自动提取名 | `王伟` → 名=`伟` | 全部 |
| `namec` | 名（已去除姓氏） | `建国` | 全部 |
| `named` | 单字名 | `伟` → `伟_p0` | 全部 |
| `namee` | 双字名首字 | `建` → `建_p1` | 全部 |
| `namef` | 双字名末字 | `国` → `国_p2` | 全部 |

## 模型表现

332 万条真实 holdout（训练时按姓名哈希切分，模型从未见过）：

| 模型 | 类别数 | 准确率 | ±1准确率 | 覆盖率 | 信号 |
|------|:--:|--:|--:|--:|:--:|
| 性别 | 2 | **88.3%** | — | 100% | 强 |
| 年代 | 6 | **41.3%** | **82.0%** | 100% | 中 |
| 四季 | 4 | 29.8% | — | 100% | 弱 |
| 星座 | 12 | 10.8% | — | 100% | 弱 |
| 节气 | 24 | 5.5% | — | 100% | 弱 |

与 v1 对比（同一份 holdout；注意 v1 训练时未切分 holdout，测试数据已被其见过，数字偏高）：

| 模型 | v1 准确率 | v2 准确率 | v1 ±1 | v2 ±1 |
|------|--:|--:|--:|--:|
| 性别 | 87.6% | **88.3%** | — | — |
| 年代 | 32.1% | **41.3%** | 70.1% | **82.0%** |
| 四季 | 29.3% | **29.8%** | — | — |
| 星座 | 11.9%* | 10.8% | — | — |
| 节气 | 7.0%* | 5.5% | — | — |

\* v1 的星座/节气表包含测试集人名（数据泄漏），真实泛化能力低于所示数字；
星座/四季/节气三类属性与姓名本质关联极弱，准确率天花板接近随机基线（8.3%/25%/4.2%），v2 的价值在于 100% 覆盖率 + 概率诚实可信。

## 训练

```bash
python scripts/train.py --input /path/有效数据.txt
# 可选: --holdout 0.1 --min-name-freq 10 --encoding gbk
```

输入格式：`姓名,属性编码`（GBK），编码内含出生日期与性别信息。
两遍扫描：pass1 数据QA + 字符级计数 + holdout切分；pass2 人名级计数。
3327 万行训练约 4 分钟，产出 10 张频率表 + `data/holdout.txt` + `data/train_stats.json`。

### 2000s 插值

训练数据止于 1999 年。2000s 类别按字插值：

1. 从 [ChineseNames](https://github.com/psychbruce/ChineseNames) 取每字 `r = 2000s频次/1990s频次`
2. 有人名/字比值时用几何均值，无比值时用相邻年代趋势外推（限幅 0.3–3.0）
3. `count_2000s = count_1990s × r × (10/9)`（10/9 修正 2000–2008 仅覆盖 9 年）

## 评估

```bash
python scripts/evaluate.py                  # 评估当前模型
python scripts/evaluate.py --limit 100000   # 限制样本数
```

## 运行测试

```bash
python tests/test_guessers.py   # 42 项测试
```

## 性能

| 场景 | 速度 |
|------|------|
| 全部 5 项 | 61,000 行/s |
| 模型加载 | <0.1s（.pkl 缓存） |

测试环境：Mac, Python 3.14, 30 万行输入。

## v1 → v2 迁移

- 旧 API `from gender_guess import guess` → `from namecore import guess_gender`
- 旧 CLI `python batch_guess.py` → `python scripts/batch_guess.py`（参数不变）
- 旧构建脚本 `build_*.py` → `python scripts/train.py`（单脚本全量）

## License

训练数据与参考数据的版权归原始数据提供方所有。代码遵循 Apache 2.0 协议。

## 致谢

- [ngender](https://github.com/observerss/ngender) — 性别识别的朴素贝叶斯实现参考
- [ChineseNames](https://github.com/psychbruce/ChineseNames) — 年代模型 2000s 类别字频数据
- [OpenCC](https://github.com/BYVoid/OpenCC) — 繁简转换引擎
