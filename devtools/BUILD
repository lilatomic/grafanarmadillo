python_sources()

python_requirements(
    name="reqs",
    source="docs_requirements.txt",
)

python_requirements(
    name="reqs0",
)

python_requirements(
    name="flake8",
    source="flake8_requirements.txt",
    resolve="flake8",
)

# <region name="radon">
python_requirement(name="radon", requirements=["radon"], resolve="radon")

code_quality_tool(
	name="radon_cc",
	runnable=":radon",
	args=["cc", "-s", "--total-average", "--no-assert", "-nb", "src/"],
	file_glob_include=["src/**/*.py"],
)
# </region>
