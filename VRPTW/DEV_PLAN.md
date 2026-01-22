# 学习与开发计划 (Roadmap)

为了防止会话结束后丢失进度，我将我们讨论的后续计划记录在此。
下次开始工作时，请直接让我“读取 DEV_PLAN.md”，我就能立刻跟上进度。

## ✅ 第一阶段：故障排除 (IIS) - [已完成]
- [x] 学习 `model.computeIIS()`。
- [x] 实现 `diagnose_infeasibility` 工具函数 (src/utils.py)。
- [x] 创建 `test_iis.py` 并成功复现无解冲突。

## 🚀 第二阶段：懒约束 (Lazy Constraints) - [下一步]
**目标**：不一次性添加所有子回路消除约束，而是按需添加，提升求解效率。

### 待办事项：
1. **创建求解函数**:
   - 在 `src/solver.py` 中添加 `solve_cvrp_lazy`。
   - 初始只包含 `x` 变量和度数约束 (Degree Constraints)。
   - 启用参数: `model.Params.LazyConstraints = 1`。

2. **实现回调逻辑 (Callback)**:
   - 编写 `subtour_callback(model, where)`。
   - 监听 `GRB.Callback.MIPSOL` (发现整数解时)。
   - 使用 DFS/BFS 算法寻找解中的连通分量。
   - 如果发现子回路 (Subtour)，使用 `model.cbLazy()` 添加切断约束。

3. **验证**:
   - 比较 Lazy 模式与现有 MTZ/Flow 模式的求解时间。

## 📅 第三阶段：启发式算法 (Heuristics)
**目标**：在大规模算例下快速找到满意解，并辅助 Gurobi 求解。

### 待办事项：
1. **构造启发式**: 实现最近邻法 (Nearest Neighbor)。
2. **改进启发式**: 实现 2-Opt 局部搜索。
3. **交互**: 使用 `model.cbSetSolution()` 在回调中将启发式解注入 Gurobi。
