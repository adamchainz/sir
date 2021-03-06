import glob
from datetime import datetime
import json
import ipaddress
import os

class FSHelper:
    def __init__(self, base_path='./data'):
        self.base_path = base_path
        files = [f.split('/')[-1] for f in glob.glob('{}/bgp-*'.format(self.base_path))]
        self.neighbors = set([n.split('-')[1].replace('_', '.') for n in files])
        dates = sorted(set([n.split('-')[2].replace('.txt', '') for n in files]))
        self.dates = [datetime.strptime(d, '%Y_%m_%dT%H_%M_%S') for d in dates]

    def get_available_dates(self):
        return self.dates

    def get_bgp_prefixes(self, date):
        date = date.replace('-', '_').replace(':', '_')

        prefixes = dict()

        for n in self.neighbors:
            prefixes[n] = list()
            f = 'bgp-{}-{}'.format(n, date).replace('.', '_')

            with open('{}/{}.txt'.format(self.base_path, f)) as data_file:
                for line in data_file.readlines():
                    json_data = json.loads(line)
                    if json_data['event_type'] == 'dump':
                        prefixes[n].append(json_data['ip_prefix'])
                data_file.close()

        return prefixes

    def get_raw_bgp(self, date):
        date = date.replace('-', '_').replace(':', '_')

        prefixes = dict()

        for n in self.neighbors:
            prefixes[n] = dict()
            f = 'bgp-{}-{}'.format(n, date).replace('.', '_')

            with open('{}/{}.txt'.format(self.base_path, f)) as data_file:
                prefixes[n] = data_file.read()
                data_file.close()

        return prefixes

    def find_prefix(self, prefix, date):
        ip_prefix_str = unicode(prefix)
        search_string = '"ip_prefix": "{}.'.format(ip_prefix_str.split('.')[0])
        ipp = ipaddress.ip_network(ip_prefix_str)

        date = date.replace('-', '_').replace(':', '_')

        prefixes = dict()

        for n in self.neighbors:
            prefixes[n] = list()
            f = 'bgp-{}-{}'.format(n, date).replace('.', '_')

            with open('{}/{}.txt'.format(self.base_path, f)) as f:
                for line in f:
                    if search_string in line:
                        data = json.loads(line)
                        other_ipp = ipaddress.ip_network(unicode(data['ip_prefix']))
                        if ipp.overlaps(other_ipp):
                            if ipp.prefixlen >= other_ipp.prefixlen:
                                prefixes[n].append(data)
        return prefixes

    def find_prefixes_asn(self, asn, date, originate_only=False):
        date = date.replace('-', '_').replace(':', '_')

        prefixes = dict()

        for n in self.neighbors:
            prefixes[n] = list()
            f = 'bgp-{}-{}'.format(n, date).replace('.', '_')

            with open('{}/{}.txt'.format(self.base_path, f)) as f:
                for line in f:
                    if asn in line:
                        data = json.loads(line)
                        as_path = data['as_path'].split(' ')
                        if originate_only:
                            if asn == as_path[-1]:
                                prefixes[n].append(data)
                        else:
                            if asn in as_path:
                                prefixes[n].append(data)
        return prefixes

    def purge_bgp(self, older_than):
        older_than = datetime.strptime(older_than, '%Y-%m-%dT%H:%M:%S')
        deleted_files = list()

        for n in self.neighbors:
            for d in self.dates:
                if older_than > d:
                    file_name = '{}/bgp-{}-{}.txt'.format(
                        self.base_path,
                        n.replace('.', '_'),
                        d.strftime('%Y_%m_%dT%H_%M_%S')
                    )
                    if os.path.isfile(file_name):
                        os.remove(file_name)
                        deleted_files.append(file_name)

        return deleted_files
