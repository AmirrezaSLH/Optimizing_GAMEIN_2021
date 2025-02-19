# GAMEIN Optimization Model

## Overview
This repository contains an optimization model for supply chain and production planning within the GAMEIN simulation. The model is built using **Pyomo** and solved using **CPLEX**. It follows the Integer Programming Multi-Level Capacitated Lot Sizing Problem (MLCLSP) approach to optimize production, inventory, and supply chain costs.

## Files in this Repository
- **model.py**: Defines the optimization model using Pyomo.
- **read_parameters.py**: Handles reading input parameters from CSV files.
- **Report_Optimizing_GAMEIN_2021.pdf**: The detailed research report outlining the model, methodology, and sensitivity analysis.

## Project Background
GAMEIN is a serious multiplayer business simulation game designed by the **Sharif University of Technology**. The simulation involves players managing supply chains and production processes to maximize business value. This project models a simplified version of GAMEIN, optimizing decision-making in raw material procurement, semi-finished and final product production, and inventory management.

## Features
- **Multi-Level Production Planning**: Includes raw materials, semi-finished products, and final products.
- **Dynamic Demand & Pricing**: Considers fluctuating demand and market-based pricing for raw materials.
- **Lot Sizing Constraints**: Ensures raw materials are purchased in predetermined quantities.
- **Setup & Inventory Costs**: Incorporates setup costs, inventory costs, and capacity limitations.
- **Sensitivity Analysis**: Examines how various parameters impact profit, production, and supply chain efficiency.

## Installation & Dependencies
To run the model, install the required dependencies:
```sh
pip install pyomo
```
You also need **IBM CPLEX** as the solver. You can install it via IBM’s academic initiative or use other Pyomo-compatible solvers.
If you do not have access to **IBM CPLEX** you can use other solvers such as **Gurobi** Academic Liscence.

## Usage
1. Ensure input CSV files (demand.csv, boms.csv, etc.) are placed inside the `data/` directory.
2. Run the model:
   ```sh
   python model.py
   ```
3. The program will output optimal values for production, inventory, and supply.

## Sensitivity Analysis
The model includes a **sensitivity analysis module**, which evaluates how changes in:
- Demand for final products
- Market price fluctuations
- Lot sizes
- Setup costs and inventory costs
impact profitability and production planning.

Results are plotted and saved in the `Sensitivity_Analyisis/` directory.

## Authors
- **Mohammadamin Vahedinia**
- **Amirreza Salehi**

## Future Improvements
- Multi-provider & multi-retailer constraints.
- Real player behavior integration for better predictions.
- Inclusion of transportation costs in decision-making.

## License
This project is for educational and research purposes only. Contact the authors for any inquiries.

---
For a complete explanation of the model and results, refer to the [Report_Optimizing_GAMEIN_2021.pdf](./Report_Optimizing_GAMEIN_2021.pdf).

