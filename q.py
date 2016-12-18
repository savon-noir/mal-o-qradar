# -*- coding: utf-8 -*-

import requests
requests.packages.urllib3.disable_warnings()


class qapi(object):
    def __init__(self, server='127.0.0.1', port=443, endpoint='/restapi/api/', token=None, ssl=True, cert_check=True):
        self._server = server
        self._port = port
        self._endpoint = endpoint
        self._token = token
        self._ssl = ssl
        self._cert_check = cert_check
        self._timeout = 5
        self._headers = {'SEC': self._token}

    def _get_resource_endpoint(self, resource=''):
        rurl = 'https://'
        if self._ssl is False:
            rurl = 'http://'
        return '{0}{1}:{2}{3}{4}'.format(rurl, self._server, self._port, self._endpoint, resource)

    def get_resource(self, resource=None):
        rit = None
        if resource is not None:
            rbase = self._get_resource_endpoint(resource)
            rit = requests.get(rbase, timeout=self._timeout, verify=self._cert_check, headers=self._headers)
        return rit

    def post_resource(self, resource=None, post_data=None):
        rit = None
        if resource is not None and post_data is not None:
            rbase = self._get_resource_endpoint(resource)
            rit = requests.post(rbase, timeout=self._timeout, verify=self._cert_check, headers=self._headers, data=post_data)
        return rit

    def delete_resource(self, resource=None):
        rit = None
        if resource is not None:
            rbase = self._get_resource_endpoint(resource)
            rit = requests.delete(rbase, timeout=self._timeout, verify=self._cert_check, headers=self._headers)
        return rit

    def get_json_resource(self, resource=None):
        rdata = None
        d = self.get_resource(resource)
        try:
            rdata = d.json()
        except ValueError:
            print("Error: data is not json format - failed to serialize data from resource: {0} (status: {1})".format(resource, d.status_code))
        return rdata

    def get_sets(self):
        d = self.get_json_resource('reference_data/sets')
        return d

    def get_sets_names(self):
        for sdict in self.get_sets():
            yield sdict['name']

    def get_set(self, name=None):
        return self.get_json_resource('reference_data/sets/{0}'.format(name))

    def add_set(self, name=None):
        pdata = {'name': name, 'element_type': 'ALN'}
        d = None
        if name is not None:
            d = self.post_resource('reference_data/sets', post_data=pdata)
        return d

    def delete_set(self, name=None):
        d = None
        if name is not None:
            d = self.delete_resource('reference_data/sets/{0}'.format(name))
        return d

    def get_set_items(self, name=None):
        ddata = None
        d = self.get_json_resource('reference_data/sets/{0}'.format(name))
        if 'data' in d:
            for ddict in d['data']:
                yield ddict['value']

    def set_exists(self, name=None):
        rval = False
        if name is not None:
            d = self.get_set(name)
            if d.status_code == 200:
                rval = True
        return rval

    def add_set_item(self, set_name=None, item_value=None, item_source='qbrick'):
        d = None
        pdata = { 'name': set_name, 'value': item_value, 'source': item_source }
        if set_name is not None and item_value is not None:
            d = self.post_resource('reference_data/sets/{0}'.format(set_name), post_data=pdata)
        return d

    def delete_set_item(self, set_name=None, item_value=None):
        if set_name is not None and item_value is not None:
            d = self.delete_resource('reference_data/sets/{0}/{1}'.format(set_name, item_value))
        return d
