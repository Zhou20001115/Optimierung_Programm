import pandas as pd
import os
import numpy as np
from scipy.spatial.distance import cdist

def load_solomon_data(file_path, num_customers=25):
    """
    专门用于读取 Solomon 算例格式的函数
    :param file_path: 算例文件的路径 (例如 'data/r105.txt')
    :param num_customers: 需要读取的客户数量
    :return: 处理好的 DataFrame
    """
    # 1. 使用你提供的读取逻辑
    # 注意：engine='python' 是为了处理不规则的空格分隔符
    data_df = pd.read_csv(file_path, sep=r'\s\s+', header=5, index_col=[0], engine='python')

    # 2. 筛选数据：保留仓库 (Index 0) 和前 n 个客户
    data_df = data_df[(data_df.index == 0) | (data_df.index <= num_customers)]

    # 3. 重置索引并命名
    data_df = data_df.reset_index(drop=True)

    # 4. 业务逻辑处理：比如你提到的需求量放大 5 倍
    # 在运筹优化中，这一步叫“数据预处理 (Data Preprocessing)”
    data_df["DEMAND"] = data_df["DEMAND"] * 5

    return data_df

def prepare_cvrp_data(data_df):
    """
    将原始 DataFrame 转换为模型需要的参数字典
    """
    demands = data_df["DEMAND"].to_dict()
    nodes = list(demands.keys())
    customers = nodes[1:]

    # 计算距离矩阵
    coords = data_df[["XCOORD.", "YCOORD."]].values
    dist_dict = cdist(coords, coords, metric='euclidean')
    dist_matrix = {(i, j): dist_dict[i, j] for i in nodes for j in nodes}

    # 新增时间窗参数
    ready_times = data_df["READY TIME"].to_dict()
    due_dates = data_df["DUE DATE"].to_dict()
    service_times = data_df["SERVICE TIME"].to_dict()

    # 计算行驶时间矩阵 (针对不同车型)
    speeds = {1: 80, 2: 60}
    car_type = list(speeds.keys())
    speeds_arr = np.array([car_type[0], car_type[1]])  # 对应车型 1 和 2
    dist_arr = cdist(coords, coords, metric='euclidean')

    # (N, N, K) 广播机制计算
    travel_times_matrix = (dist_arr[:, :, np.newaxis] / speeds_arr[np.newaxis, np.newaxis, :]) * 60
    travel_times = {
        (i, j, k): travel_times_matrix[i, j, k_idx]
        for i in nodes for j in nodes for k_idx, k in enumerate(car_type)
    }


    # 车辆参数
    capacities = {1: 150, 2: 300}
    costs_per_km = {1: 0.6, 2: 0.8}
    vehicle_types = car_type

    return (nodes, customers, demands, dist_matrix, capacities, costs_per_km, vehicle_types,
            ready_times, due_dates, service_times, travel_times)


def validate_data_preview(nodes, dist_matrix, travel_times, num_preview=5):
    """
    专门用于预览和验证运筹优化模型输入数据的函数
    """
    print("\n" + "=" * 30)
    print(f"数据预览 (前 {num_preview} 个节点)")
    print("=" * 30)

    # 1. 预览距离矩阵
    print(f"--- 距离矩阵预览 (Euclidean) ---")
    for i in nodes[:num_preview]:
        row_str = " | ".join([f"[{i}->{j}]: {dist_matrix[(i, j)]:>7.2f}" for j in nodes[:num_preview]])
        print(row_str)

        # 2. 预览行驶时间 (针对不同车型)
        # 从travel_times字典中提取车型信息
        all_vehicle_types = set(k for _, _, k in travel_times.keys())
        vehicle_types_list = sorted(list(all_vehicle_types))  # [1, 2] 或其他车型编号

        print(f"\n--- 行驶时间预览 (Travel Times, 车型{vehicle_types_list[0]} vs 车型{vehicle_types_list[1]}) ---")
        for i in nodes[:2]:  # 只看前两个起点
            for j in nodes[1:3]:  # 看两个终点
                t1 = travel_times.get((i, j, vehicle_types_list[0]), 0)  # 车型1
                t2 = travel_times.get((i, j, vehicle_types_list[1]), 0)  # 车型2
                print(
                    f"从 {i} 到 {j}: 车型{vehicle_types_list[0]}需 {t1:.1f}min, 车型{vehicle_types_list[1]}需 {t2:.1f}min")

        print("=" * 30 + "\n")


# 如果你想测试这个文件，可以加上下面这段
if __name__ == "__main__":
    # 1. 获取当前文件 (data_loader.py) 的绝对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"当前文件夹是 {current_dir}")
    file_path = os.path.join(current_dir, "data/r105.txt")
    # 2. 定位到项目根目录 (src 的上一层) 下的 data/r105.txt
    # 这样无论你在哪运行，它都会自动指向 E:\Optimierung_Programm\VRPTW\data\r105.txt
    data_path = os.path.join(current_dir, "..", "data", "r105.txt")
    print(f"数据data_path路径是 {data_path}")

    # 测试路径是否正确
    test_df = load_solomon_data(data_path, 25)
    params = prepare_cvrp_data(test_df)
    nodes, customers, demands, dist_matrix,_,_, _,_,_,_, travel_times = params
    validate_data_preview(nodes, dist_matrix, travel_times, num_preview=5)

