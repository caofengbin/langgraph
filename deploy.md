# LangGraph 二次开发 & 内部 PyPI 发布流程

## 背景

本方案涉及两个包的修改：

| 目录 | 内部 PyPI 包名 | 修改内容 |
|------|---------------|---------|
| `libs/checkpoint` | `fitest-langgraph-checkpoint`（重命名） | 修改 `langgraph/checkpoint/` 和 `langgraph/store/` 下代码 |
| `libs/langgraph` | `fitest-langgraph`（重命名） | 修改核心业务逻辑 |

> **注意**：内部 PyPI 仓库不允许与官方 PyPI 包同名，因此两个包均需重命名（加 `fitest-` 前缀），从源头避免冲突。Python import 路径（`from langgraph.checkpoint...`）不受包名影响。

---

## 版本策略

### 使用 PEP 440 本地版本号（`+` 后缀）

```toml
[project]
name = "fitest-langgraph-checkpoint"    # 重命名，与官方隔离
version = "4.1.1"               # 基于官方 4.1.1 的定制版
```


### 依赖端钉死版本

```toml
"fitest-langgraph-checkpoint==4.1.1"
```

使用 `==` 精确匹配，无论官方发什么版本，pip 都只会安装你的 `4.1.1`。

> **注意**：当你决定基于新版官方 checkpoint 重新定制时，需要同步更新两端——checkpoint 的 `name` 和 `version`，以及 langgraph 的钉死依赖。

---

## 一、修改 libs/checkpoint

### 1.1 修改代码

直接在 `libs/checkpoint/langgraph/checkpoint/` 和 `libs/checkpoint/langgraph/store/` 中完成定制修改。

### 1.2 设置版本号（PEP 440 本地版本号）

编辑 `libs/checkpoint/pyproject.toml`：

```toml
[project]
name = "fitest-langgraph-checkpoint"  # 重命名，与官方隔离
version = "4.1.1"             # "+" 后为自定义标识，不占用正常版本号
```

> 版本号格式：`<官方版本>+<自定义标识>`，如 `4.1.1+mycorp`、`4.1.1+company1`。
> 这样既高于官方 `4.1.1`，又低于 `4.1.2`，即使官方发版也不会覆盖你的定制版。

### 1.3 构建与发布

```bash
cd libs/checkpoint

# 打包前清除 [tool.uv.sources]
# （只保留发布版所需的依赖声明）

uv build
twine upload -r internal dist/*
```

> 关于 twine 的配置和内部仓库地址说明，参见下文「附录：发布到内部 PyPI 仓库」。

---

## 二、修改 libs/langgraph

### 2.1 修改代码

在 `libs/langgraph/langgraph/` 中完成定制修改。

### 2.2 修改 pyproject.toml

```toml
[project]
name = "fitest-langgraph"
version = "1.2.5"

# ⚠️ 内部发布的包用重命名后的名字，官方包保持原名
dependencies = [
    "langchain-core>=1.4.0,<2",
    "fitest-langgraph-checkpoint==4.1.1",   # 内部重命名版，钉死版本
    "langgraph-sdk>=0.4.2,<0.5.0",                 # 官方版本
    "langgraph-prebuilt>=1.1.0,<1.2.0",            # 官方版本
    "xxhash>=3.5.0",
    "pydantic>=2.7.4",
]
```

### 2.3 打包前清理 uv.sources

删除或注释掉 `[tool.uv.sources]` 段：

```toml
# 以下内容全部删除
# [tool.uv.sources]
# langgraph-prebuilt = { path = "../prebuilt", editable = true }
# fitest-langgraph-checkpoint = { path = "../checkpoint", editable = true }
# ...
```

### 2.4 构建与发布

```bash
cd libs/langgraph
uv build
twine upload -r internal dist/*
```

---

## 三、发布顺序

必须按照依赖自底向上的顺序发布：

1. **先发布** `libs/checkpoint` → 内部 PyPI 上 `fitest-langgraph-checkpoint` 发布 `4.1.1`
2. **再发布** `libs/langgraph` → 内部 PyPI 上 `fitest-langgraph` 发布 `1.2.5`

---

## 附录：发布到内部 PyPI 仓库

### 前提条件

- 已搭建或获取到内部 PyPI 仓库地址（如 `https://pypi.internal.company.com/simple/`）
- 已获取该仓库的认证凭据（用户名/密码 或 API Token）

常见的内部 PyPI 方案：**JFrog Artifactory**、**DevPI**、**pypiserver**、**Gemfury**、**AWS CodeArtifact** 等，upload 地址格式可能略有不同，以下通用。

### 配置 twine

#### 方式一：通过 `~/.pypirc` 配置

```ini
# ~/.pypirc
[distutils]
index-servers =
    internal

[internal]
repository = https://pypi.internal.company.com/simple/
username = __token__
password = your-pypi-token-here
```

配置后即可使用简化命令：

```bash
twine upload -r internal dist/*
```

#### 方式二：命令行直接指定（无需配置文件）

```bash
twine upload \
    --repository-url https://pypi.internal.company.com/simple/ \
    --username __token__ \
    --password your-pypi-token-here \
    dist/*
```

> `__token__` 是大多数内部 PyPI 通用的 Token 认证用户名，如果使用用户名/密码认证则替换为实际用户名。

### twine 常见问题

**Q: twine upload 后报 401/403 未认证？**
A: 检查 `~/.pypirc` 中的用户名和密码是否正确；确认 Token 未过期。

**Q: 报错 "410 Gone" 或 "405 Method Not Allowed"？**
A: 检查 `repository` URL 是否正确。部分仓库的 upload 地址是 `https://.../legacy/` 而不是 `/simple/`。

**Q: 发布后消费方安装不到最新版本？**
A: 内部 PyPI 可能有缓存延迟，等待 1-2 分钟或手动刷新索引。

### 替代方案：不使用 twine

如果环境受限没有 twine，也可以用 `curl` 直接上传：

```bash
# 需先执行 uv build 生成 dist/ 产物
curl -X POST https://pypi.internal.company.com/legacy/ \
    -F "content=@dist/fitest_langgraph_checkpoint-4.1.1+mycorp-py3-none-any.whl" \
    -u "__token__:your-pypi-token"
```

或通过 `hatch publish`：

```bash
cd libs/checkpoint
hatch build
hatch publish -r https://pypi.internal.company.com/simple/ -u __token__ -a your-token
```

---

## 消费端配置

使用者需将内部 PyPI 设为**优先索引**：

### pip

```ini
# ~/.config/pip/pip.conf 或 pip.ini
[global]
index-url = https://your-internal-pypi.com/simple/
extra-index-url = https://pypi.org/simple/
```

或单次命令：

```bash
pip install --index-url https://your-internal-pypi.com/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    fitest-langgraph
```

### uv

#### 方式一：单次命令安装

```bash
# --index 设内部源优先，--extra-index-url 设官方源兜底
uv pip install \
    --index-url https://your-internal-pypi.com/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    fitest-langgraph
```

#### 方式二：项目级配置（推荐）

在项目的 `pyproject.toml` 中声明索引优先级：

```toml
# pyproject.toml
[[tool.uv.index]]
name = "internal"
url = "https://your-internal-pypi.com/simple/"
priority = "explicit"       # 只为显式指定的内部包查找此源

[[tool.uv.index]]
name = "pypi"
url = "https://pypi.org/simple/"
default = true              # 默认源，未指定源的包从这里装
```

然后正常安装：

```bash
uv add fitest-langgraph
# 或
uv pip install fitest-langgraph
```

#### 方式三：全局配置

在 `~/.config/uv/uv.toml`（macOS/Linux）或 `%APPDATA%\uv\uv.toml`（Windows）中配置：

```toml
# ~/.config/uv/uv.toml
[[index]]
name = "internal"
url = "https://your-internal-pypi.com/simple/"
priority = "explicit"

[[index]]
name = "pypi"
url = "https://pypi.org/simple/"
default = true
```

配置后所有项目默认生效：

```bash
uv pip install fitest-langgraph
```

> **提示**：`priority = "explicit"` 意味着只有当包名在 `[[tool.uv.index]]` 中被显式指定时才去内部源查找，避免所有包都走内部源。如果希望内部源作为默认首选，可改为 `priority = "primary"`。

---

## 五、开发阶段本地测试

发布前，在本地验证修改后的 checkpoint + langgraph 是否正常工作：

```bash
# 在项目根目录
uv venv
source .venv/bin/activate

# 先安装本地修改后的 checkpoint（editable 模式）
uv pip install -e libs/checkpoint

# 再安装本地修改后的 langgraph（editable 模式）
# 此时需保留 [tool.uv.sources] 让 uv 解析本地路径
# 或直接手动指定
uv pip install -e libs/langgraph

# 运行测试
cd libs/langgraph && make test
```

---

## 六、完整工作流 Checklist

- [ ] 完成 `libs/checkpoint` 中 `checkpoint/` 和 `store/` 的代码修改
- [ ] 修改 `libs/checkpoint/pyproject.toml`（`name` 改为 `fitest-langgraph-checkpoint`，递增 `version`）
- [ ] 构建并发布 `libs/checkpoint` 到内部 PyPI
- [ ] 完成 `libs/langgraph` 的代码修改
- [ ] 修改 `libs/langgraph/pyproject.toml`（`name`、`version`、清理 `uv.sources`）
- [ ] 构建并发布 `libs/langgraph` 到内部 PyPI
- [ ] 配置消费端的 pip/uv 索引优先级
- [ ] 验证端到端安装：`pip install fitest-langgraph`
