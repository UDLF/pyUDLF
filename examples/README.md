# pyUDLF examples

Runnable scripts showing how to use pyUDLF. Each one runs on its own on the synthetic dataset of the repository
(`tests/data/synthetic`: 200 elements, 10 classes), so they work right after installing:

```bash
pip install -e ".[viz]"        # from a clone of the repository
pyudlf download                # the UDLF binary
python examples/quickstart.py
```

The test suite runs every script (`tests/test_examples.py`), so they stay in sync with pyUDLF.

| Script | What it shows |
|---|---|
| [quickstart.py](quickstart.py) | The basics: build ranked lists from features, re-rank them with CPRR, read the results. |
| [compare_methods.py](compare_methods.py) | All 12 UDLF methods on the same input, ranked by MAP. |
| [parameter_search.py](parameter_search.py) | Grid search over `k` and `l`, and the best combination. |
| [input_formats.py](input_formats.py) | The same data as ranked lists (numpy, file, names) and as distance and similarity matrices; output as a matrix. |
| [fusion.py](fusion.py) | Fusion of the ranked lists of two descriptors (`udlf.fuse`). |
| [per_query_analysis.py](per_query_analysis.py) | Which queries improved or got worse, how their top 10 changed, and saving the re-ranked lists. |
| [your_own_data.py](your_own_data.py) | Command line for your own files: ranked lists, a matrix or features (`.npy`), with classes. |
| [csr_engines.py](csr_engines.py) | UDLF compared with the engines of UDLF-CSR (needs a UDLF-CSR build: `scripts/build_csr.sh`). |
| [legacy_api.py](legacy_api.py) | The API of previous versions (`InputType` + `run_calls`), still supported. |

## Your own data

```bash
python examples/your_own_data.py \
    --ranked-lists my_ranked_lists.txt --lists my_lists.txt --classes my_classes.txt \
    --method CPRR --param l=400 --param k=20 --output reranked.txt

python examples/your_own_data.py --features my_features.npy --classes-list my_labels.txt --method LHRR --param l=1000
```

`pyudlf methods` lists the methods and `pyudlf describe CPRR` the parameters of one. The file formats are described
in the main [README](../README.md#file-formats).

## Exemplos (português)

Scripts prontos para rodar, cada um com o dataset sintético do repositório. A tabela acima diz o que cada um mostra;
para usar com os seus dados, veja `your_own_data.py`. Todos são executados pelos testes, então funcionam com a
versão atual do pyUDLF.
