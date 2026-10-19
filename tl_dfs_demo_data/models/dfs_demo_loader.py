"""Python loader for the configuration and transactional demo data of tl_dfs_demo_data.

Every step is idempotent: master records created here are bound to xml ids
(``tl_dfs_demo_data.<name>``, noupdate) and transactional steps are guarded by a
marker in ``ir.config_parameter`` (``tl_dfs_demo_data.step.<name>``).
"""
import logging
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from odoo import Command, api, fields, models

_logger = logging.getLogger(__name__)

MODULE = "tl_dfs_demo_data"
TZ = ZoneInfo("Europe/London")
UTC = ZoneInfo("UTC")
DEMO_PASSWORD = "northbrook"

# customer key -> (pricelist key, salesperson employee key, sales team xml id)
CUSTOMER_ACCOUNTS = {
    "dalesway": ("trade", "tfletcher", "sales_team.team_sales_department"),
    "cotswold": ("trade", "psharma", "sales_team.team_sales_department"),
    "highland": ("trade", "tfletcher", "sales_team.team_sales_department"),
    "fenland": ("key", "hprice", "crm_team_key_accounts"),
    "ironbridge": ("trade", "psharma", "sales_team.team_sales_department"),
    "thamesvalley": ("trade", "psharma", "sales_team.team_sales_department"),
    "pennine": ("key", "hprice", "crm_team_key_accounts"),
    "severn": ("trade", "psharma", "sales_team.team_sales_department"),
    "albion": ("key", "hprice", "crm_team_key_accounts"),
    "northgate": ("trade", "tfletcher", "sales_team.team_sales_department"),
    "wessex": ("edu", "psharma", "sales_team.team_sales_department"),
    "caledonian": ("edu", "tfletcher", "sales_team.team_sales_department"),
    "wmpal": ("edu", "psharma", "sales_team.team_sales_department"),
    "kentss": ("edu", "psharma", "sales_team.team_sales_department"),
    "cambrian": ("trade", "psharma", "crm_team_website"),
    "northumbria": ("trade", "tfletcher", "sales_team.team_sales_department"),
}

# employee key -> group xml ids (besides base.group_user)
USER_GROUPS = {
    "slockwood": ["sales_team.group_sale_manager", "planning.group_planning_user", "purchase.group_purchase_user"],
    "hprice": ["sales_team.group_sale_salesman_all_leads", "planning.group_planning_user"],
    "tfletcher": ["sales_team.group_sale_salesman_all_leads", "planning.group_planning_user"],
    "psharma": ["sales_team.group_sale_salesman_all_leads", "planning.group_planning_user"],
    "emorgan": ["sales_team.group_sale_salesman_all_leads", "purchase.group_purchase_user"],
    "gevans": ["planning.group_planning_manager", "helpdesk.group_helpdesk_user", "stock.group_stock_user",
               "sales_team.group_sale_salesman_all_leads", "hr_timesheet.group_hr_timesheet_user"],
    "dokafor": ["planning.group_planning_user", "helpdesk.group_helpdesk_user", "stock.group_stock_user",
                "hr_timesheet.group_hr_timesheet_user"],
    "rpatel": ["planning.group_planning_user", "helpdesk.group_helpdesk_user", "stock.group_stock_user",
               "hr_timesheet.group_hr_timesheet_user"],
    "ldoyle": ["planning.group_planning_user", "helpdesk.group_helpdesk_user", "stock.group_stock_user",
               "hr_timesheet.group_hr_timesheet_user"],
    "sturner": ["planning.group_planning_user", "helpdesk.group_helpdesk_user", "stock.group_stock_user",
                "hr_timesheet.group_hr_timesheet_user"],
    "mbennett": ["planning.group_planning_user", "helpdesk.group_helpdesk_user", "stock.group_stock_user",
                 "hr_timesheet.group_hr_timesheet_user"],
    "lchen": ["helpdesk.group_helpdesk_manager", "planning.group_planning_user", "sales_team.group_sale_salesman"],
    "bharris": ["helpdesk.group_helpdesk_user", "planning.group_planning_user", "sales_team.group_sale_salesman_all_leads"],
    "awright": ["helpdesk.group_helpdesk_user", "planning.group_planning_user"],
}
USER_LOGINS = {
    "slockwood": "Simon Lockwood", "hprice": "Hannah Price", "tfletcher": "Tom Fletcher",
    "psharma": "Priya Sharma", "emorgan": "Ellie Morgan", "gevans": "Gareth Evans",
    "dokafor": "Daniel Okafor", "rpatel": "Ravi Patel", "ldoyle": "Liam Doyle",
    "sturner": "Sophie Turner", "mbennett": "Marcus Bennett", "lchen": "Laura Chen",
    "bharris": "Ben Harris", "awright": "Amelia Wright",
}

# Opening stock -------------------------------------------------------------------------
# equipment: product key -> number of current serials in stock
OPENING_SERIALS = {
    "kd40": 4, "kd20": 3, "dn100": 2, "kt8": 2, "db20": 4, "db8": 2, "sc4": 3, "fx6": 2, "fx2": 3, "hy6": 1,
    "fb6": 1, "fb24": 2, "mb120": 5, "mb60": 3, "dm50": 2, "rc12": 3, "hc8": 2, "ch600": 2, "wb22": 4,
    "swb28": 2, "do110": 2, "mf9": 2, "vo50": 1, "lm200": 3, "km10": 2, "hg400": 2, "hs25": 3, "cf16": 3,
}
OPENING_LOTS = {  # lot-tracked spares: key -> (lot name, qty)
    "heater_kd": [("HE01-2604", 8)], "pcb_db": [("PCB1-2603", 4)], "lamp_mb": [("HL01-2605", 12)],
    "pump_rc": [("PA01-2602", 3)], "comb_tube": [("QT01-2606", 6)],
}
OPENING_EXPIRY = {  # lot + expiry (days from today)
    "cat_tabs": [("CAT-2605A", 30, 820), ("CAT-2511B", 6, 75)],
    "boric": [("BAS-2607A", 40, 420), ("BAS-2601C", 8, 35)],
}
OPENING_QTY = {
    "splash_kd": 10, "thimble_holder": 6, "peri_tubing": 25, "screen_1mm": 8, "tubes250": 60, "thimbles": 80,
    "filter_bags": 30, "pet_ether": 24, "beakers": 40, "volflask": 50, "al_dishes": 45, "tin_caps": 20,
    "buchner": 12, "dounce": 10,
}
# Installed base sold before go-live (migrated): customer, delivery address key, product, serial, delivered on
LEGACY_BASE = [
    ("dalesway", "dalesway_settle", "wb22", "WB22-220311", date(2022, 3, 14)),
    ("dalesway", "dalesway_settle", "do110", "DO110-230087", date(2023, 5, 9)),
    ("cotswold", None, "kd20", "KD20-210156", date(2021, 11, 2)),
    ("cotswold", None, "db8", "DB8-210098", date(2021, 11, 2)),
    ("cotswold", None, "mb60", "MB60-230412", date(2023, 6, 20)),
    ("pennine", None, "mf9", "MF9-220077", date(2022, 9, 5)),
    ("pennine", None, "hg400", "HG400-240231", date(2024, 2, 12)),
    ("albion", "albion_runcorn", "fx6", "FX6-230045", date(2023, 4, 18)),
    ("albion", "albion_runcorn", "fb6", "FB6-230019", date(2023, 4, 18)),
    ("albion", None, "rc12", "RC12-240158", date(2024, 1, 22)),
    ("albion", None, "ch600", "CH600-240066", date(2024, 1, 22)),
    ("wessex", None, "swb28", "SWB28-220103", date(2022, 8, 30)),
    ("wessex", None, "hs25", "HS25-230388", date(2023, 9, 11)),
    ("wmpal", None, "kd40", "KD40-220034", date(2022, 6, 7)),
    ("wmpal", None, "db20", "DB20-220051", date(2022, 6, 7)),
    ("severn", None, "hg400", "HG400-230190", date(2023, 3, 28)),
    ("severn", None, "cf16", "CF16-240219", date(2024, 7, 15)),
    ("northgate", None, "dn100", "DN100-240012", date(2024, 10, 1)),
    ("thamesvalley", None, "mb120", "MB120-240577", date(2024, 5, 13)),
]

# Sales ---------------------------------------------------------------------------------
# key, customer, contact, delivery, days ago (order), status, lines, extra
#   status: draft | sent | sale | delivered | invoiced | paid
SALES = [
    ("so_dalesway_protein_lab", "dalesway", "rhughes", None, 70, "paid",
     [("kd40", 1), ("db20", 1), ("sc4", 1), ("mb120", 2), ("tubes250", 3), ("cat_tabs", 2), ("svc_install", 2)],
     {"ref": "PO-DD-44871", "deliver_after": 14, "install": ("ldoyle", 17, 2, "4_completed")}),
    ("so_pennine_qc_upgrade", "pennine", "glomas", None, 48, "invoiced",
     [("dm50", 1), ("km10", 1), ("fx6", 1), ("thimbles", 4), ("svc_install", 1), ("svc_training", 1)],
     {"ref": "PMP/PO/2026/0912", "deliver_after": 13, "install": ("ldoyle", 15, 1, "4_completed")}),
    ("so_albion_runcorn_lab", "albion", "nbrooks", "albion_runcorn", 29, "delivered",
     [("dn100", 1), ("kd40", 1), ("db20", 1), ("cf16", 1), ("tin_caps", 2), ("svc_install", 2)],
     {"ref": "AAS-PO-10233", "deliver_after": 15, "install": ("ldoyle", 17, 2, "4_completed")}),
    ("so_highland_mill_moisture", "highland", "cfraser", None, 16, "delivered",
     [("lm200", 1), ("mb120", 1), ("screen_1mm", 2), ("al_dishes", 2), ("svc_install", 1)],
     {"ref": "HGM-7765", "deliver_after": 7, "install": ("ldoyle", 2, 1, "2_published")}),
    ("so_ironbridge_thermal", "ironbridge", "jholloway", None, 9, "sale",
     [("wb22", 2), ("rc12", 1), ("beakers", 4)], {"ref": "IBC-0419", "commitment": 8}),
    ("so_wessex_teaching_lab", "wessex", "lgrant", None, 6, "sale",
     [("fx2", 2), ("kd20", 1), ("svc_training", 1)], {"ref": "UOW-PO-552190", "commitment": 14}),
    ("so_cotswold_kjeldahl", "cotswold", "acollins", None, 5, "sent",
     [("kd20", 1), ("db8", 1), ("sc4", 1), ("svc_install", 1)], {}),
    ("so_fenland_fibre", "fenland", "pgrant", None, 4, "sent",
     [("fb24", 1), ("lm200", 1), ("mb60", 2)], {}),
    ("so_northgate_fat", "northgate", "kwalsh", None, 2, "draft", [("hy6", 1), ("fx6", 1), ("thimbles", 2)], {}),
    ("so_wmpal_dumas", "wmpal", "rkumar", None, 1, "draft", [("dn100", 1), ("svc_install", 1), ("svc_extw", 1)],
     {"pricelist": "edu"}),
]
SUBSCRIPTIONS = [
    # key, customer, product, start (days ago), invoice?
    ("sub_dalesway_gold", "dalesway", "sc_gold", 48, True),
    ("sub_pennine_silver", "pennine", "sc_silver", 18, True),
    ("sub_albion_gold", "albion", "sc_gold", 290, True),
    ("sub_wmpal_silver", "wmpal", "sc_silver", 120, False),
]

PURCHASES = [
    # key, vendor, days ago, lines, receive (days ago or None), state
    ("po_kjelmark_stock", "kjelmark", 34, [("kd40", 2), ("db20", 2), ("heater_kd", 6)], 13, "received"),
    ("po_estrava_stock", "estrava", 30, [("fx6", 2), ("filter_bags", 10)], 9, "received"),
    ("po_meridian_consumables", "meridian", 12, [("tubes250", 20), ("cat_tabs", 10), ("boric", 20), ("thimbles", 20)],
     5, "received"),
    ("po_calderbrook_thermal", "calderbrook", 6, [("rc12", 2), ("wb22", 4), ("ch600", 1)], None, "purchase"),
    ("po_feinwaage_moisture", "feinwaage", 1, [("mb120", 3), ("lamp_mb", 10)], None, "sent"),
]

# CRM opportunities: key, customer, contact, name, stage, revenue, prob(None=stage), team, user, tags, days to close,
#   activity (type, days, summary) | None, quote lines | None, extra
OPPORTUNITIES = [
    ("opp_dalesway_protein", "dalesway", "rhughes", "Dalesway - new protein laboratory (Kjeldahl + moisture)", "won",
     36800, None, "sales_team.team_sales_department", "tfletcher", ["kjeldahl", "new_lab"], -70, None, None,
     {"order": "so_dalesway_protein_lab"}),
    ("opp_pennine_qc", "pennine", "skaye", "Pennine - QC lab upgrade (fat/moisture)", "won", 44200, None,
     "crm_team_key_accounts", "hprice", ["fat", "moisture"], -48, None, None, {"order": "so_pennine_qc_upgrade"}),
    ("opp_cotswold_kjeldahl", "cotswold", "acollins", "Cotswold Creamery - replace 2011 Kjeldahl line", "crm.stage_lead3",
     12900, None, "sales_team.team_sales_department", "psharma", ["kjeldahl", "replacement"], 21,
     ("mail.mail_activity_data_call", 3, "Follow up on quotation and site services"), None,
     {"order": "so_cotswold_kjeldahl"}),
    ("opp_fenland_fibre", "fenland", "pgrant", "Fenland Cereals - fibre & milling capacity", "crm.stage_lead3", 21000,
     None, "crm_team_key_accounts", "hprice", ["replacement"], 30,
     ("mail.mail_activity_data_meeting", 6, "Technical review with Head of Quality"), None,
     {"order": "so_fenland_fibre"}),
    ("opp_northgate_fat", "northgate", "kwalsh", "Northgate Labs - automated fat extraction", "crm_stage_negotiation",
     26100, None, "sales_team.team_sales_department", "tfletcher", ["fat"], 14,
     ("mail.mail_activity_data_todo", 2, "Prepare revised price with 3-year service plan"), None,
     {"order": "so_northgate_fat"}),
    ("opp_wmpal_dumas", "wmpal", "rkumar", "WM Public Analyst - Dumas analyser (framework tender)", "crm_stage_negotiation",
     40200, 60, "sales_team.team_sales_department", "psharma", ["tender", "kjeldahl"], 45,
     ("mail.mail_activity_data_todo", 10, "Submit tender documents via procurement portal"), None,
     {"order": "so_wmpal_dumas"}),
    ("opp_caledonian_teaching", "caledonian", "ecampbell", "Caledonian Uni - teaching lab refresh", "crm_stage_demo",
     18500, None, "sales_team.team_sales_department", "tfletcher", ["education", "new_lab"], 60,
     ("mail.mail_activity_data_meeting", 8, "On-site demo of NA-FX2 and NA-KD20"),
     [("fx2", 1), ("kd20", 1), ("db8", 1)], {}),
    ("opp_highland_dumas", "highland", "imackenzie", "Highland Grain - Dumas to replace wet chemistry", "crm.stage_lead2",
     38500, None, "sales_team.team_sales_department", "tfletcher", ["kjeldahl"], 120,
     ("mail.mail_activity_data_call", 5, "Qualify budget for FY27"), None, {}),
    ("opp_severn_moisture", "severn", "hdavies", "Severn Valley - moisture analysers for 3 sites", "crm_stage_demo", 7950,
     None, "sales_team.team_sales_department", "psharma", ["moisture"], 35,
     ("mail.mail_activity_data_meeting", 4, "Demo NA-MB120 at Shrewsbury site"), [("mb120", 3), ("al_dishes", 3)], {}),
    ("opp_thames_lab", "thamesvalley", "oreed", "Thames Valley Brewery - lab expansion", "crm.stage_lead1", 9000, None,
     "sales_team.team_sales_department", "psharma", ["new_lab"], 90, ("mail.mail_activity_data_call", 1,
     "Discovery call"), None, {}),
    ("opp_albion_service", "albion", "jwhitaker", "Albion - multi-site Gold service agreement", "crm.stage_lead3", 9600,
     None, "crm_team_service", "gevans", ["service"], 25, ("mail.mail_activity_data_todo", 7,
     "Asset survey for Runcorn site"), None, {"recurring": 9600}),
    ("opp_northumbria_service", "northumbria", "crobson", "Northumbria Bakeries - Silver contract for moisture ovens",
     "crm.stage_lead2", 1450, None, "crm_team_service", "gevans", ["service"], 40, None, None, {"recurring": 1450}),
    ("opp_kent_lost", "kentss", "pfisher", "Kent Scientific - block digester replacement", "lost", 5850, None,
     "sales_team.team_sales_department", "psharma", ["replacement"], -20, None, None, {}),
    ("lead_web_cambrian", "cambrian", "rllewellyn", "Website enquiry: moisture testing for bottled water plant",
     "lead", 2650, None, "crm_team_website", "emorgan", ["website", "moisture"], 30,
     ("mail.mail_activity_data_call", 1, "Call back website enquiry"), None, {}),
    ("lead_web_bakery", None, None, "Website enquiry: fat analysis for artisan bakery group", "lead", 7900, None,
     "crm_team_website", "emorgan", ["website", "fat"], 45, ("mail.mail_activity_data_email", 2, "Send brochure"),
     None, {"contact_name": "Megan Price", "email": "megan.price@hearthstonebakers.example",
            "partner_name": "Hearthstone Bakers Ltd", "city": "York"}),
    ("lead_web_uni", None, None, "Website enquiry: circulators for food engineering lab", "lead", 8700, None,
     "crm_team_website", "emorgan", ["website", "education"], 75, None, None,
     {"contact_name": "Dr Owen Price", "email": "o.price@midlands-uni.example",
      "partner_name": "Midlands University - Food Engineering", "city": "Nottingham"}),
]

# Field service ----------------------------------------------------------------------------------
# key, customer, name, role, engineer(s), day offset, start hour, duration h, state, priority, worksheet,
#   lots (serial names), ticket key
INTERVENTIONS = [
    ("fs_cal_thames", "thamesvalley", "Annual calibration - NA-MB120 moisture analyser", "calibration", ["sturner"],
     -13, 9, 3, "4_completed", "0", "worksheet_calibration", ["MB120-240577"], None),
    ("fs_pm_cotswold", "cotswold", "Preventive maintenance - Kjeldahl line (KD20 + DB8)", "fse", ["rpatel"], -11, 8.5,
     6, "4_completed", "0", "worksheet_maintenance", ["KD20-210156", "DB8-210098"], None),
    ("fs_repair_severn", "severn", "Breakdown repair - centrifuge imbalance error E-12", "fse", ["mbennett"], -6, 10, 4,
     "4_completed", "2", "worksheet_maintenance", ["CF16-240219"], "ticket_severn_centrifuge"),
    ("fs_cal_wmpal", "wmpal", "Calibration & recovery check - NA-KD40 / NA-DB20", "calibration", ["sturner"], -5, 9, 5,
     "4_completed", "1", "worksheet_calibration", ["KD40-220034", "DB20-220051"], "ticket_wmpal_certificate"),
    ("fs_repair_albion_fx6", "albion", "URGENT breakdown - NA-FX6 solvent leak, position 3", "fse", ["dokafor"], 0, 9, 6,
     "3_in_progress", "3", "worksheet_maintenance", ["FX6-230045"], "ticket_albion_fx6"),
    ("fs_repair_northgate_dn100", "northgate", "Breakdown - NA-DN100 low nitrogen recovery / leak check", "fse",
     ["dokafor"], 1, 9, 5, "2_published", "2", "worksheet_maintenance", ["DN100-240012"], "ticket_northgate_dn100"),
    ("fs_pm_dalesway_gold", "dalesway", "Gold contract PM visit 1/2 - protein lab", "fse", ["rpatel"], 3, 8.5, 7,
     "2_published", "1", "worksheet_maintenance", "@so_dalesway_protein_lab", None),
    ("fs_cal_wessex", "wessex", "Calibration - shaking water bath & homogeniser", "calibration", ["sturner"], 4, 10, 4,
     "2_published", "0", "worksheet_calibration", ["SWB28-220103", "HS25-230388"], "ticket_wessex_bath"),
    ("fs_pm_pennine_silver", "pennine", "Silver contract PM visit - QC laboratory", "fse", ["mbennett"], 8, 8.5, 6,
     "2_published", "0", "worksheet_maintenance", ["MF9-220077", "HG400-240231"], None),
    ("fs_cal_dalesway_mb", "dalesway", "Calibration - NA-MB120 moisture analysers (x2)", "calibration", ["sturner"], 9,
     9, 4, "2_published", "0", "worksheet_calibration", "@so_dalesway_protein_lab:mb120", None),
    ("fs_install_ironbridge", "ironbridge", "Installation - circulator and water baths", "install", ["ldoyle"], 10, 9,
     6, "1_draft", "0", "worksheet_installation", [], None),
    ("fs_pm_kent_open", "kentss", "Preventive maintenance - digestion block (to be assigned)", "fse", [], 11, 9, 4,
     "1_draft", "0", "worksheet_maintenance", [], None),
]

TICKETS = [
    # key, contact, name, stage, priority, tags, agent, description, lots
    ("ticket_severn_centrifuge", "hdavies", "Centrifuge stops with imbalance error E-12", "helpdesk.stage_solved", "2",
     ["breakdown", "warranty"], "awright",
     "NA-CF16 stops after 30 s with error E-12 even with balanced tubes. Instrument is under warranty.",
     ["CF16-240219"]),
    ("ticket_albion_fx6", "glee", "NA-FX6 solvent leak at extraction position 3", "helpdesk.stage_in_progress", "3",
     ["breakdown"], "lchen",
     "Petroleum ether leaking from the condenser seal on position 3. Unit isolated, urgent for client deadlines.",
     ["FX6-230045"]),
    ("ticket_northgate_dn100", "kwalsh", "Dumas analyser: low nitrogen recovery, leak check fails",
     "helpdesk.stage_in_progress", "2", ["breakdown"], "bharris",
     "EDTA standard recovering 96.8 %. Leak check fails at the autosampler. Please send an engineer.",
     ["DN100-240012"]),
    ("ticket_cotswold_method", "sbell", "Method advice: protein in butter on NA-KD20", "helpdesk.stage_new", "1",
     ["application"], "bharris", "Could you share a validated digestion/distillation method for butter samples?",
     ["KD20-210156"]),
    ("ticket_dalesway_lamp", "msutton", "Quote for spare halogen lamps (NA-MB120)", "helpdesk.stage_on_hold", "0",
     ["spares"], "awright", "Please quote 2 x spare halogen lamps for our moisture analysers.", []),
    ("ticket_wmpal_certificate", "sroberts", "Copy of calibration certificate for UKAS audit", "helpdesk.stage_solved",
     "1", ["calibration"], "awright", "Need the latest calibration certificates for the KD40 and DB20 before audit.",
     ["KD40-220034", "DB20-220051"]),
    ("ticket_wessex_bath", "akowalski", "Shaking water bath overshoots set temperature", "helpdesk.stage_new", "1",
     ["breakdown"], "lchen", "Bath overshoots by ~2 deg C at 37 deg C set point.", ["SWB28-220103"]),
    ("ticket_cambrian_web", "bjones", "Moisture analyser not powering on (website form)", "helpdesk.stage_new", "0",
     [], False, "Submitted via website support form: unit does not power on after a power cut.", []),
]

# hr_skills
SKILLS = {
    "Instrument Service Certification": (["Kjeldahl & Digestion", "Dumas Combustion", "Soxhlet / Fat Extraction",
                                          "Moisture Analysers", "Thermal (baths, ovens, circulators)"],
                                         [("Trainee", 25), ("Certified", 60), ("Master Technician", 100)]),
}
EMPLOYEE_SKILLS = {
    "gevans": [("Kjeldahl & Digestion", "Master Technician"), ("Dumas Combustion", "Certified")],
    "dokafor": [("Dumas Combustion", "Master Technician"), ("Soxhlet / Fat Extraction", "Certified")],
    "rpatel": [("Kjeldahl & Digestion", "Certified"), ("Moisture Analysers", "Certified")],
    "ldoyle": [("Kjeldahl & Digestion", "Certified"), ("Thermal (baths, ovens, circulators)", "Certified")],
    "sturner": [("Moisture Analysers", "Master Technician"), ("Thermal (baths, ovens, circulators)", "Certified")],
    "mbennett": [("Soxhlet / Fat Extraction", "Certified"), ("Thermal (baths, ovens, circulators)", "Trainee")],
}


class TlDfsDemoLoader(models.AbstractModel):
    _name = "tl.dfs.demo.loader"
    _description = "DFS Demo Data Loader"

    # ------------------------------------------------------------------ helpers
    def _ref(self, name):
        return self.env.ref(name if "." in name else f"{MODULE}.{name}", raise_if_not_found=False)

    def _bind(self, name, record):
        self.env["ir.model.data"].create({
            "module": MODULE, "name": name, "model": record._name, "res_id": record.id, "noupdate": True,
        })
        return record

    def _ensure(self, name, model, vals):
        rec = self._ref(name)
        if rec:
            return rec
        if callable(vals):
            vals = vals()
        return self._bind(name, self.env[model].create(vals))

    def _step_done(self, step):
        return self.env["ir.config_parameter"].get_bool(f"{MODULE}.step.{step}")

    def _mark_step(self, step):
        self.env["ir.config_parameter"].set_bool(f"{MODULE}.step.{step}", True)

    def _today(self):
        return fields.Date.today()

    def _day(self, offset):
        return self._today() + timedelta(days=offset)

    def _workday(self, offset):
        day = self._day(offset)
        while day.weekday() >= 5:
            day += timedelta(days=1 if offset >= 0 else -1)
        return day

    def _utc(self, day, hour):
        h, m = int(hour), int(round((hour - int(hour)) * 60))
        return datetime.combine(day, time(h, m), tzinfo=TZ).astimezone(UTC).replace(tzinfo=None)

    def _product(self, key):
        return self._ref("product_" + key).product_variant_id

    def _partner(self, key):
        return self._ref("partner_" + key)

    def _contact(self, key):
        return self._ref("partner_contact_" + key)

    def _user(self, emp_key):
        emp = self._ref("hr_employee_" + emp_key)
        return emp.user_id if emp else self.env["res.users"]

    def _our_records(self, model):
        imd = self.env["ir.model.data"].search([("module", "=", MODULE), ("model", "=", model)])
        return self.env[model].browse(imd.mapped("res_id")).exists()

    def _lot(self, product, name):
        return self.env["stock.lot"].search([("product_id", "=", product.id), ("name", "=", name)], limit=1)

    # ------------------------------------------------------------------ entry points
    def action_load_all(self):
        self = self.sudo().with_context(  # noqa: PLW0642
            tracking_disable=True, mail_create_nolog=True, mail_notrack=True, mail_create_nosubscribe=True,
            no_reset_password=True, mail_auto_subscribe_no_notify=True, tz="Europe/London",
        )
        for step in (
            "_setup_company", "_setup_settings", "_setup_users", "_setup_master_misc", "_setup_stock",
            "_setup_legacy_base", "_setup_purchases", "_setup_sales", "_setup_subscriptions", "_setup_crm", "_setup_quote_templates",
            "_setup_helpdesk", "_setup_interventions", "_setup_shifts", "_setup_skills", "_setup_repair",
        ):
            _logger.info("tl_dfs_demo_data: %s", step)
            getattr(self, step)()
            self.env.flush_all()
        self.action_load_custom_data()
        return self._notify("Northbrook Analytical demo data loaded.")

    def _notify(self, message, kind="success"):
        return {
            "type": "ir.actions.client", "tag": "display_notification",
            "params": {"title": "DFS demo data", "message": message, "type": kind, "sticky": False},
        }

    # ------------------------------------------------------------------ company / accounting
    def _setup_company(self):
        company = self.env.ref("base.main_company")
        if not company.chart_template:
            self.env["account.chart.template"].try_loading("uk", company, install_demo=False)
        # the generic chart scheduled by account's install must not be loaded on top of ours
        if hasattr(self.env.registry, "_auto_install_template"):
            del self.env.registry._auto_install_template
        company = self.env.ref("base.main_company")
        vals = {}
        incoterm = self.env.ref("account.incoterm_DAP", raise_if_not_found=False)
        if incoterm and "incoterm_id" in company._fields:
            vals["incoterm_id"] = incoterm.id
        if vals:
            company.write(vals)
        sale_tax, purchase_tax = company.account_sale_tax_id, company.account_purchase_tax_id
        for tmpl in self._our_records("product.template"):
            if sale_tax and not tmpl.taxes_id:
                tmpl.taxes_id = [Command.set(sale_tax.ids)]
            if purchase_tax and tmpl.purchase_ok and not tmpl.supplier_taxes_id:
                tmpl.supplier_taxes_id = [Command.set(purchase_tax.ids)]
        self.env.ref("base.user_admin").tz = "Europe/London"

    def _setup_settings(self):
        if self._step_done("settings"):
            return
        Settings = self.env["res.config.settings"]
        wanted = {
            "group_uom": True, "group_product_variant": False, "group_stock_production_lot": True,
            "group_lot_on_delivery_slip": True, "group_stock_multi_locations": True,
            "group_product_pricelist": True, "group_discount_per_so_line": True, "group_use_lead": True,
            "group_use_recurring_revenues": True, "po_order_approval": True, "po_double_validation": "two_step",
            "po_double_validation_amount": 20000.0, "quotation_validity_days": 30,
            "group_field_service_allow_material": True, "group_field_service_allow_equipment": True,
            "group_field_service_allow_customer_report": True, "group_field_service_allow_quotations": True,
            "group_display_incoterm": True, "group_sale_delivery_address": True,
        }
        vals = {k: v for k, v in wanted.items() if k in Settings._fields}
        Settings.create(vals).execute()
        self._mark_step("settings")

    # ------------------------------------------------------------------ users & teams
    def _setup_users(self):
        Users = self.env["res.users"].with_context(no_reset_password=True)
        for emp_key, groups in USER_GROUPS.items():
            emp = self._ref("hr_employee_" + emp_key)
            if not emp or emp.user_id:
                continue
            login = emp.work_email
            user = Users.search([("login", "=", login)], limit=1)
            if not user:
                group_ids = [self.env.ref("base.group_user").id]
                for xid in groups:
                    group = self.env.ref(xid, raise_if_not_found=False)
                    if group:
                        group_ids.append(group.id)
                user = Users.create({
                    "name": emp.name, "login": login, "email": login, "password": DEMO_PASSWORD,
                    "tz": "Europe/London", "group_ids": [Command.set(group_ids)],
                    "image_1920": emp.image_1920,
                })
                self._bind("user_" + emp_key, user)
            emp.user_id = user

        teams = {
            "sales_team.team_sales_department": ("slockwood", ["slockwood", "tfletcher", "psharma"]),
            "crm_team_key_accounts": ("hprice", ["hprice", "bharris"]),
            "crm_team_website": ("emorgan", ["emorgan"]),
            "crm_team_service": ("gevans", ["gevans", "lchen"]),
        }
        for team_xid, (leader, members) in teams.items():
            team = self._ref(team_xid)
            users = self.env["res.users"]
            for m in members:
                users |= self._user(m)
            team.write({"user_id": self._user(leader).id, "member_ids": [Command.set(users.ids)]})

        hd_team = self.env.ref("helpdesk.helpdesk_team1")
        agents = self.env.ref("base.user_admin")
        for m in ("lchen", "awright", "bharris", "gevans"):
            agents |= self._user(m)
        hd_team.write({"member_ids": [Command.set(agents.ids)], "auto_assignment": True})

    # ------------------------------------------------------------------ misc master data
    def _setup_master_misc(self):
        pricelists = {k: self._ref("pricelist_" + k) for k in ("trade", "key", "edu")}
        payment_60 = self._ref("payment_term_60")
        for cust, (pl, sp, team) in CUSTOMER_ACCOUNTS.items():
            partner = self._partner(cust)
            vals = {"property_product_pricelist": pricelists[pl].id, "user_id": self._user(sp).id,
                    "team_id": self._ref(team).id}
            if cust in ("wmpal", "kentss"):
                vals["property_payment_term_id"] = payment_60.id
            partner.write({k: v for k, v in vals.items() if k in partner._fields})
        for vendor in self.env["res.partner"].search([("id", "in", self._our_records("res.partner").ids),
                                                      ("supplier_rank", ">", 0)]):
            if not vendor.property_supplier_payment_term_id:
                vendor.property_supplier_payment_term_id = self.env.ref("account.account_payment_term_30days")

        # eCommerce accessories = consumable/spare optional products
        if "accessory_product_ids" in self.env["product.template"]._fields:
            for tmpl in self._our_records("product.template"):
                acc = tmpl.optional_product_ids.filtered(lambda t: t.type == "consu").product_variant_id
                if acc and not tmpl.accessory_product_ids:
                    tmpl.accessory_product_ids = [Command.set(acc.ids)]

        # equipment that belongs to a serial: Track CPE etc. are handled in the custom loader
        warehouse = self.env["stock.warehouse"].search([("company_id", "=", self.env.company.id)], limit=1)
        if warehouse and warehouse.name != "Milton Keynes Warehouse":
            warehouse.name = "Milton Keynes Warehouse"
        for key, name in (("instruments", "Instruments"), ("spares", "Spares Cage"),
                          ("consumables", "Consumables"), ("quarantine", "Quarantine / Returns")):
            self._ensure("location_" + key, "stock.location", {
                "name": name, "location_id": warehouse.lot_stock_id.id, "usage": "internal",
            })

        # website
        website = self.env["website"].search([], limit=1)
        if website:
            wvals = {"name": "Northbrook Analytical"}
            web_team = self._ref("crm_team_website")
            for fname, value in (("crm_default_team_id", web_team.id), ("crm_default_user_id", self._user("emorgan").id),
                                 ("salesteam_id", web_team.id), ("salesperson_id", self._user("emorgan").id)):
                if fname in website._fields:
                    wvals[fname] = value
            website.write(wvals)

    # ------------------------------------------------------------------ stock
    def _apply_inventory(self, items):
        """items: list of (product, location, lot or False, qty)"""
        Quant = self.env["stock.quant"].with_context(inventory_mode=True)
        quants = Quant
        for product, location, lot, qty in items:
            quant = Quant.search([("product_id", "=", product.id), ("location_id", "=", location.id),
                                  ("lot_id", "=", lot.id if lot else False)], limit=1)
            if quant:
                quant.inventory_quantity = quant.quantity + qty
            else:
                quant = Quant.create({"product_id": product.id, "location_id": location.id,
                                      "lot_id": lot.id if lot else False, "inventory_quantity": qty})
            quants |= quant
        if quants:
            quants.action_apply_inventory()

    def _setup_stock(self):
        if self._step_done("stock"):
            return
        loc = {k: self._ref("location_" + k) for k in ("instruments", "spares", "consumables")}
        yy = self._today().year % 100
        Lot = self.env["stock.lot"]
        items = []
        for key, count in OPENING_SERIALS.items():
            product = self._product(key)
            short = product.default_code.replace("NA-", "")
            for n in range(1, count + 1):
                lot = Lot.create({"name": f"{short}-{yy:02d}{n:04d}", "product_id": product.id})
                items.append((product, loc["instruments"], lot, 1))
        for key, lots in OPENING_LOTS.items():
            product = self._product(key)
            for name, qty in lots:
                items.append((product, loc["spares"], Lot.create({"name": name, "product_id": product.id}), qty))
        for key, lots in OPENING_EXPIRY.items():
            product = self._product(key)
            for name, qty, days in lots:
                lot = Lot.create({"name": name, "product_id": product.id,
                                  "expiration_date": datetime.combine(self._day(days), time(12))})
                items.append((product, loc["consumables"], lot, qty))
        for key, qty in OPENING_QTY.items():
            product = self._product(key)
            target = loc["spares"] if self._ref("product_" + key).categ_id == self._ref("product_category_spares") \
                else loc["consumables"]
            items.append((product, target, False, qty))
        self._apply_inventory(items)
        self._mark_step("stock")

    def _validate_picking(self, picking, lots_by_product=None, new_lots=None, done_date=None):
        """Process a picking completely.

        :param lots_by_product: {product: stock.lot recordset} to deliver specific serials
        :param new_lots: {product: [(lot_name, qty, expiration_date|None)]} for receipts
        """
        lots_by_product = lots_by_product or {}
        new_lots = new_lots or {}
        if picking.state == "draft":
            picking.action_confirm()
        if picking.state != "assigned":
            picking.action_assign()
        for move in picking.move_ids:
            product = move.product_id
            if product in lots_by_product:
                move.move_line_ids.unlink()
                for lot in lots_by_product[product]:
                    quant = self.env["stock.quant"].search([("lot_id", "=", lot.id), ("quantity", ">", 0),
                                                            ("location_id.usage", "=", "internal")], limit=1)
                    self.env["stock.move.line"].create({
                        "move_id": move.id, "picking_id": picking.id, "product_id": product.id,
                        "uom_id": move.uom_id.id, "location_id": quant.location_id.id or move.location_id.id,
                        "location_dest_id": move.location_dest_id.id, "lot_id": lot.id, "quantity": 1.0,
                    })
            elif product in new_lots:
                move.move_line_ids.unlink()
                for lot_name, qty, expiry in new_lots[product]:
                    vals = {
                        "move_id": move.id, "picking_id": picking.id, "product_id": product.id,
                        "uom_id": move.uom_id.id, "location_id": move.location_id.id,
                        "location_dest_id": move.location_dest_id.id, "lot_name": lot_name, "quantity": qty,
                    }
                    if expiry:
                        vals["expiration_date"] = expiry
                    self.env["stock.move.line"].create(vals)
            elif not move.quantity:
                move.quantity = move.product_uom_qty
            move.picked = True
        res = picking.with_context(skip_backorder=True, picking_ids_not_to_backorder=picking.ids,
                                   skip_sms=True, skip_expired=True).button_validate()
        if isinstance(res, dict) and res.get("res_model"):
            wizard = self.env[res["res_model"]].with_context(res.get("context", {})).create({})
            wizard.process() if hasattr(wizard, "process") else None
        if done_date:
            dt = done_date if isinstance(done_date, datetime) else self._utc(done_date, 11)
            picking.write({"date_done": dt, "scheduled_date": dt})
            picking.move_ids.write({"date": dt})
            picking.move_ids.move_line_ids.write({"date": dt})
        return picking

    def _setup_legacy_base(self):
        """Installed base sold before go-live: migrated through backdated deliveries."""
        if self._step_done("legacy_base"):
            return
        Lot = self.env["stock.lot"]
        loc = self._ref("location_instruments")
        items = []
        for _cust, _dlv, pkey, serial, _d in LEGACY_BASE:
            product = self._product(pkey)
            items.append((product, loc, Lot.create({"name": serial, "product_id": product.id}), 1))
        self._apply_inventory(items)
        warehouse = loc.warehouse_id
        groups = {}
        for cust, dlv, pkey, serial, delivered in LEGACY_BASE:
            groups.setdefault((cust, dlv, delivered), []).append((pkey, serial))
        for i, ((cust, dlv, delivered), units) in enumerate(sorted(groups.items(), key=lambda g: g[0][2])):
            partner = self._ref("partner_delivery_" + dlv) if dlv else self._partner(cust)
            moves, lots_by_product = [], {}
            for pkey, serial in units:
                product = self._product(pkey)
                lots_by_product.setdefault(product, Lot)
                lots_by_product[product] |= self._lot(product, serial)
            for product, lots in lots_by_product.items():
                moves.append(Command.create({
                    "product_id": product.id, "product_uom_qty": len(lots), "uom_id": product.uom_id.id,
                    "location_id": warehouse.lot_stock_id.id,
                    "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                }))
            picking = self.env["stock.picking"].create({
                "partner_id": partner.id, "picking_type_id": warehouse.out_type_id.id,
                "location_id": warehouse.lot_stock_id.id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "origin": "Legacy installed base (pre-Odoo migration)", "move_ids": moves,
            })
            self._bind("picking_legacy_%02d" % i, picking)
            self._validate_picking(picking, lots_by_product=lots_by_product, done_date=delivered)
        self._mark_step("legacy_base")

    # ------------------------------------------------------------------ purchases
    def _setup_purchases(self):
        PO = self.env["purchase.order"]
        for key, vendor, days_ago, lines, receive, state in PURCHASES:
            if self._ref(key):
                continue
            po = PO.create({
                "partner_id": self._ref("partner_vendor_" + vendor).id,
                "date_order": self._utc(self._workday(-days_ago), 10),
                "user_id": self._user("emorgan").id or self.env.uid,
                "order_line": [Command.create({"product_id": self._product(p).id, "product_qty": q}) for p, q in lines],
            })
            self._bind(key, po)
            if state == "sent":
                po.write({"state": "sent"})
                continue
            po.button_confirm()
            if po.state == "to approve":
                po.button_approve()
            po.date_approve = self._utc(self._workday(-days_ago), 15)
            if receive is None:
                continue
            new_lots = {}
            recv_day = self._workday(-receive)
            for p, q in lines:
                product = self._product(p)
                short = product.default_code.replace("NA-", "").replace("CG-", "").replace("SP-", "")
                if product.tracking == "serial":
                    new_lots[product] = [(f"{short}-{recv_day:%y}{500 + i:04d}", 1.0, None) for i in range(int(q))]
                elif product.tracking == "lot":
                    expiry = None
                    if product.use_expiration_date:
                        expiry = datetime.combine(recv_day + timedelta(days=product.expiration_time), time(12))
                    new_lots[product] = [(f"{short}-{recv_day:%y%m}R", float(q), expiry)]
            for picking in po.picking_ids.filtered(lambda pk: pk.state not in ("done", "cancel")):
                self._validate_picking(picking, new_lots=new_lots, done_date=recv_day)

    # ------------------------------------------------------------------ sales
    def _create_so(self, key, cust, contact, delivery, days_ago, lines, extra):
        partner = self._partner(cust)
        pl = extra.get("pricelist")
        vals = {
            "partner_id": partner.id,
            "partner_invoice_id": partner.id,
            "partner_shipping_id": (delivery and self._ref("partner_delivery_" + delivery) or partner).id,
            "date_order": self._utc(self._workday(-days_ago), 10),
            "user_id": partner.user_id.id or self.env.uid,
            "team_id": self._ref(CUSTOMER_ACCOUNTS[cust][2]).id,
            "client_order_ref": extra.get("ref") or False,
            "order_line": [Command.create({"product_id": self._product(p).id, "product_uom_qty": q}) for p, q in lines],
        }
        if pl:
            vals["pricelist_id"] = self._ref("pricelist_" + pl).id
        if contact and "partner_contact_id" in self.env["sale.order"]._fields:
            vals["partner_contact_id"] = self._contact(contact).id
        if extra.get("commitment"):
            vals["commitment_date"] = self._utc(self._workday(extra["commitment"]), 12)
        so = self.env["sale.order"].create(vals)
        # quotation templates are optional: add a note mentioning the contact
        if contact:
            so.note = f"<p>Attention: {self._contact(contact).name}, {self._contact(contact).function}</p>"
        return self._bind(key, so)

    def _invoice_order(self, so, inv_date, pay=False):
        invoice = so._create_invoices()
        invoice.write({"invoice_date": inv_date})
        invoice.action_post()
        if pay:
            self.env["account.payment.register"].with_context(
                active_model="account.move", active_ids=invoice.ids,
            ).create({"payment_date": inv_date + timedelta(days=21)})._create_payments()
        return invoice

    def _schedule_install(self, so, engineer, days, length, state):
        slots = self.env["planning.slot"].search([("sale_line_id", "in", so.order_line.ids)])
        line = so.order_line.filtered(lambda l: l.product_id == self._product("svc_install"))[:1]
        resource = self._ref("hr_employee_" + engineer).resource_id
        start_day = self._workday(days)
        end_day = start_day
        for _i in range(int(length) - 1):
            end_day = self._workday((end_day - self._today()).days + 1)
        lots = so.picking_ids.move_line_ids.lot_id
        vals = {
            "name": f"Installation & commissioning - {so.name}",
            "start_datetime": self._utc(start_day, 8.5), "end_datetime": self._utc(end_day, 17),
            "resource_ids": [Command.set(resource.ids)], "partner_id": (so.partner_shipping_id or so.partner_id).id,
            "role_id": self._ref("planning_role_install").id,
            "worksheet_template_id": self._ref("worksheet_installation").id,
        }
        if lots and "lot_ids" in self.env["planning.slot"]._fields:
            vals["lot_ids"] = [Command.set(lots.ids)]
        slot = slots.filtered(lambda s: not s.start_datetime)[:1] or slots[:1]
        if slot:
            slot.with_context(from_slot_scheduling=True).write(vals)
        else:
            vals.update({"sale_line_id": line.id})
            slot = self.env["planning.slot"].create(vals)
        slot.write({"state": "2_published"})
        if state != "2_published":
            slot.write({"state": state})
        if not self._ref("slot_install_" + so.name.replace("/", "_")):
            self._bind("slot_install_" + so.name.replace("/", "_"), slot)
        return slot

    def _setup_sales(self):
        for key, cust, contact, delivery, days_ago, status, lines, extra in SALES:
            if self._ref(key):
                continue
            so = self._create_so(key, cust, contact, delivery, days_ago, lines, extra)
            order_date = self._utc(self._workday(-days_ago), 10)
            if status == "draft":
                continue
            if status == "sent":
                so.action_quotation_sent()
                continue
            so.action_confirm()
            so.write({"date_order": order_date})
            if status == "sale":
                continue
            deliver_day = self._workday(-days_ago + extra.get("deliver_after", 7))
            for picking in so.picking_ids.filtered(lambda p: p.state not in ("done", "cancel")):
                self._validate_picking(picking, done_date=deliver_day)
            if extra.get("install"):
                engineer, after, length, state = extra["install"]
                offset = after if state == "2_published" else -days_ago + after
                self._schedule_install(so, engineer, offset, length, state)
            if status in ("invoiced", "paid"):
                self._invoice_order(so, deliver_day + timedelta(days=1), pay=(status == "paid"))

    def _setup_subscriptions(self):
        plan = self.env.ref("sale_subscription.subscription_plan_year", raise_if_not_found=False)
        for key, cust, pkey, days_ago, invoice in SUBSCRIPTIONS:
            if self._ref(key):
                continue
            partner = self._partner(cust)
            start = self._day(-days_ago)
            vals = {
                "partner_id": partner.id, "user_id": self._user("gevans").id or self.env.uid,
                "team_id": self._ref("crm_team_service").id, "start_date": start,
                "date_order": self._utc(start, 10),
                "order_line": [Command.create({"product_id": self._product(pkey).id, "product_uom_qty": 1})],
                "client_order_ref": "Service agreement %s" % start.year,
            }
            if plan:
                vals["plan_id"] = plan.id
            so = self._bind(key, self.env["sale.order"].create(vals))
            so.action_confirm()
            so.write({"date_order": self._utc(start, 10)})
            if invoice:
                inv = so._create_invoices()
                inv.write({"invoice_date": start})
                inv.action_post()

    # ------------------------------------------------------------------ CRM
    def _setup_crm(self):
        Lead = self.env["crm.lead"]
        stages = {
            "won": self.env.ref("crm.stage_lead4"),
        }
        for (key, cust, contact, name, stage, revenue, prob, team, user, tags, close_days, activity, quote,
             extra) in OPPORTUNITIES:
            if self._ref(key):
                continue
            partner = self._contact(contact) if contact else self.env["res.partner"]
            vals = {
                "name": name, "type": "lead" if stage == "lead" else "opportunity",
                "partner_id": partner.id or False, "expected_revenue": revenue,
                "team_id": self._ref(team).id, "user_id": self._user(user).id or False,
                "tag_ids": [Command.set([self._ref("crm_tag_" + t).id for t in tags])],
                "date_deadline": self._day(close_days),
                "priority": "2" if revenue > 30000 else ("1" if revenue > 10000 else "0"),
            }
            if stage not in ("lead", "won", "lost"):
                vals["stage_id"] = self._ref(stage).id
            if prob is not None:
                vals["probability"] = prob
            if extra.get("recurring"):
                vals.update({"recurring_revenue": extra["recurring"],
                             "recurring_plan": self.env.ref("crm.crm_recurring_plan_yearly").id})
            for f in ("contact_name", "email", "partner_name", "city"):
                if extra.get(f):
                    vals[{"email": "email_from"}.get(f, f)] = extra[f]
            if not partner and extra.get("partner_name"):
                vals["country_id"] = self.env.ref("base.uk").id
            lead = self._bind(key, Lead.create(vals))
            if extra.get("order"):
                order = self._ref(extra["order"])
                if order:
                    order.opportunity_id = lead
            if quote:
                so = self.env["sale.order"].create({
                    "partner_id": partner.commercial_partner_id.id, "opportunity_id": lead.id,
                    "user_id": lead.user_id.id, "team_id": lead.team_id.id,
                    "order_line": [Command.create({"product_id": self._product(p).id, "product_uom_qty": q})
                                   for p, q in quote],
                })
                self._bind(key + "_quote", so)
            if activity:
                act_type, days, summary = activity
                lead.activity_schedule(act_type, date_deadline=self._workday(days), summary=summary,
                                       user_id=lead.user_id.id or self.env.uid)
            if stage == "won":
                lead.write({"stage_id": stages["won"].id})
                lead.action_set_won()
            elif stage == "lost":
                lead.action_set_lost(lost_reason_id=self._ref("crm_lost_reason_budget").id)

    # ------------------------------------------------------------------ helpdesk
    # PDF Quote Builder: (template key, name, quotation documents, lines, optional lines, extra vals)
    QUOTE_TEMPLATES = [
        ("quote_tmpl_protein", "Protein Analysis Lab Package (Kjeldahl)",
         ("cover", "about", "service", "terms"),
         [("kd40", 1), ("db20", 1), ("sc4", 1), ("tubes250", 2), ("cat_tabs", 1), ("boric", 2),
          ("svc_install", 1), ("svc_training", 1)],
         ["kt8", "svc_extw", "svc_cal"], {}),
        ("quote_tmpl_fat_fibre", "Fat & Fibre Analysis Package",
         ("cover", "about", "service", "terms"),
         [("fx6", 1), ("fb6", 1), ("thimbles", 4), ("pet_ether", 2), ("filter_bags", 1),
          ("svc_install", 2), ("svc_training", 1)],
         ["thimble_holder", "hy6", "svc_extw"], {}),
        ("quote_tmpl_service_visit", "Calibration & Preventive Maintenance Visit",
         ("cover", "service", "terms"),
         [("svc_pm", 1), ("svc_cal", 1)],
         ["svc_callout", "heater_kd", "lamp_mb", "svc_training"], {"number_of_days": 14}),
        ("quote_tmpl_contract_gold", "Annual Service Contract - Gold",
         ("cover", "service", "terms"),
         [("sc_gold", 1)],
         ["svc_training"], {"plan": "sale_subscription.subscription_plan_year"}),
    ]

    @api.model
    def _setup_quote_templates(self):
        """Quotation templates using the PDF Quote Builder documents, applied to open demo quotes.

        Also called from data/quote_builder_data.xml so module updates pick it up. Idempotent.
        """
        self = self.sudo()  # noqa: PLW0642
        Template = self.env["sale.order.template"]
        docs = {k: self._ref("quote_doc_" + k) for k in ("cover", "about", "service", "terms")}
        if not all(docs.values()):
            return
        note = ("<p>Prices are in GBP and exclude VAT. Delivery DAP to your UK site. Payment 30 days end of month. "
                "Full terms of sale are included at the end of this quotation.</p>")
        for key, name, doc_keys, lines, optional, extra in self.QUOTE_TEMPLATES:
            if self._ref(key) or not all(self._product(p) for p, _q in lines):
                continue
            vals = {
                "name": name,
                "note": note,
                "number_of_days": extra.get("number_of_days", 30),
                "require_signature": True,
                "quotation_document_ids": [Command.set([docs[d].id for d in doc_keys])],
                "sale_order_template_line_ids": [
                    Command.create({"product_id": self._product(p).id, "product_uom_qty": q}) for p, q in lines
                ] + [
                    Command.create({"product_id": self._product(p).id, "product_uom_qty": 1, "is_optional": True})
                    for p in optional if self._product(p)
                ],
            }
            plan = extra.get("plan") and self.env.ref(extra["plan"], raise_if_not_found=False)
            if plan and "plan_id" in Template._fields:
                vals["plan_id"] = plan.id
            self._bind(key, Template.create(vals))

        # Open demo quotations get the cover/about/service/terms pages and the datasheets of their instruments.
        doc_ids = [d.id for d in docs.values()]
        orders = self._our_records("sale.order").filtered(lambda o: o.state in ("draft", "sent"))
        for order in orders:
            order.quotation_document_ids = [Command.link(i) for i in doc_ids]
            for line in order.order_line:
                sheets = line.available_product_document_ids.filtered(lambda d: d.name.startswith("Datasheet"))
                if sheets:
                    line.product_document_ids = [Command.link(i) for i in sheets.ids]

    def _setup_helpdesk(self):
        team = self.env.ref("helpdesk.helpdesk_team1")
        tags = {
            "breakdown": "helpdesk_tag_breakdown", "warranty": "helpdesk_tag_warranty",
            "application": "helpdesk_tag_application", "spares": "helpdesk_tag_spares",
            "calibration": "helpdesk_tag_calibration",
        }
        for key, contact, name, stage, priority, tag_keys, agent, desc, _lots in TICKETS:
            if self._ref(key):
                continue
            partner = self._contact(contact)
            ticket = self.env["helpdesk.ticket"].create({
                "name": name, "team_id": team.id, "partner_id": partner.id, "priority": priority,
                "tag_ids": [Command.set([self._ref(tags[t]).id for t in tag_keys])],
                "user_id": self._user(agent).id if agent else False, "description": f"<p>{desc}</p>",
            })
            ticket.stage_id = self.env.ref(stage)
            self._bind(key, ticket)

    # ------------------------------------------------------------------ field service
    def _intervention_lots(self, spec):
        Lot = self.env["stock.lot"]
        if isinstance(spec, str) and spec.startswith("@"):
            so_key, _sep, pkey = spec[1:].partition(":")
            so = self._ref(so_key)
            lots = so.picking_ids.move_line_ids.lot_id if so else Lot
            lots = lots.filtered(lambda lot: lot.product_id.tracking == "serial")
            if pkey:
                lots = lots.filtered(lambda lot: lot.product_id == self._product(pkey))
            return lots
        return Lot.search([("name", "in", spec)])

    def _setup_interventions(self):
        Slot = self.env["planning.slot"]
        for (key, cust, name, role, engineers, offset, hour, duration, state, priority, worksheet, lots,
             ticket_key) in INTERVENTIONS:
            if self._ref(key):
                continue
            day = self._workday(offset)
            resources = self.env["resource.resource"]
            for e in engineers:
                resources |= self._ref("hr_employee_" + e).resource_id
            vals = {
                "name": name, "partner_id": self._partner(cust).id, "role_id": self._ref("planning_role_" + role).id,
                "start_datetime": self._utc(day, hour), "end_datetime": self._utc(day, hour + duration),
                "resource_ids": [Command.set(resources.ids)], "priority": priority,
            }
            if "worksheet_template_id" in Slot._fields:
                vals["worksheet_template_id"] = self._ref(worksheet).id
            lot_recs = self._intervention_lots(lots)
            if lot_recs and "lot_ids" in Slot._fields:
                vals["lot_ids"] = [Command.set(lot_recs.ids)]
            if ticket_key and "helpdesk_ticket_id" in Slot._fields:
                vals["helpdesk_ticket_id"] = self._ref(ticket_key).id
            slot = self._bind(key, Slot.create(vals))
            if state != "1_draft":
                slot.write({"state": "2_published"})
                if state != "2_published":
                    slot.write({"state": state})
            if state == "4_completed":
                slot.write({"worksheet_signed_by": self._partner(cust).child_ids[:1].name or self._partner(cust).name})

    def _setup_shifts(self):
        """Workshop / on-call shifts for the field engineers (current and next week) on days without interventions."""
        if self._step_done("shifts"):
            return
        Slot = self.env["planning.slot"]
        monday = self._today() - timedelta(days=self._today().weekday())
        engineers = ["gevans", "dokafor", "rpatel", "ldoyle", "sturner", "mbennett"]
        for e in engineers:
            emp = self._ref("hr_employee_" + e)
            resource = emp.resource_id
            for d in range(10):
                day = monday + timedelta(days=d + (2 if d >= 5 else 0))
                start, end = self._utc(day, 8), self._utc(day, 17)
                busy = Slot.search_count([("resource_ids", "in", resource.ids), ("start_datetime", "<", end),
                                          ("end_datetime", ">", start)])
                if busy:
                    continue
                if e == "gevans":
                    name, role = "Service desk & engineer scheduling", "fse"
                elif day.weekday() == 4:
                    name, role = "On-call breakdown cover (Midlands & North)", "fse"
                else:
                    name = "Workshop: refurbishment & pre-delivery inspection"
                    role = {"ldoyle": "install", "sturner": "calibration"}.get(e, "fse")
                Slot.create({
                    "name": name, "start_datetime": start, "end_datetime": end,
                    "resource_ids": [Command.set(resource.ids)], "role_id": self._ref("planning_role_" + role).id,
                    "state": "2_published",
                })
        # sales engineers: demo days
        for e, offset, cust, title in (("tfletcher", 6, "caledonian", "Demo day - NA-FX2 / NA-KD20"),
                                       ("psharma", 3, "severn", "Demo - NA-MB120 moisture analyser")):
            day = self._workday(offset)
            Slot.create({
                "name": title, "start_datetime": self._utc(day, 9), "end_datetime": self._utc(day, 15),
                "resource_ids": [Command.set(self._ref("hr_employee_" + e).resource_id.ids)],
                "role_id": self._ref("planning_role_sales_eng").id, "partner_id": self._partner(cust).id,
                "state": "2_published",
            })
        self._mark_step("shifts")

    # ------------------------------------------------------------------ skills / repair
    def _setup_skills(self):
        if "hr.skill.type" not in self.env or self._step_done("skills"):
            return
        levels_by_name, skills_by_name = {}, {}
        for type_name, (skills, levels) in SKILLS.items():
            stype = self._ensure("skill_type_service", "hr.skill.type", {
                "name": type_name,
                "skill_ids": [Command.create({"name": s}) for s in skills],
                "skill_level_ids": [Command.create({"name": n, "level_progress": p, "default_level": i == 1})
                                    for i, (n, p) in enumerate(levels)],
            })
            levels_by_name.update({lv.name: lv for lv in stype.skill_level_ids})
            skills_by_name.update({sk.name: sk for sk in stype.skill_ids})
            for emp_key, entries in EMPLOYEE_SKILLS.items():
                emp = self._ref("hr_employee_" + emp_key)
                self.env["hr.employee.skill"].create([{
                    "employee_id": emp.id, "skill_type_id": stype.id, "skill_id": skills_by_name[s].id,
                    "skill_level_id": levels_by_name[lv].id,
                } for s, lv in entries])
        self._mark_step("skills")

    def _setup_repair(self):
        if self._ref("repair_cotswold_mb60"):
            return
        product = self._product("mb60")
        lot = self._lot(product, "MB60-230412")
        repair = self.env["repair.order"].create({
            "product_id": product.id, "lot_id": lot.id, "partner_id": self._partner("cotswold").id,
            "under_warranty": False,
            "internal_notes": "<p>Returned to base: balance cell drift after lab flood. Quote for cell replacement.</p>",
        })
        self._bind("repair_cotswold_mb60", repair)

    # ------------------------------------------------------------------ custom modules (guarded)
    def action_load_custom_data(self):
        """Load data for the CGUK custom models when their modules are installed.

        Safe to run any number of times. Exposed as server action
        ``tl_dfs_demo_data.action_load_custom_data``.
        """
        self = self.sudo().with_context(tracking_disable=True, mail_notrack=True)  # noqa: PLW0642
        done = []
        if "customer.asset" in self.env:
            done.append("%d customer assets" % self._load_customer_assets())
        if "service.contract" in self.env:
            done.append("%d service contracts" % self._load_service_contracts())
        quote = self._load_website_quote_settings()
        if quote:
            done.append("website quote settings")
        message = ("Loaded: " + ", ".join(done)) if done else "No custom module installed: nothing to load."
        _logger.info("tl_dfs_demo_data custom loader: %s", message)
        return self._notify(message, "success" if done else "info")

    def _customer_move_lines(self):
        return self.env["stock.move.line"].search([
            ("state", "=", "done"), ("lot_id", "!=", False), ("location_dest_id.usage", "=", "customer"),
            ("product_id.tracking", "=", "serial"),
            ("product_id.product_tmpl_id", "in", self._our_records("product.template").ids),
        ], order="date")

    def _load_customer_assets(self):
        Asset = self.env["customer.asset"]
        F = Asset._fields
        tmpl_fields = self.env["product.template"]._fields
        equipment = self._our_records("product.template").filtered(lambda t: t.tracking == "serial")
        if "track_cpe" in tmpl_fields:
            equipment.write({"track_cpe": True})
        tickets_by_lot, slots_by_lot = {}, {}
        for key, *_rest, lots in TICKETS:
            ticket = self._ref(key)
            for lot in self.env["stock.lot"].search([("name", "in", lots)]) if ticket else []:
                tickets_by_lot.setdefault(lot.id, self.env["helpdesk.ticket"])
                tickets_by_lot[lot.id] |= ticket
        slot_model = self.env["planning.slot"]
        if "lot_ids" in slot_model._fields:
            for slot in slot_model.search([("lot_ids", "!=", False)]):
                for lot in slot.lot_ids:
                    slots_by_lot.setdefault(lot.id, slot_model)
                    slots_by_lot[lot.id] |= slot
        subscriptions = {}
        for key, cust, *_rest in SUBSCRIPTIONS:
            sub = self._ref(key)
            if sub:
                subscriptions[self._partner(cust).id] = sub
        count = 0
        for ml in self._customer_move_lines():
            picking = ml.picking_id
            so = picking.sale_id if "sale_id" in picking._fields else self.env["sale.order"]
            customer = (so.partner_id or picking.partner_id)
            company = customer.commercial_partner_id
            delivered = (picking.date_done or ml.date).date()
            install = delivered + timedelta(days=3)
            months = 24 if "24-month" in (ml.product_id.description_sale or "") else 12
            warranty = install + timedelta(days=round(months * 30.44))
            vals = {
                "product_id": ml.product_id.id, "product_lot_id": ml.lot_id.id, "sale_date": so.date_order.date()
                if so else delivered, "install_date": install, "warranty_expiry": warranty,
                "under_warranty": warranty >= self._today(), "customer_company_id": company.id,
                "partner_id": company.id, "contact_id": (so.partner_contact_id.id if so and
                                                         "partner_contact_id" in so._fields else False),
                "delivery_address_id": picking.partner_id.id if picking.partner_id.type == "delivery" else False,
                "sale_order_id": so.id or False, "stock_picking_id": picking.id, "move_line_id": ml.id,
                "active_asset": True,
            }
            if not vals.get("contact_id"):
                vals["contact_id"] = company.child_ids.filtered(lambda c: c.type == "contact")[:1].id or False
            if company.id in subscriptions:
                vals["subscription_id"] = subscriptions[company.id].id
            for fname, comodel, recs in (
                ("intervention_ids", "planning.slot", slots_by_lot.get(ml.lot_id.id)),
                ("helpdesk_ticket_ids", "helpdesk.ticket", tickets_by_lot.get(ml.lot_id.id)),
            ):
                target = fname if fname in F else next(
                    (n for n, f in F.items() if f.type == "many2many" and f.comodel_name == comodel), None)
                if target and recs:
                    vals[target] = [Command.set(recs.ids)]
            vals = {k: v for k, v in vals.items() if k in F}
            asset = Asset.search([("product_lot_id", "=", ml.lot_id.id)], limit=1)
            if asset:
                asset.write(vals)
            else:
                asset = Asset.create(vals)
            name = "asset_%s" % ml.lot_id.name.replace("-", "_").lower()
            if not self._ref(name):
                self._bind(name, asset)
            count += 1
        # subscriptions: link assets of the customer to the contract order
        so_fields = self.env["sale.order"]._fields
        if "subscription_customer_assets_ids" in so_fields:
            for partner_id, sub in subscriptions.items():
                assets = Asset.search([("customer_company_id", "=", partner_id)])
                if assets:
                    sub.subscription_customer_assets_ids = [Command.set(assets.ids)]
        # repair order
        repair = self._ref("repair_cotswold_mb60")
        if repair and "customer_asset_id" in repair._fields:
            asset = Asset.search([("product_lot_id", "=", repair.lot_id.id)], limit=1)
            if asset:
                repair.customer_asset_id = asset
        return count

    def _load_service_contracts(self):
        Contract = self.env["service.contract"]
        Line = self.env["service.contract.line"] if "service.contract.line" in self.env else None
        count = 0
        for key, *_rest in SUBSCRIPTIONS:
            sub = self._ref(key)
            if not sub:
                continue
            contract = Contract.search([("sale_id", "=", sub.id)], limit=1)
            if not contract:
                contract = Contract.create({"sale_id": sub.id})
                if Line is not None:
                    line = Line.create({"sale_id": sub.id, "contract_id": contract.id})
                    if "contract_line_id" in sub._fields:
                        sub.contract_line_id = line
            if not self._ref("contract_" + key):
                self._bind("contract_" + key, contract)
            count += 1
        return count

    def _load_website_quote_settings(self):
        """Point any 'quote' settings of the website quote module to the Website Enquiries team / Ellie."""
        team = self._ref("crm_team_website")
        user = self._user("emorgan")
        changed = False
        for model in ("website", "res.company"):
            if model not in self.env:
                continue
            records = self.env[model].search([])
            for fname, field in self.env[model]._fields.items():
                if "quote" not in fname or field.type != "many2one" or field.compute and not field.inverse \
                        and not field.store:
                    continue
                if field.comodel_name == "crm.team" and team:
                    records.write({fname: team.id})
                    changed = True
                elif field.comodel_name == "res.users" and user:
                    records.write({fname: user.id})
                    changed = True
        return changed
