import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-pms",
    description="Meta package for oca-pms Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-multi_pms_properties',
        'odoo14-addon-payment_acquirer_multi_pms_properties',
        'odoo14-addon-pms',
        'odoo14-addon-pms_housekeeping',
        'odoo14-addon-pms_l10n_es',
        'odoo14-addon-pms_rooming_xls',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
