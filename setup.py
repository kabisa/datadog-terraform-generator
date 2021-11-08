from setuptools import setup

# I've tried pyproject.toml but console_scripts weren't supported yet
setup(
    name="datadog_terraform_generator",
    description="Datadog Terraform Generator",
    packages=["datadog_terraform_generator"],
    package_data={"datadog_terraform_generator": ["*.tf", "tf_monitor_defaults.yaml"]},
    install_requires=["requests", "pyyaml", "argcomplete", "arrow"],
    entry_points={
        "console_scripts": ["ddtfgen=datadog_terraform_generator.main:main"],
    },
)
