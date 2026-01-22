import gurobipy as gp
from gurobipy import GRB
import random
import itertools

def solve_tsp(n=20):
    print(f"\n--- Scenario 1: TSP Subtour Elimination (N={n}) ---")
    
    # Generate random points
    random.seed(42)
    points = [(random.randint(0, 100), random.randint(0, 100)) for _ in range(n)]
    
    # Calculate distance matrix
    dist = {(i, j): ((points[i][0]-points[j][0])**2 + (points[i][1]-points[j][1])**2)**0.5
            for i in range(n) for j in range(n) if i != j}
    
    m = gp.Model("tsp")
    
    # Create variables
    vars = m.addVars(dist.keys(), obj=dist, vtype=GRB.BINARY, name="x")
    
    # Degree constraints
    # Incoming
    m.addConstrs(vars.sum('*', j) == 1 for j in range(n))
    # Outgoing
    m.addConstrs(vars.sum(i, '*') == 1 for i in range(n))
    
    # Callback for subtour elimination
    def subtourelim(model, where):
        if where == GRB.Callback.MIPSOL:
            # Get solution values
            vals = model.cbGetSolution(vars)
            selected = gp.tuplelist((i, j) for i, j in vars.keys() if vals[i, j] > 0.5)
            
            # Find the shortest cycle in the selected edge list
            tour = subtour(selected)
            if len(tour) < n:
                # Add subtour elimination constraint
                print(f"Callback: Found subtour of length {len(tour)}, adding cut.")
                model.cbLazy(gp.quicksum(vars[i, j] for i, j in itertools.permutations(tour, 2)) <= len(tour) - 1)

    # Helper to find subtour
    def subtour(edges):
        unvisited = list(range(n))
        cycle = range(n+1) # initial length has to be greater than n
        while unvisited: 
            thiscycle = []
            neighbors = unvisited
            while neighbors:
                current = neighbors[0]
                thiscycle.append(current)
                unvisited.remove(current)
                neighbors = [j for i, j in edges.select(current, '*') if j in unvisited]
            if len(cycle) > len(thiscycle):
                cycle = thiscycle
        return cycle

    # Must set LazyConstraints parameter to 1 to use cbLazy
    m.Params.LazyConstraints = 1
    m.optimize(subtourelim)
    
    if m.status == GRB.OPTIMAL:
        print(f"Optimal tour length: {m.objVal}")
        vals = m.getAttr('x', vars)
        selected = gp.tuplelist((i, j) for i, j in vars.keys() if vals[i, j] > 0.5)
        tour = subtour(selected)
        print(f"Tour: {tour}")

if __name__ == "__main__":
    solve_tsp()
