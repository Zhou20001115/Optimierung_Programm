# VRPTW Optimization Project

这是一个基于 Python 和 Gurobi 的车辆路径问题（Vehicle Routing Problem）求解项目。
项目旨在解决两类核心问题：
1. **CVRP** (Capacitated Vehicle Routing Problem): 仅考虑车辆容量限制的路径规划。
2. **VRPTW** (Vehicle Routing Problem with Time Windows): 在 CVRP 基础上增加客户服务时间窗约束。

## 📂 项目结构 (Project Structure)

```text
E:/Optimierung_Programm/VRPTW
├── data/                   # 存放 Solomon 格式的算例文件 (如 r105.txt)
├── results/                # 存放批量实验的输出结果 (CSV 格式)
├── src/                    # 核心源代码目录
│   ├── data_loader.py      # 数据读取与预处理
│   ├── solver.py           # Gurobi 优化模型 (MIP)
│   ├── utils.py            # 结果解析、打印与可视化
│   └── __init__.py
├── main.py                 # 单个算例运行入口
├── batch_experiments.py    # 批量实验运行脚本
├── environment.yml         # Conda 环境配置文件
└── README.md               # 项目说明文档
```

## 🧩 模块功能详解

### 1. 数据加载 (`src/data_loader.py`)
负责读取 Solomon 标准格式的文本文件，并进行业务逻辑预处理。
- **Solomon 解析**: 自动跳过头部元数据，读取客户坐标、需求和时间窗。
- **数据预处理**: 
  - 包含需求量放大逻辑 (Demand * 5)。
  - 筛选前 N 个客户进行测试。
- **矩阵计算**:
  - 计算欧几里得距离矩阵。
  - 根据不同车型速度 (Type 1: 80km/h, Type 2: 60km/h) 计算行驶时间矩阵。

### 2. 核心求解器 (`src/solver.py`)
基于 `gurobipy` 构建混合整数规划 (MIP) 模型。
- **`solve_cvrp_model`**: 
  - 目标：最小化总运输成本。
  - 约束：车辆容量、流平衡、每个客户访问一次。
- **`solve_vrptw_model`**:
  - 目标：同上。
  - 新增约束：
    - **时间窗**: 车辆必须在 `[ReadyTime, DueDate]` 区间内开始服务。
    - **时间推进**: 考虑服务时间和行驶时间，确保时间逻辑连续。

### 3. 工具库 (`src/utils.py`)
- **结果打印**: 解析 Gurobi 的 `x` (路径) 和 `y` (时间) 变量，在控制台输出详细的车辆路线和载重情况。
- **可视化**: 使用 `matplotlib` 绘制仓库和客户的散点图，直观展示节点分布。

### 4. 运行入口
- **`main.py`**: 
  - 针对单个算例 (默认 `data/r105.txt`) 运行。
  - 依次求解 CVRP 和 VRPTW，并对比结果。
  - 展示可视化图表。
- **`batch_experiments.py`**:
  - 自动扫描 `data/` 目录下所有 `.txt` 文件。
  - 批量运行并记录 CVRP 与 VRPTW 的成本差异及求解时间。
  - 结果保存在 `results/batch_summary.csv`。

## 🛠️ 环境依赖 (Requirements)

本项目依赖以下 Python 库：
- **gurobipy**: 商业优化求解器 (需 License)。
- **pandas**: 数据处理。
- **numpy & scipy**: 矩阵运算与距离计算。
- **matplotlib**: 绘图。

安装命令示例:
```bash
pip install pandas numpy scipy matplotlib gurobipy
```

## 🚀 快速开始 (Usage)

### 运行单个测试
```bash
python main.py
```
程序将输出数据预览、CVRP 求解结果、VRPTW 求解结果，并弹窗显示地图。

### 运行批量实验
```bash
python batch_experiments.py
```
程序将处理 `data` 文件夹下的所有算例，并在 `results` 文件夹生成汇总 CSV。

## 📅 规划中 (Roadmap)
- [ ] **启发式算法模块**: 引入最近邻法 (Nearest Neighbor) 和 2-Opt 局部搜索，以应对大规模算例。
- [ ] **混合求解策略**: 结合启发式初解与 Gurobi 精确求解。
