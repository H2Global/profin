# PROFIN - A Python Package for <u>Pro</u>ject <u>Fin</u>ance

This repository holds a Python package named pyproject, 
which can be used to conduct financial analysis
of energy projects.

PROFIN has been developed as an open-source tool by 
[H2 Global Fondation](https://www.h2-global.de/) 
in the [BMBF](https://www.bmbf.de/bmbf/en/home/home_node.html)-funded
research project “H2Global meets Africa".
 

Version 1.0 of this package was published on PyPI on 27/02/2024.

<img alt="Alt text" src="H2G_logo.png"/>

---
## Contents

- [Contents](#contents)
- [Model Purpose and General Information](#Model-Purpose-and-General-Information)
- [Installation Instructions](#Installation-Instructions)
- [Workflow](#Workflow)
- [Examples](#Examples)
- [Testing](#Testing)
- [Contributing](#Contributing)
- [License](#License)
---

## Model Purpose and General Information
PROFIN enables discounted cash flow analysis for energy projects.

### <u>INPUT</u>
- Energy input and output
- Financial metrics: CAPEX and OPEX, depreciation period, price developments, 
equity ratio, country risk, interest on debt, subsidies, tax rate

### <u>DCF analysis</u>
Additional features:

- Monte-Carlo simulation of specific project risks
- Simulation of funding demand (H2Global, CfD, etc.) to achieve positive net present value
- API link to  [yahoo-finance](https://finance.yahoo.com) for latest financial data

### <u>OUTPUT</u>
- Weighted Average Cost of Capital (**WACC**)
- Net Present Value (**NPV**)
- Internal Rate of Return (**IRR**)
- Value-at-Risk (**VaR**)
- Levelized Cost of Energy (**LCOE**)
- **Sharpe-ratio** (risk measure)
- **Cashflow** visualization
- **Funding demand** for NPV=0

## Installation Instructions

1. Download or clone the repository to a local folder:
   ```bash
   git clone <repository-url>

2. Open (Anaconda) Prompt.

3. Create a new environment from reference_environment.yml file (recommended):
    ```bash
   conda env create -f reference_environment.yml
   
4. Activate the environment with:
    ```bash
   conda activate env_mode_behave
   
5. cd to the directory, where you stored the repository and where the setup.py file is located.

6. In this folder run:
    ```bash
   pip install mode-behave

7. Alternatively, run:
    ```bash
    pip install -e

## Examples


## Testing


## Contributing
Communication and contribution: We encourage active participation in the software development process to adapt it to user needs. 
If you would like to contribute to the project or report any bugs, please refer to the contribution-file or simply create an issue in the repository. 
For any other interests (e.g. potential research collaborations), please directly contact the project maintainers via email, as indicated and updated on GitHub.

## License
profin is licensed under the open source
[MIT License](https://github.com/H2Global/profin/blob/master/LICENSE.txt)
