

**Authors:** Gustavo Rosseto Leticio, [Lucas Pascotti Valem](http://www.lucasvalem.com) and [Daniel Carlos Guimarães Pedronette](http://www.ic.unicamp.br/~dcarlos/)

Dept. of Statistic, Applied Math. and Computing, Universidade Estadual Paulista ([UNESP](http://www.rc.unesp.br/)), Rio Claro, Brazil

----------------------
* [Overview](#overview)
* [How to install](#how-to-install)
* [First Steps](#first-steps)
* [Execution example](#execution-example)
* [Examples](#examples)
* [Documentation](#documentation)
* [Contribution](#contribution)
* [Applications](#applications)
* [Contact](#contact)
* [Acknowledgments](#acknowledgments)
* [License](#license)
----------------------
## Overview
The <strong>pyUDLF</strong> acts as a Python wrapper for the UDLF that is in C/C++.
This way, all the calls are made as if the UDLF is in Python, but pyUDLF actually calls from the binary of the original version. If the user does not have the binary, pyUDLF will download it and the configuration file.

----------------------
## How to install
python setup.py install

----------------------
## First Steps
1) Paths

The user is able to define the path to the UDLF binary and config, if not defined, pyUDLF defaults to the user path. **Note that if the files do not exist in the defined paths, they will be downloaded.**

2) Configuration

After configuring the paths, the user is able to configure the UDLF configuration file, such as assigning or receiving values, listing all parameters and values, among other features, all through pyUDLF, without the need to manually change the config. An example of an advantage gained with this functionality would be a run with the result obtained from another run, or successive runs...
**It is important to note that the input object comes with the parameters and values that are defined in the config for the given path!**

3) Execution

You can run pyUDLF in three ways:

+ **Available config file**: runs the UDLF with some provided config.
+ **Unavailable config file**: through an "input" object, you can configure at will and execute, without the need to have the config file saved on the machine.
+ **Returns**: The previous two ways but with returns, i.e. the result log in a dictionary and the ranked list or return matrix.

4) Returns

On completion, pyUDLF and performs an execution as specified.
In cases where the result of the operation is requested, a dictionary is returned, with the outputs specified in the config.


These 4 steps are exemplified in the following topic, where a simple execution example is provided. Remember that there is more than one way to define, configure and execute.

----------------------
## Execution example

This example is simple, just to show one way of execution. More complex examples or different ways of execution are in [Examples](#Examples).
Note that the example had the paths set, some parameters changed and the return was requested.

```python
from pyUDLF import run_calls as udlf
from pyUDLF import inputType

# Setting the binary and config path (1)
udlf.setBinaryPath("/home/usr/Desktop/UDLF/UDLF/bin/udlf")
udlf.setConfigPath = ("/home/usr/Desktop/UDLF/UDLF/bin/minha_config.ini")

# Defining the input object, named input_data (2)
input_data = inputType.InputType()

# Changing config values. (2)
#most used parameters
#set_*param_name*(param_value)
files_path = "../Soccer/matrices/distance/acc.txt"
classes_path = "/home/gustavo/Desktop/UDLF/UDLF/Soccer/classes.txt"
input_data.set_method_name("CPRR")   #(NONE|CPRR|RLRECOM|...)Selection of method to be executed
input_data.set_input_files(files_path)   #Path of the main input file (matrix/ranked lists) for UDL tasks
input_data.set_lists_file(".../Soccer/lists.txt")    #Path of the lists file
input_data.set_classes_file(classes_path)   #Path of the classes file
...

#generic parameter
#set_param("param_name", param_value) 
input_data.set_param("UDL_TASK", "UDL")     #(UDL|FUSION): Selection of task to be executed
input_data.set_param("PARAM_NONE_L", 1400)  #(TUint): Size of the ranked list (must be lesser than SIZE_DATASET)
...

# Running (3)
output = udlf.run(input_data, get_output = True)

# Result
output.print_log()
results = output.get_log()
print(results["MAP"]["After"]) # or ["Before"] or ["Gain"]
print(results["MAP"])
print(results["Time"])

```

----------------------
## Examples
More detailed examples, with further definition/configuration and execution forms, can be found on the [examples page](https://github.com/UDLF/pyUDLF/wiki/Examples). On this page you will be shown a basic step by step how to do it, not being the only way to do it, just one of them, and finally more examples, as follows: 

* [How To](https://github.com/UDLF/pyUDLF/wiki/Examples##how-to)
* [More examples](https://github.com/UDLF/pyUDLF/wiki/Examples##more-examples)

PyUDLF enables new ways to manage UDLF. But the right sequence of operations would be:
1) [Setting the file paths](https://github.com/UDLF/pyUDLF/wiki/Examples##1-setting-the-file-paths).
2) [Setting the values for the parameters](https://github.com/UDLF/pyUDLF/wiki/Examples##2-setting-the-values-for-the-parameters).
3) [Execution](https://github.com/UDLF/pyUDLF/wiki/Examples##3-execution).
4) [Results, if requested at execution](https://github.com/UDLF/pyUDLF/wiki/Examples##4-results).

----------------------
## Documentation

Highest level operation of PyUDLF:

![basic2](https://user-images.githubusercontent.com/69856485/161096018-417ba18b-b8a2-40df-b5c5-bf16c076edb8.png)

Documentation for the functions is available at [documentation page](https://github.com/UDLF/pyUDLF/wiki/Documentation)

----------------------
## Contribution
We welcome suggestions, ideas, and contributions.
If you would like to contribute, feel free to [Contact](#Contact) us.

----------------------
## Applications

aplications

----------------------
## Contact
**Gustavo Rosseto Leticio**: `gustavo.leticio@gmail.com` ou `gustavo.leticio@unesp.br`

**Lucas Pascotti Valem**: `lucaspascottivalem@gmail.com` ou `lucas.valem@unesp.br`

**Daniel Carlos Guimarães Pedronette**: `daniel.pedronette@unesp.br`

----------------------
## Acknowledgments

The authors are grateful to São Paulo Research Foundation – FAPESP (grants 2013/08645-0, 2014/04220-8, 2018/15597-6) and Brazilian National Council for Scientific and Technological Development – CNPq (grants 309439/2020-5 and 422667/2021-8).

----------------------
## License

This project is licensed under GPLv2. See [details.](https://github.com/UDLF/pyUDLF/blob/main/LICENSE)
