python_distribution(
    name="grafanarmadillo",
    dependencies=[
        "//src/grafanarmadillo:grafanarmadillo",
        "//:docs",
        "//:pyproject",
#        "//:package_info",
    ],
    provides=python_artifact(
        name="grafanarmadillo",
        version="0.7.1",
    ),
    generate_setup=False,
)

files(
    name="docs",
    sources=["README.rst", "docs/**"],
)

python_requirements(
    name="reqs0",
    source="pyproject.toml",
)

resource(name="pyproject", source="pyproject.toml")
resources(name="package_info", sources=["LICENSE", "README.rst"])
