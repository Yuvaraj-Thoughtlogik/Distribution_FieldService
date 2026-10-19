import logging

from odoo import Command, api, models

_logger = logging.getLogger(__name__)

# Instruments assembled in-house at Milton Keynes, sold in configurable variants and built to order
# (product route Replenish on Order (MTO); the warehouse Manufacture route builds anything with a BoM).
#
# attributes: (attribute name, [(value, price extra GBP)]) - the first value of each is the default combination,
#             which keeps the instrument's original variant (stock, serials, sales and assets stay on it).
# components: (xml key, name, internal ref, cost GBP, qty per unit, only for these attribute values or None)
# operations: (name, work centre key, minutes per unit)
# codes: internal reference per combination (values in attribute order)
MANUFACTURED = {
    "db20": {
        "attributes": [
            ("Tube Size", [("250 mL", 0.0), ("100 mL", 0.0)]),
            ("Lift", [("Automatic", 0.0), ("Manual", -650.0)]),
        ],
        "components": [
            ("cmp_db20_block", "NA-DB20 Aluminium Heating Block, 20 x 250 mL", "CMP-DB20-BLK", 640.0, 1, ("250 mL",)),
            ("cmp_db20_block100", "NA-DB20 Aluminium Heating Block, 20 x 100 mL", "CMP-DB20-BLK100", 590.0, 1, ("100 mL",)),
            ("cmp_heater_400", "Cartridge Heater 400 W, 230 V", "CMP-HTR-400", 28.0, 6, None),
            ("cmp_tc_probe", "K-Type Thermocouple Probe, 150 mm", "CMP-TC-K150", 19.5, 2, None),
            ("cmp_ctrl_pcb", "NA-DB Temperature Controller PCB", "CMP-DB-PCB", 210.0, 1, None),
            ("cmp_lift", "NA-DB20 Automatic Lift Assembly", "CMP-DB20-LIFT", 385.0, 1, ("Automatic",)),
            ("cmp_lift_manual", "NA-DB20 Manual Lift Handle & Rack Kit", "CMP-DB20-MLK", 95.0, 1, ("Manual",)),
            ("cmp_manifold", "Exhaust Manifold, 20 Positions (PTFE)", "CMP-DB20-MAN", 165.0, 1, None),
            ("cmp_housing_db20", "NA-DB20 Stainless Steel Housing", "CMP-DB20-HSG", 240.0, 1, None),
            ("cmp_loom", "Mains Inlet, Fusing & Wiring Loom", "CMP-LOOM-230", 42.0, 1, None),
            ("cmp_pack_l", "Shipping Crate, Large + Manual Pack", "CMP-PACK-L", 35.0, 1, None),
        ],
        "operations": [
            ("Mechanical assembly", "assembly", 120),
            ("Electrical wiring & PAT safety test", "assembly", 45),
            ("Temperature calibration & 4 h burn-in", "test", 60),
            ("Final inspection & packing", "test", 20),
        ],
        "codes": {
            ("250 mL", "Automatic"): "NA-DB20", ("250 mL", "Manual"): "NA-DB20-M",
            ("100 mL", "Automatic"): "NA-DB20-100", ("100 mL", "Manual"): "NA-DB20-100M",
        },
    },
    "sc4": {
        "attributes": [
            ("Configuration", [("3-stage", 0.0), ("2-stage", -290.0)]),
            ("Pump", [("Standard", 0.0), ("Chemically resistant (PTFE)", 420.0)]),
        ],
        "components": [
            ("cmp_sc4_housing", "NA-SC4 Polypropylene Scrubber Housing", "CMP-SC4-HSG", 155.0, 1, None),
            ("cmp_pump_24v", "Diaphragm Vacuum Pump, 24 V DC", "CMP-PUMP-24V", 185.0, 1, ("Standard",)),
            ("cmp_pump_ptfe", "PTFE Diaphragm Vacuum Pump, 24 V DC (chemically resistant)", "CMP-PUMP-PTFE", 410.0, 1,
             ("Chemically resistant (PTFE)",)),
            ("cmp_bottle_2l", "Neutralisation Bottle 2 L with Cap", "CMP-BTL-2L", 22.0, 1, None),
            ("cmp_bottle_2l", None, None, None, 1, ("3-stage",)),  # second bottle on 3-stage units
            ("cmp_carbon", "Activated Carbon Filter Cartridge", "CMP-CARB-01", 38.0, 1, ("3-stage",)),
            ("cmp_tubing", "PTFE / Silicone Tubing Set", "CMP-TUBE-SET", 26.0, 1, None),
            ("cmp_sc4_ctrl", "NA-SC4 Control Board & 24 V PSU", "CMP-SC4-CTRL", 120.0, 1, None),
            ("cmp_pack_m", "Shipping Carton, Medium + Manual Pack", "CMP-PACK-M", 18.0, 1, None),
        ],
        "operations": [
            ("Assembly & leak test", "assembly", 60),
            ("Flow test & final inspection", "test", 25),
        ],
        "codes": {
            ("3-stage", "Standard"): "NA-SC4", ("2-stage", "Standard"): "NA-SC4-2S",
            ("3-stage", "Chemically resistant (PTFE)"): "NA-SC4-PTFE",
            ("2-stage", "Chemically resistant (PTFE)"): "NA-SC4-2S-PTFE",
        },
    },
}
WORKCENTERS = {
    "assembly": ("Assembly Bench", "ASM", 55.0),
    "test": ("Test & Calibration Bay", "TST", 65.0),
}
COMPONENT_STOCK = 6  # enough to build several units of each instrument


class TlDfsDemoLoader(models.AbstractModel):
    _inherit = "tl.dfs.demo.loader"

    @api.model
    def _setup_manufacturing(self):
        """Variants, work centres, components, BoMs and MTO + Manufacture routes for in-house instruments.

        Called from data/manufacturing_data.xml (install and update) and from action_load_all. Idempotent.
        """
        self = self.sudo().with_context(tracking_disable=True, mail_create_nolog=True)  # noqa: PLW0642
        # The historical demo sales ship these instruments from stock: only switch them to MTO afterwards.
        # (On a fresh install, data files run before the sales exist; action_load_all calls this again.)
        if "mrp.bom" not in self.env or not self._ref("so_dalesway_protein_lab"):
            return
        try:
            self.env["res.config.settings"].create({
                "group_mrp_routings": True, "group_product_variant": True,
            }).execute()
        except Exception:  # noqa: BLE001 - settings are a nicety, BoMs and variants work without them
            _logger.exception("tl_dfs_demo_data: could not enable work orders / variants")

        warehouse = self.env["stock.warehouse"].search([("company_id", "=", self.env.company.id)], limit=1)
        mto = self.env.ref("stock.route_warehouse0_mto")
        if not mto.active:
            mto.with_context(active_test=False).rule_ids.action_unarchive()
            mto.action_unarchive()
        # Odoo 20: "Manufacture" is a warehouse route (not product-selectable) used for products with a BoM.
        warehouse.manufacture_to_resupply = True

        centres = {
            key: self._ensure(f"mrp_workcenter_{key}", "mrp.workcenter", {
                "name": name, "code": code, "costs_hour": cost, "time_efficiency": 100,
                "company_id": self.env.company.id,
            })
            for key, (name, code, cost) in WORKCENTERS.items()
        }
        category = self._ensure("product_category_components", "product.category", {
            "name": "Components & Sub-assemblies",
            "parent_id": self._ref("product_category_lab_equipment").id,
        })
        vendor = self._ref("partner_vendor_kjelmark")

        for product_key, spec in MANUFACTURED.items():
            finished = self._ref("product_" + product_key)
            if not finished:
                continue
            ptav = self._setup_variants(finished, spec)
            lines = []
            for key, name, ref, cost, qty, applies in spec["components"]:
                component = self._ensure(f"product_{key}", "product.template", lambda name=name, ref=ref, cost=cost: {
                    "name": name, "default_code": ref, "type": "consu", "is_storable": True,
                    "categ_id": category.id, "standard_price": cost, "list_price": round(cost * 1.6, 2),
                    "sale_ok": False, "purchase_ok": True, "is_published": False,
                    "seller_ids": [Command.create({"partner_id": vendor.id, "price": cost, "delay": 10})]
                    if vendor else [],
                })
                lines.append(Command.create({
                    "product_id": component.product_variant_id.id, "product_qty": qty,
                    "bom_product_template_attribute_value_ids": [Command.set([ptav[v].id for v in applies])]
                    if applies else [],
                }))
            self._ensure(f"mrp_bom_{product_key}", "mrp.bom", {
                "product_tmpl_id": finished.id, "product_qty": 1, "type": "normal", "code": finished.default_code,
                "produce_delay": 5,
                "bom_line_ids": lines,
                "operation_ids": [
                    Command.create({"name": name, "workcenter_id": centres[wc].id, "time_cycle_manual": minutes,
                                    "sequence": 10 * (i + 1)})
                    for i, (name, wc, minutes) in enumerate(spec["operations"])
                ],
            })
            finished.route_ids = [Command.link(mto.id)]

        if not self._step_done("mrp_component_stock"):
            products = {
                self._ref(f"product_{key}").product_variant_id
                for spec in MANUFACTURED.values() for key, *_rest in spec["components"]
            }
            self._apply_inventory([
                (product, warehouse.lot_stock_id, False, COMPONENT_STOCK * 2) for product in products
            ])
            self._mark_step("mrp_component_stock")

        self._setup_mto_demo_order()

    def _setup_variants(self, template, spec):
        """Add the configurable attributes, keeping the existing variant as the default combination.

        Adding attributes makes Odoo archive the original variant and create new ones; the original one
        carries stock, serial numbers, sales and customer assets, so it takes over the default combination
        instead. Returns {value name: product.template.attribute.value}.
        """
        Attribute = self.env["product.attribute"]
        if not template.attribute_line_ids:
            original = template.product_variant_id
            lines = []
            for attr_name, values in spec["attributes"]:
                attribute = Attribute.search([("name", "=", attr_name)], limit=1) or Attribute.create({
                    "name": attr_name, "create_variant": "always", "display_type": "pills",
                })
                for value_name, _extra in values:
                    if value_name not in attribute.value_ids.mapped("name"):
                        attribute.value_ids = [Command.create({"name": value_name})]
                lines.append(Command.create({
                    "attribute_id": attribute.id,
                    "value_ids": [Command.set(attribute.value_ids.filtered(
                        lambda v: v.name in [n for n, _e in values]).ids)],
                }))
            template.attribute_line_ids = lines
            first_value = {attr_name: values[0][0] for attr_name, values in spec["attributes"]}
            default = template.attribute_line_ids.product_template_value_ids.filtered(
                lambda v: v.name == first_value[v.attribute_id.name])
            template.product_variant_ids.filtered(lambda p: p.product_template_attribute_value_ids == default).unlink()
            original.write({"product_template_attribute_value_ids": [Command.set(default.ids)], "active": True})

        ptav = {v.name: v for v in template.attribute_line_ids.product_template_value_ids}
        for _attr, values in spec["attributes"]:
            for value_name, extra in values:
                ptav[value_name].price_extra = extra
        for variant in template.product_variant_ids:
            key = tuple(variant.product_template_attribute_value_ids.sorted(
                lambda v: [a for a, _vals in spec["attributes"]].index(v.attribute_id.name)).mapped("name"))
            if spec["codes"].get(key):
                variant.default_code = spec["codes"][key]
        return ptav

    def _variant(self, product_key, *values):
        template = self._ref("product_" + product_key)
        return template.product_variant_ids.filtered(
            lambda p: set(p.product_template_attribute_value_ids.mapped("name")) == set(values))[:1]

    @api.model
    def _setup_mto_demo_order(self):
        """A confirmed sale of configured, built-to-order instruments: one MO built, one waiting to start."""
        if self._ref("so_mto_01") or not self._ref("mrp_bom_db20"):
            return
        self = self.sudo().with_context(tracking_disable=True, mail_create_nolog=True)  # noqa: PLW0642
        db20 = self._variant("db20", "100 mL", "Automatic")
        sc4 = self._variant("sc4", "3-stage", "Chemically resistant (PTFE)")
        so = self._create_so("so_mto_01", "highland", None, None, 3, [("db20", 1), ("sc4", 1)],
                             {"ref": "HD-PO-7731", "commitment": 12})
        for line, variant in zip(so.order_line, (db20, sc4)):
            if variant:
                line.product_id = variant
        so.action_confirm()
        productions = so.mrp_production_ids
        _logger.info("tl_dfs_demo_data: %s created manufacturing orders %s", so.name, productions.mapped("name"))

        # Build the block digester; leave the scrubber for the user to process.
        mo = productions.filtered(lambda p: p.product_id.product_tmpl_id == self._ref("product_db20"))[:1]
        if mo:
            try:
                mo.action_assign()
                lot = self.env["stock.lot"].create({
                    "name": f"DB20-{self._today():%y%m}01", "product_id": mo.product_id.id,
                    "company_id": mo.company_id.id,
                })
                mo.lot_producing_ids = [Command.set(lot.ids)]
                mo.qty_producing = 1
                for move in mo.move_raw_ids:
                    move.quantity = move.product_uom_qty
                    move.picked = True
                mo.button_mark_done()
            except Exception:  # noqa: BLE001 - keep the MO open rather than failing the demo load
                _logger.exception("tl_dfs_demo_data: could not complete demo MO %s", mo.name)
