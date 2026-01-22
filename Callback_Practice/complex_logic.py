import gurobipy as gp
from gurobipy import GRB

def solve_complex_logic():
    print("\n--- Scenario 2: Complex Logic (No-good Cut) ---")
    
    # Simple problem: Select 3 items out of 5
    # But there is a hidden rule: Cannot select items {0, 2, 4} together
    
    m = gp.Model("complex_logic")
    
    items = range(5)
    x = m.addVars(items, vtype=GRB.BINARY, name="x")
    
    # Base constraint: Select exactly 3 items
    m.addConstr(x.sum() == 3, "Select3")
    
    # Objective: Maximize index sum (just to have an objective)
    m.setObjective(gp.quicksum(i * x[i] for i in items), GRB.MAXIMIZE)
    
    # Callback
    def check_complex_rule(model, where):
        if where == GRB.Callback.MIPSOL:
            vals = model.cbGetSolution(x)
            selected = [i for i in items if vals[i] > 0.5]
            
            # Complex logic check (simulated)
            # Rule: Cannot have 0, 2, and 4 selected simultaneously
            if 0 in selected and 2 in selected and 4 in selected:
                print(f"Callback: Invalid combination {selected} found via complex check. Adding No-good cut.")
                # Add No-good cut: sum(x for x in forbidden) <= len(forbidden) - 1
                # Or more generally for binary vars: sum(x_in_set) - sum(x_not_in_set) <= |set| - 1
                # Here we just forbid {0, 2, 4} specifically
                model.cbLazy(x[0] + x[2] + x[4] <= 2)

    m.Params.LazyConstraints = 1
    m.optimize(check_complex_rule)
    
    if m.status == GRB.OPTIMAL:
        selected = [i for i in items if x[i].X > 0.5]
        print(f"Optimal selection: {selected}")

if __name__ == "__main__":
    solve_complex_logic()
