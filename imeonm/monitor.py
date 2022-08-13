import requests
import json
import time
import sys
import numbers


from prometheus_client import Gauge, start_http_server

class ImeonStatus():

    def __init__(self, ip, resolution=5):

        if not ip:
            raise Exception("An IP must be provided")

        # Main Config 
        self._ip = ip
        self._resolution = resolution

        # Request cache
        self._last_req = {}

        # User CTX 
        self._session_id = None
        self._TSTMD = None
        self._USDT = None
        self._USRL = None

        self._login()

    def _login(self):
        login_data= {
            "do_login": True,
            "email": "user@local",
            "passwd": "password",
            "usrl": self._USRL,
            "usdt": self._USDT,
            "tstmd": self._TSTMD,
            "url_host": "http://{}/login".format(self._ip)
        }

        loginreq = requests.post(login_data["url_host"], data=login_data)
 
        # Gather context infos
        responsedat = loginreq.json()
        if "TSTMD" in responsedat:
            self._TSTMD = responsedat["TSTMD"]

        if "USDT" in responsedat:
            self._USDT = responsedat["USDT"]

        if "USRL" in responsedat:
            self._USDT = responsedat["USRL"]

        # Extract session ID
        lcookies = requests.utils.dict_from_cookiejar(loginreq.cookies)
        if "session" not in lcookies:
            raise Exception("Failed to login to http://{}/".format(self._ip))
        
        self._session_id = lcookies["session"]

    def _check_for_current_data(self, action, args):
        def _dict_are_equal(a, b):
            if not a or not b:
                return 1

            for k,v in a.items():
                # Scan is special as it holds the ts
                # we therefore ignore it for equality
                if action == "scan" and k == "scan_time":
                    continue

                if k not in b:
                    return 0
                if b[k] != v:
                    return 0

            return 1

        if action in self._last_req:
            lastr = self._last_req[action]

            # Make sure args are the same
            if not _dict_are_equal(lastr["args"], args):
                # Parameters are different force request
                return None
            # If we are here param are the same
            # Now check the resolution param
            ts = lastr["ts"]
            delta = time.time() - ts
            if delta < self._resolution:
                # Cache hit
                return lastr["data"]

        # Cache miss
        return None

    def _save_in_cache(self, action, args, resp):
        data = {"ts" : time.time(), "args" : args, "data" : resp}
        self._last_req[action] = data


    def _do_req(self, action, payload=None):
        # First check in cache
        cache = self._check_for_current_data(action, payload)

        if cache:
            return cache

        url = "http://{}/{}".format(self._ip, action)
        session = {"session" : self._session_id}
        resp = requests.get(url, params=payload, cookies=session)

        if resp.status_code != 200 :
            # There was an issue try to login again
            self._login()
        
            resp = requests.get(url, params=payload, cookies=session)

            if resp.status_code != 200:
                raise Exception("Could not request {}".format(action))

        jsdat = resp.json()
        self._save_in_cache(action, payload, jsdat)
        return jsdat

    # This are the "raw" requests to the various endpoints of interest

    def req_scan(self, single=True):
        args = {"scan_time" : int(time.time())}
        if single:
            args["single"] = "true"
        return self._do_req("scan", args)

    def req_status(self):
        return self._do_req("imeon-status")

    def req_update_status(self):
        return self._do_req("flash-firmware/get-update-status")

    def req_data(self):
        return self._do_req("data")

    def req_soft_status(self):
        return self._do_req("about/soft_status")

    def req_battery_status(self):
        return self._do_req("battery-status")

    def req_data_lithium(self):
        return self._do_req("data-lithium")

    def res(self):
        return self._resolution


class PrometeusExporter():

    def __init__(self, imeon, port=13371, debug=False):
        self._gauges = {}
        self._imeon = imeon
        self._debug = debug

        # Start exporter
        start_http_server(port)

        print("Started IMEON Prometheus Exporter on port {}".format(port))

        self._run()

    def _imeon_name(self, k):
        return "imeon_{}".format(k)

    def _hit_gauge(self, k, v):
        if k not in self._gauges:
            self._gauges[k] = Gauge(self._imeon_name(k), k)
        self._gauges[k].set(v)

    def _unpack(self, data):
        if not "val" in data:
            raise Exception("Unexpected data-format")

        ks = data["val"][0]

        for k, v in ks.items():
            if not v:
                continue
            
            if not isinstance(v, numbers.Number):
                continue

            # Timestamps are not interesting
            if k == "timestamp":
                continue

            self._hit_gauge(k, v)

            if self._debug:
                print("{} = {}".format(k, v))


    def _run(self):

        err_count = 0

        while True:
            try:
                data = self._imeon.req_scan()
                self._unpack(data)
                # Wait for the monitor resolution
                time.sleep(self._imeon.res())
            except Exception as e:
                print(e)
                err_count= err_count + 1
                if 100 < err_count:
                    raise Exception("Maximum attemps reached in prometheus exporter: too many errors")
