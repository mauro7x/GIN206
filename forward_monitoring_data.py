import subprocess
import json
import os
from time import sleep
import requests

THINGSBOARD_TOKEN = "MONITOKEN2"
THINGSBOARD_URL = "http://mauro.rezel.net:8080/api/v1/{}/telemetry".format(THINGSBOARD_TOKEN)
HOME = os.environ.get("HOME")
MONITORING_DATA_PATH = HOME + "/.iot-lab/{}/{}/{}.oml"  # fill experiment id, type of monitoring, node id
UPDATE_FREQ = 5  # in seconds
ENERGY_MSG_RATE = 2  # use every xth datapoint. Forwarding is not fast enough to use all data.


def get_experiment_info():
    try:
        exp_info = json.loads(subprocess.getoutput("iotlab-experiment get -p"))
        exp_id = exp_info["id"]
        nodes_list = list()
        for node in exp_info["nodes"]:
            node_id = node.split(".", maxsplit=1)[0]
            node_id = node_id.replace("-", "_")  # node ids are inconsistent on iot-lab
            nodes_list.append(node_id)
        return exp_id, nodes_list
    except json.decoder.JSONDecodeError:
        print("Error: Make sure exactly one experiment is running")
        raise
    except KeyError:
        print("Error: Unexpected experiment info")
        raise


def get_monitoring_data(exp_id, monitoring_type, node):
    """
    Retrieve monitoring data from OML file.
    :param exp_id: ID of monitored experiment
    :param monitoring_type: One of ["consumption", "radio"]
    :param node: ID of node, e.g., m3-100
    :return: List of monitoring data separated into lines
    """
    with open(MONITORING_DATA_PATH.format(exp_id, monitoring_type, node)) as file:
        monitoring_data = _get_oml_lines(file.read())
    return monitoring_data


def _get_oml_lines(oml_content):
    """
    Strips oml header and returns only lines containing monitoring data in a list.
    :param oml_content: raw oml file content
    :return: list of monitoring data separated into lines
    """
    all_oml_lines = oml_content.splitlines()
    # split at empty line
    if "" not in all_oml_lines:
        raise RuntimeError("Error: Could not parse data."
                           " Maybe you just started the experiment and there is not enough data yet?")
    usable_oml_lines = all_oml_lines[all_oml_lines.index("")+1:]
    return usable_oml_lines


def make_energy_telemetry_msg(datapoint, node):
    """
    Construct a timestamped message for ThingsBoard.
    :param datapoint: single line from energy consumption monitoring .oml file
    :param node: identifier of the monitored device
    :return: message dict, containing timestamp and values
    """
    fields = datapoint.split()
    try:
        timestamp = fields[3] + fields[4][:3]
        current, voltage, power = fields[5], fields[6], fields[7]
    except IndexError:
        print("Error: malformed radio datapoint?", datapoint)
        raise
    msg = {"ts": timestamp, "values": {
        f"current-{node}": current,
        f"voltage-{node}": voltage,
        f"power-{node}": power
    }}
    return msg


def make_radio_telemetry_msg(datapoint, node):
    """
    Construct a timestamped message for ThingsBoard.
    :param datapoint: single line from radio monitoring .oml file
    :param node: identifier of the monitored device
    :return: message dict, containing timestamp and values
    """
    fields = datapoint.split()
    try:
        timestamp = fields[3] + fields[4][:3]
        channel = fields[5]
        rssi = fields[6]
    except IndexError:
        print("Error: malformed radio datapoint?", datapoint)
        raise
    msg = {"ts": timestamp, "values": {f"{channel}-{node}": rssi}}
    return msg


def send_to_thingsboard(telemetry_msg):
    """
    Send a single message to the ThingsBoard endpoint defined globally
    :param telemetry_msg: list of dicts or json-like dict with values to send
    """
    r = requests.post(THINGSBOARD_URL, json=telemetry_msg)
    if r.status_code != 200:
        raise RuntimeError("Could not send message {} to ThingsBoard URL {}".format(
            telemetry_msg, THINGSBOARD_URL
        ))


def main():
    # initial setup
    exp_id, nodes_list = get_experiment_info()
    last_datapoint_index = {node: {"consumption": 0, "radio": 0} for node in nodes_list}
    while True:
        energy_monitoring_data = {node: get_monitoring_data(exp_id, "consumption", node) for node in nodes_list}
        radio_monitoring_data = {node: get_monitoring_data(exp_id, "radio", node) for node in nodes_list}
        # send all new data points to Thingsboard
        # 1. energy
        for node, node_data in energy_monitoring_data.items():
            start_idx = last_datapoint_index[node]["consumption"] + 1
            # the final node is usually still incompletely written, so we skip it in this iteration
            for datapoint in node_data[start_idx:-1:ENERGY_MSG_RATE]:
                telemetry_msg = make_energy_telemetry_msg(datapoint, node)
                send_to_thingsboard(telemetry_msg)
            # save the latest datapoint so it is not resent
            last_datapoint_index[node]["consumption"] = len(node_data)
        # 2. radio
        # for node, node_data in radio_monitoring_data.items():
        #     start_idx = last_datapoint_index[node]["radio"] + 1
        #     # the final node is usually still incompletely written, so we skip it in this iteration
        #     for datapoint in node_data[start_idx:-1]:
        #         telemetry_msg = make_radio_telemetry_msg(datapoint, node)
        #         send_to_thingsboard(telemetry_msg)
        #     # save the latest datapoint so it is not resent
        #     last_datapoint_index[node]["radio"] = len(node_data)
        sleep(UPDATE_FREQ)


if __name__ == "__main__":
    main()