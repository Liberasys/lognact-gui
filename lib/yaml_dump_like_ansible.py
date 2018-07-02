# lognact GUI : HTML gui for interacting with ansible scripts of lognact.>
#
#    Copyright (C) 2018 HUSSON CONSULTING SAS - Liberasys
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.



from io import StringIO
import re
import yaml

def yaml_dump_like_ansible(data, indent_size=2):
    stream = StringIO(yaml.dump(data, explicit_start=True, default_flow_style=False, indent=indent_size))
    out = StringIO()
    pat = re.compile('(\s*)([^:]*)(:*)')
    last = None

    prefix = 0
    for s in stream:
        indent, key, colon = pat.match(s).groups()
        if indent == "" and key[0] != '-':
            prefix = 0
        if last:
            if len(last[0]) == len(indent) and last[2] == ':':
                if all([
                        not last[1].startswith('-'),
                        s.strip().startswith('-')
                        ]):
                    prefix += indent_size
        out.write(" "*prefix+s)
        last = indent, key, colon
    return out.getvalue()
