# Schemate

**Analyzes NoSQL or JSON documents to try to infer a schema or general properties.**

## Developer Information

If you are a schemate developer there are several helper utilities built into the library that will allow you to manage datasets and models both locally and in the cloud. But first, there are additional dependencies that you must install.

In `requirements.txt` uncomment the section that says: `"# Packaging Dependencies"`, e.g. your requirements should now have a section that appears similar to:

```
# Packaging Dependencies
black==25.1.0
build==1.2.2.post1
flake8==7.2.0
packaging==24.2
pip==25.0.1
setuptools==75.3.0
twine==6.1.0
wheel==0.45.1
```

**NOTE:** the README might not be up to date with all required dependencies, so make sure you use the latest `requirements.txt`.

Then install these dependencies and the test dependencies:

```
$ pip install -r requirements.txt
$ pip install -r tests/requirements.txt
```

### Tests and Linting

All tests are in the `tests` folder and are structured identically to the `schemate` module. All tests can be run with `pytest`:

```
$ pytest
```

We use `flake8` for linting as configured in `setup.cfg` -- note that the `.flake8` file is for IDEs only and is not used when running tests. If you want to use `black` to automatically format your files:

```
$ black path/to/file.py
```

### Releases

To release the schemate library and deploy to PyPI run the following commands:

```
$ python -m build
$ twine upload dist/*
```