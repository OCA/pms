import openerp.addons.connector.backend as backend


wubook = backend.Backend('wubook')
# version 1.2
wubook_1_2_0_0 = backend.Backend(parent=wubook, version='1.2')
