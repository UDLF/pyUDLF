# build package
python setup.py bdist_wheel

# install package
pip install --force dist/*.whl

