# main.py
import sys
import os

from src.data_loader import load_solomon_data, prepare_cvrp_data 
# 引入新的 solve_cvrp_hybrid
from src.solver import solve_cvrp_model, solve_vrptw_model, solve_cvrp_lazy, solve_cvrp_hybrid
from src.utils import plot_locations, get_and_print_results, get_and_print_vrptw_results

# 获取当前脚本 main.py 的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print(f"当前文件夹{BASE_DIR}")

def main():
    # 1. 加载基础数据
    file_path = os.path.join(BASE_DIR, "data", "r105.txt")
    print(f"当前数据路径{file_path}")
    
    # 为了测试 Lazy 效果，我们可以适当增加点数，比如 25 或 50
    df = load_solomon_data(file_path, num_customers=35)
    print("✅ 数据加载成功")

    # 2. 准备所有参数
    params = prepare_cvrp_data(df)
    (nodes, customers, demands, dist_matrix, capacities, costs_per_km, vehicle_types,
     ready_times, due_dates, service_times, travel_times) = params

    # 可视化原始点位
    # plot_locations(df)

    # ---------------------------------------------------------
    # 策略 A: 求解普通 CVRP (Flow Formulation)
    # ---------------------------------------------------------
    print("\n" + " 策略 A: 普通 CVRP (Flow) ".center(60, "*"))
    model_c, x_c, f_c = solve_cvrp_model(
        nodes, customers, demands, dist_matrix, capacities, costs_per_km, vehicle_types
    )
    if model_c:
        get_and_print_results(model_c, x_c, nodes, customers, vehicle_types)

    # ---------------------------------------------------------
    # 策略 C: 求解 Lazy CVRP (Callback) - 纯 Lazy 模式
    # ---------------------------------------------------------
    # print("\n" + " 策略 C: Lazy CVRP (Callback) ".center(60, "*"))
    # model_l, x_l, _ = solve_cvrp_lazy(
    #     nodes, customers, demands, dist_matrix, capacities, costs_per_km, vehicle_types
    # )
    # if model_l:
    #     get_and_print_results(model_l, x_l, nodes, customers, vehicle_types)

    # ---------------------------------------------------------
    # 策略 D: 求解 Hybrid CVRP (Flow + Lazy Callback)
    # ---------------------------------------------------------
    # print("\n" + " 策略 D: Hybrid CVRP (Flow + Lazy) ".center(60, "*"))
    # model_h, x_h, f_h = solve_cvrp_hybrid(
    #     nodes, customers, demands, dist_matrix, capacities, costs_per_km, vehicle_types
    # )
    # if model_h:
    #     get_and_print_results(model_h, x_h, nodes, customers, vehicle_types)

    # ---------------------------------------------------------
    # 策略 B: 求解带时间窗的 VRPTW
    # ---------------------------------------------------------
    # print("\n" + " 策略 B: 带时间窗 VRPTW ".center(60, "*"))
    # model_t, x_t, y_t = solve_vrptw_model(
    #     nodes, customers, demands, dist_matrix, capacities, costs_per_km, vehicle_types,
    #     ready_times, due_dates, service_times, travel_times
    # )
    # if model_t:
    #     get_and_print_vrptw_results(model_t, x_t, y_t, nodes, customers, vehicle_types)

if __name__ == "__main__":
    main()