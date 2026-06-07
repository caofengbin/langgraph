# LangGraph 二次开发 & 内部 PyPI 发布流程

> 本方案仅针对 `libs/langgraph` 核心包的二次修改与独立发布。底层子包（checkpoint / prebuilt / sdk / cli）不做修改，直接依赖官方 PyPI 版本。

---

## 一、修改流程

### 1.1 修改包名和版本

编辑 `libs/langgraph/pyproject.toml`：

```toml
[project]
name = "mycorp-langgraph"          # 原: "langgraph"
version = "0.1.0"                  # 从自定版本开始，与官方隔离
```

> 外部依赖（`langgraph-checkpoint`、`langgraph-sdk`、`langgraph-prebuilt` 等）**不需要修改**，它们仍然从官方 PyPI 安装。

### 1.2 移除本地 uv.sources（打包前清理）

`libs/langgraph/pyproject.toml` 中的 `[tool.uv.sources]` 段是开发阶段的本地路径映射，**打包前应删除或注释掉**，否则发布后会导致依赖解析异常：

```toml
# 删除或注释掉这部分
# [tool.uv.sources]
# langgraph-prebuilt = { path = "../prebuilt", editable = true }
# langgraph-checkpoint = { path = "../checkpoint", editable = true }
# ...
```

### 1.3 二次修改代码

直接在 `libs/langgraph/langgraph/` 目录下完成你的定制化修改。开发测试时仍可保留 `[tool.uv.sources]` 来使用本地子包，打包前再清理。

---

## 二、打包流程

```bash
# 1. 进入核心包目录
cd libs/langgraph

# 2. 构建分发包
uv build

# 产物在 dist/ 目录下：
#   dist/mycorp_langgraph-0.1.0-py3-none-any.whl
#   dist/mycorp_langgraph-0.1.0.tar.gz
```

---

## 三、发布流程（到内部 PyPI）

```bash
# 1. 安装 twine
pip install twine

# 2. 配置 ~/.pypirc（一次性的）
cat >> ~/.pypirc <<EOF
[distutils]
index-servers =
    internal

[internal]
repository = https://your-internal-pypi.com/simple/
username = __token__
password = your-pypi-token
EOF

# 3. 上传（仅上传 langgraph 包）
cd libs/langgraph
twine upload -r internal dist/*
```

### 一键脚本

在项目根目录创建 `scripts/publish_langgraph.sh`：

```bash
#!/bin/bash
set -e
cd "$(dirname "$0")/../libs/langgraph"
REPO_URL="${REPO_URL:-https://your-internal-pypi.com/simple/}"

rm -rf dist
uv build
echo "=== Uploading to internal PyPI ==="
twine upload --repository-url "$REPO_URL" --username __token__ --password "${PYPI_TOKEN}" dist/*
echo "=== Done ==="
```

使用：

```bash
PYPI_TOKEN=your-token ./scripts/publish_langgraph.sh
```

---

## 四、完整工作流 Checklist

- [ ] 修改 `libs/langgraph/pyproject.toml`：`name`、`version`
- [ ] 打包前移除 `[tool.uv.sources]` 段
- [ ] 在 `libs/langgraph/langgraph/` 中完成定制开发
- [ ] 运行测试：`cd libs/langgraph && make test`
- [ ] 构建：`cd libs/langgraph && uv build`
- [ ] 上传到内部 PyPI：`twine upload -r internal dist/*`
- [ ] 消费方安装：`pip install --index-url <内部仓库> mycorp-langgraph`
