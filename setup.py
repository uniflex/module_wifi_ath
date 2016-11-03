from setuptools import setup, find_packages


def readme():
    with open('README.md') as f:
        return f.read()


setup(
    name='uniflex_module_wifi_ath',
    version='0.1.0',
    packages=find_packages(),
    url='https://github.com/uniflex',
    license='',
    author='Piotr Gawlowicz',
    author_email='gawlowicz@tu-berlin.de',
    description='UniFlex ATH Modules',
    long_description='UniFlex ATH Modules',
    keywords='wireless control',
    install_requires=['netifaces', 'scapy-python3', 'numpy', 'python-iptables', 'pyroute2']
)
