# Kimi 任务书：Dashboard 添加扫描动画

## 背景

当前 Dashboard 启动时瞬间加载 `/demo` 数据，给人感觉是"提前写死的"，不像真实扫描。

**目标：** 添加一个模拟扫描过程的动画，让 Demo 看起来像真实分析。

## 具体需求

### 需求：Demo 数据加载时显示扫描动画

当 Dashboard 加载 demo 数据时，不要立刻显示结果，而是：

**阶段 1：提交动画（1-2 秒）**
- 显示 "🚀 Analysis submitted..." 提示
- 任务卡片出现，状态为 ⏳ PENDING，进度 0%

**阶段 2：扫描中动画（3-5 秒）**
- 任务卡片状态变为 🔍 SCANNING
- 进度条从 0% 逐步增长到 100%（用 st.progress 或自定义动画）
- 每隔 0.5-1 秒更新一次进度，显示不同阶段文字：
  - "Cloning repository..."
  - "Running static analysis..."
  - "Running semantic analysis..."
  - "Running verification..."
  - "Generating report..."

**阶段 3：完成**
- 状态变为 ✅ COMPLETED
- 进度 100%
- 自动选中该任务，Report Preview 显示漏洞详情

### 技术实现建议

用 `st.empty()` + `time.sleep()` 或 `st.spinner()` 实现动画效果：

```python
# 伪代码
placeholder = st.empty()
for progress in range(0, 101, 5):
    placeholder.progress(progress)
    time.sleep(0.1)
placeholder.success("Analysis complete!")
```

或者用 `st.status()` 组件：
```python
with st.status("Analyzing repository...", expanded=True) as status:
    st.write("Cloning repository...")
    time.sleep(1)
    st.write("Running static analysis...")
    time.sleep(1)
    st.write("Running semantic analysis...")
    time.sleep(1)
    status.update(label="Analysis complete!", state="complete")
```

### 注意事项

1. 动画只在首次加载 demo 数据时触发一次，刷新页面不要重复播放
2. 用 `st.session_state` 控制：如果 `demo_animation_done == True`，跳过动画直接显示结果
3. 动画总时长控制在 4-6 秒（太长评委不耐烦，太短不真实）
4. 动画结束后自动选中 demo 任务并显示 Report Preview
5. 不影响正常的任务提交流程

## 交付物

修改后的 dashboard.py（直接替换即可）。

## 验证标准

1. `docker compose up --build -d dashboard` 构建成功
2. 打开 `http://localhost:8501` 能看到扫描动画
3. 动画结束后自动显示漏洞详情
4. 刷新页面不再重复动画（直接显示结果）
