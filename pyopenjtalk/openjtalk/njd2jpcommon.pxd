# distutils: language = c++

from .jpcommon cimport JPCommon
from .njd cimport NJD

cdef extern from "njd2jpcommon.h":
    void njd2jpcommon(JPCommon * jpcommon, NJD * njd) nogil
