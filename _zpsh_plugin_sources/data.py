from __future__ import absolute_import, division, unicode_literals, print_function

import contextlib

from com.xhaus.jyson import JysonCodec as json


class PluginData(object):

    FILENAME = 'plugins/zpsh.json'

    def __init__(self):
        try:
            with open(self.FILENAME, 'r') as f:
                self.data = json.loads(f.read())
        except IOError:
            self.data = {
                'players': {},
                'tests': {}
            }
            self.dump()

    def dump(self):
        with open(self.FILENAME, 'w') as f:
            f.write(json.dumps(self.data))

    @contextlib.contextmanager
    def session(self):
        rollback = False
        try:
            yield self.data
        except:
            rollback = True
            raise
        finally:
            if not rollback:
                self.dump()

