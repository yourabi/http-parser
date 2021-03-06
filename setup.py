# -*- coding: utf-8 -
#
# This file is part of http-parser released under the MIT license. 
# See the NOTICE for more information.

from __future__ import with_statement

from distutils.core import setup
from distutils.command import build_ext
from distutils.extension import Extension
import glob
from imp import load_source
import os
import sys
import traceback

if not hasattr(sys, 'version_info') or \
        sys.version_info < (2, 6, 0, 'final'):
    raise SystemExit("http-parser requires Python 2.6x or later")

CLASSIFIERS = [
        'Development Status :: 4 - Beta',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Internet',
        'Topic :: Utilities',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]


MODULES = ["http_parser"]

INCLUDE_DIRS = ["http_parser"]
SOURCES = [os.path.join("http_parser", "parser.c"),
        os.path.join("http_parser", "http_parser.c")]

class my_build_ext(build_ext.build_ext):
    user_options = (build_ext.build_ext.user_options
                    + [("cython=", None, "path to the cython executable")])

    def initialize_options(self):
        build_ext.build_ext.initialize_options(self)
        self.cython = "cython"

    def compile_cython(self):
        sources = glob.glob('http_parser/*.pyx')
        if not sources:
            if not os.path.exists('http_parser/parser.c'):
                print >> sys.stderr, 'Could not find http_parser/parser.c'

        if os.path.exists('http_parser/parser.c'):
            core_c_mtime = os.stat('http_parser/parser.c').st_mtime
            changed = [filename for filename in sources if \
                    (os.stat(filename).st_mtime - core_c_mtime) > 1]
            if not changed:
                return
            print >> sys.stderr, 'Running %s (changed: %s)' % (self.cython, ', '.join(changed))
        else:
            print >> sys.stderr, 'Running %s' % self.cython
        cython_result = os.system('%s http_parser/parser.pyx' % self.cython)
        if cython_result:
            if os.system('%s -V 2> %s' % (self.cython, os.devnull)):
                # there's no cython in the system
                print >> sys.stderr, 'No cython found, cannot rebuild parser.c'
                return
            sys.exit(1)

    def build_extension(self, ext):
        if self.cython:
            self.compile_cython()
        result = build_ext.build_ext.build_extension(self, ext)
        # hack: create a symlink from build/../parser.so to http_parser/parser.so
        # to prevent "ImportError: cannot import name core" failures
        try:
            fullname = self.get_ext_fullname(ext.name)
            modpath = fullname.split('.')
            filename = self.get_ext_filename(ext.name)
            filename = os.path.split(filename)[-1]
            if not self.inplace:
                filename = os.path.join(*modpath[:-1] + [filename])
                path_to_build_core_so = os.path.abspath(
                        os.path.join(self.build_lib, filename))
                path_to_core_so = os.path.abspath(
                        os.path.join('http_parser', 
                            os.path.basename(path_to_build_core_so)))
                if path_to_build_core_so != path_to_core_so:
                    try:
                        os.unlink(path_to_core_so)
                    except OSError:
                        pass
                    if hasattr(os, 'symlink'):
                        print 'Linking %s to %s' % (path_to_build_core_so, path_to_core_so)
                        os.symlink(path_to_build_core_so, path_to_core_so)
                    else:
                        print 'Copying %s to %s' % (path_to_build_core_so, path_to_core_so)
                        import shutil
                        shutil.copyfile(path_to_build_core_so, path_to_core_so)
        except Exception:
            traceback.print_exc()
        return result


def main():
    http_parser = load_source("http_parser", os.path.join("http_parser",
        "__init__.py"))

    # read long description
    with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
        long_description = f.read()

    PACKAGES = {}
    for name in MODULES:
        PACKAGES[name] = name.replace(".", "/")

    DATA_FILES = [
        ('http_parser', ["LICENSE", "MANIFEST.in", "NOTICE", "README.rst",
                        "THANKS",])
        ]
    
    
    EXT_MODULES = [Extension("http_parser.parser", 
            sources=SOURCES, include_dirs=INCLUDE_DIRS)]

    options = dict(
            name = 'http-parser',
            version = http_parser.__version__,
            description = 'http request/response parser',
            long_description = long_description,
            author = 'Benoit Chesneau',
            author_email = 'benoitc@e-engura.com',
            license = 'MIT',
            url = 'http://github.com/benoitc/http-parser',
            classifiers = CLASSIFIERS,
            packages = PACKAGES.keys(),
            package_dir = PACKAGES,
            data_files = DATA_FILES,
            cmdclass = {'build_ext': my_build_ext},
            ext_modules = EXT_MODULES
    )

    setup(**options)

if __name__ == "__main__":
    main()

