from __future__ import annotations

import shutil
from pathlib import Path

from deciphon_core.cffi import ffi, lib
from deciphon_core.error import DeciphonError
from deciphon_core.filepath import FilePath
from deciphon_core.seq import SeqIter
from deciphon_core.cseq import CSeqIter

__all__ = ["Scan"]


class Scan:
    def __init__(self, hmm: FilePath, db: FilePath, seqit: SeqIter, prod: FilePath):
        self._cscan = ffi.NULL
        self._hmm = Path(hmm)
        self._db = Path(db)
        self._seqit = CSeqIter(seqit)
        self._prod = Path(prod)
        self._nthreads = 1
        self._port = 51371
        self._lrt_threshold = 10.0
        self._multi_hits = True
        self._hmmer3_compat = False

    @property
    def nthreads(self):
        return self._nthreads

    @nthreads.setter
    def nthreads(self, x: int):
        self._nthreads = x

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, x: int):
        self._port = x

    @property
    def lrt_threshold(self):
        return self._lrt_threshold

    @lrt_threshold.setter
    def lrt_threshold(self, x: float):
        self._lrt_threshold = x

    @property
    def multi_hits(self):
        return self._multi_hits

    @multi_hits.setter
    def multi_hits(self, x: bool):
        self._multi_hits = x

    @property
    def hmmer3_compat(self):
        return self._hmmer3_compat

    @hmmer3_compat.setter
    def hmmer3_compat(self, x: bool):
        self._hmmer3_compat = x

    @property
    def product_filename(self):
        return self._prod.parent / f"{self._prod.name}.dcs"

    def run(self):
        prod = self._prod
        if rc := lib.dcp_scan_run(self._cscan, str(prod).encode()):
            raise DeciphonError(rc)

        archive = shutil.make_archive(str(prod), "zip", base_dir=prod)
        shutil.move(archive, self.product_filename)
        shutil.rmtree(prod)

    def open(self):
        self._cscan = lib.dcp_scan_new(self._port)
        if self._cscan == ffi.NULL:
            raise MemoryError()

        if rc := lib.dcp_scan_set_nthreads(self._cscan, self._nthreads):
            raise DeciphonError(rc)

        lib.dcp_scan_set_lrt_threshold(self._cscan, self._lrt_threshold)
        lib.dcp_scan_set_multi_hits(self._cscan, self._multi_hits)
        lib.dcp_scan_set_hmmer3_compat(self._cscan, self._hmmer3_compat)

        if rc := lib.dcp_scan_set_db_file(self._cscan, bytes(self._db)):
            raise DeciphonError(rc)

        it = self._seqit
        lib.dcp_scan_set_seq_iter(self._cscan, it.c_callback, it.c_self)

    def close(self):
        pass

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *_):
        self.close()

    def __del__(self):
        if self._cscan != ffi.NULL:
            lib.dcp_scan_del(self._cscan)
            self._cscan = ffi.NULL
