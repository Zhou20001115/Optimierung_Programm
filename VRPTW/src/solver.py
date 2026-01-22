# 建议存放在 src/solver.py
import gurobipy as gp
from gurobipy import GRB
import math

def solve_cvrp_model(nodes, customers, demands, dist_matrix, capacities, costs_per_km, vehicle_types):
    env = gp.Env()
    model = gp.Model(name='CVRP', env=env)

    # 1. 变量定义
    x = model.addVars(nodes, nodes, vehicle_types, vtype=GRB.BINARY, name="x")
    f = model.addVars(nodes, nodes, vehicle_types, vtype=GRB.CONTINUOUS, lb=0, name="f")

    # 3. 设置目标函数：最小化总运输成本
    obj_expr = gp.quicksum(
        costs_per_km[k] * dist_matrix[(i, j)] * x[i, j, k]
        for k in vehicle_types
        for i in nodes
        for j in nodes
        if i != j
    )
    model.setObjective(obj_expr, GRB.MINIMIZE)

    # 4. 添加约束条件 (此处粘贴你代码中的 addConstr 部分)

    # 每种车型至少一辆出发
    for k in vehicle_types:
        model.addConstr(
            gp.quicksum(x[0, j, k] for j in customers) >= 1,
            name=f"MinFleet_{k}"
        )

    # Each customer is visited exactly once by exactly one vehicle
    for j in customers:
        model.addConstr(
            gp.quicksum(x[i, j, k] for i in nodes for k in vehicle_types if i != j) == 1,
            name=f"Visit_{j}"
        )

    # Incoming correspond to outgoing vehicles at each customer location
    for i in nodes:
        for k in vehicle_types:
            model.addConstr(
                gp.quicksum(x[j, i, k] for j in nodes if j != i) ==
                gp.quicksum(x[i, j, k] for j in nodes if j != i),
                name=f"FlowCons_{i}_{k}"
            )

    # The demand of each customer is satisfied by the transport flow
    for i in customers:
        for k in vehicle_types:
            flow_in = gp.quicksum(f[j, i, k] for j in nodes if j != i)
            flow_out = gp.quicksum(f[i, j, k] for j in nodes if j != i)

            # Vehicle k visits node i implies sum(x[j, i, k] for j...) == 1
            is_visited = gp.quicksum(x[j, i, k] for j in nodes if j != i)

            model.addConstr(
                flow_in - flow_out == demands[i] * is_visited,
                name=f"Demand_{i}_{k}"
            )

    # # 提紧载重与流量约束
    for i in nodes:
        for j in nodes:
            if i != j:
                for k in vehicle_types:
                    # 基础逻辑：如果不走这条路，流量必为 0
                    # 如果走这条路，流量受限于车辆容量

                    # 计算该弧段最紧的上界 (Tightened Upper Bound)
                    if i == 0:
                        # 从仓库出发，最大载重即为车型容量
                        upper_bound_M = capacities[k]
                    else:
                        # 从客户 i 离开，最大载重不能超过 容量 - i的需求
                        upper_bound_M = capacities[k] - demands[i]

                    # 1. 提紧的上界约束
                    model.addConstr(
                        f[i, j, k] <= upper_bound_M * x[i, j, k],
                        name=f"CapUB_{i}_{j}_{k}"
                    )

                    # 2. 增加下界约束 (如果去往客户 j，流量至少为 demands[j])
                    if j != 0:
                        model.addConstr(
                            f[i, j, k] >= demands[j] * x[i, j, k],
                            name=f"CapLB_{i}_{j}_{k}"
                        )
                    else:
                        # 如果是回仓库的弧段，流量理论上应该为 0
                        model.addConstr(
                            f[i, j, k] == 0,
                            name=f"ReturnEmpty_{i}_{j}_{k}"
                        )
    # 流量平衡、货物平衡、以及你写的“提紧载重与流量约束”...
    # [此处省略你代码中剩下的 addConstr 逻辑，按原样粘贴即可]

    # 5. 设置求解参数
    model.setParam('MIPGap', 0.03)
    model.setParam('MIPFocus', 3)

    # 6. 执行求解
    model.optimize()

    # 7. 返回结果
    # 修改：即使无解，也返回 model 对象，以便进行 IIS 诊断
    if model.SolCount > 0:
        return model, x, f
    else:
        return model, x, f

def solve_vrptw_model(nodes, customers, demands, dist_matrix, capacities, costs_per_km, vehicle_types,
                      ready_times, due_dates, service_times, travel_times):
    """
    构建并求解带时间窗的车辆路径问题 (VRPTW)
    """
    env = gp.Env()
    model = gp.Model(name='VRPTW', env=env)

    # ==========================================
    # 1. 变量定义
    # ==========================================
    # x[i,j,k]: 二进制决策变量，表示路径选择
    x = model.addVars(nodes, nodes, vehicle_types, vtype=GRB.BINARY, name="x")
    # f[i,j,k]: 连续变量，表示货物流量（载重跟踪）
    f = model.addVars(nodes, nodes, vehicle_types, vtype=GRB.CONTINUOUS, lb=0, name="f")
    # y[i]: 连续变量，表示在节点 i 开始服务的时刻 (NEW)
    y = model.addVars(nodes, vtype=GRB.CONTINUOUS, lb=0, name="y")

    # ==========================================
    # 2. 目标函数：最小化总行驶成本 (与 CVRP 一致)
    # ==========================================
    obj_expr = gp.quicksum(
        costs_per_km[k] * dist_matrix[(i, j)] * x[i, j, k]
        for k in vehicle_types
        for i in nodes
        for j in nodes
        if i != j
    )
    model.setObjective(obj_expr, GRB.MINIMIZE)

    # ==========================================
    # 3. 基础 CVRP 约束 (继承逻辑)
    # ==========================================
    # 3.1 车型启动约束
    for k in vehicle_types:
        model.addConstr(gp.quicksum(x[0, j, k] for j in customers) >= 1, name=f"MinFleet_{k}")

    # 3.2 客户访问唯一性
    for j in customers:
        model.addConstr(gp.quicksum(x[i, j, k] for i in nodes for k in vehicle_types if i != j) == 1, name=f"Visit_{j}")

    # 3.3 路径连续性 (车辆流平衡)
    for i in nodes:
        for k in vehicle_types:
            model.addConstr(
                gp.quicksum(x[j, i, k] for j in nodes if j != i) ==
                gp.quicksum(x[i, j, k] for j in nodes if j != i),
                name=f"FlowCons_{i}_{k}"
            )

    # 3.4 货物需求平衡 (载重流)
    for i in customers:
        for k in vehicle_types:
            is_visited = gp.quicksum(x[j, i, k] for j in nodes if j != i)
            model.addConstr(
                gp.quicksum(f[j, i, k] for j in nodes if j != i) -
                gp.quicksum(f[i, j, k] for j in nodes if j != i) == demands[i] * is_visited,
                name=f"Demand_{i}_{k}"
            )

    # 3.5 载重容量与提紧约束
    for i in nodes:
        for j in nodes:
            if i != j:
                for k in vehicle_types:
                    # 计算提紧的 M (载重上界)
                    upper_M = capacities[k] if i == 0 else capacities[k] - demands[i]
                    # 载重上界约束
                    model.addConstr(f[i, j, k] <= upper_M * x[i, j, k], name=f"CapUB_{i}_{j}_{k}")
                    # 载重下界约束 (若去客户 j，则至少运送 demands[j])
                    if j != 0:
                        model.addConstr(f[i, j, k] >= demands[j] * x[i, j, k], name=f"CapLB_{i}_{j}_{k}")
                    else:
                        model.addConstr(f[i, j, k] == 0, name=f"ReturnEmpty_{i}_{j}_{k}")

    # ==========================================
    # 4. 时间窗约束 (NEW)
    # ==========================================
    # 4.1 时间推进约束 (Constraint 7): 确保服务时刻的逻辑连贯
    # y[j] >= y[i] + service_time[i] + travel_time[i,j] - M * (1 - x[i,j,k])
    for i in nodes:
        for j in customers:
            if i != j:
                for k in vehicle_types:
                    t_ij = travel_times[(i, j, k)]
                    s_i = service_times[i]
                    # 运筹优化提紧：计算针对弧 (i,j) 专属的最小 Big-M
                    tight_M = max(due_dates[i] + s_i + t_ij - ready_times[j], 0)

                    model.addConstr(
                        y[j] >= y[i] + s_i + t_ij - tight_M * (1 - x[i, j, k]),
                        name=f"TimeProp_{i}_{j}_{k}"
                    )

    # 4.2 时间窗口上下界 (Constraint 8)
    for i in nodes:
        model.addConstr(y[i] >= ready_times[i], name=f"TW_Start_{i}")
        model.addConstr(y[i] <= due_dates[i], name=f"TW_End_{i}")

    # ==========================================
    # 5. 参数设置与求解
    # ==========================================
    model.setParam('MIPGap', 0.03)
    model.setParam('MIPFocus', 3)
    # model.setParam('TimeLimit', 60) # 建议大型算例开启

    model.optimize()

    # 返回结果
    # 修改：即使无解，也返回 model 对象，以便进行 IIS 诊断
    if model.SolCount > 0:
        return model, x, y
    else:
        return model, x, y

def solve_cvrp_lazy(nodes, customers, demands, dist_matrix, capacities, costs_per_km, vehicle_types):
    """
    使用 Lazy Constraints (DFJ 模型) 求解 CVRP
    注意：这里不使用流变量 f，也不使用 MTZ 约束，而是通过 Callback 动态添加子回路消除约束
    """
    env = gp.Env()
    model = gp.Model(name='CVRP_Lazy', env=env)

    # 1. 变量定义 (只有 x，没有 f)
    x = model.addVars(nodes, nodes, vehicle_types, vtype=GRB.BINARY, name="x")

    # 2. 目标函数
    obj_expr = gp.quicksum(
        costs_per_km[k] * dist_matrix[(i, j)] * x[i, j, k]
        for k in vehicle_types
        for i in nodes
        for j in nodes
        if i != j
    )
    model.setObjective(obj_expr, GRB.MINIMIZE)

    # 3. 基础约束 (Degree Constraints)
    
    # 3.1 访问唯一性
    for j in customers:
        model.addConstr(
            gp.quicksum(x[i, j, k] for i in nodes for k in vehicle_types if i != j) == 1,
            name=f"Visit_{j}"
        )

    # 3.2 流平衡 (进 = 出)
    for i in nodes:
        for k in vehicle_types:
            model.addConstr(
                gp.quicksum(x[j, i, k] for j in nodes if j != i) ==
                gp.quicksum(x[i, j, k] for j in nodes if j != i),
                name=f"FlowCons_{i}_{k}"
            )
            
    # 4. 开启 Lazy Constraints 模式
    model.Params.LazyConstraints = 1

    # 5. 定义 Callback 函数 (这是核心！)
    def subtour_callback(model, where):
        # 只有当发现一个新的整数解 (MIPSOL) 时才检查
        if where == GRB.Callback.MIPSOL:
            # 1. 获取当前的解值
            x_vals = model.cbGetSolution(x)
            
            # 2. 遍历每辆车，寻找子回路
            for k in vehicle_types:
                # 构建邻接表: adj[i] = j 表示车 k 从 i 走到 j
                adj = {}
                for i in nodes:
                    for j in nodes:
                        if i != j and x_vals[i, j, k] > 0.5:
                            adj[i] = j
                
                # 3. 找圈算法 (寻找连通分量)
                visited = set()
                for start_node in nodes:
                    if start_node in adj and start_node not in visited:
                        # 发现一条新路径，开始追踪
                        cycle = []
                        curr = start_node
                        while curr not in visited and curr in adj:
                            visited.add(curr)
                            cycle.append(curr)
                            curr = adj[curr]
                        
                        # 检查是否形成了圈
                        if curr in cycle:
                            idx = cycle.index(curr)
                            real_cycle = cycle[idx:]
                            
                            # 4. 判断圈是否合法
                            # 情况 A: 不含仓库的圈 (Subtour) -> 必须切断
                            if 0 not in real_cycle:
                                print(f"🔪 发现子回路: {real_cycle} (车 {k})，添加切断约束...")
                                model.cbLazy(
                                    gp.quicksum(x[i, j, k] for i in real_cycle for j in real_cycle if i != j) 
                                    <= len(real_cycle) - 1
                                )
                            
                            # 情况 B: 含仓库的圈 (Valid Tour?) -> 检查容量
                            else:
                                # 计算该路径的总需求
                                route_demand = sum(demands[c] for c in real_cycle if c != 0)
                                vehicle_cap = capacities[k]
                                
                                if route_demand > vehicle_cap:
                                    # 🚨 超载了！虽然连通，但也是非法的
                                    # 计算至少需要几辆车: ceil(TotalDemand / Capacity)
                                    # 例如需求 500，容量 300，则至少需要 2 辆车
                                    min_vehicles = math.ceil(route_demand / vehicle_cap)
                                    
                                    print(f"⚖️ 发现超载路径: {real_cycle} (需求 {route_demand} > 容量 {vehicle_cap})，添加容量割...")
                                    
                                    # 添加广义子回路消除约束 (GSEC)
                                    # sum(x_ij) <= |S| - min_vehicles
                                    # S 是路径中的客户集合 (不含仓库)
                                    customers_in_route = [c for c in real_cycle if c != 0]
                                    model.cbLazy(
                                        gp.quicksum(x[i, j, k] for i in customers_in_route for j in customers_in_route if i != j)
                                        <= len(customers_in_route) - min_vehicles
                                    )

    # 6. 求解 (传入 callback)
    model.optimize(subtour_callback)

    # 7. 返回结果
    return model, x, None # 没有 f 变量

def solve_cvrp_hybrid(nodes, customers, demands, dist_matrix, capacities, costs_per_km, vehicle_types):
    """
    混合策略 (Hybrid Strategy):
    - 使用 Flow 变量 (f) 处理容量约束 (高效)
    - 使用 Lazy Callback 处理子回路消除 (高效)
    """
    env = gp.Env()
    model = gp.Model(name='CVRP_Hybrid', env=env)

    # 1. 变量定义 (x 和 f 都有)
    x = model.addVars(nodes, nodes, vehicle_types, vtype=GRB.BINARY, name="x")
    f = model.addVars(nodes, nodes, vehicle_types, vtype=GRB.CONTINUOUS, lb=0, name="f")

    # 2. 目标函数
    obj_expr = gp.quicksum(
        costs_per_km[k] * dist_matrix[(i, j)] * x[i, j, k]
        for k in vehicle_types
        for i in nodes
        for j in nodes
        if i != j
    )
    model.setObjective(obj_expr, GRB.MINIMIZE)

    # 3. 基础约束
    
    # 3.1 访问唯一性
    for j in customers:
        model.addConstr(
            gp.quicksum(x[i, j, k] for i in nodes for k in vehicle_types if i != j) == 1,
            name=f"Visit_{j}"
        )

    # 3.2 流平衡 (进 = 出)
    for i in nodes:
        for k in vehicle_types:
            model.addConstr(
                gp.quicksum(x[j, i, k] for j in nodes if j != i) ==
                gp.quicksum(x[i, j, k] for j in nodes if j != i),
                name=f"FlowCons_{i}_{k}"
            )
            
    # 3.3 容量约束 (使用 Flow 变量，这是 Hybrid 的核心)
    for i in customers:
        for k in vehicle_types:
            flow_in = gp.quicksum(f[j, i, k] for j in nodes if j != i)
            flow_out = gp.quicksum(f[i, j, k] for j in nodes if j != i)
            is_visited = gp.quicksum(x[j, i, k] for j in nodes if j != i)
            model.addConstr(
                flow_in - flow_out == demands[i] * is_visited,
                name=f"Demand_{i}_{k}"
            )
            
    # 3.4 载重上界 (CapUB) & 下界 (CapLB) & 回程空载 (ReturnEmpty)
    for i in nodes:
        for j in nodes:
            if i != j:
                for k in vehicle_types:
                    # 计算该弧段最紧的上界 (Tightened Upper Bound)
                    if i == 0:
                        upper_bound_M = capacities[k]
                    else:
                        upper_bound_M = capacities[k] - demands[i]

                    # 1. 提紧的上界约束
                    model.addConstr(
                        f[i, j, k] <= upper_bound_M * x[i, j, k],
                        name=f"CapUB_{i}_{j}_{k}"
                    )

                    # 2. 增加下界约束 (如果去往客户 j，流量至少为 demands[j])
                    if j != 0:
                        model.addConstr(
                            f[i, j, k] >= demands[j] * x[i, j, k],
                            name=f"CapLB_{i}_{j}_{k}"
                        )
                    else:
                        # 如果是回仓库的弧段，流量理论上应该为 0
                        model.addConstr(
                            f[i, j, k] == 0,
                            name=f"ReturnEmpty_{i}_{j}_{k}"
                        )
                    
    # 4. 开启 Lazy Constraints 模式
    model.Params.LazyConstraints = 1
    
    # 5. 设置求解参数 (与 solve_cvrp_model 保持一致)
    model.setParam('MIPGap', 0.03)
    model.setParam('MIPFocus', 3)

    # 6. 定义 Callback 函数 (只负责找圈，不管容量)
    def subtour_callback(model, where):
        if where == GRB.Callback.MIPSOL:
            x_vals = model.cbGetSolution(x)
            for k in vehicle_types:
                adj = {}
                for i in nodes:
                    for j in nodes:
                        if i != j and x_vals[i, j, k] > 0.5:
                            adj[i] = j
                
                visited = set()
                for start_node in nodes:
                    if start_node in adj and start_node not in visited:
                        cycle = []
                        curr = start_node
                        while curr not in visited and curr in adj:
                            visited.add(curr)
                            cycle.append(curr)
                            curr = adj[curr]
                        
                        if curr in cycle:
                            idx = cycle.index(curr)
                            real_cycle = cycle[idx:]
                            
                            # 只处理不含仓库的圈 (Subtour)
                            if 0 not in real_cycle:
                                print(f"🔪 发现子回路: {real_cycle} (车 {k})，添加切断约束...")
                                model.cbLazy(
                                    gp.quicksum(x[i, j, k] for i in real_cycle for j in real_cycle if i != j) 
                                    <= len(real_cycle) - 1
                                )

    # 7. 求解
    model.optimize(subtour_callback)

    # 8. 返回结果
    return model, x, f
