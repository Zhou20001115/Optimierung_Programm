# batch_experiments.py
import os
import csv
import time
# 从你的 main.py 中导入已经写好的核心逻辑
from main import load_solomon_data, prepare_cvrp_data, BASE_DIR
from src.solver import solve_cvrp_model, solve_vrptw_model


def run_batch_analysis():
    """批量运行 data 文件夹下所有算例并记录结果"""
    data_folder = os.path.join(BASE_DIR, "data")
    # 筛选出文件夹中所有的 .txt 算例文件
    instance_files = [f for f in os.listdir(data_folder) if f.endswith('.txt')]

    # 准备结果保存路径
    results_path = os.path.join(BASE_DIR, "results", "batch_summary.csv")
    os.makedirs(os.path.dirname(results_path), exist_ok=True)

    print(f"📊 发现 {len(instance_files)} 个算例，准备开始实验...")

    with open(results_path, mode='w', newline='') as f:
        writer = csv.writer(f)
        # 写入表头：算例名, CVRP成本, VRPTW成本, 成本增加比例, 求解耗时
        writer.writerow(["Instance", "CVRP_Cost", "VRPTW_Cost", "Increase_%", "Time_sec"])

        for filename in instance_files:
            file_path = os.path.join(data_folder, filename)
            print(f"\n🔎 正在处理: {filename}")

            try:
                # 1. 加载数据 (复用 main 中的函数)
                df = load_solomon_data(file_path, num_customers=25)
                params = prepare_cvrp_data(df)

                # 2. 运行 CVRP
                start_time = time.time()
                m_cvrp, _, _ = solve_cvrp_model(*params[:7])
                cost_cvrp = m_cvrp.ObjVal if m_cvrp else 0

                # 3. 运行 VRPTW
                m_tw, _, _ = solve_vrptw_model(*params)
                cost_tw = m_tw.ObjVal if m_tw else 0

                # 4. 计算指标
                increase = ((cost_tw - cost_cvrp) / cost_cvrp * 100) if cost_cvrp > 0 else 0
                duration = time.time() - start_time

                # 5. 记录结果
                writer.writerow([filename, f"{cost_cvrp:.2f}", f"{cost_tw:.2f}", f"{increase:.2f}%", f"{duration:.2f}"])
                print(f"✅ {filename} 完成: VRPTW 比 CVRP 成本高出 {increase:.2f}%")

            except Exception as e:
                print(f"❌ 处理 {filename} 时出错: {e}")

    print(f"\n🚀 所有实验已完成！结果保存在: {results_path}")


if __name__ == "__main__":
    run_batch_analysis()