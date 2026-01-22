# src/utils.py
import gurobipy as gp
from gurobipy import GRB
import matplotlib.pyplot as plt
import os


def get_and_print_results(model, x, nodes, customers, vehicle_types):
    """
    解析 Gurobi 的解，提取路径并打印结果
    """
    # 核心逻辑检查：是否有可行解
    if model.SolCount > 0:
        # 初始化结果字典，用于后续可能的 Excel 导出或画图
        results = {
            "obj_val": model.ObjVal,
            "routes": {},
            "vehicle_counts": {}
        }

        # 打印总体求解信息
        print("\n" + "=" * 60)
        if model.status == GRB.OPTIMAL:
            print(f"✅ 状态: 已找到全球最优解")
        else:
            print(f"⚠️ 状态: 找到可行解 (当前 Gap: {model.MIPGap:.2%})")

        print(f"💰 最小总成本: {model.ObjVal:.2f} Euro")
        print("=" * 60)

        # 遍历车型 k
        for k in vehicle_types:
            # 1. 识别从仓库 (0) 出发的边
            start_nodes = [j for j in customers if x[0, j, k].X > 0.5]
            num_vehicles = len(start_nodes)
            results["vehicle_counts"][k] = num_vehicles

            print(f"▶ 车型 {k}: 实际出车数 {num_vehicles}")

            vehicle_routes = []

            # 2. 路径追踪
            for i, start_node in enumerate(start_nodes):
                route = [0, start_node]
                curr = start_node

                while curr != 0:
                    next_node = None
                    for candidate in nodes:
                        if candidate != curr:
                            if x[curr, candidate, k].X > 0.5:
                                next_node = candidate
                                break

                    if next_node is not None:
                        route.append(next_node)
                        curr = next_node
                    else:
                        print(f"  ❌ 警告: 车辆 {i + 1} 路径在节点 {curr} 中断")
                        break

                vehicle_routes.append(route)
                route_str = " -> ".join(map(str, route))
                print(f"  🚚 车辆 {i + 1} 路线: {route_str}")

            results["routes"][k] = vehicle_routes
            print("-" * 60)

        return results

    else:
        # 无解处理
        print("\n" + "!" * 60)
        if model.status == GRB.INFEASIBLE:
            print("❌ 错误：模型数学上无解。")
            diagnose_infeasibility(model) # 调用诊断函数
        else:
            print(f"❌ 错误：求解异常，状态码: {model.status}")
        print("!" * 60)
        return None

def get_and_print_vrptw_results(model, x, y, nodes, customers, vehicle_types):
    """
    解析 VRPTW 求解结果：提取路径、服务时间并打印
    """
    if model.SolCount > 0:
        results = {
            "obj_val": model.ObjVal,
            "routes": {},
            "service_times": {},  # 记录每个节点的开始服务时间
            "vehicle_counts": {}
        }

        print("\n" + "=" * 70)
        status_str = "✅ 全球最优解" if model.status == GRB.OPTIMAL else f"⚠️ 可行解 (Gap: {model.MIPGap:.2%})"
        print(f"状态: {status_str} | 总成本: {model.ObjVal:.2f} Euro")
        print("=" * 70)

        for k in vehicle_types:
            # 1. 识别从仓库 (0) 出发的车辆
            start_nodes = [j for j in customers if x[0, j, k].X > 0.5]
            num_vehicles = len(start_nodes)
            results["vehicle_counts"][k] = num_vehicles

            print(f"▶ 车型 {k}: 使用车辆数 {num_vehicles}")

            vehicle_routes = []

            for i, start_node in enumerate(start_nodes):
                # 初始路径和时间提取
                # y[node].X 获取该节点的服务开始时间
                route = [0]
                route_times = [y[0].X]

                curr = start_node
                while True:
                    route.append(curr)
                    route_times.append(y[curr].X)

                    if curr == 0:  # 回到仓库，路径结束
                        break

                    # 寻找下一跳
                    next_node = None
                    for candidate in nodes:
                        if candidate != curr and x[curr, candidate, k].X > 0.5:
                            next_node = candidate
                            break

                    if next_node is not None:
                        curr = next_node
                    else:
                        print(f"  ❌ 警告: 车辆 {i + 1} 在节点 {curr} 异常中断")
                        break

                vehicle_routes.append(route)

                # 格式化输出：节点 (时间) -> 节点 (时间)
                # 例如: 0(0.0) -> 5(85.2) -> 12(110.0) -> 0(155.0)
                path_elements = [f"{node}({time:.1f}min)" for node, time in zip(route, route_times)]
                route_str = " -> ".join(path_elements)
                print(f"  🚚 车辆 {i + 1} 路线: {route_str}")

            results["routes"][k] = vehicle_routes
            print("-" * 70)

        return results

    else:
        print("\n" + "!" * 60)
        print("❌ 错误：未找到可行解。")
        if model.status == GRB.INFEASIBLE:
            print("提示：请检查时间窗或载重约束是否过于严苛。")
            diagnose_infeasibility(model) # 调用诊断函数
        print("!" * 60)
        return None

def diagnose_infeasibility(model):
    """
    当模型无解时，计算 IIS (Irreducible Inconsistent Subsystem) 并打印冲突约束
    """
    print("\n🔍 正在启动 IIS 诊断工具...")
    try:
        model.computeIIS()
        print("\n" + "=" * 40)
        print("⚠️  发现冲突约束 (IIS Report)")
        print("=" * 40)
        
        # 遍历所有约束，找出属于 IIS 的部分
        conflict_count = 0
        for constr in model.getConstrs():
            if constr.IISConstr:
                conflict_count += 1
                print(f"  ❌ 冲突约束: {constr.ConstrName}")
        
        # 也可以检查变量的上下界是否冲突 (Bounds)
        # for v in model.getVars():
        #     if v.IISLB > 0 or v.IISUB > 0:
        #         print(f"  ❌ 变量边界冲突: {v.VarName}")

        print("-" * 40)
        print(f"共发现 {conflict_count} 个相互矛盾的约束。")
        
        # 导出为 .ilp 文件，这是 Gurobi 专门的冲突文件格式
        output_file = "model_diagnosis.ilp"
        model.write(output_file)
        print(f"📄 详细诊断报告已保存至: {os.path.abspath(output_file)}")
        print("建议：打开 .ilp 文件查看具体数学表达式，或检查上述约束名称对应的业务逻辑。")
        print("=" * 40 + "\n")
        
    except gp.GurobiError as e:
        print(f"IIS 计算失败: {e}")

def plot_locations(data_df):
    """
    可视化算例点分布
    :param data_df: 从 data_loader 读取的 DataFrame
    """
    # 1. 创造图对象 (fig) 和坐标系对象 (ax)
    fig, ax = plt.subplots(figsize=(6, 5))

    # 2. 准备数据
    depot = data_df.iloc[0]
    customers = data_df.iloc[1:]

    # 3. 绘制客户点
    ax.scatter(customers["XCOORD."], customers["YCOORD."],
               c='blue', marker='o', label='Verkaufsstellen (Kunden)')

    # 4. 绘制仓库
    ax.scatter(depot["XCOORD."], depot["YCOORD."],
               c='red', marker='s', s=80, label='Großbäckerei (Depot)')

    # 5. 设置元数据与美化
    ax.set_title("Standorte des Backwarenbetriebs (VRPTW Nodes)")
    ax.set_xlabel("X-Koordinate [km]")
    ax.set_ylabel("Y-Koordinate [km]")
    ax.legend(loc='upper right', fontsize='small')
    ax.grid(True, linestyle='--', alpha=0.7)

    # 显示图像
    plt.show()