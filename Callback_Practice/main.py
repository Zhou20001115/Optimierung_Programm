import tsp_subtour
import complex_logic
import weakening_constraints

if __name__ == '__main__':
    print("Starting Callback Practice...")
    
    # 1. Exponential Constraints (TSP Subtour)
    tsp_subtour.solve_tsp(n=15)
    
    # 2. Complex Logic (No-good Cut)
    complex_logic.solve_complex_logic()
    
    # 3. Weakening Constraints (Lazy addition)
    weakening_constraints.solve_weakening_constraints()
