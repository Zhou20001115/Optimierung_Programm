import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize

# ==========================================
# 1. 问题定义
# ==========================================
# 目标函数: min (x1 - 1)^2 + (x2 - 2)^2
def f(x):
    return (x[0] - 1)**2 + (x[1] - 2)**2

# 等式约束: h(x) = x1^2 - x2 = 0
def h(x):
    return x[0]**2 - x[1]

# 不等式约束: g(x) = x1 + x2 - 1.5 <= 0
def g(x):
    return x[0] + x[1] - 1.5

# ==========================================
# 2. 增广拉格朗日函数 (ALM)
# ==========================================
def augmented_lagrangian(x, lam, mu, rho):
    """
    构造增广拉格朗日函数 L_rho(x, lambda, mu)
    """
    # 1. 目标函数
    obj = f(x)
    
    # 2. 等式约束项: lambda * h(x) + (rho/2) * h(x)^2
    h_val = h(x)
    eq_term = lam * h_val + (rho / 2) * h_val**2
    
    # 3. 不等式约束项 (PHR形式): (1/2rho) * (max(0, mu + rho*g(x))^2 - mu^2)
    g_val = g(x)
    ineq_term = (1 / (2 * rho)) * (np.maximum(0, mu + rho * g_val)**2 - mu**2)
    
    return obj + eq_term + ineq_term

# ==========================================
# 3. ALM 求解算法
# ==========================================
def solve_alm(max_iter=20, tol=1e-4):
    # 初始化
    x = np.array([0.0, 0.0]) # 初始点
    lam = 0.0                # 等式乘子
    mu = 0.0                 # 不等式乘子
    rho = 10.0               # 初始罚参数
    
    history = []
    
    print(f"{'Iter':<5} | {'x1':<8} | {'x2':<8} | {'h(x)':<8} | {'g(x)':<8} | {'lambda':<8} | {'mu':<8} | {'rho':<5}")
    print("-" * 90)
    
    for k in range(max_iter):
        # 1. 求解子问题 (无约束优化)
        # 使用 BFGS 算法求解 min L_rho
        res = minimize(augmented_lagrangian, x, args=(lam, mu, rho), method='BFGS')
        x_next = res.x
        
        # 计算约束违反量
        h_val = h(x_next)
        g_val = g(x_next)
        
        # 记录历史
        history.append({
            'iter': k,
            'x': x_next,
            'h': h_val,
            'g': g_val,
            'lam': lam,
            'mu': mu,
            'rho': rho
        })
        
        print(f"{k:<5} | {x_next[0]:<8.4f} | {x_next[1]:<8.4f} | {h_val:<8.4f} | {g_val:<8.4f} | {lam:<8.4f} | {mu:<8.4f} | {rho:<5.1f}")
        
        # 2. 检查收敛性
        # 约束违反量足够小 (等式接近0，不等式要么满足(<0)要么接近0)
        # 对于不等式，严格来说应该检查 max(0, g(x))，但这里简单起见看绝对值或正值
        violation = max(abs(h_val), max(0, g_val))
        
        if violation < tol:
            print("\n✅ 算法收敛！")
            break
            
        # 3. 更新乘子
        # lambda <- lambda + rho * h(x)
        lam = lam + rho * h_val
        # mu <- max(0, mu + rho * g(x))
        mu = max(0, mu + rho * g_val)
        
        # 4. 更新罚参数 (可选)
        # 如果违反量没有显著下降，可以增大 rho
        # rho = min(rho * 1.1, 1000)
        
        x = x_next
        
    return x, history

# ==========================================
# 4. 可视化
# ==========================================
def plot_results(history):
    x1 = np.linspace(-1.5, 2.5, 400)
    x2 = np.linspace(-1, 3, 400)
    X1, X2 = np.meshgrid(x1, x2)
    
    # 1. 绘制目标函数等高线
    Z = (X1 - 1)**2 + (X2 - 2)**2
    plt.figure(figsize=(10, 8))
    contour = plt.contour(X1, X2, Z, levels=20, cmap='viridis', alpha=0.6)
    plt.clabel(contour, inline=True, fontsize=8)
    
    # 2. 绘制等式约束 (抛物线)
    plt.plot(x1, x1**2, 'r-', linewidth=2, label=r'$h(x): x_2 = x_1^2$')
    
    # 3. 绘制不等式约束边界 (直线)
    plt.plot(x1, 1.5 - x1, 'b--', linewidth=2, label=r'$g(x): x_1 + x_2 = 1.5$')
    
    # 4. 填充可行域
    # 简单的可行域示意 (直线下方)
    plt.fill_between(x1, -1, 1.5 - x1, color='blue', alpha=0.1, label='Feasible Region')
    
    # 5. 标记无约束最优解
    plt.plot(1, 2, 'k*', markersize=15, label='Unconstrained Min (1, 2)')
    
    # 6. 绘制迭代轨迹
    hist_x = np.array([h['x'] for h in history])
    plt.plot(hist_x[:, 0], hist_x[:, 1], 'ko-', markersize=5, label='ALM Trajectory')
    
    # 标记起点和终点
    plt.plot(hist_x[0, 0], hist_x[0, 1], 'go', label='Start')
    plt.plot(hist_x[-1, 0], hist_x[-1, 1], 'mo', label='Optimal Solution')
    
    plt.xlim(-1.5, 2.5)
    plt.ylim(-1, 3)
    plt.xlabel('$x_1$')
    plt.ylabel('$x_2$')
    plt.title('Augmented Lagrangian Method (ALM) Demo')
    plt.legend(loc='upper left')
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    print("🚀 开始 ALM 优化演示...")
    x_opt, history = solve_alm()
    
    print(f"\n最终结果:")
    print(f"最优解 x*: {x_opt}")
    print(f"目标函数值 f(x*): {f(x_opt):.4f}")
    print(f"等式约束 h(x*): {h(x_opt):.4f} (应接近 0)")
    print(f"不等式约束 g(x*): {g(x_opt):.4f} (应 <= 0)")
    
    print("\n📊 正在绘制图像...")
    plot_results(history)