#!/usr/bin/python3
import sys
import re
from typing import Dict, AnyStr, Any

def get_fields(s: AnyStr) -> Dict[AnyStr, Any]:
   d : Dict = {}
   field = None
   main_package = True
   in_multi = False
   for l in iter(s.splitlines()):
      l = l.strip()
      if '#' in l:
         continue
      elif ":" in l and main_package and not in_multi:
         (f, v) = re.split(r'\s*:\s*', l, 1)
         if "%" in f:
            continue
         field = f
         value = v
         if field not in d:
            d[field] = value
         elif type(d[field]) is not list:
            d[field] = [d[field], value]
         else:
            d[field].append(value)
      elif re.match(r'%prep', l):
         return d
      elif re.match(r'%package', l):
         main_package = False
         in_multi = False
      else:
         r = re.match(r'^%(\w+)$', l)
         if r is not None:
            f = r.group(1)
            if f == "description":
               main_package = True
               in_multi = True
               field = f
            else:
               continue
         elif re.match(r'^%description+\s+\w+', l):
            main_package = False
            in_multi = True
         elif re.match(r'^%', l) is not None:
            continue
         elif field is not None and main_package:
            if field not in d and l != "":
               d[field] = l
            else:
               d[field] += '\n'
               d[field] += l
   return d

def process_lines(string : AnyStr) -> str:
   new_string : str = ""
   pkg_devel_flag = False

   for l in iter(string.splitlines()):
      l = l.replace('%{?_isa}', '')
      l = l.replace('%{?nmainpkg}', '')
      if "Vendor:" in l:
         continue
      elif "Epoch:" in l:
         continue 
      elif "BuildRoot:" in l:
         continue
      elif '%defattr(-,root,root,-)' in l:
         continue
      elif '%package' in l and '%{develname}' in l:
         pkg_devel_flag = True
      elif pkg_devel_flag and "Requires:" in l:
         new_string += "Provides: %{name}-devel = %{version}-%{release}\n"
         pkg_devel_flag = False
      
      l = re.sub(r'%{epoch}:', '', l)
      l = re.sub(r'System Environment/Libraries', 'System/Libraries', l)
      l = re.sub(r'Development/Libraries', 'Development/Other', l)
      l = re.sub(r"Requires:(\s+)([\w\-]+)-devel\s+", lambda x: "Requires:" + x.group(1) + "pkgconfig(" + x.group(2) + ") ", l)
      l = re.sub(r'%{mainpkg}', '%{name}', l)
      new_string += l + "\n"
   return new_string

string : str = sys.stdin.read()
string : str = re.sub(r'%{?nmainpkg}', '', string)

d : Dict[AnyStr, Any] = get_fields(string)
string : str = string.split("%changelog", 1)[0]
string : str = """%%define major 0
%%define libname %%mklibname %s %%{major}
%%define develname %%mklibname %s -d

""" % (d['Name'], d['Name']) + string

string : str = re.sub(r'([\w\.]+)%\{\?dist\}', 
   lambda x: '%mkrel ' + x.group(1), string)
string : str = re.sub(r'%\{\?_isa\}', '', string)
string : str = re.sub(r'(%package|%description|%files)\s+devel', lambda x: x.group(1) + " -n %{develname}", string)
string : str = re.sub(r'%files\s*\n', '%files -n %{libname}\n', string)
string : str = re.sub(r'%description\s*\n', 
   '%description\n' + d['description'] + \
      '\n%package -n %{libname}\n' + \
      'Summary: ' + d['Summary'] + \
      'Provides: %{name} = %{release}-%{version}'
      '\n%description -n %{libname}\n', 
   string)

string : str = process_lines(string)
print(string)
