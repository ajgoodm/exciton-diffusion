from setuptools import find_packages, setup

from exciton_diffusion import __version__ as version

setup(
    name="exciton_diffusion",
    version=version,
    packages=find_packages(),
    install_requires=["click"],
    entry_points={"console_scripts": ["exciton-diffusion=exciton_diffusion.cli:cli"]},
    include_package_data=True,
)
