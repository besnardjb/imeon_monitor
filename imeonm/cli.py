#!/bin/env python3
import sys
import argparse
import json
from imeonm.monitor import ImeonStatus, PrometeusExporter


def handle_raw_printing(imeon, args):

    printdata = None

    if args.scan:
        printdata = imeon.req_scan(single=True);
    elif args.status:
        printdata = imeon.req_status()
    elif args.update_status:
        printdata = imeon.req_update_status()
    elif args.data:
        printdata = imeon.req_data()
    elif args.soft_status:
        printdata = imeon.req_soft_status()
    elif args.battery_status:
        printdata = imeon.req_battery_status()
    elif args.lithium_status:
        printdata = imeon.req_data_lithium()

    if printdata:
        print(json.dumps(printdata, indent=4))
        sys.exit(0)




def run():

    #
    # Argument parsing
    #

    parser = argparse.ArgumentParser(description='IMEON Monitoring Interface.')

    parser.add_argument('-i', '--imeon', type=str, help="URL/IP of the IMEON 3.6 OS", required=True)
    parser.add_argument('-s', "--scan",  action='store_true', help="Output raw scan data in JSON")
    parser.add_argument('-S', "--status",  action='store_true', help="Output raw status data in JSON")
    parser.add_argument('-u', "--update-status",  action='store_true', help="Output raw update status data in JSON")
    parser.add_argument('-d', "--data",  action='store_true', help="Output raw general data data in JSON")
    parser.add_argument('-f', "--soft-status",  action='store_true', help="Output raw software status in JSON")
    parser.add_argument('-b', "--battery-status",  action='store_true', help="Output raw software status in JSON")
    parser.add_argument('-l', "--lithium-status",  action='store_true', help="Output raw lithium status in JSON")

    parser.add_argument('-t', "--scan-period", type=int, default=60, help="How often to pull samples when polling")
    parser.add_argument('-p', "--prometheus-exporter",  action='store_true', help="Enable the prometheus exporter")
    parser.add_argument('-P', "--prometheus-exporter-port", type=int, default=13371, help="Port on which to run the prometheus exporter")

    """
        parser.add_argument('-p', "--plot",  action='store_true', help="Plot given series")
        parser.add_argument('-g', "--gather-plots",  action='store_true', help="Plot on the same plot")
        parser.add_argument('-L', "--ls", action='store_true', help="Plot in logarithmic scale")
        parser.add_argument('-j', "--json",  action='store_true', help="Output the given series in JSON")
        parser.add_argument('-t', "--text",  action='store_true', help="Output the given series in text format")
        parser.add_argument('-l', "--list",  action='store_true', help="List available series in the file")

        parser.add_argument('-i', "--input", nargs='*', required=False, help="Input iocrawl file")

        parser.add_argument('-s', '--series', nargs='*', help="Series to be processed (add D: before to derivate)")
        parser.add_argument('-a', "--all",  action='store_true', help="Load all series in the file")
        parser.add_argument('-f', "--filter",  type=str, help="Select series using regular expression")


        parser.add_argument('-S', '--statistics', action='store_true', help="Generate statistics for given series")

        parser.add_argument('-A', '--average', type=int, help="Apply sliding average of N to the series")


        parser.add_argument('-m', '--merge', nargs='*', help="Merge multiple file together (optionnal tag with TAG:PATH)")
        parser.add_argument('-o', '--output', type=str, help="File to store the result to")
    """

    args = parser.parse_args(sys.argv[1:])

    # Login to the IMEON
    imeon = ImeonStatus(args.imeon, resolution=args.scan_period)

    # Handle printing parameters (this may not return if one is processed)
    handle_raw_printing(imeon, args)

    if args.prometheus_exporter:
        exp = PrometeusExporter(imeon, port=args.prometheus_exporter_port, debug=False)