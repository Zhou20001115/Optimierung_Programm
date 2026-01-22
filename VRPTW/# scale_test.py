# scale_test.py
import os
import csv
import time
from src.data_loader import load_solomon_data, prepare_cvrp_data
from src.solver import solve_cvrp_model, solve_vrptw_model

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def run_scale_experiment():
    file_path = os.path.join(BASE_DIR, "data", "r105.txt")
    node_scales = [25, 50]

    results_path = os.path.join(BASE_DIR, "results", "scale_comparison.csv")
    os.makedirs(os.path.dirname(results_path), exist_ok=True)

    print(f"🚀 开始算例规模压力测试（CVRP vs VRPTW）")

    with open(results_path, mode='w', newline='') as f:
        writer = csv.writer(f)
        # 表头：规模, CVRP成本, CVRP耗时, VRPTW成本, VRPTW耗时, 成本增加(%), 难度增加(倍数)
        writer.writerow(["Nodes", "CVRP_Cost", "CVRP_Time", "VRPTW_Cost", "VRPTW_Time", "Cost_Inc_%", "Time_Mult"])

        for n in node_scales:
            print(f"\n--- 正在测试规模: {n} 个点 ---")

            # 1. 加载并准备参数 (params 包含所有 11 个参数)
            df = load_solomon_data(file_path, num_customers=n)
            params = prepare_cvrp_data(df)

            # 2. 求解 CVRP (只需要前 7 个参数)
            start_c = time.time()
            model_c, _, _ = solve_cvrp_model(*params[:7])
            time_c = time.time() - start_c
            cost_c = model_c.ObjVal if model_c else 0

            # 3. 求解 VRPTW (需要全部 11 个参数)
            start_t = time.time()
            model_t, _, _ = solve_vrptw_model(*params)
            time_t = time.time() - start_t
            cost_t = model_t.ObjVal if model_t else 0

            # 4. 计算对比指标
            cost_inc = ((cost_t - cost_c) / cost_c * 100) if cost_c > 0 else 0
            time_mult = (time_t / time_c) if time_c > 0 else 0

            # 5. 记录并打印
            writer.writerow([n, f"{cost_c:.2f}", f"{time_c:.2f}", f"{cost_t:.2f}", f"{time_t:.2f}", f"{cost_inc:.2f}",
                             f"{time_mult:.2f}"])
            print(f"📊 规模 {n}: VRPTW 成本增加了 {cost_inc:.1f}%, 耗时是 CVRP 的 {time_mult:.1f} 倍")

    print(f"\n✅ 对比测试结束！结果已保存至: {results_path}")


if __name__ == "__main__":
    run_scale_experiment()