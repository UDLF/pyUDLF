A ideia é que o <strong>pyUDLF</strong> atue como um wrapper em Python para o UDLF que está em C/C++.
Dessa forma, todas as chamadas serão feitas como se o UDLF estivesse em Python, mas na verdade o pyUDLF fará as chamadas pelo binário da versão original.
Sugere-se que o código seja feito seguindo os padrões do PEP8.

O pyUDLF pode ser estruturado assim (proposta inicial):

```
pyUDLF
└──── run_calls
│    │    setBinaryPath
│    │    runConfig
│    └─ methods
│    │    CPRR
│    │    LHRR
│    │    BFSTREE
│    │    ...
│    └─ utils
│    │   readData (leitura de rks e matrizes do .txt)
│    └─  configGenerator (cria arquivos config)
...
```

Mas, vamos por partes ...

1) Por padrão, o pyUDLF deve ter um caminho para o binário do UDLF.
No entanto, o usuário deve ser capaz de alterá-lo.
```python
from pyUDLF import run_calls as udlf

udlf.setBinaryPath("udlf.out")
cur_path = udlf.getBinaryPath()
print(cur_path)
```

2) A função runConfig chama o binário do UDLF e realiza uma execução com o config fornecido.
Nessa etapa, nada é retornado no código Python.
```python
from pyUDLF import run_calls as udlf

udlf.setBinaryPath("udlf.out")
udlf.runConfig("my_config.ini", get_output=False)
```

3) A função runConfig chama o binário do UDLF e realiza uma execução com o config fornecido.
Nessa etapa, é retornado um dicionário (chamado output) com as saídas especificadas no config.
```python
from pyUDLF import run_calls as udlf

udlf.setBinaryPath("udlf.out")
output = udlf.runConfig("my_config.ini", get_output=True)
```
Espera-se que o dicionário da etapa 3 seja estruturado, como se segue:
```python
map = output["measures"]["map"]
precisions = output["measures"]["precisions"]
rks = output["ranked_lists"]
matrix = output["matrix"]
```
O conteúdo do dicionário depende do que foi especificado no config.
Caso o config não especifique uma matriz de distância como saída, por exemplo, o dicionário não irá conter essa chave ou o conteúdo será vazio.
O UDLF exporta os ranked lists e matrizes para arquivos .txt, o pyUDLF deve ler esses arquivos para fazer o retorno.

