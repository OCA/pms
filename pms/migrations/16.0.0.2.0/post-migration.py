from openupgradelib import openupgrade


def populate_properties_analytic_data(env):
    properties = env["pms.property"].search([("analytic_account_id", "=", False)])
    for pms_property in properties:
        analytic_acc_id = env["account.analytic.account"].create(
            {
                "name": pms_property.name,
                "code": pms_property.pms_property_code,
                "plan_id": env.ref("pms.main_pms_analytic_plan").id,
                "company_id": pms_property.company_id.id,
            }
        )
        pms_property.analytic_account_id = analytic_acc_id.id

        env["account.analytic.distribution.model"].create(
            {
                "pms_property_id": pms_property.id,
                "analytic_distribution": {analytic_acc_id.id: 100},
                "company_id": pms_property.company_id.id,
            }
        )


def recompute_analytic_lines(env):
    properties = env["pms.property"].search([])
    for pms_property in properties:
        result = env["account.move.line"]._read_group(
            domain=[
                ("pms_property_id", "=", pms_property.id),
                ("account_id.account_type", "in", ("income", "expense")),
            ],
            fields=["analytic_distribution", "ids:array_agg(id)"],
            groupby=["analytic_distribution"],
        )
        for res in result:
            distribution_dict = res["analytic_distribution"] or {}
            distribution_dict.update({pms_property.analytic_account_id.id: 100})
            lines = (
                env["account.move.line"]
                .with_context(
                    skip_account_move_synchronization=True, check_move_validity=False
                )
                .browse(res["ids"])
            )
            lines.write({"analytic_distribution": distribution_dict})


@openupgrade.migrate()
def migrate(env, version):
    populate_properties_analytic_data(env)

    # with a lot of data maybe will be better to run this manually in other moment
    # recompute_analytic_lines(env)
