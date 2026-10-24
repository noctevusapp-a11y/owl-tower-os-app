"""Scratch PostgreSQL for the database tests.

  * PGHOST / PGPORT / PGUSER set  -> use that server (it must answer).
  * otherwise                     -> start a throw-away cluster in a temp directory (initdb + pg_ctl from /usr/lib/postgresql/*/bin or
                                     the PATH; as the `postgres` OS user when running as root) and stop + delete it at exit.
  * no server obtainable          -> RuntimeError: the database tests FAIL, they are never silently skipped.
                                     Only COSTDB_SKIP_PG=1 skips them, and the skip message says so.
"""
from __future__ import annotations

import atexit
import glob
import os
import pwd
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path

_STATE: dict = {}


class NoPostgres(RuntimeError):
    pass


def _bin(name: str) -> str | None:
    cands = sorted(glob.glob(f"/usr/lib/postgresql/*/bin/{name}"))
    return cands[-1] if cands else shutil.which(name)


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _answers(env: dict) -> bool:
    r = subprocess.run(["psql", "-At", "-d", "postgres", "-c", "select 1"], capture_output=True, text=True, env=env)
    return r.returncode == 0 and r.stdout.strip() == "1"


def skip_requested() -> bool:
    return os.environ.get("COSTDB_SKIP_PG") == "1"


def ensure() -> str:
    """Make PGHOST/PGPORT/PGUSER point at a working server; return a one-line description."""
    if "desc" in _STATE:
        return _STATE["desc"]
    if os.environ.get("PGHOST") or os.environ.get("PGPORT"):
        if not _answers(dict(os.environ)):
            raise NoPostgres(f"PGHOST={os.environ.get('PGHOST')} PGPORT={os.environ.get('PGPORT')} is set but the server does not answer")
        _STATE["desc"] = "existing server " + (os.environ.get("PGHOST") or "") + ":" + (os.environ.get("PGPORT") or "")
        return _STATE["desc"]
    initdb, pg_ctl, psql = _bin("initdb"), _bin("pg_ctl"), shutil.which("psql")
    if not (initdb and pg_ctl and psql):
        raise NoPostgres("PostgreSQL binaries (initdb, pg_ctl, psql) not found and PGHOST/PGPORT not set. Install PostgreSQL 14+ or point "
                         "PGHOST/PGPORT/PGUSER at a scratch server; set COSTDB_SKIP_PG=1 only if you knowingly want to skip these tests.")
    root = os.geteuid() == 0
    base = Path(tempfile.mkdtemp(prefix="costdb_pg_"))
    data, sock = base / "data", base / "sock"
    sock.mkdir()
    user = "postgres" if root else pwd.getpwuid(os.geteuid()).pw_name
    if root:
        try:
            pwd.getpwnam("postgres")
        except KeyError:
            shutil.rmtree(base, ignore_errors=True)
            raise NoPostgres("running as root and no 'postgres' OS user exists to run the server")
        for p in (base, sock):
            shutil.chown(p, "postgres", "postgres")
            os.chmod(p, 0o755)
    port = _free_port()

    def run(cmd: list[str]) -> subprocess.CompletedProcess:
        full = ["su", "postgres", "-c", " ".join(map(_q, cmd))] if root else cmd
        return subprocess.run(full, capture_output=True, text=True)
    r = run([initdb, "-D", str(data), "-A", "trust", "-E", "UTF8", "--locale=C.UTF-8", "-U", user])
    if r.returncode:
        shutil.rmtree(base, ignore_errors=True)
        raise NoPostgres("initdb failed: " + r.stderr[-400:])
    r = run([pg_ctl, "-D", str(data), "-o", f"-p {port} -k {sock} -c listen_addresses=", "-l", str(base / "log"), "start", "-w"])
    if r.returncode:
        log = (base / "log").read_text() if (base / "log").exists() else ""
        shutil.rmtree(base, ignore_errors=True)
        raise NoPostgres("pg_ctl start failed: " + r.stderr[-300:] + log[-300:])

    def stop():
        run([pg_ctl, "-D", str(data), "-m", "immediate", "stop"])
        shutil.rmtree(base, ignore_errors=True)
    atexit.register(stop)
    os.environ.update(PGHOST=str(sock), PGPORT=str(port), PGUSER=user)
    if not _answers(dict(os.environ)):
        stop()
        raise NoPostgres("a scratch server was started but does not answer")
    _STATE["desc"] = f"scratch cluster {sock} port {port}"
    return _STATE["desc"]


def _q(s: str) -> str:
    return "'" + s.replace("'", "'\\''") + "'"
