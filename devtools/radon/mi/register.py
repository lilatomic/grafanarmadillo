"""Plugin for Radon."""
from pants.backend.adhoc.code_quality_tool import CodeQualityToolRuleBuilder


def rules():
    """Plugin stub to create rules for Radon."""
    radon_cc = CodeQualityToolRuleBuilder(
        goal="lint", target="//devtools:radon_mi", name="Radon MI", scope="radon_mi"
    )
    return radon_cc.rules()
