python_requirements(
    name="reqs",
    module_mapping={
        "urllib3-future": ["urllib3", "urllib3.future"],
    },
)

python_test_utils(
    name="test_utils",
    dependencies=[":test_resources"],
)

python_sources()

python_tests(
    name="tests0",
    sources=["test_*.py", "*_test.py", "tests.py", "!test_doc_examples.py"],
)

pex_binary(
    name="grafanarmadillo",
    dependencies=[
        "//:grafanarmadillo",
    ],
    script="grafanarmadillo",
    output_path="tests/grafanarmadillo",  # ensure that there is no suffix on the PEX
)

python_tests(
    name="doc_example_tests",
    sources=["test_doc_examples.py"],
    runtime_package_dependencies=[
        ":grafanarmadillo",
    ],
    dependencies=[
        ":test_resources",
        "//tests/flow:flow",
    ],
)

files(
    name="test_resources",
    sources=["*.json", "**/*.json", "**/*.bash"],
)
