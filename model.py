from copy import deepcopy

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pyomo.environ as pyo

from read_parameters import ParametersReader

M = pyo.ConcreteModel()

DATA_DIR = "data/"

SENSITIVITY_ANALYSIS = False

RAW_MAT_COUNT = 9
WIP_PROD_COUNT = 5
FINAL_PROD_COUNT = 3
TIME_HORIZON = 6
BigM = 1000000000

ICR0 = 1
ICS0 = 2
ICF0 = 5

SCPS0 = 375_000
SCPF0 = 150_000

PVCS0 = 5
PVCF0 = 100

# Initializing Readers
demands_reader = ParametersReader(DATA_DIR + "demand.csv", FINAL_PROD_COUNT, TIME_HORIZON)  # d_{i, t}
demands_table = demands_reader.read_csv()

BOMS_reader = ParametersReader(DATA_DIR + "boms.csv", WIP_PROD_COUNT, RAW_MAT_COUNT)  # BOMS_{j, k}
BOMS_table = BOMS_reader.read_csv()

BOMF_reader = ParametersReader(DATA_DIR + "bomf.csv", FINAL_PROD_COUNT, WIP_PROD_COUNT)  # BOMF_{i, j}
BOMF_table = BOMF_reader.read_csv()

PR_reader = ParametersReader(DATA_DIR + "price_raw.csv", RAW_MAT_COUNT, TIME_HORIZON)
PR_table = PR_reader.read_csv()

MPF_reader = ParametersReader(DATA_DIR + "MPF.csv", FINAL_PROD_COUNT, TIME_HORIZON)
MPF_table = MPF_reader.read_csv()

MPS_reader = ParametersReader(DATA_DIR + "MPS.csv", WIP_PROD_COUNT, TIME_HORIZON)
MPS_table = MPS_reader.read_csv()

# Sets
M.T = pyo.Set(initialize=demands_reader.axis_1_titles)
M.I = pyo.Set(initialize=demands_reader.axis_0_titles)
M.J = pyo.Set(initialize=BOMS_reader.axis_0_titles)
M.K = pyo.Set(initialize=BOMS_reader.axis_1_titles)


# Params
def init_table(table):
    def init_dem(model, i, j):
        return table[i][j]

    return init_dem


M.demands = pyo.Param(M.I, M.T, initialize=init_table(demands_table), mutable=True)
M.BOMS = pyo.Param(M.J, M.K, initialize=init_table(BOMS_table), mutable=True)
M.BOMF = pyo.Param(M.I, M.J, initialize=init_table(BOMF_table), mutable=True)

M.PR = pyo.Param(M.K, M.T, initialize=init_table(PR_table), mutable=True)
M.MPS = pyo.Param(M.J, M.T, initialize=init_table(MPS_table), mutable=True)
M.MPF = pyo.Param(M.I, M.T, initialize=init_table(MPF_table), mutable=True)

## Production costs for Semi-Final products
M.PVCS = pyo.Param(initialize=PVCS0, mutable=True)

## Production costs for Final products
M.PVCF = pyo.Param(initialize=PVCF0, mutable=True)

## Setup Costs
M.SCPS = pyo.Param(initialize=SCPS0, mutable=True)
M.SCPF = pyo.Param(initialize=SCPF0, mutable=True)

## Inventory costs
M.ICR = pyo.Param(initialize=ICR0, mutable=True)  # Raw Materials
M.ICS = pyo.Param(initialize=ICS0, mutable=True)  # Semi-Final Products
M.ICF = pyo.Param(initialize=ICF0, mutable=True)  # Final Products

## Capacities
M.IFCap = pyo.Param(initialize=60000, mutable=True)
M.ISCap = pyo.Param(initialize=240000, mutable=True)
M.IRCap = pyo.Param(initialize=3000000, mutable=True)
M.PFCap = pyo.Param(initialize=3000, mutable=True)
M.PSCap = pyo.Param(initialize=35000, mutable=True)

##Setup Limitations
M.PFSL = pyo.Param(initialize=1, mutable=True)
M.PSSL = pyo.Param(initialize=5, mutable=True)

## LOT-SIZE
M.LSR = pyo.Param(initialize=1000, mutable=True)

## Sell/Buy price ratio for S products
M.SBR = pyo.Param(initialize=0.8, mutable=True)

# Variables

## Inventory
M.IR = pyo.Var(M.K, M.T, within=pyo.NonNegativeIntegers)  # Inventory of Raw Materials
M.IS = pyo.Var(M.J, M.T, within=pyo.NonNegativeIntegers)  # Inventory of Semi-Products
M.IF = pyo.Var(M.I, M.T, within=pyo.NonNegativeIntegers)  # Inventory of Final Products
M.BF = pyo.Var(M.I, M.T, within=pyo.NonNegativeIntegers)

## Production
M.SR = pyo.Var(M.K, M.T, within=pyo.NonNegativeIntegers)  # Real Supply of Raw Materials
M.KSR = pyo.Var(M.K, M.T, within=pyo.NonNegativeIntegers)  # To make SR multiplies of LSR
M.PS = pyo.Var(M.J, M.T, within=pyo.NonNegativeIntegers)  # Production of Semi-Products
M.PF = pyo.Var(M.I, M.T, within=pyo.NonNegativeIntegers)  # Production of Final Products

## Setup
M.PFS = pyo.Var(M.I, M.T, within=pyo.Binary)  # Setup Variable Finished Products
M.PSS = pyo.Var(M.J, M.T, within=pyo.Binary)  # Setup Variable Semi-Finished Products

## Contracts
M.SSC = pyo.Var(M.J, M.T, within=pyo.NonNegativeIntegers)
M.OSC = pyo.Var(M.J, M.T, within=pyo.NonNegativeIntegers)

## Sum of Inventory Costs
M.CIR = pyo.Var(within=pyo.NonNegativeReals)
M.CIS = pyo.Var(within=pyo.NonNegativeReals)
M.CIF = pyo.Var(within=pyo.NonNegativeReals)

## Sum of Production Costs
M.CSR = pyo.Var(within=pyo.NonNegativeReals)
M.CPS = pyo.Var(within=pyo.NonNegativeReals)
M.CPF = pyo.Var(within=pyo.NonNegativeReals)

# Revenue and Costs
M.TR = pyo.Var(within=pyo.NonNegativeReals)
M.TC = pyo.Var(within=pyo.NonNegativeReals)


# Constraints
M.TCR_CONSTRAINS = pyo.ConstraintList()
M.PRODUCTION = pyo.ConstraintList()
M.INVENTORY = pyo.ConstraintList()
M.BALANCE = pyo.ConstraintList()
M.COSTS = pyo.ConstraintList()
M.SETUP = pyo.ConstraintList()

M.TCR_CONSTRAINS.add(M.TC - M.CIR - M.CIS - M.CIF - M.CSR - M.CPS - M.CPF == 0)
M.TCR_CONSTRAINS.add(
    M.TR
    - sum((M.demands[i, t] - M.BF[i, t]) * M.MPF[i, t] for i in M.I for t in M.T)
    - M.SBR * sum(M.SSC[j, t] * M.MPS[j, t] for j in M.J for t in M.T)
    == 0
)

for t in M.T:
    M.PRODUCTION.add(sum(M.PF[i, t] for i in M.I) <= M.PFCap)
    M.PRODUCTION.add(sum(M.PS[j, t] for j in M.J) <= M.PSCap)

    M.INVENTORY.add(sum(M.IF[i, t] for i in M.I) <= M.IFCap)
    M.INVENTORY.add(sum(M.IS[j, t] for j in M.J) <= M.ISCap)
    M.INVENTORY.add(sum(M.IR[k, t] for k in M.K) <= M.IRCap)

for t in M.T:
    int_t = int(t)
    M.SETUP.add(sum(M.PFS[i, t] for i in M.I) <= M.PFSL)
    M.SETUP.add(sum(M.PSS[j, t] for j in M.J) <= M.PSSL)
    for i in M.I:
        M.SETUP.add(M.PF[i, t] <= M.PFS[i, t] * BigM)
        if int_t == 1:
            M.BALANCE.add(-M.IF[i, t] + M.PF[i, t] + M.BF[i, t] == M.demands[i, t])
        else:
            M.BALANCE.add(-M.IF[i, t] + M.IF[i, str(int_t - 1)] + M.PF[i, t] + M.BF[i, t] == M.demands[i, t])

    for j in M.J:
        M.SETUP.add(M.PS[j, t] <= M.PSS[j, t] * BigM)
        if int_t == 1:
            M.BALANCE.add(sum(M.BOMF[i, j] * M.PF[i, t] for i in M.I) == M.PS[j, t] - M.IS[j, t] + M.OSC[j, t] - M.SSC[j, t])
        else:
            M.BALANCE.add(
                sum(M.BOMF[i, j] * M.PF[i, t] for i in M.I) == M.IS[j, str(int_t - 1)] + M.PS[j, t] - M.IS[j, t] + M.OSC[j, t] - M.SSC[j, t]
            )

    for k in M.K:
        M.PRODUCTION.add(M.SR[k, t] == M.LSR * M.KSR[k, t])
        if int_t == 1:
            M.BALANCE.add(sum(M.BOMS[j, k] * M.PS[j, t] for j in M.J) == M.SR[k, t] - M.IR[k, t])
        else:
            M.BALANCE.add(sum(M.BOMS[j, k] * M.PS[j, t] for j in M.J) == M.IR[k, str(int_t - 1)] + M.SR[k, t] - M.IR[k, t])

RHS_CIR = 0
RHS_CIS = 0
RHS_CIF = 0

RHS_CSR = 0
RHS_CPS = 0
RHS_CPF = 0

for t in M.T:
    for i in M.I:
        RHS_CIF += M.ICF * M.IF[i, t]
        RHS_CPF += M.PF[i, t] * M.PVCF + M.SCPF * M.PFS[i, t]

    for j in M.J:
        RHS_CIS += M.ICS * M.IS[j, t]
        RHS_CPS += M.PS[j, t] * M.PVCS + M.SCPS * M.PSS[j, t] + M.OSC[j, t] * M.MPS[j, t]

    for k in M.K:
        RHS_CIR += M.ICR * M.IR[k, t]
        RHS_CSR += M.PR[k, t] * M.SR[k, t]

M.COSTS.add(M.CIR == RHS_CIR)
M.COSTS.add(M.CIS == RHS_CIS)
M.COSTS.add(M.CIF == RHS_CIF)

M.COSTS.add(M.CSR == RHS_CSR)
M.COSTS.add(M.CPS == RHS_CPS)
M.COSTS.add(M.CPF == RHS_CPF)

# Objective Function
M.OBJ = pyo.Objective(expr=M.TR - M.TC, sense=pyo.maximize)

opt = pyo.SolverFactory("cplex")
results = opt.solve(M)

print(pyo.value(M.OBJ))

print("------------------------PF--------------------")
for i in M.I:
    print(f"{i}", end="&")
    for t in M.T:
        end = "&"
        if t == str(TIME_HORIZON):
            end = ""
        print(f"{pyo.value(M.PF[i, t]):0.0f}", end=end)

    print("\\\\")

print("------------------------IF--------------------")
for i in M.I:
    print(f"{i}", end="&")
    for t in M.T:
        end = "&"
        if t == str(TIME_HORIZON):
            end = ""
        print(f"{pyo.value(M.IF[i, t]):0.0f}", end=end)

    print("\\\\")


print("------------------------PS--------------------")
for j in M.J:
    print(f"{j}", end="&")
    for t in M.T:
        end = "&"
        if t == str(TIME_HORIZON):
            end = ""
        print(f"{pyo.value(M.PS[j, t]):0.0f}", end=end)

    print("\\\\")


print("------------------------IS--------------------")
for j in M.J:
    print(f"{j}", end="&")
    for t in M.T:
        end = "&"
        if t == str(TIME_HORIZON):
            end = ""
        print(f"{pyo.value(M.IS[j, t]):0.0f}", end=end)

    print("\\\\")

print("------------------------SR--------------------")
for i in M.K:
    print(f"{i}", end="&")
    for t in M.T:
        end = "&"
        if t == str(TIME_HORIZON):
            end = ""
        print(f"{pyo.value(M.SR[i, t]):0.0f}", end=end)

    print("\\\\")

print("------------------------IR--------------------")
for i in M.K:
    print(f"{i}", end="&")
    for t in M.T:
        end = "&"
        if t == str(TIME_HORIZON):
            end = ""
        print(f"{pyo.value(M.IR[i, t]):0.0f}", end=end)

    print("\\\\")


print("------------------------OSC--------------------")
for i in M.J:
    print(f"{i}", end="&")
    for t in M.T:
        end = "&"
        if t == str(TIME_HORIZON):
            end = ""
        print(f"{pyo.value(M.OSC[i, t]):0.0f}", end=end)

    print("\\\\")


print("------------------------SSC--------------------")
for i in M.J:
    print(f"{i}", end="&")
    for t in M.T:
        end = "&"
        if t == str(TIME_HORIZON):
            end = ""
        print(f"{pyo.value(M.SSC[i, t]):0.0f}", end=end)

    print("\\\\")


# Sesitivity Analysis

if SENSITIVITY_ANALYSIS:

    analysis = {}
    money = {"profit": [], "revenue": [], "costs": []}
    production = {prod: [] for prod in M.I}

    def extract_data(model, key, x):
        analysis[key]["x"].append(x)
        for prod in M.I:
            analysis[key]["left"][prod].append(sum(pyo.value(model.PF[prod, t]) for t in M.T))
        analysis[key]["right"]["profit"].append(pyo.value(model.TR) - pyo.value(model.TC))
        analysis[key]["right"]["revenue"].append(pyo.value(model.TR))
        analysis[key]["right"]["costs"].append(pyo.value(model.TC))

    ## Demands: increasing and decreasing Demands for each product by multipliers of 5%

    for i in M.I:
        key = f"Demands SA - {i}"
        analysis[key] = {"left": deepcopy(production), "right": deepcopy(money), "x": []}
        for mul in range(-50, 1301, 10):
            for t in M.T:
                M.demands[i, t] *= 1 + mul / 100

            opt = pyo.SolverFactory("cplex")
            results = opt.solve(M)

            extract_data(M, key, f"{mul}%")

            for t in M.T:
                M.demands[i, t] = demands_table[i][t]

    ## MPR

    for k in M.K:
        key = f"Market Price for Raw Materials SA - {k}"
        analysis[key] = {"left": deepcopy(production), "right": deepcopy(money), "x": []}
        for mul in range(-50, 1301, 10):  # 30%
            for t in M.T:
                M.PR[k, t] *= 1 + mul / 100

            opt = pyo.SolverFactory("cplex")
            results = opt.solve(M)

            extract_data(M, key, f"{mul}%")

            for t in M.T:
                M.PR[k, t] = PR_table[k][t]

    ## MPF

    for i in M.I:
        key = f"Market Price for Final Products SA - {i}"
        analysis[key] = {"left": deepcopy(production), "right": deepcopy(money), "x": []}
        for mul in range(-50, 1301, 10):  # 30%
            for t in M.T:
                M.MPF[i, t] *= 1 + mul / 100

            opt = pyo.SolverFactory("cplex")
            results = opt.solve(M)

            extract_data(M, key, f"{mul}%")

            for t in M.T:
                M.MPF[i, t] = MPF_table[i][t]

    ## LS

    key = f"Lot Size SA"
    analysis[key] = {"left": deepcopy(production), "right": deepcopy(money), "x": []}
    for ls in range(1000, 500000, 10000):
        M.LSR = ls

        opt = pyo.SolverFactory("cplex")
        results = opt.solve(M)

        extract_data(M, key, ls)

    M.LSR = 1000

    ## ICR

    key = f"ICR SA"
    analysis[key] = {"left": deepcopy(production), "right": deepcopy(money), "x": []}
    for icr in range(1, 51):
        M.ICR = icr
        opt = pyo.SolverFactory("cplex")
        results = opt.solve(M)

        extract_data(M, key, icr)

    M.ICR = ICR0

    ## ICS

    key = f"ICS SA"
    analysis[key] = {"left": deepcopy(production), "right": deepcopy(money), "x": []}

    for ics in range(1, 51):
        M.ICS = ics
        opt = pyo.SolverFactory("cplex")
        results = opt.solve(M)

        extract_data(M, key, ics)

    M.ICS = ICS0

    ## ICF

    key = f"ICF SA"
    analysis[key] = {"left": deepcopy(production), "right": deepcopy(money), "x": []}
    for icf in range(1, 51):
        M.ICF = icf
        opt = pyo.SolverFactory("cplex")
        results = opt.solve(M)

        extract_data(M, key, icf)

    M.ICF = ICF0

    ## SBR

    key = f"SBR SA"
    analysis[key] = {"left": deepcopy(production), "right": deepcopy(money), "x": []}
    for val in range(1, 41):
        M.SBR = val * 0.025
        opt = pyo.SolverFactory("cplex")
        results = opt.solve(M)

        extract_data(M, key, val * 0.025)

    M.SBR = 0.8

    ## Plot analyses

    for key in analysis:

        plt.figure(key)

        fig, ax = plt.subplots(1, 2, figsize=(24, 8))
        fig.suptitle(key, fontsize=36)

        ### Left Plots
        for prod in analysis[key]["left"]:
            ax[0].plot([x for x in analysis[key]["x"]], [y for y in analysis[key]["left"][prod]], label=prod)
            ax[0].legend(fontsize=14)
            ax[0].xaxis.set_major_locator(ticker.AutoLocator())
            ax[0].xaxis.set_minor_locator(ticker.AutoMinorLocator())

        for series in analysis[key]["right"]:
            ax[1].plot([x for x in analysis[key]["x"]], [y for y in analysis[key]["right"][series]], label=series)
            ax[1].legend(fontsize=14)
            ax[1].xaxis.set_major_locator(ticker.AutoLocator())
            ax[1].xaxis.set_minor_locator(ticker.AutoMinorLocator())

        plt.savefig("SA/" + f"{key}.png")
        plt.close(key)

    print(analysis)
