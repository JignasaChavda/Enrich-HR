app_name = "enrich_hrms"
app_title = "Enrich HRMS"
app_publisher = "jignasha@sanskartechnolab.com"
app_description = "Enrich HRMS"
app_email = "jignasha@sanskartechnolab.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "enrich_hrms",
# 		"logo": "/assets/enrich_hrms/logo.png",
# 		"title": "Enrich HRMS",
# 		"route": "/enrich_hrms",
# 		"has_permission": "enrich_hrms.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/enrich_hrms/css/enrich_hrms.css"
# app_include_js = "/assets/enrich_hrms/js/enrich_hrms.js"

# include js, css files in header of web template
# web_include_css = "/assets/enrich_hrms/css/enrich_hrms.css"
# web_include_js = "/assets/enrich_hrms/js/enrich_hrms.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "enrich_hrms/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "enrich_hrms/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "enrich_hrms.utils.jinja_methods",
# 	"filters": "enrich_hrms.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "enrich_hrms.install.before_install"
# after_install = "enrich_hrms.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "enrich_hrms.uninstall.before_uninstall"
# after_uninstall = "enrich_hrms.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "enrich_hrms.utils.before_app_install"
# after_app_install = "enrich_hrms.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "enrich_hrms.utils.before_app_uninstall"
# after_app_uninstall = "enrich_hrms.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "enrich_hrms.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------
scheduler_events = {
    "set_attendance_date": {
        "55 23 * * *": [
            "enrich_hrms.utils.set_attendance_date"
        ]
    }
    # "daily": [
    #     "clevision.utils.get_last_sync_of_checkin"
    # ]
}
# scheduler_events = {
# 	"all": [
# 		"enrich_hrms.tasks.all"
# 	],
# 	"daily": [
# 		"enrich_hrms.tasks.daily"
# 	],
# 	"hourly": [
# 		"enrich_hrms.tasks.hourly"
# 	],
# 	"weekly": [
# 		"enrich_hrms.tasks.weekly"
# 	],
# 	"monthly": [
# 		"enrich_hrms.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "enrich_hrms.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "enrich_hrms.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "enrich_hrms.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["enrich_hrms.utils.before_request"]
# after_request = ["enrich_hrms.utils.after_request"]

# Job Events
# ----------
# before_job = ["enrich_hrms.utils.before_job"]
# after_job = ["enrich_hrms.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"enrich_hrms.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
fixtures = [
    "Workflow",
    "Workflow State",
    "Workflow Action Master",
    
    {"dt":"Print Format","filters":[
        [
            "module","in",[
               "Enrich HRMS"
            ],
        ]
    ]},
    {"dt":"Custom Field","filters":[
        [
            "module","in",[
               "Enrich HRMS"
            ],
        ]
    ]},
    {"dt":"Property Setter","filters":[
        [
            "module","in",[
               "Enrich HRMS"
            ],
        ]
    ]},
    {"dt":"Client Script","filters":[
        [
            "module","in",[
               "Enrich HRMS"
            ],
        ]
    ]},
    {"dt":"Server Script","filters":[
        [
            "module","in",[
               "Enrich HRMS"
            ],
        ]
    ]},
    {"dt":"Report","filters":[
        [
            "module","in",[
               "Enrich HRMS"
            ],
        ]
    ]}

]

