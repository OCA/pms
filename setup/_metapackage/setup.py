import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-pms",
    description="Meta package for oca-pms Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-multi_pms_properties>=16.0dev,<16.1dev',
        'odoo-addon-pms>=16.0dev,<16.1dev',
        'odoo-addon-pms_account_move_budget>=16.0dev,<16.1dev',
        'odoo-addon-pms_hr_property>=16.0dev,<16.1dev',
        'odoo-addon-pms_l10n_es>=16.0dev,<16.1dev',
        'odoo-addon-pms_l10n_es_sii>=16.0dev,<16.1dev',
        'odoo-addon-pms_partner_identification>=16.0dev,<16.1dev',
        'odoo-addon-pms_partner_second_lastname>=16.0dev,<16.1dev',
        'odoo-addon-pos_pms_link>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
