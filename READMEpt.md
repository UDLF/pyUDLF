# pyUDLF

[![tests](https://github.com/UDLF/pyUDLF/actions/workflows/tests.yml/badge.svg)](https://github.com/UDLF/pyUDLF/actions/workflows/tests.yml)

**Wrapper Python para o [UDLF](https://github.com/UDLF/UDLF) (Unsupervised Distance Learning Framework).**

[English version](README.md)

**Autores:** Gustavo Rosseto Leticio, [Lucas Pascotti Valem](http://www.lucasvalem.com) e [Daniel Carlos Guimarães Pedronette](http://www.ic.unicamp.br/~dcarlos/)

Departamento de Estatística, Matemática Aplicada e Computação, Universidade Estadual Paulista ([UNESP](http://www.rc.unesp.br/)), Rio Claro, Brasil

----------------------
* [Visão geral](#visão-geral)
* [Instalação](#instalação)
* [Início rápido](#início-rápido)
* [Exemplos](#exemplos)
* [Uso](#uso)
* [Rodando o seu próprio config](#rodando-o-seu-próprio-config)
* [API antiga](#api-antiga)
* [Linha de comando](#linha-de-comando)
* [Formatos de arquivo](#formatos-de-arquivo)
* [Desenvolvimento](#desenvolvimento)
* [Aplicações](#aplicações)
* [Citação](#citação)
* [Contato](#contato)
* [Agradecimentos](#agradecimentos)
* [Licença](#licença)


## Visão geral

O UDLF é um framework em C++ de métodos de aprendizado de distância não supervisionado para
recuperação de imagens e multimídia: dadas as listas ranqueadas (ou uma matriz de distância /
similaridade) de um dataset, um método as re-ranqueia usando a informação contextual que elas
contêm, sem rótulos.
O pyUDLF executa esses métodos a partir do Python: você passa arrays numpy (ou arquivos) e recebe
de volta as listas re-ranqueadas e as medidas de avaliação (MAP, Precision@k, Recall@k) como
arrays numpy e números. Os arquivos de configuração, os arquivos de entrada e o binário do UDLF
ficam por conta do pyUDLF. A mesma API também roda o [UDLF-CSR](#udlf-csr), que implementa CPRR e LHRR com motores esparsos
para datasets grandes.

Métodos (UDLF 1.70), com os nomes e artigos listados pelo UDLF:

| Nome no pyUDLF | Método (artigo) |
|---|---|
| `CPRR` | [CPRR](http://dx.doi.org/10.1109/SIBGRAPI.2016.042) |
| `LHRR` | [LHRR](http://doi.org/10.1109/TIP.2019.2920526) |
| `RDPAC` | [RDPAC](https://doi.org/10.3390/jimaging7030049) |
| `RFE` | [RFE](https://doi.org/10.1109/TIP.2023.3268868) |
| `BFSTREE` | [BFSTree](https://doi.org/10.1016/j.patcog.2020.107666) |
| `CONTEXTRR` | [ContextRR](http://dl.acm.org/citation.cfm?id=1948207.1948291) |
| `CORGRAPH` | [Correlation Graph](http://dx.doi.org/10.1016/j.neucom.2016.03.081) |
| `RKGRAPH` | [Rk Graph Dist.](http://dx.doi.org/10.1016/j.patrec.2016.05.021) |
| `RECKNNGRAPH` | [ReckNNGraph](http://dx.doi.org/10.1016/j.imavis.2013.12.009) |
| `RLRECOM` | [RL-Recom](http://dx.doi.org/10.1145/2671188.2749336) |
| `RLSIM` | [RL-Sim*](http://dx.doi.org/10.1145/2671188.2749335) |
| `NONE` | sem re-ranqueamento (avalia a entrada) |


## Instalação

Requer Python 3.9+.

```bash
pip install git+https://github.com/UDLF/pyUDLF.git          # núcleo
pip install "pyUDLF[viz] @ git+https://github.com/UDLF/pyUDLF.git"  # + imagens das listas ranqueadas (Pillow)
```

Depois, instale o binário do UDLF (release oficial, conferido pelo SHA-256):

```bash
pyudlf download
```

Ele vai para `~/.pyudlf/bin` (ou `$PYUDLF_HOME/bin`); `pyudlf where` mostra o binário em uso.
Há builds oficiais para Linux e Windows. Em outros sistemas (por exemplo macOS), compile o UDLF
a partir do código-fonte (`make` no [repositório do UDLF](https://github.com/UDLF/UDLF), ou
`scripts/build_udlf.sh` aqui) e use-o com `UDLF(bin_path=...)` ou a variável de ambiente `UDLF_BIN`.


## Início rápido

```python
import numpy as np
from pyUDLF import UDLF

# A small dataset: 200 elements in 10 classes, with noisy 32-D features
rng = np.random.default_rng(7)
labels = np.repeat(np.arange(10), 20)
features = rng.normal(size=(10, 32))[labels] + rng.normal(scale=1.4, size=(200, 32))

# Ranked lists: each row is a query, with all elements sorted by distance
distances = np.linalg.norm(features[:, None] - features[None], axis=2)
ranked_lists = np.argsort(distances, axis=1, kind="stable")

# Re-rank them with CPRR (needs the UDLF binary: run `pyudlf download` once)
udlf = UDLF()
res = udlf.run("CPRR", ranked_lists=ranked_lists, params={"l": 100, "k": 10},
               classes=labels)

print(res)                       # Result(method='CPRR', ranked_lists=(200, 100), MAP 0.5471 -> 0.7602)
print(res.metrics["before"]["P@10"], "->", res.metrics["after"]["P@10"])   # 0.631 -> 0.8315
before, after = res.per_query()  # average precision of each query
print((after > before).sum(), "of 200 queries improved")                  # 186 of 200 queries improved
```

O exemplo gera 200 elementos em 10 classes, monta as listas ranqueadas pela distância euclidiana
e as re-ranqueia com o CPRR: o MAP sobe de 0,5471 para 0,7602 e 186 das 200 consultas melhoram.
Este script também está em [examples/quickstart.py](examples/quickstart.py).


## Exemplos

Scripts prontos para rodar em [examples/](examples/README.md), com o dataset sintético do repositório (`python examples/<script>.py`). Os testes executam todos eles.

| Script | O que mostra |
|---|---|
| [compare_methods.py](examples/compare_methods.py) | os 12 métodos na mesma entrada, ordenados pelo MAP |
| [parameter_search.py](examples/parameter_search.py) | busca em grade de `k` e `l` |
| [input_formats.py](examples/input_formats.py) | listas ranqueadas (numpy, arquivo, nomes) e matrizes de distância / similaridade |
| [fusion.py](examples/fusion.py) | fusão de dois descritores |
| [per_query_analysis.py](examples/per_query_analysis.py) | consultas que melhoraram ou pioraram |
| [your_own_data.py](examples/your_own_data.py) | linha de comando para os seus arquivos |
| [csr_engines.py](examples/csr_engines.py) | UDLF comparado aos motores do UDLF-CSR |
| [legacy_api.py](examples/legacy_api.py) | a API das versões anteriores |


## Uso

Os exemplos abaixo continuam o início rápido.

### Entradas

```python
# Ranked lists: one row per query with element indices (numpy array, list of lists or file)
res = udlf.run("LHRR", ranked_lists=ranked_lists, params={"l": 100}, classes=labels)
res = udlf.run("LHRR", ranked_lists="ranked_lists.txt", params={"l": 100}, classes=labels)

# Distance or similarity matrix (N x N)
res = udlf.run("RDPAC", matrix=distances, matrix_type="dist", params={"l": 50}, classes=labels)

# Files in the UDLF formats: ranked lists, element names ("lists") and "name:class" classes
res = udlf.run("CPRR", ranked_lists="ranked_lists.txt", names="lists.txt",
               classes="classes.txt", params={"l": 100})
```

Arquivos de entrada são usados no lugar; arrays são gravados num diretório temporário, apagado
depois da execução. Sem `classes`, a avaliação não é feita (e um aviso é registrado no log).

### Parâmetros

`params` recebe os parâmetros do método pelo nome; os demais ficam com os valores padrão da
configuração de referência do UDLF. Para listá-los, use `UDLF.describe`:

```python
print(UDLF.describe("CPRR"))
# CPRR parameters (params={name: value}):
#   l = 400 (int): Size of ranked lists (must be lesser than SIZE_DATASET)
#   k = 20 (int): Number of nearest neighbors
#   t = 2 (int): Number of iterations
```

`UDLF.methods()` lista os métodos. Atenção: o `l` padrão de vários métodos (por exemplo 400 ou
1400) supõe datasets maiores; ele não pode ser maior que o número de elementos, e as listas
ranqueadas de entrada precisam ter pelo menos `l` elementos.

### Resultados

```python
res.ranked_lists          # re-ranked lists: numpy array (queries x output size)
res.metrics               # {"before": {...}, "after": {...}, "gain": {...}}: MAP, P@k, Recall@k
res.map_before, res.map_after
res.time                  # execution time of the method, in seconds (measured by UDLF)
res.per_query("MAP")      # value of each query, before and after (also "precision", "recall")
res.config, res.stdout    # configuration used and UDLF output, for reproducibility
```

As medidas são calculadas pelo UDLF até o tamanho das listas de saída (MAP@L); `gain` é o ganho
relativo em porcentagem. Outras opções:

```python
# Output as a distance (or similarity) matrix instead of ranked lists
res = udlf.run("CPRR", ranked_lists=ranked_lists, params={"l": 100}, output="matrix")
res.matrix.shape          # (200, 200)

# Choose the P@k / Recall@k values and keep the files of the run
res = udlf.run("CPRR", ranked_lists=ranked_lists, params={"l": 100}, classes=labels,
               precisions=[5, 10], recalls=[10], keep_files=True)
res.files                 # paths of the config, log, inputs and output of the run
```

### Fusão

```python
# Fuse ranked lists of the same dataset obtained with different features / distances
unit = features / np.linalg.norm(features, axis=1, keepdims=True)
ranked_lists_cosine = np.argsort(-(unit @ unit.T), axis=1, kind="stable")
res = udlf.fuse("CPRR", [ranked_lists, ranked_lists_cosine], params={"l": 100}, classes=labels)
res.map_after             # FUSION results only have metrics after fusion
```

### UDLF-CSR

O [UDLF-CSR](https://github.com/andreTomi/UDLF-CSR) é uma reescrita do UDLF que roda CPRR e LHRR
com vários motores (`dense`, `sparse`, `mkl`, `blas`, `eigen`) para escalar a datasets grandes.
Ele não tem build oficial: compile-o (`scripts/build_csr.sh` compila os motores `dense` e
`sparse`; `scripts/build_csr.sh --full` compila todos e precisa de Intel MKL, GraphBLAS e Eigen) e
passe o caminho com `bin_path=` ou com a variável de ambiente `UDLF_CSR_BIN`.

```python
csr = UDLF(backend="csr", threads=1)      # binary from UDLF_CSR_BIN
res = csr.run("CPRR", ranked_lists=ranked_lists, params={"l": 100, "k": 10},
              classes=labels, engine="sparse")
print(res)   # Result(method='CPRR_SPARSE', ranked_lists=(200, 100), MAP 0.5471 -> 0.7633)
res.warnings                              # problems found in the results (see below)
res.raw_metrics                           # measures computed by UDLF-CSR itself
```

O resultado é o mesmo `Result` do UDLF. As `metrics` são calculadas pelo pyUDLF com as definições
do UDLF, então resultados do UDLF e do UDLF-CSR são diretamente comparáveis (o UDLF-CSR calcula o
recall com média por consulta, não por classe). O UDLF-CSR só aceita listas ranqueadas com índices
(sem matriz, nomes ou fusão); `output="matrix"` devolve a matriz de distância dele.
Comportamentos do UDLF-CSR (commit `b391800`) tratados pelo pyUDLF:

- os motores `sparse` devolvem listas com elementos repetidos, o que infla as medidas: isso é
  informado em `res.warnings`;
- os motores `dense` dão resultados ligeiramente diferentes a cada execução com várias threads:
  use `threads=1` para resultados reproduzíveis;
- um erro intermitente na inicialização ("Failed to open backing file") é repetido
  automaticamente e informado em `res.warnings`.

### Erros

Problemas viram exceções, sempre que possível antes de executar o UDLF:

```python
from pyUDLF import UDLFParamError

try:
    udlf.run("CPRR", ranked_lists=ranked_lists, params={"l": 500})
except UDLFParamError as e:
    print(e)   # PARAM_CPRR_L = 500 is larger than the dataset (N = 200). Pass a smaller value in params.
```

`UDLFParamError` (método, parâmetro ou entrada inválidos), `UDLFRunError` (o UDLF falhou: tem
`.problems`, `.output` e `.config`) e `UDLFNotFoundError` (binário ausente) derivam de
`UDLFError`. Avisos e erros são registrados com o módulo padrão `logging`; chame
`pyUDLF.enable_logging("INFO")` para ver também as mensagens informativas.


## Rodando o seu próprio config

Um arquivo de configuração do UDLF roda como está. Caminhos relativos são relativos ao diretório
atual:

```python
res = udlf.run_config("config.ini")
res.ranked_lists, res.metrics, res.files
```


## API antiga

A API das versões anteriores (`InputType` e `run_calls`) continua disponível e dá os mesmos
resultados. A [wiki](https://github.com/UDLF/pyUDLF/wiki/Documentation) a documenta.

```python
from pyUDLF import run_calls
from pyUDLF.utils.inputType import InputType

inp = InputType()                      # starts from the UDLF reference configuration
inp.set_method_name("CPRR")
inp.set_input_file("ranked_lists.txt")
inp.set_lists_file("lists.txt")
inp.set_classes_file("classes.txt")
inp.set_dataset_size(200)
inp.set_method_parameters("CPRR", l=100, k=10)
inp.set_output_file_format("RK")
inp.set_output_rk_format("NUM")
inp.set_output_file_path("output")     # writes output.txt
inp.set_output_log_file_path("log.txt")

output = run_calls.run(inp, get_output=True)
print(output.log_dict["MAP"])   # {'Before': 0.5471, 'After': 0.7602, 'Gain': 38.9512}
```

Veja no [CHANGELOG](CHANGELOG.md) as mudanças de comportamento desta versão.


## Linha de comando

```bash
pyudlf download              # install the official UDLF binary (--version, --dest, --force)
pyudlf where                 # binary used by pyUDLF
pyudlf methods               # available methods
pyudlf describe CPRR         # parameters of a method
```


## Formatos de arquivo

Estes são os formatos que o UDLF lê (veja a [wiki do UDLF](https://github.com/UDLF/UDLF/wiki/File-Formats)):

- **Listas ranqueadas**: uma linha por consulta, elementos separados por espaços, como índices
  (`0 12 25 ...`) ou como nomes (`img_0001.jpg img_0013.jpg ...`, passando então `names=`).
  Cada linha precisa ter pelo menos `l` elementos; em geral a própria consulta é o primeiro.
- **Matriz**: N linhas com N valores (distâncias ou similaridades) separados por espaços.
- **Lista de elementos** (`names=`): um nome de elemento por linha, na ordem do dataset.
- **Classes** (`classes=`): um `nome:classe` por linha.

O UDLF não consegue ler, nos seus arquivos de configuração, caminhos com espaços ou `#`; por isso
o pyUDLF os recusa.


## Desenvolvimento

```bash
git clone https://github.com/UDLF/pyUDLF.git && cd pyUDLF
python3 -m venv .venv && .venv/bin/pip install -e ".[viz,test]"
scripts/build_udlf.sh            # builds UDLF 1.70 from source into .udlf/ (used by the tests)
.venv/bin/python -m pytest
```

Os testes comparam cada execução do pyUDLF com o UDLF executado diretamente com a mesma
configuração, usando o dataset sintético em `tests/data/synthetic`. O GitHub Actions os executa a
cada push e pull request (`.github/workflows/tests.yml`): Linux com Python 3.9 a 3.13, o pacote
gerado, e Windows / macOS.


## Aplicações

Os métodos disponíveis no pyUDLF têm sido usados em diversos cenários de multimídia e aprendizado
de máquina. Entre eles:
- Recuperação de imagens e vídeos
- Re-identificação de pessoas (Person Re-ID)
- Classificação fracamente supervisionada
- Agrupamento (clustering)


## Citação
Se você usar este software, por favor cite

 ```latex
@inproceedings{pyUDLF,
    author = {Gustavo Leticio and Lucas Pascotti Valem and Leonardo Tadeu Lopes and Daniel Carlos Guimar\~{a}es Pedronette},
    title = {PyUDLF: A Python Framework for Unsupervised Distance Learning Tasks},
    year = {2023},
    isbn = {9798400701085},
    publisher = {Association for Computing Machinery},
    address = {New York, NY, USA},
    url = {https://doi.org/10.1145/3581783.3613466},
    doi = {10.1145/3581783.3613466},
    booktitle = {Proceedings of the 31st ACM International Conference on Multimedia},
    pages = {9680–9684},
    numpages = {5},
    series = {MM '23}
}
```

## Contato
**Gustavo Rosseto Leticio**: `gustavo.leticio@gmail.com` ou `gustavo.leticio@unesp.br`

**Lucas Pascotti Valem**: `lucaspascottivalem@gmail.com` ou `lucas.valem@unesp.br`

**Daniel Carlos Guimarães Pedronette**: `daniel.pedronette@unesp.br`


## Agradecimentos

Os autores agradecem à Fundação de Amparo à Pesquisa do Estado de São Paulo – FAPESP (processos 2013/08645-0, 2014/04220-8, 2018/15597-6) e ao Conselho Nacional de Desenvolvimento Científico e Tecnológico – CNPq (processos 309439/2020-5 e 422667/2021-8).


## Licença

Este projeto é licenciado sob a GPLv2. Veja os [detalhes.](https://github.com/UDLF/pyUDLF/blob/main/LICENSE)
