python_distribution(
    name="grafanarmadillo",
    dependencies=[
        "//:setup.py",
        "//src/grafanarmadillo:grafanarmadillo",
        "//:docs",
    ],
    provides=python_artifact(
        name="grafanarmadillo",
        version="0.5.0",
    ),
    generate_setup=False,
)

files(
    name="docs",
    sources=["README.rst", "docs/**"],
)

python_sources(
    name="setup.py",
)

python_requirements(
    name="reqs0",
    source="pyproject.toml",
)
