import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-pms",
    description="Meta package for oca-pms Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-pms_account',
        'odoo14-addon-pms_base',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
