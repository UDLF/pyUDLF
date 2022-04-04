# pyUDLF (⚠️WARNING: under development)

**Authors:** Gustavo Rosseto Leticio, [Lucas Pascotti Valem](http://www.lucasvalem.com) and [Daniel Carlos Guimarães Pedronette](http://www.ic.unicamp.br/~dcarlos/)

Dept. of Statistic, Applied Math. and Computing, Universidade Estadual Paulista ([UNESP](http://www.rc.unesp.br/)), Rio Claro, Brazil

----------------------
* [Visão Geral](#visão-geral)
* [Como instalar](#como-instalar)
* [Primeiros passos](#primeiros-passos)
* [Exemplo de execução](#exemplo-de-execução)
* [Exemplos](#exemplos)
* [Documentação](#documentação)
* [Contribuição](#contribuição)
* [Aplicações](#Aplicações)
* [Contato](#contato)
* [Agradecimentos](#agradecimentos)
* [Licença](#Licença)
----------------------
## Visão Geral
O <strong>pyUDLF</strong> atua como um wrapper em Python para o UDLF que está em C/C++.
Dessa forma, todas as chamadas são feitas como se o UDLF estivesse em Python, mas na verdade o pyUDLF faz as chamadas pelo binário da versão original. Caso o usuário não possua o binário, o pyUDLF irá baixa-lo, bem como o arquivo de configuração.

----------------------
## Como instalar
python setup.py install (ver como escrever)

## Primeiros passos
1) Caminhos

O usuário é capaz de definir o caminho para o binário e o config do UDLF, caso não seja definido, o pyUDLF possui o caminho do usuário como padrão. **Note que, se os arquivos não existirem nos caminhos definidos, eles serão baixados**.

2) Configuração

Após a configuração dos caminhos, o usuário é capaz de configurar o arquivo de configuração do UDLF, como por exemplo, atribuir ou receber valores, listar todos os parâmetros e valores, entre outras funcionalidades, tudo através do pyUDLF, sem a necessidade de alteração manual do config. Um exemplo de vantagem adquirida com essa funcionalidade seria uma execução com o resultado obtido de uma outra execução ou sucessivas execuções...
**É importante ressaltar que, o objeto input vira com os parâmetros e valores que estão definidos no config do caminho fornecido !** 

3) Execução

É possível executar o pyUDLF de 3 maneiras, sao elas:

+ **Arquivo config disponibilizado**: executa o UDLF com alguma config fornecida.
+ **Arquivo config nao disponibilizado**: através de um objeto "input", pode-se configurar a vontade e executar, sem a necessidade de ter o arquivo config salvo na máquina.
+ **Retornos**: As duas maneiras anteriores mas com retornos, ou seja, o log de resultados em um dicionário e a lista ranqueada ou matrix de retorno

4) Retornos

Por conclusão, o pyUDLF e realiza uma execução, conforme especificada.
Nos casos que o resultado da operação é solicitado, é retornado um dicionário, com as saídas especificadas no config.


Estes 4 passos estão exemplificados no tópico seguinte, onde está disponibilizado um exemplo de execução de maneira simples. Lembrando que, existe mais de uma maneira de definição, configuração e execução.

----------------------
## Exemplo de execução

Este exemplo é simples, apenas para mostrar uma maneira de execução. Exemplos mais complexos ou de diferentes maneiras de executar encontram-se no tópico [Exemplos](#exemplos).
Note que, o exemplo teve os caminhos setados, alguns parâmetros alterados e o retorno foi solicitado.

```python
from pyUDLF import run_calls as udlf
from pyUDLF import inputType

# Setando o caminho do binário e do config (1)
udlf.setBinaryPath("/home/usr/Desktop/UDLF/UDLF/bin/udlf")
udlf.setConfigPath = ("/home/usr/Desktop/UDLF/UDLF/bin/minha_config.ini")

# Definindo o objeto input, com o nome de input_data (2)
input_data = inputType.InputType()

# Alterando valores do config. (2)
#parametros mais usados
#set_*param_name*(param_value)
files_path = "../Soccer/matrices/distance/acc.txt"
classes_path = "/home/gustavo/Desktop/UDLF/UDLF/Soccer/classes.txt"
input_data.set_method_name("CPRR")   #(NONE|CPRR|RLRECOM|...)Selection of method to be executed
input_data.set_input_files(files_path)   #Path of the main input file (matrix/ranked lists) for UDL tasks
input_data.set_lists_file(".../Soccer/lists.txt")    #Path of the lists file
input_data.set_classes_file(classes_path)   #Path of the classes file
...

#parâmetro genérico
#set_param("param_name", param_value) 
input_data.set_param("UDL_TASK", "UDL")     #(UDL|FUSION): Selection of task to be executed
input_data.set_param("PARAM_NONE_L", 1400)  #(TUint): Size of the ranked list (must be lesser than SIZE_DATASET)
...

# Executando (3)
output = udlf.run(input_data, get_output = True)

# Resultado
output.print_log()
results = output.get_log()
print(results["MAP"]["After"]) # or ["Before"] or ["Gain"]
print(results["MAP"])
print(results["Time"])

```

----------------------
## Exemplos
Exemplo mais detalhados, com outras formar de definição/configuração e execução se encontram na [pagina de exemplos](https://github.com/UDLF/pyUDLF/wiki/Examples)

----------------------
## Documentação

Funcionamento mais alto nível do PyUDLF:

![basic2](https://user-images.githubusercontent.com/69856485/161096018-417ba18b-b8a2-40df-b5c5-bf16c076edb8.png)

A documentação das funções se encontra disponível na [pagina de documentação](https://github.com/UDLF/pyUDLF/wiki/Documentation)

----------------------
## Contribuição
Agradecemos sugestões, ideias e contribuições.
Se você quiser contribuir, sinta-se à vontade para entrar em [contato](#contato) conosco.

----------------------
## Contato
**Gustavo Rosseto Leticio**: `gustavo.leticio@gmail.com` ou `gustavo.leticio@unesp.br`

**Lucas Pascotti Valem**: `lucaspascottivalem@gmail.com` ou `lucas.valem@unesp.br`

**Daniel Carlos Guimarães Pedronette**: `daniel.pedronette@unesp.br`

----------------------
## Agradecimentos
TESTE

----------------------
## licença
[link](https://github.com/UDLF/pyUDLF/blob/main/LICENSE)
