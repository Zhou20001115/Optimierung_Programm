import os
from src.data_loader import load_solomon_data, prepare_cvrp_data
from src.solver import solve_vrptw_model
from src.utils import get_and_print_vrptw_results

# 获取当前脚本的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def run_infeasible_test():
    print("🧪 启动 IIS 诊断测试 (故意制造无解场景)...")
    
    # 1. 加载基础数据
    file_path = os.path.join(BASE_DIR, "data", "r105.txt")
    df = load_solomon_data(file_path, num_customers=5) 
    
    # 2. 😈 故意制造冲突
    print(f"原始需求: {df.loc[1, 'DEMAND']}")
    df.loc[1, 'DEMAND'] = 10000
    print(f"修改后需求: {df.loc[1, 'DEMAND']} (已超过车辆容量)")

    # 3. 准备参数 (完全照搬 main.py 的写法)
    params = prepare_cvrp_data(df)
    
    # 👇 显式解包：把 params 拆成一个个有名字的变量，清晰明了
    (nodes, customers, demands, dist_matrix, capacities, costs_per_km, vehicle_types,
     ready_times, due_dates, service_times, travel_times) = params
    
    # 4. 运行 VRPTW 模型
    print("\n🚀 开始求解 VRPTW 模型...")
    # 这里也可以直接传 *params，效果一样
    model, x, y = solve_vrptw_model(nodes, customers, demands, dist_matrix, capacities, costs_per_km, vehicle_types,
                                    ready_times, due_dates, service_times, travel_times)
    
    # 5. 打印结果
    # 👇 现在可以直接用变量名传参了，和 main.py 一模一样，不会再传错了
    get_and_print_vrptw_results(model, x, y, nodes, customers, vehicle_types)

if __name__ == "__main__":
    run_infeasible_test()