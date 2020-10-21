import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-pms",
    description="Meta package for oca-pms Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-pms',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
