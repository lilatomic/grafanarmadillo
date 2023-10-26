import json

from grafana_client import GrafanaApi

from grafanarmadillo.alerter import Alerter
from grafanarmadillo.find import Finder


def export_alert(gfn: GrafanaApi, alert_folder, alert_name, destination_file):
	finder, alerter = Finder(gfn), Alerter(gfn)

	# find the alert info
	alert_info = finder.get_alert(alert_folder, alert_name)

	# export the alert. You could save this into a file and commit that to git
	exported_alert, _exported_folder = alerter.export_alert(alert_info)

	destination_file.write(json.dumps(exported_alert))


def import_alert(gfn: GrafanaApi, folder, template):
	alerter = Alerter(gfn)

	alert = template
	alerter.import_alert(alert, folder)
