# profin - A Python Package for <u>Pro</u>ject <u>Fin</u>ance

This repository holds a Python package named profin, 
which can be used to conduct financial analysis
of energy projects.

profin has been developed as an open-source tool by 
[H2 Global Foundation](https://www.h2-global.de/) 
in the [BMBF](https://www.bmbf.de/bmbf/en/home/home_node.html)-funded
research project “H2Global meets Africa".
 

Version 1.0 of this package was published on PyPI on 27/02/2024.

<img alt="Alt text" src="H2G_logo.png"/>

---
## Contents

- [Contents](#contents)
- [Model Purpose and General Information](#Model-Purpose-and-General-Information)
- [Installation Instructions](#Installation-Instructions)
- [Example](#Example)
- [Testing](#Testing)
- [Contributing](#Contributing)
- [License](#License)
---

## Model Purpose and General Information
profin enables discounted cash flow analysis for energy projects.

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
To set up profin locally, follow these steps:

1. Download or clone the repository to a local folder:
   ```bash
   git clone <https://github.com/H2Global/profin>

2. Open Anaconda Prompt.

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

## Example
An example project configuration and calculation are provided in
[example_project](https://github.com/H2Global/profin/blob/master/deployment/example_project.py).  
This example illustrates the variables that must be defined in a Project-type class. 
Some variables may require an array, while others may be a single number.
There are also some variables that are optional; if not defined, they will retain their default values.

```py
import profin as pp

#Create a project instance with necessary parameters_ 
p_example = pp.Project(  
                 E_in = [], # Energy input in kWh per year  
                 E_out = [] , # Energy output in kWh per year  
                 K_E_in = [], # Energy input price in $ per kWh  
                 K_E_out = [], # Energy output price in $ per kWh  
                 K_INVEST = [], # Investment costs in $  
                 TERMINAL_VALUE = ..., # Liquidation revenues at the end of the period in $  
                 TECHNICAL_LIFETIME = ..., # Analyzed lifetime of the project in years  
                 OPEX = [], #  Annual costs (not including energy costs) in $ per year  
                 EQUITY_SHARE = ..., # Share of equity investment in %  
                 COUNTRY_RISK_PREMIUM = ..., # Extra return demanded by investors for higher risks in foreign markets  
                 INTEREST = ..., # Interest rate to be paid on the debt capita   
                 CORPORATE_TAX_RATE = ..., # Tax rate the project must pay within the country of operation in %  
                 RISK_PARAM = ..., # Define risk parameters. Set to {} to ignore risk   
                 OBSERVE_PAST = ..., # Days back from today to start the 10-year data window   
                 #OPTIONAL:  
                 BETA_UNLEVERED = ..., # Unlevered BETA factor of the project, defaults to 0.54.
                 DEPRECIATION_PERIOD = ..., # Repayment period for loans and depreciation for equity in years, defaults to project's lifetime  
                 SUBSIDY = ..., # Annual subsidy for the project, defaults to 0    
                 ENDOGENOUS_PROJECT_RISK = ..., # Set True to calculate project-specific risk from RISK_PARAM, otherwise False  
                 CRP_EXPOSURE = ..., # Project's exposure to country risk, ranging from 0 to 1, defaults to 1   
                 )

#Calculate Internal Rate of Return (IRR)
IRR = p_example.get_IRR()
print("____IRR:", IRR.mean())

#Calculate WACC for further calculations: 
WACC = p_example.get_WACC()
print("____WACC:", WACC.mean())

#Calculate net present value (NPV):  
NPV = p_example.get_NPV(WACC)
print("____mean NPV:", NPV.mean())

#Calculate the value-at-risk (VaR):
VaR = p_example.get_VaR(NPV)
print("____VaR:", VaR)

#Calculate the Levelized Cost of Energy (LCOE): 
LCOE = p_example.get_LCOE(WACC)
print("____LCOE:", LCOE.mean())

#Calculate Operating and non-operating cashflows:
operating_cashflow, operating_cashflow_std, non_operating_cashflow, non_operating_cashflow_std = p_example.get_cashflows(WACC)
```

## Testing
The testing suite is located in the [test](https://github.com/H2Global/profin/tree/master/test) directory. 
All functionalities are thoroughly tested in the file [test_model.py](https://github.com/H2Global/profin/blob/master/test/test_model.py).   
Tests are carried out utilizing a predefined project, `p_example`, to maintain consistent conditions across all tests.  
In the example, R_FREE and ERP_MATURE are defined as constants
so that the results are not influenced by financial information, which may vary over time.

It is recommended to run the test after any significant updates 
to the codebase to ensure that all functionalities continue to operate as expected.


## Contributing
Communication and contribution: We encourage active participation
in the software development process to adapt it to user needs. 
If you would like to contribute to the project or report any bugs, 
please refer to the contribution-file or simply create an issue in the repository. 
For any other interests (e.g. potential research collaborations), 
please directly contact the project maintainers via email, as indicated and updated on GitHub.

## License
profin is licensed under the open source
[MIT License](https://github.com/H2Global/profin/blob/master/LICENSE.txt)
